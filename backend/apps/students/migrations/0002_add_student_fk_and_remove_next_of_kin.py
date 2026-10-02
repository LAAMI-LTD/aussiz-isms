# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
        ('accounts', '0002_add_email_and_timestamps'),  # Ensure accounts migration is applied first? Actually, we don't need accounts for this, but it's safe to depend on the latest accounts migration
    ]

    operations = [
        migrations.AddField(
            model_name='nextofkin',
            name='student',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='next_of_kin_entries', to='students.student'),
        ),
        migrations.RemoveField(
            model_name='student',
            name='next_of_kin',
        ),
    ]
