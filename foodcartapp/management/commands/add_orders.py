from django.core.management.base import BaseCommand
from random import choices, randint

from foodcartapp.models import Order, OrderItem, Product


class Command(BaseCommand):
    help = 'Создание n случайных заказов'

    def add_arguments(self, parser):
        parser.add_argument('n', type=int, default=3, nargs='?', help='number of orders to add')

    def handle(self, *args, **options):
        products = tuple(Product.objects.available().all())
        last_order = Order.objects.last()
        max_id = last_order.id if last_order else 1
        for i in range(max_id, max_id + options['n']):
            order = Order.objects.create(address=f'address_{i}',
                                         firstname=f'{i}_customer_name',
                                         lastname=f'{i}_customer_last_name',
                                         phonenumber=f'+7{i}031000000',
                                         )
            for product in choices(products, k=3):
                OrderItem.objects.create(product_id=product,
                                         order=order,
                                         quantity=randint(1, 3),
                                         item_price=product.price,
                                         )

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully added {} orders'.format(
                    options['n'],
                )
            )
        )
