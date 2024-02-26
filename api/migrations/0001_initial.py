# Generated by Django 5.0.2 on 2024-02-12 18:19

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=200)),
                ('last_name', models.CharField(max_length=200)),
                ('username', models.CharField(max_length=200)),
                ('mobile', models.CharField(blank=True, max_length=20, null=True)),
                ('password', models.CharField(max_length=256, validators=[django.core.validators.MinLengthValidator(6)])),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('register_at', models.DateField(default=datetime.date.today, editable=False)),
            ],
        ),
    ]
