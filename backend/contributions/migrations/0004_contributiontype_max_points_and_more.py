# Generated by Django 5.2.1 on 2025-05-23 12:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contributions', '0003_contribution_contribution_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='contributiontype',
            name='max_points',
            field=models.PositiveIntegerField(default=100, help_text='Maximum points allowed for this contribution type'),
        ),
        migrations.AddField(
            model_name='contributiontype',
            name='min_points',
            field=models.PositiveIntegerField(default=0, help_text='Minimum points allowed for this contribution type'),
        ),
    ]
