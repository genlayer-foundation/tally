# Generated by Django 5.2.1 on 2025-05-22 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leaderboard', '0003_alter_contributiontypemultiplier_options_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='multiplierperiod',
            name='valid_until_after_valid_from',
        ),
        migrations.RemoveField(
            model_name='contributiontypemultiplier',
            name='multiplier',
        ),
        migrations.RemoveField(
            model_name='multiplierperiod',
            name='valid_until',
        ),
        migrations.AddField(
            model_name='multiplierperiod',
            name='description',
            field=models.CharField(blank=True, help_text='Reason for this multiplier value', max_length=255),
        ),
        migrations.AddField(
            model_name='multiplierperiod',
            name='multiplier_value',
            field=models.DecimalField(decimal_places=2, default=1.0, max_digits=5),
        ),
    ]
