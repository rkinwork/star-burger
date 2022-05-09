import logging
from itertools import chain

import requests
from django.conf import settings
from geopy import distance

from .models import Address


def prepare_lookup(raw_addresses):
    raw_addresses = set(address.lower()
                        for address in raw_addresses)

    address_lookup = Address.objects.filter(
        name__in=raw_addresses,
    ).values()

    address_lookup = {address['name']: address
                      for address in address_lookup}
    for address in raw_addresses:
        if address not in address_lookup:
            address_lookup[address] = {'name': address}
            long, lat = fetch_coordinates(address)
            address_lookup[address]['long'] = long
            address_lookup[address]['lat'] = lat
            Address.objects.create(
                **address_lookup[address]
            )

    return address_lookup


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
    wrn_msg = 'problems with authorizing to {}, ' \
              'check your STAR_BURGER__YANDEX_MAP_API_KEY'.format(base_url)
    if response.status_code == 403:
        logging.warning(wrn_msg)
        return None, None

    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection'][
        'featureMember']

    if not found_places:
        logging.warning('cannot find coordinates for address: {}' % address)
        return None, None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return float(lon), float(lat)


class Distance:

    def __init__(self, address_lookup: dict):
        self._address_lookup = address_lookup

    def get_distance(self, address_a: str, address_b: str) -> [int]:
        address_a = address_a.lower()
        address_b = address_b.lower()
        address_a_coords = (self._address_lookup[address_a]['long'],
                            self._address_lookup[address_a]['lat'])
        address_b_coords = (self._address_lookup[address_b]['long'],
                            self._address_lookup[address_b]['lat'])
        if not all(chain(address_a_coords, address_b_coords)):
            return None
        return distance.distance(address_a_coords, address_b_coords).kilometers
