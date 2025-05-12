from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.conf import settings
from django.contrib import messages
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from utils.email import send_order_confirmation_email
from products.models import Payment, Product, Category, Cart, CartItem, Order, OrderItem
from .forms import OrderCreateForm


def index(request):
    categories = Category.objects.all()
    category_id = request.GET.get("category")  # Отримуємо вибрану категорію з GET-запиту
    sort_by = request.GET.get("sort_by")  # Отримуємо параметр сортування

    products = Product.objects.all()
    
    if category_id:
        products = products.filter(category_id=category_id)

    if sort_by == "price_asc":
        products = products.order_by("price")
    elif sort_by == "price_desc":
        products = products.order_by("-price")
    elif sort_by == "rating":
        products = products.order_by("-rating")

    return render(request, 'index.html', {"products": products, "categories": categories})

def home(request):
    return render(request, 'base.html')

def about(request):
    return render(request, 'base.html')  # TODO

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {"product": product})

