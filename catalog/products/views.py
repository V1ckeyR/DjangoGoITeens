from django.http import HttpResponse
from django.shortcuts import render

from products.models import Product, Category

# Create your views here.
def index(request):
    products = Product.objects.all()
    return render(request, 'index.html', {"products": products})

def home(request):
    return render(request, 'base.html')

def about(request):
    return render(request, 'base.html')  # TODO
