import threading
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from base.models import Model
from updates.services.face_with_target_size import FaceNotDetectedError
from updates.services.poster import PosterTemplate


def validate_profile_photo(value):
    filesize = value.size

    if filesize > 1000 * 1024:
        raise ValidationError("The maximum file size that can be uploaded is 1MB")
    return value


# Create your models here.

class Poster(Model):
    profile_photo = models.ImageField(upload_to='profile_photos', null=True, validators=[validate_profile_photo])
    poster = models.ImageField(upload_to='posters', null=True, blank=True)
    is_generated = models.BooleanField(default=False)
    member = models.ForeignKey('makeaton.TeamMember', on_delete=models.CASCADE)
    poster_template = None
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Poster"
        verbose_name_plural = "Posters"
        abstract = True

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.pk])

    def generate_poster(self):
        if self.profile_photo and self.poster_template:
            # Get the file path of the uploaded profile photo
            profile_photo_path = self.profile_photo.path

            # Generate the poster using the poster template
            try:
                result_image = self.poster_template.place_head(profile_photo_path)

                # Save the result image to a BytesIO object
                from io import BytesIO
                from django.core.files.base import ContentFile

                img_io = BytesIO()
                result_image.save(img_io, format='PNG')
                img_content = ContentFile(img_io.getvalue(), f'poster_{self.pk}.png')
                timestamp = timezone.now().strftime('%Y%m%d%H%M%S') + uuid.uuid4().hex[:6]
                # Save the generated poster to the poster field
                self.poster.save(f'poster_{timestamp}.png', img_content)
            except FaceNotDetectedError:
                self.remarks = "Face not detected in the uploaded photo. Please upload a photo with a clear face."
            except Exception as e:
                self.remarks = str(e)
        else:
            self.remarks = "Profile photo or poster template not provided. Please upload a profile photo."
        self.save(update_fields=['poster', 'remarks'])


class IdCard(Poster):
    class Meta:
        verbose_name = "ID Card"
        verbose_name_plural = "ID Cards"


class ImParticipating(Poster):
    poster_template = PosterTemplate(
        base_image_path="updates/static/imparticipating.png",
        circle_diameter=780,
        center_coordinates=(175, 875),  # Top-left corner where the head will be placed
    )

    class Meta:
        verbose_name = "I'm Participating Poster"
        verbose_name_plural = "I'm Participating Posters"


thread_locals = threading.local()


@receiver(pre_save, sender=ImParticipating)
def detect_profile_photo_change(sender, instance, **kwargs):
    if not instance.pk:
        # New instance, so the poster needs to be generated
        thread_locals.generate_poster = True
    else:
        try:
            previous = ImParticipating.objects.get(pk=instance.pk)
            if previous.profile_photo != instance.profile_photo:
                # The profile_photo has changed
                thread_locals.generate_poster = True
            else:
                thread_locals.generate_poster = False
        except ImParticipating.DoesNotExist:
            # Instance does not exist, so the poster needs to be generated
            thread_locals.generate_poster = True


@receiver(post_save, sender=ImParticipating)
def generate_poster_post_save(sender, instance, **kwargs):
    generate_poster = getattr(thread_locals, 'generate_poster', False)
    if generate_poster and instance.profile_photo:
        # Generate the poster
        instance.generate_poster()
        # Save the poster field without triggering signals
        from django.db.models.signals import post_save
        # Temporarily disconnect the signal to avoid recursion
        post_save.disconnect(generate_poster_post_save, sender=ImParticipating)
        instance.save(update_fields=['poster'])
        # Reconnect the signal
        post_save.connect(generate_poster_post_save, sender=ImParticipating)
