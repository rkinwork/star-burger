from django.core.management.base import BaseCommand
from random import choices, randint

from foodcartapp.models import Order, OrderItem, RestaurantMenuItem


class Command(BaseCommand):
    help = 'Создание n случайных заказов'

    def add_arguments(self, parser):
        parser.add_argument('n', type=int, default=3, nargs='?', help='number of orders to add')

    def handle(self, *args, **options):
        m_items = RestaurantMenuItem.objects.filter(availability=True).all()
        product_ids = tuple(set(m_item.product_id for m_item in m_items))
        last_order = Order.objects.last()
        max_id = last_order.id if last_order else 1
        for i in range(max_id, max_id + options['n']):
            order = Order.objects.create(address=f'address_{i}',
                                         firstname=f'{i}_customer_name',
                                         lastname=f'{i}_customer_last_name',
                                         phonenumber=f'+7{i}031000000',
                                         )
            for product_id in choices(product_ids, k=3):
                OrderItem.objects.create(product_id=product_id,
                                         order=order,
                                         quantity=randint(1, 3),
                                         )

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully added {} orders'.format(
                    options['n'],
                )
            )
        )
