from django.contrib import admin
from django.contrib.auth.models import Group
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field

from authentication.models import User
from base.utils import clean_mobile_number
from makeaton.models import TeamMember
from .models import CampusAmbassador


# Define a resource class for import/export functionality
class CampusAmbassadorResource(resources.ModelResource):
    """
    Timestamp
    Email address
    Primary Email Address
    Full Name
    Phone Number
    Name of Institution
    Name of course
    Year of Study
    Coupon ID
    """

    coupon_code = Field(attribute='coupon_code', column_name='Coupon ID')
    year = Field(attribute='year', column_name='Year of Study')
    course = Field(attribute='course', column_name='Name of course')
    college = Field(attribute='college', column_name='Name of Institution')

    class Meta:
        model = CampusAmbassador

    def before_save_instance(self, instance, row, **kwargs):
        # Get the necessary fields from the CSV row
        email = row.get('Primary Email Address')
        full_name = row.get('Full Name')
        phone_number = clean_mobile_number(row.get('Phone Number'))
        coupon_code = row.get('Coupon ID')
        try:
            # Use `get_or_create` to fetch the user or create a new one
            user, created = User.objects.get_or_create(
                email=email,
                mobile_number=phone_number,
                defaults={
                    'full_name': full_name,
                    'mobile_number': phone_number,
                    "is_active": True,
                    "is_staff": True,
                }
            )
            if created:
                user.set_password(f"{coupon_code}{phone_number[-4:]}")
                user.save()
                grp = Group.objects.get_or_create(name='Campus Ambassador')
                user.groups.add(grp[0])

                # Assign the fetched or created user to the CampusAmbassador instance
            instance.user = user
        except Exception as e:
            print(e)

    def skip_row(self, instance, original, row, import_validation_errors=None):
        # Skip rows where the coupon code is empty
        already_exists = CampusAmbassador.objects.filter(coupon_code=row.get('Coupon ID')).exists()
        return super().skip_row(instance, original, row, import_validation_errors) or already_exists


# Define the admin class for filters, search, and import/export
@admin.register(CampusAmbassador)
class CampusAmbassadorAdmin(ImportExportModelAdmin):
    resource_class = CampusAmbassadorResource

    # Define which fields to display in the list view
    list_display = (
        'user',
        'college',
        'course',
        'year',
        'coupon_code',
        'referral',
        'mobile_number'
    )

    # Add search functionality for user and college fields
    search_fields = (
        'user__email',
        'user__full_name',
        'user__mobile_number',
        'college',
        'coupon_code'
    )

    # Add filter functionality for these fields
    list_filter = (
        'college',
        'course',
        'year'
    )

    def referral(self, obj):
        return obj.referrals.count()

    def mobile_number(self, obj):
        return obj.user.mobile_number
