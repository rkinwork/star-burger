import json
import pprint

from django.http import JsonResponse, HttpRequest
from django.templatetags.static import static
import phonenumbers
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Product, Order, OrderItem, REGION_CODE


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request: Request):
    form_data = request.data
    pprint.pprint(form_data)
    pure_phone = phonenumbers.parse(form_data['phonenumber'], REGION_CODE)
    order = Order(first_name=form_data['firstname'],
                  last_name=form_data['lastname'],
                  phone_number=pure_phone,
                  address=form_data['address'],
                  )
    order.save()
    for order_item in form_data['products']:
        OrderItem.objects.create(
            order=order,
            product_id=order_item['product'],
            quantity=order_item['quantity'],
        )
    return Response(form_data)
