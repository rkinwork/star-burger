from django.test import TestCase
from ..models import Order


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
