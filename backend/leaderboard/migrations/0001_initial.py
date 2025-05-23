# Generated by Django 5.2.1 on 2025-05-21 14:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contributions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaderboardEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('total_points', models.PositiveIntegerField(default=0)),
                ('rank', models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Leaderboard entries',
                'ordering': ['-total_points', 'user__name'],
            },
        ),
        migrations.CreateModel(
            name='ContributionTypeMultiplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('multiplier', models.DecimalField(decimal_places=2, default=1.0, max_digits=5)),
                ('is_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('contribution_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='multipliers', to='contributions.contributiontype')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
