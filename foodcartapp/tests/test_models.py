from django.core.exceptions import ValidationError
from django.db.models import F
from django.test import TestCase

from ..models import Order, OrderItem, Product


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
                "order_status": Order.OrderStatus.PROCESSED,
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
                                     item_price=product.price,
                                     )

        order = Order.objects.total_price()[0]
        self.assertEqual(order.total_price, total_price)

    def test_total_price_unchanged(self):
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
                                     item_price=product.price,
                                     )

        order = Order.objects.total_price()[0]
        self.assertEqual(order.total_price, total_price)
        product = Product.objects.first()
        product.price = F('price') * 2
        product.save()
        self.assertEqual(order.total_price, total_price)


class TestOrderItem(TestCase):
    _price = 1000

    def setUp(self) -> None:
        Order.objects.create(**{
            "firstname": "Иван",
            "lastname": "Петров",
            "phonenumber": "+79291000000",
            "address": "Москва",
        })
        Product.objects.create(name='test burger 1',
                               price=self._price,
                               )

    def test_negative_total(self):
        order = Order.objects.first()
        product = Product.objects.first()
        order_item = OrderItem(
            order=order,
            product=product,
            quantity=2,
            item_price=-100
        )

        try:
            order_item.full_clean()
        except ValidationError as err:
            self.assertIn('item_price', err.message_dict)

    def test_negative_quantity(self):
        order = Order.objects.first()
        product = Product.objects.first()
        order_item = OrderItem(
            order=order,
            product=product,
            quantity=-2,
            item_price=100
        )

        try:
            order_item.full_clean()
        except ValidationError as err:
            self.assertIn('quantity', err.message_dict)

    def test_min_value(self):
        order = Order.objects.first()
        product = Product.objects.first()
        order_item = OrderItem(
            order=order,
            product=product,
            quantity=2,
            item_price=0
        )

        order_item.full_clean()
