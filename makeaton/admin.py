import logging
import threading

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.models import Group
from django.db.models import Count, Q
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin

from authentication.models import User
from base.utils import clean_mobile_number
from ca.models import CampusAmbassador
from .models import Team, TeamMember, Participants, Leaderboard, MyTeam, TeamLeader, MyTeamMember, Issue, RaiseAnIssue, \
    TeamLlmReview
from .utils import bulk_started_status_check, send_rsvp_email

logger = logging.getLogger('home')

common_exclude = ['is_active', 'deleted', 'deleted_at', 'deleted_by', 'created_at', 'updated_at']


class TeamMemberResource(resources.ModelResource):
    """
    CSV Import/Export for Team Members with field mappings
    """
    # Define field mappings between CSV columns and model fields
    # team_name = fields.Field(attribute='team__name',
    #                          column_name='Team Name( Ensure that other members have registered with same team name)')
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

        team_name = row.get('Team Name( Ensure that other members have registered with same team name)')
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
            leader = User.objects.filter(mobile_number__contains=leader_phone.strip('+'))
            if leader.exists():
                team.leader = leader.first()
                team.save()
        instance.team = team
        instance.phone_number = phone_number

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
                    grp = Group.objects.get_or_create(name='Team Leader')
                    user.groups.add(grp[0])
                    user.save()
                    team.leader = user
                    team.save()

    def after_import(self, dataset, result, **kwargs):
        from makeaton.utils import cross_match_referrals, update_leader_phone_numbers
        threading.Thread(target=cross_match_referrals).start()
        threading.Thread(target=update_leader_phone_numbers, args=(dataset,)).start()

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
            'Team Name( Ensure that other members have registered with same team name)'), clean_mobile_number(
            row.get("phone_number", '')), clean_mobile_number(row.get("Team Leader's Phone number", ''))
        phone_number = clean_mobile_number(phone_number)
        already_exists = TeamMember.objects.filter(phone_number__contains=phone_number.strip('+')).exists()

        valid = bool(team_name) and bool(phone_number) and not already_exists and bool(
            leader_phone) and leader_phone != '+91'
        if not valid:
            logger.error(
                f"Invalid row: {row}" + "\n-----" * 2 + f"{already_exists = } {valid = } {team_name = } {phone_number = } {leader_phone = }")
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
    list_display = (
        'name', 'email', 'phone_number', 'team', 'id_card', 'track', 'team_leader', 'leader_phone_number',
        'starred_conductor', 'level',)
    search_fields = ('name', 'email', 'phone_number', 'team__name')
    list_filter = (
        'team', 'team_leader', 'starred_conductor', 'referral', 'level', 'team__approved', 'id_card',)

    actions = ['check_stars', 'add_id_card', 'generate_user']

    def check_stars(self, request, queryset):
        threading.Thread(target=bulk_started_status_check, args=(queryset,)).start()
        # bulk_started_status_check(queryset)

    def add_id_card(self, request, queryset):
        queryset.update(id_card=True)

    def track(self, obj):
        return obj.team.track

    def generate_user(self, request, queryset):
        for member in queryset:
            if not User.objects.filter(email=member.email).exists():
                user = User.objects.create(
                    full_name=member.name,
                    email=member.email,
                    mobile_number=member.phone_number,
                    is_staff=True,
                    is_active=True
                )
                grp = Group.objects.get_or_create(name="Team Member")
                grp[0].user_set.add(user)
                member.user = user
                member.save()


class TeamMemberInline(admin.StackedInline):
    model = TeamMember
    extra = 0
    exclude = ['is_active', 'is_staff', 'is_superuser', 'groups', 'deleted', 'deleted_at', 'deleted_by', 'created_at',
               'updated_at']


class MyTeamMemberInline(admin.StackedInline):
    model = MyTeamMember
    extra = 0
    exclude = ['is_active', 'is_staff', 'is_superuser', 'groups', 'deleted', 'deleted_at', 'deleted_by', 'created_at',
               'updated_at']


class HasLeaderFilter(SimpleListFilter):
    title = 'Has Leader'  # The title shown in the filter dropdown
    parameter_name = 'has_leader'  # The URL parameter for the filter

    def lookups(self, request, model_admin):
        # Defines the two filter options ('Yes' and 'No')
        return (
            ('yes', 'Has Leader'),
            ('no', 'No Leader'),
        )

    def queryset(self, request, queryset):
        # Filters based on whether the team has a leader or not
        if self.value() == 'yes':
            return queryset.exclude(leader__isnull=True)
        elif self.value() == 'no':
            return queryset.filter(leader__isnull=True)
        return queryset


