from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import OuterRef, Subquery, Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

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
            RestaurantMenuItem.objects.filter(availability=True).values_list(
                'product',
            )
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


class OrderCustomQuerySet(models.QuerySet):
    def new(self):
        return self.filter(order_status=Order.OrderStatus.NEW)

    def total_price(self):
        return self.annotate(total_price=models.Sum(
            models.F('items__item_price') * models.F('items__quantity')
        )
        )

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        NEW = 'Ne', _('Новый заказ')
        PROCESSED = 'Pr', _('Обработанный')
        FINISHED = 'Fi', _('Завершенный')

    class PaymentMethod(models.TextChoices):
        UNKNOWN = 'NA', _('Не известно')
        ONLINE = 'ON', _('Электронно')
        CASH = 'CH', _('Наличностью')

    address = models.CharField('адрес', max_length=200)
    firstname = models.CharField('имя', max_length=50)
    lastname = models.CharField('фамилия', max_length=50)
    phonenumber = PhoneNumberField('телефон',
                                   region=REGION_CODE,
                                   db_index=True,
                                   )
    created_at = models.DateTimeField('создан в',
                                      default=timezone.now,
                                      db_index=True,
                                      )
    called_at = models.DateTimeField('подтверждён в',
                                     blank=True,
                                     null=True,
                                     db_index=True,
                                     )
    delivered_at = models.DateTimeField('доставлен в',
                                        blank=True,
                                        null=True,
                                        db_index=True,
                                        )
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

    objects = OrderCustomQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.firstname} {self.lastname} {self.address}'

    @property
    def client_full_name(self):
        return f'{self.firstname} {self.lastname}'

    def get_available_restaurants(self) -> models.QuerySet:
        available_products = models.Count(
            'menu_items__product__items__id',
            distinct=True,
            filter=(
                models.Q(menu_items__availability=True) &
                models.Q(menu_items__product__items__order=self.id)
            ),
        )

        ordered_products = models.Count(
            'menu_items__product__items__order__items__id',
            distinct=True,
            filter=models.Q(menu_items__product__items__order=self.id),
        )

        return Restaurant.objects \
            .filter(menu_items__product__items__order=self.id) \
            .annotate(available_cnt=available_products) \
            .annotate(ordered_cnt=ordered_products) \
            .filter(available_cnt=models.F('ordered_cnt'))


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
                                       MinValueValidator(1),
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
