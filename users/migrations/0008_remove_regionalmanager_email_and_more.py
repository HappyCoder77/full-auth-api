# Generated by Django 5.0.6 on 2024-09-27 11:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_rename_sex_baseprofile_gender'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='regionalmanager',
            name='email',
        ),
        migrations.RemoveField(
            model_name='regionalmanager',
            name='user',
        ),
        migrations.AddField(
            model_name='baseprofile',
            name='email',
            field=models.EmailField(default='saul@ejemplo.com', max_length=254, unique=True, verbose_name='Email field'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='baseprofile',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]