from django.db import models

from authentication.models import User
from base.models import Model
from ca.models import CampusAmbassador


# Create your models here.


class Team(Model):
    name = models.CharField(max_length=255)
    conductor_track = models.BooleanField(default=False)  # Whether the team is competing in the Conductor Track
    why_should_select_you = models.TextField(
        default="Describe your team, whether you are beginners or pros aiming to win big! Don't use GPT for this")  # Details about projects built or planned
    leader_phone = models.CharField(max_length=15)  # Cleaned phone number of the team leader
    leader = models.ForeignKey('authentication.User', on_delete=models.RESTRICT,
                               related_name='team_leader', blank=True, null=True)  # Team leader
    ## Hardware or Software default is Software
    track = models.CharField(max_length=255, default='Software',
                             choices=(('Software', 'Software'), ('Hardware', 'Hardware')))
    level = models.CharField(max_length=255, blank=True, null=True, choices=(
        ('beginner', 'beginner'), ('intermediate', 'intermediate'), ('advanced', 'advanced')))  # Level of expertise
    llm_review = models.TextField(blank=True, null=True)  # Review by the LLM
    llm_score = models.FloatField(default=0)  # Score given by the LLM

    def __str__(self):
        return self.name

    @property
    def members(self):
        return self.teammember_set.all()

    @property
    def member_count(self):
        return self.members.count()


class TeamMember(Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')  # Links the member to a team
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)  # Cleaned phone number
    approval_status = models.CharField(max_length=50)  # Approval status of the application
    age = models.IntegerField(blank=True, null=True)  # Age of the participant
    gender = models.CharField(max_length=50, blank=True, null=True)  # Gender of the participant
    level_of_study = models.CharField(max_length=100)  # Level of study (e.g., undergraduate, postgraduate)
    college_name = models.CharField(max_length=255)  # College or university name
    major_field_of_study = models.CharField(max_length=255)  # Major or field of study
    year_of_study = models.IntegerField(blank=True, null=True)  # Year of study
    state = models.CharField(max_length=100, blank=True, null=True)  # State of residence (if applicable)
    first_time_hackathon = models.CharField(max_length=50, blank=True, null=True, choices=(
        ('Yes', 'Yes'), ('No', 'No')))  # Whether this is the participant's first hackathon
    github_profile = models.URLField(blank=True, null=True)  # Link to GitHub profile
    linkedin_profile = models.URLField(blank=True, null=True)  # Link to LinkedIn profile
    t_shirt_size = models.CharField(max_length=10, blank=True, null=True)  # T-shirt size
    applied_before = models.CharField(max_length=255, blank=True, null=True, choices=(
        ('Yes', 'Yes'), ('No', 'No')))  # Whether the participant has applied before
    source = models.CharField(max_length=255, blank=True, null=True)  # How they heard about Make-a-Ton
    resume = models.URLField(blank=True, null=True)  # Link to resume
    team_leader = models.CharField(max_length=255, blank=True, null=True,
                                   choices=(('Yes', 'Yes'), ('No', 'No')))  # Whether the participant is a team leader
    coupon_code = models.CharField(max_length=255, blank=True, null=True)  #
    referral = models.ForeignKey('ca.CampusAmbassador', on_delete=models.RESTRICT, blank=True,
                                 null=True, related_name='referrals')  # Referral from a Campus Ambassador
    about = models.TextField(blank=True, null=True)  # About the participant
    diet = models.CharField(max_length=255, blank=True, null=True,
                            choices=(('Veg', 'Veg'), ('Non-Veg', 'Non-Veg')))  # Dietary preference
    starred_conductor = models.BooleanField(default=False)  # Whether the participant has started the Conductor Track
    last_start_checked = models.DateTimeField(blank=True, null=True)  # Last time the start was checked
    leader_phone_number = models.CharField(max_length=15, blank=True,
                                           null=True)  # Cleaned phone number of the team leader
    level = models.CharField(max_length=255, blank=True, null=True, choices=(
        ('beginner', 'beginner'), ('intermediate', 'intermediate'), ('advanced', 'advanced')))  # Level of expertise

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"
        ordering = ('team',)


class Participants(TeamMember):
    class Meta:
        verbose_name = "Participant"
        verbose_name_plural = "Participants"
        proxy = True


class Leaderboard(CampusAmbassador):
    class Meta:
        verbose_name = "Leaderboard"
        verbose_name_plural = "Leaderboard"
        proxy = True


class MyTeam(Team):
    class Meta:
        verbose_name = "My Team"
        verbose_name_plural = "My Team"
        proxy = True


class TeamLeader(User):
    class Meta:
        verbose_name = "Team Leader"
        verbose_name_plural = "Team Leaders"
        proxy = True


class MyTeamMember(TeamMember):
    class Meta:
        verbose_name = "My Team Member"
        verbose_name_plural = "My Team Members"
        proxy = True


class Issue(Model):
    title = models.CharField(max_length=255)
    description = models.TextField(
        default='Explain the issue in detail below\n\n\n\n\nMention the suggestions to be implemented below')
    status = models.CharField(max_length=50, default='Pending',
                              choices=(('Pending', 'Pending'), ('Resolved', 'Resolved'), ('Rejected', 'Rejected')))
    response = models.TextField(blank=True, null=True)
    raised_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='issues')
    team = models.ForeignKey(Team, on_delete=models.RESTRICT, related_name='issues', blank=True, null=True)

    def __str__(self):
        return self.title


class RaiseAnIssue(Issue):
    class Meta:
        verbose_name = "Issue Raised"
        verbose_name_plural = "Issues Raised"
        proxy = True


class TeamLlmReview(Team):
    class Meta:
        verbose_name = "Team LLM Review"
        verbose_name_plural = "Team LLM Reviews"
        proxy = True


class TeamRsvp(Team):
    class Meta:
        verbose_name = "Team RSVP"
        verbose_name_plural = "Team RSVPs"
        proxy = True
