# Generated by Django 4.2.16 on 2024-09-18 12:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
        ('makeaton', '0012_team_leader'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamLeader',
            fields=[
            ],
            options={
                'verbose_name': 'Team Leader',
                'verbose_name_plural': 'Team Leaders',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('authentication.user',),
        ),
    ]
