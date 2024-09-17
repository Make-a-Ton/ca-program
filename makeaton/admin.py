from django.contrib.auth.models import Group
from django.db.models import Count
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin

from base.utils import clean_mobile_number
from ca.models import CampusAmbassador
from .models import Team, TeamMember, Participants, Leaderboard
from authentication.models import User
import logging

logger = logging.getLogger('home')


class TeamMemberResource(resources.ModelResource):
    """
    CSV Import/Export for Team Members with field mappings
    """
    # Define field mappings between CSV columns and model fields
    # team_name = fields.Field(attribute='team__name',
    #                          column_name='Team Name( Ensure that other members have registered)')
    # leader_phone = fields.Field(attribute='team__leader_phone', column_name="Team Leader's Phone number")
    name = fields.Field(attribute='name', column_name='name')
    email = fields.Field(attribute='email', column_name='email')
    phone_number = fields.Field(attribute='phone_number', column_name='phone_number')
    approval_status = fields.Field(attribute='approval_status', column_name='approval_status')
    age = fields.Field(attribute='age', column_name='Age')
    gender = fields.Field(attribute='gender', column_name='Gender')
    level_of_study = fields.Field(attribute='level_of_study', column_name='Level of Study')
    college_name = fields.Field(attribute='college_name', column_name='College Name (select other if not present)')
    major_field_of_study = fields.Field(attribute='major_field_of_study',
                                        column_name='Major/Field of Study (if not present, select other)')
    year_of_study = fields.Field(attribute='year_of_study', column_name='Year of Study')
    state = fields.Field(attribute='state', column_name='State (if not from India, select other)')
    first_time_hackathon = fields.Field(attribute='first_time_hackathon', column_name='Is this you first hackathon?')
    github_profile = fields.Field(attribute='github_profile', column_name='Share your Github profile link')
    linkedin_profile = fields.Field(attribute='linkedin_profile', column_name='Provide your LinkedIn profile URL')
    t_shirt_size = fields.Field(attribute='t_shirt_size', column_name='T-shirt Size')
    applied_before = fields.Field(attribute='applied_before', column_name='Have you applied for Make-a-Ton before?')
    source = fields.Field(attribute='source', column_name='How did you hear about this event?')
    resume = fields.Field(attribute='resume',
                          column_name='Would you like to share your resume link with our sponsors for potential internships and opportunities? It\'s completely optional and won\'t be used for shortlisting.')
    coupon_code = fields.Field(attribute='coupon_code', column_name='Coupon Code (if any)')

    # Fields not included in your current model, but present in the CSV (you can add custom logic for these if needed)
    eth_address = fields.Field(attribute=None, column_name='eth_address')
    solana_address = fields.Field(attribute=None, column_name='solana_address')
    project_details = fields.Field(attribute='about',
                                   column_name='Feel free to share about the existing projects that you have built or planning to build')
    team_leader = fields.Field(attribute='team_leader', column_name='Are you the team leader?')
    diet = fields.Field(attribute='diet', column_name='Dietary Restrictions')

    class Meta:
        model = TeamMember
        # fields = ('team_name', 'leader_phone', 'name', 'email', 'phone_number', 'approval_status', 'age', 'gender',
        #           'level_of_study', 'college_name', 'major_field_of_study', 'year_of_study', 'state',
        #           'first_time_hackathon', 'github_profile', 'linkedin_profile', 't_shirt_size', 'applied_before',
        #           'source', 'resume', 'coupon_code')
        # export_order = ['team_name', 'name', 'email', 'phone_number', 'leader_phone', 'approval_status', 'age',
        #                 'gender', 'level_of_study', 'college_name', 'major_field_of_study', 'year_of_study',
        #                 'state', 'first_time_hackathon', 'github_profile', 'linkedin_profile', 't_shirt_size',
        #                 'applied_before', 'source', 'resume', 'coupon_code']

    def before_save_instance(self, instance, row, **kwargs):

        team_name = row.get('Team Name( Ensure that other members have registered)')
        leader_phone = clean_mobile_number(row.get("Team Leader's Phone number", ''))
        phone_number = clean_mobile_number(row.get('phone_number', ''))
        row['phone_number'] = phone_number
        # Check if the team exists by name and leader's phone number
        if not team_name or not leader_phone:
            logger.error(f"Invalid row: Team Name or Leader's Phone Number is empty {row}" + "\n-----" * 5)
            return
        team, created = Team.objects.get_or_create(
            name=team_name,
            leader_phone=leader_phone,
        )

        if created:
            team.conductor_track = row.get('Do you want to compete in Conductor Track (exclusive prizes)',
                                           'no').lower() == 'yes'
        instance.team = team

        coupon_code = row.get('Coupon Code (if any)', '')

        if coupon_code:
            ca = CampusAmbassador.objects.filter(coupon_code=coupon_code)
            if ca.exists():
                instance.referral = ca.first()
        college = row.get('College Name (select other if not present)', row.get('Other College Name', ''))
        if college:
            instance.college_name = college

        major = row.get('Major/Field of Study (if not present, select other)', row.get('Other Field of Study', ''))
        # If the user is a team leader, mark them as the leader
        if major:
            instance.major_field_of_study = major

        state = row.get('State (if not from India, select other)', row.get('Other State', ''))
        is_team_leader = row.get('Are you the team leader?', 'no') == 'Yes' or phone_number == leader_phone
        instance.team_leader = "Yes" if is_team_leader else "No"
        if is_team_leader:
            team.leader_phone = leader_phone
            team.save()

            name = row.get('name', '')
            email = row.get('email', '')
            if email:
                user, created = User.objects.get_or_create(
                    email=email,
                )
                if created:
                    user.full_name = name
                    user.mobile_number = phone_number
                    user.is_staff = True
                    user.is_active = True
                    user.set_password(f'makeaton@2024')
                    grp = Group.objects.get_or_create(name='Team Leader')
                    user.groups.add(grp[0])
                    user.save()

    def after_import(self, dataset, result, **kwargs):
        from makeaton.utils import cross_match_referrals
        cross_match_referrals()
        # Assign the team to the team member instance

        # instance.phone_number = clean_mobile_number(row.get('Phone Number', ''))  # Clean the phone number

    def after_save_instance(self, instance, row, **kwargs):
        leader_phone = clean_mobile_number(row.get("Team Leader's Phone number", ''))
        phone_number = clean_mobile_number(row.get('phone_number', ''))

        is_team_leader = row.get('Are you the team leader?', 'no') == 'Yes' or phone_number == leader_phone
        instance.team_leader = "Yes" if is_team_leader else "No"
        instance.save()

    def import_instance(self, instance, row, **kwargs):
        return super().import_instance(instance, row, **kwargs)

    def skip_row(self, instance, original, row, import_validation_errors=None):
        # Skip rows where the coupon code is empty
        team_name, phone_number, leader_phone = row.get(
            'Team Name( Ensure that other members have registered)'), clean_mobile_number(
            row.get("phone_number", '')), clean_mobile_number(row.get("Team Leader's Phone number", ''))
        phone_number = clean_mobile_number(phone_number)
        already_exists = TeamMember.objects.filter(phone_number=phone_number).exists()
        valid = bool(team_name) and bool(phone_number) and not already_exists and bool(leader_phone)
        if not valid:
            return True
        return super().skip_row(instance, original, row, import_validation_errors)


