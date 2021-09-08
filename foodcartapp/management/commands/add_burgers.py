from urllib.parse import urljoin
from io import BytesIO

from django.core.management.base import BaseCommand, CommandError
from django.core.files.images import ImageFile
import requests

from foodcartapp.models import Product, ProductCategory

MEDIA_GH_URL = 'https://github.com/devmanorg/star-burger-products/tree/master/media'
MEDIA_GH_RAW_URL = 'https://raw.githubusercontent.com/devmanorg/star-burger-products/master/media/'
BURGERS_JSON = 'https://raw.githubusercontent.com/devmanorg/star-burger-products/master/products.json'


class Command(BaseCommand):
    help = 'Upload burgers'

    def handle(self, *args, **options):
        with requests.get(BURGERS_JSON) as req:
            if not req.ok:
                raise CommandError(
                    f'Problems with accessing {options["gh_url"]}'
                )
            burgers = req.json()

        for burger in burgers:
            category, _ = ProductCategory.objects.get_or_create(
                name=burger['type']
            )
            product, created = Product.objects.get_or_create(
                name=burger['title'],
                defaults={
                    'category': category,
                    'price': burger['price'],
                    'description': burger['description'],
                }

            )
            if not created:
                continue

            with requests.get(urljoin(MEDIA_GH_RAW_URL, burger['img'])) as r:
                if not r.ok:
                    continue
                img_bin = BytesIO(r.content)
                img_bin.seek(0)

            product.image.save(name=burger['img'],
                               content=ImageFile(img_bin),
                               save=True)
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully added "{}"'.format(burger['title'])
                )
            )
