# Generated by Django 3.2 on 2022-04-12 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coordinates_keeper', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='update_ts',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
