# Generated by Django 4.2.16 on 2024-09-22 07:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('makeaton', '0015_issue_raiseanissue'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='issues', to='makeaton.team'),
        ),
    ]
