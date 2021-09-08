from django.core.management.base import BaseCommand, CommandError
import requests

from foodcartapp.models import Restaurant

RESTAURANT_SOURCE_URL = 'https://raw.githubusercontent.com/devmanorg/star-burger-products/master/restaurants.json'


class Command(BaseCommand):
    help = 'Базовый импорт ресторанов'

    def handle(self, *args, **options):
        res = requests.get(RESTAURANT_SOURCE_URL)
        res.raise_for_status()
        raw_restaurants = res.json()
        for raw_rest in raw_restaurants:
            _, created = Restaurant.objects.get_or_create(
                name=raw_rest['title'],
                defaults={
                    'address': raw_rest.get('address', ''),
                    'contact_phone': raw_rest.get('contact_phone', ''),
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        'Successfully added "{}"'.format(raw_rest['title'])
                    )
                )
