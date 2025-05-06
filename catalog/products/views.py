from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.conf import settings
from django.contrib import messages
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters

from utils.email import send_order_confirmation_email
from products.models import Payment, Product, Category, Cart, CartItem, Order, OrderItem
from .forms import OrderCreateForm
from .serializers import ProductSerializer, CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    DRF сам зробить імена:
    products-list → для GET /api/products/
    products-detail → для GET /api/products/<pk>/
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category']  # ?category=1
    ordering_fields = ['price', 'rating']  # ?ordering=price / -price / rating


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

def index(request):
    return render(request, 'index.html')

def home(request):
    return render(request, 'base.html')

def about(request):
    return render(request, 'base.html')  # TODO

def product_detail(request, product_id):
    return render(request, 'product_detail.html', {"product_id": product_id})

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
            total_price = sum(item.item_total for item in cart_items)
    
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

def checkout(request):
    # Якщо кошик порожній – перенаправити назад, нічого оформлювати
    if (request.user.is_authenticated and not getattr(request.user, 'cart', None)) or \
       (not request.user.is_authenticated and not request.session.get(settings.CART_SESSION_ID)):
        messages.error(request, "Кошик порожній. Додайте товари перш ніж оформити замовлення.")
        return redirect("cart_detail")

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # Створити Order але поки не зберігати в базу (commit=False)
            order: Order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.save()  # тепер зберегли замовлення, маємо order.id
            # Додати товари з кошика до OrderItem
            if request.user.is_authenticated:
                cart = getattr(request.user, 'cart')
                cart_items = cart.items.select_related('product').all()
            else:
                session_cart = request.session.get(settings.CART_SESSION_ID, {})
                cart_items = []
                for prod_id, quantity in session_cart.items():
                    product = Product.objects.get(id=prod_id)
                    cart_items.append( 
                        {"product": product, "quantity": quantity}
                    )

            items = OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                for item in cart_items
            ])
    
            method = form.cleaned_data['payment_method']
            total_price = sum(item.product.price * item.quantity for item in items)

            if method != "cash":
                Payment.objects.create(order=order, provider=method, amount=total_price, status="pending")
            else:
                # Оплата при отриманні, вважаємо не онлайн
                order.status = Order.Status.PROCESSING  # замовлення одразу в роботу, оплату чекатимемо офлайн
                order.save()

            # Очищення кошика після оформлення
            if request.user.is_authenticated:
                # Видалити всі товари кошика з БД (або можна видалити сам об'єкт Cart)
                cart.items.all().delete()
            request.session[settings.CART_SESSION_ID] = {}  # очистити сесію
            # Надсилання email підтвердження (див. наступний розділ)
            send_order_confirmation_email(order)
            messages.success(request, f"Дякуємо за замовлення! Номер вашого замовлення: {order.id}. Деталі надіслано на email.")
            return redirect("index")  # перенаправити на головну чи сторінку подяки
    else:
        # GET request – показати форму
        form = OrderCreateForm()
        # Якщо користувач увійшов, можна заповнити початкові значення:
        if request.user.is_authenticated:
            if request.user.first_name:
                form.initial["contact_name"] = request.user.first_name.capitalize()
            form.initial["contact_email"] = request.user.email
            # якщо у профілі є ім'я чи телефон, теж можна initial...
    return render(request, "cart/checkout.html", {"form": form})