@admin.register(Team)
class TeamAdmin(ImportExportModelAdmin):
    resource_class = TeamResource
    list_display = ('name', 'conductor_track', 'leader_phone', 'member_count', 'approved')
    search_fields = ('name', 'leader_phone')
    inlines = [TeamMemberInline]
    list_filter = (HasLeaderFilter, 'conductor_track', 'approved', 'rsvp')  # Adding the custom filter here

    actions = ['approve_teams', 'disapprove_teams', 'rsvp_mail', 'send_rsvp_email']

    def member_count(self, obj):
        return obj.members.count()

    member_count.short_description = 'Member Count'

    def refresh_leaders(self, request, queryset):
        count_success = 0
        count_fail = 0
        queryset = queryset.order_by('id')
        for team in queryset:
            conductor_track = all([member.starred_conductor for member in team.members.all()])
            if conductor_track:
                # print(f"Conductor Track: {team.name}",team.conductor_track, conductor_track)
                team.conductor_track = True
                team.save()
            team_leader = User.objects.filter(mobile_number__contains=team.leader_phone.strip('+'))
            if team_leader.exists():
                count_success += 1
                team.leader = team_leader.first()
                team.save()
            if team_leader.exists() and Team.objects.filter(
                    leader_phone__contains=team_leader.first().mobile_number.strip('+')).count() > 1:
                dup_teams = Team.objects.filter(
                    leader_phone__contains=team_leader.first().mobile_number.strip('+')).exclude(id=team.id)
                all_members = TeamMember.objects.filter(team__id__in=dup_teams.values_list('id', flat=True))
                for member in all_members:
                    member.team = team
                    member.save()
                for issues in Issue.objects.filter(team__id__in=dup_teams.values_list('id', flat=True)):
                    issues.team = team
                    issues.save()
                try:
                    dup_teams.delete()
                except Exception as e:
                    count_fail += 1
                    logger.error(f"Error in deleting duplicate teams({[t.name for t in dup_teams]}): {e}")
            # all_members = TeamMember.objects.filter(team__leader_phone__contains=team.leader_phone.strip('+'))
            # for member in all_members:
            #     member.team = team
            #     member.save()
            #     print(member.name)

        self.message_user(request, f"Successfully updated {count_success} teams. Failed to update {count_fail} teams.")

    def approve_teams(self, request, queryset):
        approved_grp = Group.objects.get_or_create(name='Approved Team')[0]
        for team in queryset:
            team.approved = True
            team.save()
            team.leader.groups.add(approved_grp)
            team.leader.save()
            for member in team.members.all():
                member.approval_status = 'approved'
                member.save()

    def disapprove_teams(self, request, queryset):
        approved_grp = Group.objects.get_or_create(name='Approved Team')[0]
        queryset = queryset.filter(approved=True)
        for team in queryset:
            team.approved = False
            team.save()
            team.leader.groups.remove(approved_grp)
            team.leader.save()
            for member in team.members.all():
                member.approval_status = 'Declined'
                member.save()

    def send_rsvp_email(self, request, queryset):
        queryset = queryset.filter(approved=True)
        threading.Thread(target=send_rsvp_email, args=(queryset,)).start()

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            member_no=Count('members')
        ).order_by('-member_no')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Participants)
class ParticipantsAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'college_name', 'team', 'starred_conductor')
    search_fields = ('name', 'phone_number',)
    list_filter = ['starred_conductor']

    fields = (
        'name', 'email', 'phone_number', 'college_name')

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return super().get_queryset(request).filter(referral=request.user.campusambassador)
        return super().get_queryset(request)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('rank', 'name', 'college_name',)
    fields = ['name', 'college']

    def name(self, obj):
        return obj.user.full_name

    def college_name(self, obj):
        return obj.college

    def get_queryset(self, request):
        # Filter Campus Ambassadors who have referrals, and among the referred members, only include those who have starred_conductor=True
        queryset = super().get_queryset(request).annotate(
            referral_count=Count('referrals', filter=Q(referrals__starred_conductor=True))
        ).filter(referral_count__gt=0).order_by('-referral_count')
        # Save the queryset so it can be used in the rank calculation
        self.rank_cache = queryset
        return queryset

    def rank(self, obj):
        # Rank is based on the queryset ordering
        for idx, item in enumerate(self.rank_cache, start=1):
            if item == obj:
                return idx
        return None

    rank.short_description = 'Rank'


