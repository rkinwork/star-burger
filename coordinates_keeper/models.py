import logging
from typing import Iterable

from django.db import models
from django.conf import settings
from geopy import distance
import requests


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


class Distance:

    def __init__(self, addresses_raw: Iterable[str]):
        addresses_raw = [addr.lower() for addr in addresses_raw]
        self._address_lookup = self._prep_addresses(addresses_raw)

    def _prep_addresses(self, raw_addresses):
        address_lookup = Address.objects.filter(name__in=raw_addresses).values()
        address_lookup = {addr['name']: addr for addr in address_lookup}
        for r_a in raw_addresses:
            if r_a not in address_lookup:
                address_lookup[r_a] = {'name': r_a}
                address_lookup[r_a]['long'], address_lookup[r_a]['lat'] = self.fetch_coordinates(r_a)
                if all([address_lookup[r_a]['long'], address_lookup[r_a]['lat']]):
                    # create only if we have coordinates
                    Address.objects.create(**address_lookup[r_a])

        return address_lookup

    def get_distance(self, address_a: str, address_b: str) -> [int]:
        address_a = address_a.lower()
        address_b = address_b.lower()
        address_a_coords = self._address_lookup[address_a]['long'], self._address_lookup[address_a]['lat']
        address_b_coords = self._address_lookup[address_b]['long'], self._address_lookup[address_b]['lat']
        if not all((address_a_coords, address_b_coords)):
            return None
        return distance.distance(address_a_coords, address_b_coords).kilometers

    @staticmethod
    def fetch_coordinates(address) -> tuple[float, float] | tuple[None, None]:
        if not settings.YANDEX_MAP_API_KEY:
            logging.warning('STAR_BURGER__YANDEX_MAP_API_KEY has not been set')
            return None, None

        base_url = "https://geocode-maps.yandex.ru/1.x"
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": settings.YANDEX_MAP_API_KEY,
            "format": "json",
        })
        if response.status_code == 403:
            logging.warning(
                'problems with authorizing to {}, check your STAR_BURGER__YANDEX_MAP_API_KEY'.format(base_url))
            return None, None

        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']

        if not found_places:
            logging.warning('cannot find coordinates for address: {}'.format(address))
            return None, None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        return float(lon), float(lat)
