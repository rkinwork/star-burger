from django.db import transaction

from phonenumber_field import serializerfields
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .models import Order, OrderItem, Product


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
                OrderItem.objects.create(order=order,
                                         product=order_item['product'],
                                         quantity=order_item['quantity'],
                                         item_price=order_item['product'].price,
                                         )

        return order
