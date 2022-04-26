from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.db import models
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views


from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem

from coordinates_keeper.distance_calc import Distance


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    # sometimes in future we can add pagination
    orders = enrich_orders_with_restaurants(Order.objects.new().total_price())
    return render(request, template_name='order_items.html', context={
        'order_items': orders
    })


@dataclass
class RestaurantItem:
    name: str
    address: str
    distance: [float] = None


def enrich_orders_with_restaurants(orders: models.QuerySet) -> Iterable[Order]:
    menu_items_prefetch = models.Prefetch(
        'items__product__menu_items',
        queryset=RestaurantMenuItem.objects.select_related('restaurant',
                                                           'product',
                                                           ).filter(
            availability=True,
        ),
    )
    orders_with_menu_items = orders.prefetch_related(menu_items_prefetch)

    orders_with_available_restaurants = []
    addresses_raw = set()
    for order in orders_with_menu_items:
        addresses_raw.add(order.address)
        counter = Counter()
        ordered_products = [order_item.product for order_item in
                            order.items.all()]
        menu_items = []
        for product in ordered_products:
            menu_items.extend(product.menu_items.all())

        for menu_item in menu_items:
            if menu_item.product in ordered_products:
                counter[menu_item.restaurant] += 1

        restaurants = []
        for restaurant in [restaurant
                           for restaurant, cnt in dict(counter).items()
                           if cnt >= len(ordered_products)]:
            addresses_raw.add(restaurant.address)
            restaurants.append(
                RestaurantItem(name=restaurant.name,
                               address=restaurant.address,
                               )
            )
        order.restaurants = restaurants
        orders_with_available_restaurants.append(order)

    dist = Distance(addresses_names=addresses_raw)
    for order in orders_with_available_restaurants:
        order_address = order.address
        for rest in order.restaurants:
            rest.distance = dist.get_distance(order_address, rest.address)

        order.restaurants = sorted(order.restaurants,
                                   key=lambda e: (
                                       e.distance is None, e.distance))

    return orders_with_available_restaurants
