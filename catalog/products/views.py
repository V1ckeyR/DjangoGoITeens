from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.conf import settings

from products.models import Product, Category, Cart, CartItem

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

def cart_add(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        # Отримати кошик користувача або створити новий, якщо немає
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Спробувати знайти існуючий CartItem для цього товару
        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not item_created:
            # Якщо такий товар вже був у кошику - збільшимо кількість
            cart_item.quantity += 1
        else:
            cart_item.quantity = 1
        cart_item.save()
    
    else:
        product = get_object_or_404(Product, id=product_id)
        cart = request.session.get(settings.CART_SESSION_ID, {})
        # Додаємо товар: якщо вже є, то +1, якщо ні – встановити 1
        cart[str(product.id)] = cart.get(str(product.id), 0) + 1
        request.session[settings.CART_SESSION_ID] = cart  # зберегти назад в сесію

    return redirect("cart_detail")

def cart_detail(request):
    if request.user.is_authenticated:
        try:
            cart = request.user.cart  # завдяки related_name="cart"
        except Cart.DoesNotExist:
            cart = None
    
        if not cart or cart.items.count() == 0:
            cart_items = []
            total_price = 0
        else:
            cart_items = cart.items.select_related('product').all()
            total_price = sum(item.product.price * item.quantity for item in cart_items)
    
    else:
        # Якщо користувач не увійшов - використовуємо сесію
        cart = request.session.get(settings.CART_SESSION_ID, {})
        product_ids = cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        # Створити список товарів з кількістю і підсумковою ціною
        cart_items = []
        total_price = 0
        for product in products:
            quantity = cart[str(product.id)]
            item_total = product.price * quantity
            total_price += item_total
            cart_items.append({
                "product": product,
                "quantity": quantity,
                "item_total": item_total
            })

    return render(request, "cart/detail.html", {
        "cart_items": cart_items,
        "total_price": total_price
    })
