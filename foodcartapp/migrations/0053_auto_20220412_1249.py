# Generated by Django 3.2 on 2022-04-12 12:49

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0052_auto_20220412_1239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='called_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='подтверждён в'),
        ),
        migrations.AlterField(
            model_name='order',
            name='created_at',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='создан в'),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivered_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='доставлен в'),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('Ne', 'Новый заказ'), ('Pr', 'Обработанный'), ('Fi', 'Завершенный')], db_index=True, default='Ne', max_length=2, verbose_name='статус'),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('NA', 'Не известно'), ('ON', 'Электронно'), ('CH', 'Наличностью')], db_index=True, default='NA', max_length=2, verbose_name='метод оплаты'),
        ),
    ]
