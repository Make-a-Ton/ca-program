from django.db import models

from base.models import Model


class CampusAmbassador(Model):
    """
    Campus Ambassador model
    """
    user = models.OneToOneField("authentication.User", on_delete=models.RESTRICT)
    college = models.CharField(max_length=255)
    course = models.CharField(max_length=255)
    year = models.IntegerField()
    coupon_code = models.CharField(max_length=255)

    def __str__(self):
        return self.user.full_name + " - " + self.coupon_code
