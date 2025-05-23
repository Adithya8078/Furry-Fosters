# Generated by Django 5.1.4 on 2025-01-18 10:49

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_delete_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='full_name',
            field=models.CharField(default='Unknown', help_text='Enter your full name.', max_length=150),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='phone_number',
            field=models.CharField(blank=True, help_text='Enter a valid 10-digit phone number.', max_length=10, null=True, validators=[django.core.validators.RegexValidator('^\\d{10}$', 'Only digits are allowed, and it must be exactly 10 digits.')]),
        ),
    ]