class TeamResource(resources.ModelResource):
    """
    CSV Import/Export for Teams
    """

    class Meta:
        model = Team


# Admin registration for Team and TeamMember
@admin.register(TeamMember)
class TeamMemberAdmin(ImportExportModelAdmin):
    resource_class = TeamMemberResource
    list_display = ('name', 'email', 'phone_number', 'team', 'team_leader')
    search_fields = ('name', 'email', 'phone_number', 'team__name')
    list_filter = ('team', 'team_leader')


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 0


@admin.register(Team)
class TeamAdmin(ImportExportModelAdmin):
    resource_class = TeamResource
    list_display = ('name', 'conductor_track', 'leader_phone', 'member_count')
    search_fields = ('name', 'leader_phone')
    inlines = [TeamMemberInline]

    def member_count(self, obj):
        return obj.members.count()

    member_count.short_description = 'Member Count'


@admin.register(Participants)
class ParticipantsAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'college_name', 'team',)
    search_fields = ('name', 'phone_number',)

    fields = (
        'name', 'email', 'phone_number', 'college_name')

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return super().get_queryset(request).filter(referral=request.user.campusambassador)
        return super().get_queryset(request)


@admin.register(Leaderboard)
class ParticipantsAdmin(admin.ModelAdmin):
    list_display = ('name', 'college_name', 'number_of_referrals')
    search_fields = ('name',)
    fields = ['name', 'college']
    # disble ordering for college
    ordering = ['id']

    def name(self, obj):
        return obj.user.full_name

    def college_name(self, obj):
        return obj.college

    def number_of_referrals(self, obj):
        return obj.referrals.count()

    def get_queryset(self, request):
        # order by number of referral and only show greater than 0
        if not request.user.is_superuser:
            return super().get_queryset(request).annotate(referral_count=Count('referrals')).filter(
                referral_count__gt=0).order_by('-referral_count')
        return super().get_queryset(request).annotate(referral_count=Count('referrals')).order_by('-referral_count')
