from django.db import models

# Create your models here.
from django.db import models

from base.models import Model
from makeaton.models import Team


class RSVP(Model):
    team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name="rsvp")
    confirmed = models.BooleanField(choices=[(True, 'Yes'), (False, 'No')], null=True, blank=True)  # RSVP status
    id_cards_generated = models.BooleanField(default=False)  # Have ID cards been generated
    posters_generated = models.BooleanField(default=False)  # Have "I'm Participating" posters been generated
    submission_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RSVP for {self.team.name}"
