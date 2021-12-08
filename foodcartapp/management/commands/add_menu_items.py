from django.core.management.base import BaseCommand

from foodcartapp.models import Restaurant, Product, RestaurantMenuItem


class Command(BaseCommand):
    help = 'Создание случайного меню'

    def handle(self, *args, **options):
        for restaurant in Restaurant.objects.all():
            for random_product in Product.objects.order_by('?').all()[:2]:
                _, created = RestaurantMenuItem.objects.get_or_create(
                    restaurant=restaurant,
                    product=random_product,
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            'Successfully added "{}" to {}'.format(
                                random_product.name,
                                restaurant.name,
                            )
                        )
                    )
