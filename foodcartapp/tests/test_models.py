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