@admin.register(MyTeam)
class MyTeamAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'conductor_track', 'leader_phone', 'track', 'approval_status'
    )
    exclude = common_exclude + ['llm_review', 'llm_score', 'level', 'approved']

    inlines = [MyTeamMemberInline]
    readonly_fields = ['leader', 'leader_phone', 'name', 'conductor_track', 'why_should_select_you', 'track']

    def approval_status(self, obj):
        return "Approved" if obj.approved else "Declined"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(Q(leader=request.user) | Q(members__user=request.user)).distinct()

    # def has_change_permission(self, request, obj=None):
    #   return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(MyTeamMember)
class MyTeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'starred_conductor')
    exclude = common_exclude + ['approval_status', 'level']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(Q(team__leader=request.user) | Q(team__members__user=request.user)).distinct()

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


class TeamInline(admin.StackedInline):
    model = Team
    extra = 0
    exclude = ['is_active', 'is_staff', 'is_superuser', 'groups', 'deleted', 'deleted_at', 'deleted_by', 'created_at',
               'updated_at']


@admin.register(TeamLeader)
class TeamLeaderAdmin(admin.ModelAdmin):
    list_display = ('mobile_number', 'full_name', 'email', 'team_count')

    inlines = [TeamInline]
    exclude = ['is_active', 'is_staff', 'is_superuser', 'groups', 'deleted', 'deleted_at', 'deleted_by', 'created_at',
               'updated_at', 'password', 'id', 'user_permissions', 'last_login', 'date_joined']

    def get_queryset(self, request):
        return Group.objects.get(name='Team Leader').user_set.all().annotate(
            team_count=Count('team_leader')
        ).order_by('-team_count')

    def team_count(self, obj):
        return Team.objects.filter(leader=obj).count()

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    exclude = common_exclude
    list_display = ('title', 'status', 'response', 'team')
    list_filter = ('status', 'team',)
    search_fields = (
        'title', 'description', 'raised_by__full_name', 'team__name', 'raised_by__email', 'raised_by__mobile_number')

    def get_readonly_fields(self, request, obj=None):
        return ('raised_by', 'title', 'description', 'team')

    def has_add_permission(self, request):
        return False


@admin.register(RaiseAnIssue)
class RaiseAnIssueAdmin(admin.ModelAdmin):
    exclude = common_exclude + ['team']
    list_display = ('title', 'status', "response",)
    list_filter = ('status',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(raised_by=request.user)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ('response', 'status', 'raised_by')
        return ('raised_by',)

    def has_change_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:  # Only set the raised_by field when creating a new object
            obj.raised_by = request.user
            obj.team = Team.objects.filter(leader=request.user).first()
        super().save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'raised_by']
        return fields


class TeamLLMResource(resources.ModelResource):
    leader_phone = fields.Field(attribute='leader_phone', column_name='Team Leader Phone Number')
    level = fields.Field(attribute='level', column_name='Classification')
    team_score = fields.Field(attribute='llm_score', column_name='Score')
    llm_review = fields.Field(attribute='llm_review', column_name='Reason')

    class Meta:
        model = Team
        fields = ('leader_phone', 'level', 'llm_score', 'llm_review')
        export_order = ('leader_phone', 'level', 'llm_score', 'llm_review')
        import_id_fields = ('leader_phone',)  # This ensures that the import identifies records by leader_phone
        skip_unchanged = True  # Skips records that haven’t changed
        report_skipped = True  # Reports any records that were skipped due to no changes
        update_or_create = False  # Only update existing records, do not create new ones

    def get_instance(self, instance_loader, row):
        """
        Overrides the default get_instance method to query using icontains for leader_phone
        """
        # Retrieve the value from the CSV row for 'Team Leader Phone Number'
        leader_phone = row.get('Team Leader Phone Number')

        # Use icontains to match team by leader_phone (partial match, case-insensitive)
        return Team.objects.filter(leader_phone__icontains=leader_phone).first()

    def before_import_row(self, row, **kwargs):
        """
        This method is called before each row is imported.
        You can add custom validation logic here if needed.
        """
        pass


@admin.register(TeamLlmReview)
class TeamLlmReviewAdmin(ImportExportModelAdmin):
    resource_class = TeamLLMResource
    list_display = ('name', 'leader_phone', 'track', 'level', 'llm_score')
    search_fields = ('name', 'leader_phone')
