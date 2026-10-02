# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Course Category',
                'verbose_name_plural': 'Course Categories',
                'db_table': 'course_categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('course_code', models.CharField(max_length=20, unique=True, help_text='e.g., IELTS-001, COMP-001')),
                ('name', models.CharField(max_length=200)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='courses.coursecategory')),
                ('description', models.TextField()),
                ('course_type', models.CharField(choices=[('ielts', 'IELTS Preparation'), ('computer_package', 'Computer Package')], max_length=20)),
                ('duration_weeks', models.PositiveIntegerField(help_text='Duration in weeks')),
                ('duration_hours', models.PositiveIntegerField(help_text='Total hours')),
                ('delivery_mode', models.CharField(choices=[('in_person', 'In-Person'), ('online', 'Online'), ('hybrid', 'Hybrid')], default='in_person', max_length=20)),
                ('fee', models.DecimalField(decimal_places=2, help_text='Course fee in KES', max_digits=10)),
                ('registration_fee', models.DecimalField(decimal_places=2, default=0, help_text='Registration fee in KES', max_digits=10)),
                ('minimum_students', models.PositiveIntegerField(default=1, help_text='Minimum students to run course')),
                ('maximum_students', models.PositiveIntegerField(help_text='Maximum students allowed')),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('maintenance', 'Under Maintenance')], default='active', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses_created', to='accounts.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses_updated', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Course',
                'verbose_name_plural': 'Courses',
                'db_table': 'courses',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classes', to='courses.course')),
                ('name', models.CharField(max_length=100, help_text='e.g., IELTS Morning Sep 2026')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('planned', 'Planned'), ('ongoing', 'Ongoing'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('on_hold', 'On Hold')], default='planned', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='classes_created', to='accounts.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='classes_updated', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Class',
                'verbose_name_plural': 'Classes',
                'db_table': 'classes',
                'ordering': ['-start_date'],
            },
        ),
    ]