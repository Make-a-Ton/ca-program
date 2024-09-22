import re
import threading
from django.contrib import admin
from django.contrib.admin import SimpleListFilter

from authentication.utils import send_email, send_bulk_email
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils.html import strip_tags

from authentication.models import User
from config import settings


def is_sha256_hash(text):
    # Check if the text contains 'sha256' substring
    if 'sha256' not in text:
        return False
    return True


class HasSendMailFilter(SimpleListFilter):
    title = 'Send Mail'  # The title shown in the filter dropdown
    parameter_name = 'send_mail'  # The URL parameter for the filter

    def lookups(self, request, model_admin):
        # Defines the two filter options ('Yes' and 'No')
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        # Filters based on whether the team has a leader or not
        if self.value() == 'yes':
            return queryset.exclude(password='')
        elif self.value() == 'no':
            return queryset.filter(password='')
        return queryset


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'mobile_number', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups', HasSendMailFilter)
    search_fields = ('email', 'full_name', 'mobile_number')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'mobile_number',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    actions = ('set_password',)

    def save_model(self, request, obj, form, change):
        # Get the password from the form if provided
        password = form.cleaned_data.get('password')
        if password:
            if not is_sha256_hash(password):
                obj.set_password(password)
            else:
                obj.password = password
        elif 'password' in form.changed_data:
            # If password field is modified but no new password is provided, ignore the password field
            form.cleaned_data.pop('password', None)

        super().save_model(request, obj, form, change)

    def set_password(self, request, queryset):
        threading.Thread(target=send_bulk_email, args=(queryset,)).start()

        self.message_user(request, 'Emails with password will be sent to the selected users.')
