# Generated by Django 5.1.4 on 2025-01-03 12:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_customuser_is_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='is_approved',
        ),
    ]
