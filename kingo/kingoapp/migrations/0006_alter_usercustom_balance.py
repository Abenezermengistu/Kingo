# Generated by Django 5.2 on 2025-04-12 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kingoapp', '0005_usercustom_telegram_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercustom',
            name='balance',
            field=models.DecimalField(decimal_places=2, default=100.0, max_digits=10),
        ),
    ]
