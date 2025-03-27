from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from products.models import Product, Category

def index(request):
    categories = Category.objects.all()
    category_id = request.GET.get("category")  # Отримуємо вибрану категорію з GET-запиту
    sort_by = request.GET.get("sort_by")  # Отримуємо параметр сортування

    products = Product.objects.all()
    
    print(categories, category_id)
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
