# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import migrations


def create_initial_attendance_statuses(apps, schema_editor):
    """Create initial attendance statuses."""
    AttendanceStatus = apps.get_model('attendance', 'AttendanceStatus')

    statuses = [
        {
            'code': 'P',
            'name': 'Present',
            'description': 'Student is present for the session',
            'is_present': True,
            'points': 1.00,
            'color': '#10B981',  # Green
        },
        {
            'code': 'A',
            'name': 'Absent',
            'description': 'Student is absent from the session',
            'is_present': False,
            'points': 0.00,
            'color': '#EF4444',  # Red
        },
        {
            'code': 'L',
            'name': 'Late',
            'description': 'Student arrived late for the session',
            'is_present': True,
            'points': 0.50,
            'color': '#F59E0B',  # Amber/Yellow
        },
        {
            'code': 'E',
            'name': 'Excused',
            'description': 'Student is excused from the session',
            'is_present': False,
            'points': 0.00,
            'color': '#6B7280',  # Gray
        },
    ]

    for status_data in statuses:
        AttendanceStatus.objects.get_or_create(
            code=status_data['code'],
            defaults=status_data
        )


def reverse_initial_attendance_statuses(apps, schema_editor):
    """Remove initial attendance statuses."""
    AttendanceStatus = apps.get_model('attendance', 'AttendanceStatus')
    AttendanceStatus.objects.filter(code__in=['P', 'A', 'L', 'E']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_remove_attendancerecord_unique_session_student_and_more'),
    ]

    operations = [
        migrations.RunPython(
            create_initial_attendance_statuses,
            reverse_initial_attendance_statuses
        ),
    ]