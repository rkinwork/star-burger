from typing import Iterable
from collections import Counter
from dataclasses import dataclass

from django.utils import timezone

from django.db import models, transaction

from django.core.validators import MinValueValidator
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field import serializerfields
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from coordinates_keeper.models import Distance

REGION_CODE = 'RU'
REMOTENESS_ATTR_NAME = 'remoteness'


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
                .filter(availability=True)
                .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderStatus(models.TextChoices):
    NEW = 'Ne', _('Новый заказ')
    PROCESSED = 'Pr', _('Обработанный')
    FINISHED = 'Fi', _('Завершенный')


class PaymentMethod(models.TextChoices):
    UNKNOWN = 'NA', _('Не известно')
    ONLINE = 'ON', _('Электронно')
    CASH = 'CH', _('Наличностью')


class NewOrderManager(models.QuerySet):
    def new(self):
        return self.filter(order_status=OrderStatus.NEW)

    def total_price(self):
        return self.annotate(total_price=models.Sum(
            models.F('items__item_price') * models.F('items__quantity')
        )
        )


class Order(models.Model):
    address = models.CharField('адрес', max_length=200)
    firstname = models.CharField('имя', max_length=50)
    lastname = models.CharField('фамилия', max_length=50)
    phonenumber = PhoneNumberField('телефон', region=REGION_CODE, db_index=True)
    created_at = models.DateTimeField('создан в', default=timezone.now, db_index=True)
    called_at = models.DateTimeField('подтверждён в', blank=True, null=True, db_index=True)
    delivered_at = models.DateTimeField('доставлен в', blank=True, null=True, db_index=True)
    order_status = models.CharField(
        verbose_name='статус',
        max_length=2,
        choices=OrderStatus.choices,
        db_index=True,
        default=OrderStatus.NEW,
    )
    payment_method = models.CharField(
        verbose_name='метод оплаты',
        max_length=2,
        choices=PaymentMethod.choices,
        db_index=True,
        default=PaymentMethod.UNKNOWN,
    )
    comment = models.TextField('комментарий', blank=True)
    restaurant = models.ForeignKey('Restaurant',
                                   related_name='orders',
                                   on_delete=models.SET_NULL,
                                   verbose_name='ресторан исполнитель',
                                   blank=True,
                                   null=True,
                                   )

    objects = NewOrderManager.as_manager()

    @property
    def client(self):
        return f'{self.firstname} {self.lastname}'

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.firstname} {self.lastname} {self.address}'


class OrderItem(models.Model):
    product = models.ForeignKey('Product',
                                related_name='items',
                                on_delete=models.CASCADE,
                                verbose_name='продукт в заказе',
                                )
    order = models.ForeignKey('Order',
                              related_name='items',
                              on_delete=models.CASCADE,
                              verbose_name='заказ',
                              )
    quantity = models.IntegerField('количество',
                                   validators=[
                                       MinValueValidator(0),
                                   ],
                                   )
    item_price = models.DecimalField('цена в заказе',
                                     max_digits=9,
                                     decimal_places=2,
                                     validators=[
                                         MinValueValidator(0)
                                     ]
                                     )

    class Meta:
        verbose_name = 'наименование'
        verbose_name_plural = 'наименований'

    def __str__(self):
        return f'{self.product} {self.order}'


@receiver(models.signals.pre_save, sender=OrderItem)
def calculate_total(sender, instance: OrderItem, **kwargs):
    if instance.id is None:
        instance.item_price = instance.product.price


class OrderItemSerializer(ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = OrderItem
        fields = ('product', 'quantity')


class OrderSerializer(ModelSerializer):
    phonenumber = serializerfields.PhoneNumberField()
    products = OrderItemSerializer(many=True,
                                   allow_empty=False,
                                   source='items',
                                   )

    class Meta:
        model = Order
        fields = (
            'id',
            'address',
            'firstname',
            'lastname',
            'phonenumber',
            'products',
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        items = validated_data.pop('items')
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for order_item in items:
                OrderItem.objects.create(order=order, **order_item)

        return order


@dataclass
class RestaurantItem:
    name: str
    address: str
    distance: [float] = None


def enrich_orders_with_restaurants(orders: models.QuerySet) -> Iterable[Order]:
    menu_items_prefetch = models.Prefetch(
        'items__product__menu_items',
        queryset=RestaurantMenuItem.objects.select_related('restaurant', 'product').filter(availability=True),
    )
    orders = orders.prefetch_related(menu_items_prefetch)

    result_orders = []
    for order in orders:
        counter = Counter()
        ordered_products = [order_item.product for order_item in order.items.all()]
        menu_items = []
        for product in ordered_products:
            menu_items.extend(product.menu_items.all())

        for menu_item in menu_items:
            if menu_item.product in ordered_products:
                counter[menu_item.restaurant] += 1

        restaurants = []
        for restaurant in [restaurant for restaurant, cnt in dict(counter).items() if cnt >= len(ordered_products)]:
            restaurants.append(
                RestaurantItem(name=restaurant.name,
                               address=restaurant.address,
                               )
            )
        order.restaurants = restaurants
        order.restaurants = sorted(restaurants, key=lambda e: (e.distance is None, e.distance))
        result_orders.append(order)

    # prepare coordinates and addresses
    addresses_raw = set()
    for order in result_orders:
        addresses_raw.add(order.address)
        for rest in order.restaurants:
            addresses_raw.add(rest.address)
    d = Distance(addresses_raw=addresses_raw)

    for order in result_orders:
        order_address = order.address
        for rest in order.restaurants:
            rest.distance = d.get_distance(order_address, rest.address)

        order.restaurants = sorted(order.restaurants, key=lambda e: (e.distance is None, e.distance))

    return result_orders
