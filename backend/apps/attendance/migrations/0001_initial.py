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
        ('students', '0001_initial'),
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttendanceStatus',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
                ('is_present', models.BooleanField(default=False)),
                ('points', models.DecimalField(decimal_places=2, default=1.00, max_digits=3)),
                ('color', models.CharField(default='#6B7280', help_text='Hex color for UI display', max_length=7)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Attendance Status',
                'verbose_name_plural': 'Attendance Statuses',
                'db_table': 'attendance_statuses',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='AttendanceSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('session_date', models.DateField()),
                ('session_number', models.PositiveIntegerField(help_text='Session number within the class (1, 2, 3, etc.)')),
                ('topic', models.CharField(max_length=200, blank=True)),
                ('description', models.TextField(blank=True)),
                ('start_time', models.TimeField(blank=True, null=True)),
                ('end_time', models.TimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('class_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_sessions', to='courses.class')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attendance_sessions_created', to='accounts.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attendance_sessions_updated', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Attendance Session',
                'verbose_name_plural': 'Attendance Sessions',
                'db_table': 'attendance_sessions',
                'ordering': ['-session_date', 'session_number'],
            },
        ),
        migrations.CreateModel(
            name='AttendanceRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('remarks', models.TextField(blank=True)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='attendance.attendancesession')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='students.student')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='attendance.attendancestatus')),
                ('recorded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attendance_records_recorded', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Attendance Record',
                'verbose_name_plural': 'Attendance Records',
                'db_table': 'attendance_records',
                'ordering': ['-recorded_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='attendancesession',
            constraint=models.UniqueConstraint(fields=('class_instance', 'session_date', 'session_number'), name='unique_class_session'),
        ),
        migrations.AddConstraint(
            model_name='attendancerecord',
            constraint=models.UniqueConstraint(fields=('session', 'student'), name='unique_session_student'),
        ),
    ]