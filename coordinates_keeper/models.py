from django.db import models


class Address(models.Model):
    name = models.CharField(
        'адрес',
        max_length=100,
        unique=True,
    )
    lat = models.FloatField('Широта')
    long = models.FloatField('Долгота')
    update_ts = models.DateTimeField(auto_now_add=True,
                                     blank=True,
                                     db_index=True,
                                     verbose_name='изменён в',
                                     )

    class Meta:
        verbose_name = 'адрес'
        verbose_name_plural = 'адреса'

    def __str__(self):
        return f'{self.name} {self.lat} {self.long}'
