# Generated by Django 5.0.6 on 2024-09-26 12:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_baseprofile_regionalmanager'),
    ]

    operations = [
        migrations.RenameField(
            model_name='baseprofile',
            old_name='sex',
            new_name='gender',
        ),
    ]
