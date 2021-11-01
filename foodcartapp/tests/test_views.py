from typing import NamedTuple

from rest_framework import status
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Product, Order


class CheckCase(NamedTuple):
    name: str
    payload: str
    want: int


class TestNewOrder(TestCase):
    def setUp(self) -> None:
        Product.objects.create(id=1, name='test product name', price=1)

        self.cases = (
            CheckCase(
                'products is not list',
                """{"products": "HelloWorld",
                "firstname": "Иван", "lastname": "Петров",
                "phonenumber": "+79291000000", "address": "Москва"}""",
                status.HTTP_400_BAD_REQUEST
            ),
            CheckCase(
                'products is null',
                """{"products": null,
                "firstname": "Иван", "lastname": "Петров",
                "phonenumber": "+79291000000", "address": "Москва"}""",
                status.HTTP_400_BAD_REQUEST
            ),
            CheckCase(
                'products empty list',
                """{"products": [],
                "firstname": "Иван", "lastname": "Петров",
                "phonenumber": "+79291000000",
                "address": "Москва"}""",
                status.HTTP_400_BAD_REQUEST
            ),
            CheckCase(
                'products are absent',
                """{"firstname": "Иван", "lastname": "Петров",
                "phonenumber": "+79291000000", "address": "Москва"}""",
                status.HTTP_400_BAD_REQUEST
            ),
            CheckCase(
                'first name is null',
                """{"products": [{"product": 1, "quantity": 1}],
                "firstname": null, "lastname": "Петров",
                "phonenumber": "+79291000000", "address": "Москва"}""",
                status.HTTP_400_BAD_REQUEST
            ),
            CheckCase(
                'only products',
                """{"products": [{"product": 1, "quantity": 1}]}""",
                status.HTTP_400_BAD_REQUEST
            ),
            CheckCase(
                'null main order keys',
                """{"products": [{"product": 1, "quantity": 1}],
                "firstname": null, "lastname": null, "phonenumber": null,
                "address": null}""",
                status.HTTP_400_BAD_REQUEST
            ),
            CheckCase(
                'phone number is empty',
                """{"products": [{"product": 1, "quantity": 1}],
                "firstname": null, "lastname": null, "phonenumber": null,
                "address": null}""",
                status.HTTP_400_BAD_REQUEST,
            ),
            CheckCase(
                'incorrect phone number',
                """{"products": [{"product": 1, "quantity": 1}],
                "firstname": "Тимур", "lastname": "Иванов",
                "phonenumber": "+70000000000", "address":
                "Москва, Новый Арбат 10"}""",
                status.HTTP_400_BAD_REQUEST,
            ),
            CheckCase(
                'order with not existing product',
                """{"products": [{"product": 9999, "quantity": 1}],
                "firstname": "Иван", "lastname": "Петров",
                "phonenumber": "+79291000000", "address": "Москва"}""",
                status.HTTP_400_BAD_REQUEST,
            ),
            CheckCase(
                'fist name not valid string',
                """{"products": [{"product": 1, "quantity": 1}],
                "firstname": [], "lastname": "Петров",
                "phonenumber": "+79291000000", "address": "Москва"}""",
                status.HTTP_400_BAD_REQUEST,
            ),
            CheckCase(
                'valid order',
                """{"products": [{"product": 1, "quantity": 1}],
                "firstname": "Иван", "lastname": "Петров",
                "phonenumber": "+79291000000", "address": "Москва"}""",
                status.HTTP_201_CREATED,
            ),

        )
        self.client = Client()

    def test_creation_cases(self):
        for case in self.cases:
            with self.subTest(msg=case.name):
                response = self.client.post(
                    reverse('foodcartapp:order'),
                    data=case.payload,
                    content_type='application/json',
                )
                self.assertEqual(response.status_code, case.want)

    def test_creation_response(self):
        payload = """{"products": [{"product": 1, "quantity": 1}],
        "firstname": "Василий", "lastname": "Васильевич",
        "phonenumber": "+79123456789", "address": "Лондон"}"""
        response = self.client.post(
            reverse('foodcartapp:order'),
            data=payload,
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

    def test_transaction_behavior(self):
        cases = (
            CheckCase(
                'order with not existing product',
                """{"products": [{"product": 9999, "quantity": 1}],
                "firstname": "Иван", "lastname": "Петров",
                "phonenumber": "+79291000000", "address": "Москва"}""",
                0,
            ),
            CheckCase(
                'products are absent',
                """{"firstname": "Иван", "lastname": "Петров",
                "phonenumber": "+79291000000", "address": "Москва"}""",
                0
            ),
            CheckCase(
                'products empty list',
                """{"products": [],
                "firstname": "Иван", "lastname": "Петров",
                "phonenumber": "+79291000000",
                "address": "Москва"}""",
                0
            ),
            CheckCase(
                'valid order',
                """{"products": [{"product": 1, "quantity": 1}],
                "firstname": "Иван", "lastname": "Петров",
                "phonenumber": "+79291000000", "address": "Москва"}""",
                1,
            ),
        )
        for case in cases:
            with self.subTest(msg=case.name):
                self.client.post(
                    reverse('foodcartapp:order'),
                    data=case.payload,
                    content_type='application/json',
                )
                orders = Order.objects.all()
                self.assertEqual(len(orders), case.want)
                orders.delete()

