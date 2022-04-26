# Generated by Django 3.2 on 2022-04-26 11:23

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0053_auto_20220412_1249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='quantity',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='количество'),
        ),
    ]
