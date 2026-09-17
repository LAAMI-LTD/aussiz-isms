# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import uuid
import apps.students.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NextOfKin',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('relationship', models.CharField(max_length=50)),
                ('phone_number', models.CharField(max_length=20, validators=[django.core.validators.RegexValidator(regex=r'^\\+?1?\\d{9,15}$', message='Enter a valid phone number')])),
                ('email', models.EmailField(blank=True)),
                ('address', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Next of Kin',
                'verbose_name_plural': 'Next of Kin',
                'db_table': 'next_of_kin',
            },
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('student_id', models.CharField(max_length=20, unique=True, blank=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], max_length=1)),
                ('date_of_birth', models.DateField()),
                ('nationality', models.CharField(choices=[('KE', 'Kenyan'), ('UG', 'Ugandan'), ('TZ', 'Tanzanian'), ('ET', 'Ethiopian'), ('SO', 'Somali'), ('OTHER', 'Other')], default='KE', max_length=10)),
                ('national_id_passport', models.CharField(max_length=50, unique=True)),
                ('phone_number', models.CharField(max_length=20, validators=[django.core.validators.RegexValidator(regex=r'^\\+?1?\\d{9,15}$', message='Enter a valid phone number')])),
                ('email', models.EmailField()),
                ('address', models.TextField()),
                ('previous_education', models.TextField(blank=True)),
                ('english_level', models.CharField(choices=[('beginner', 'Beginner'), ('elementary', 'Elementary'), ('pre_intermediate', 'Pre-Intermediate'), ('intermediate', 'Intermediate'), ('upper_intermediate', 'Upper Intermediate'), ('advanced', 'Advanced'), ('proficiency', 'Proficiency')], max_length=20, blank=True)),
                ('previous_ielts_attempts', models.PositiveIntegerField(default=0)),
                ('target_band', models.DecimalField(decimal_places=1, max_digits=3, blank=True, null=True)),
                ('intended_destination', models.CharField(max_length=100, blank=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('deferred', 'Deferred'), ('suspended', 'Suspended'), ('completed', 'Completed'), ('withdrawn', 'Withdrawn'), ('inactive', 'Inactive')], default='active', max_length=20)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='apps.students.models.student_photo_upload_path')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='students_created', to='accounts.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='students_updated', to='accounts.user')),
                ('next_of_kin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='students', to='students.nextofkin')),
            ],
            options={
                'verbose_name': 'Student',
                'verbose_name_plural': 'Students',
                'db_table': 'students',
                'ordering': ['-date_created'],
            },
        ),
        migrations.CreateModel(
            name='StudentDocument',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('document_type', models.CharField(choices=[('id_passport', 'ID/Passport'), ('passport_photo', 'Passport Photo'), ('admission_form', 'Admission Form'), ('ielts_result', 'IELTS Result'), ('supporting_doc', 'Supporting Document'), ('other', 'Other')], max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('file', models.FileField(upload_to='student_documents/%Y/%m/%d/')),
                ('file_size', models.PositiveIntegerField(help_text='File size in bytes')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_documents', to='accounts.user')),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='students.student')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user')),
            ],
            options={
                'verbose_name': 'Student Document',
                'verbose_name_plural': 'Student Documents',
                'db_table': 'student_documents',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]