# Generated by Django 4.2.16 on 2024-10-05 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('updates', '0002_idcard_remarks_imparticipating_remarks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='idcard',
            name='profile_photo',
            field=models.ImageField(null=True, upload_to='profile_photos'),
        ),
        migrations.AlterField(
            model_name='imparticipating',
            name='profile_photo',
            field=models.ImageField(null=True, upload_to='profile_photos'),
        ),
    ]
