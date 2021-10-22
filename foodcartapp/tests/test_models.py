from django.test import TestCase
from ..models import Order, Product, OrderItem


class OrderTest(TestCase):
    def test_order_create(self):
        order_raw = {
            "firstname": "Иван",
            "lastname": "Петров",
            "phonenumber": "+79291000000",
            "address": "Москва",
        }
        order = Order.objects.create(**order_raw)
        self.assertIsNotNone(order)

    def test_only_new_orders_retrieve(self):
        orders_raw = (
            {
                "firstname": "Иван",
                "lastname": "Петров",
                "phonenumber": "+79291000000",
                "address": "Москва",
            },
            {
                "firstname": "Иван",
                "lastname": "Петров",
                "phonenumber": "+79291000000",
                "address": "Москва",
            },
            {
                "firstname": "Петр",
                "lastname": "Петров",
                "phonenumber": "+79291000000",
                "address": "Москва",
                "is_new_order": False,
            }
        )
        for order in orders_raw:
            Order.objects.create(**order)

        self.assertEqual(len(Order.objects.new()), 2)

    def test_total_price(self):
        order = {
            "firstname": "Иван",
            "lastname": "Петров",
            "phonenumber": "+79291000000",
            "address": "Москва",
        }
        price = 100
        quantity = 2
        products = [
            {
                'name': 'test burger 1',
                'price': price,
            },
            {
                'name': '2 test burger',
                'price': price,
            }
        ]
        total_price = price * quantity * len(products)

        order = Order.objects.create(**order)

        for product in products:
            product = Product.objects.create(**product)
            OrderItem.objects.create(product=product,
                                     order=order,
                                     quantity=quantity,
                                     )

        order = Order.objects.total_price()[0]
        self.assertEqual(order.total_price, total_price)
