from django.db import models
from django.urls import reverse

from base.models import Model


# Create your models here.

class Poster(Model):
    profile_photo = models.ImageField(upload_to='profile_photos', null=True, blank=True)
    poster = models.ImageField(upload_to='posters', null=True, blank=True)
    is_generated = models.BooleanField(default=False)
    member = models.ForeignKey('makeaton.TeamMember', on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Poster"
        verbose_name_plural = "Posters"
        abstract = True

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.pk])


class IdCard(Poster):
    class Meta:
        verbose_name = "ID Card"
        verbose_name_plural = "ID Cards"


class ImParticipating(Poster):
    class Meta:
        verbose_name = "I'm Participating Poster"
        verbose_name_plural = "I'm Participating Posters"
