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

class CartViewSet(viewsets.ViewSet):
    """
    Це ViewSet без моделі (ViewSet, не ModelViewSet), тому логіка повністю кастомна. Маршрути створюються через @action.
    """
    @action(detail=False, methods=["post"], url_path="add/(?P<product_id>[^/.]+)")
    def add(self, request, product_id=None):
        """
        Перевіряє, чи користувач авторизований

        🔹 Якщо авторизований:
        Отримує або створює Cart для користувача

        Отримує або створює CartItem з цим товаром

        Якщо такий товар вже є — збільшує кількість, інакше ставить 1

        🔹 Якщо неавторизований:
        Завантажує словник cart із сесії (request.session)

        Додає/оновлює кількість товару по ID

        Оновлює сесію
        """
        product = get_object_or_404(Product, id=product_id)
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
            cart_item.quantity = cart_item.quantity + 1 if not created else 1
            cart_item.save()
        else:
            cart = request.session.get(settings.CART_SESSION_ID, {})
            cart[str(product.id)] = cart.get(str(product.id), 0) + 1
            request.session[settings.CART_SESSION_ID] = cart
        return Response({"message": "Товар додано до кошика"}, status=200)

    @action(detail=False, methods=["get"])
    def detail(self, request):
        """
        🔹 Якщо авторизований:
        Повертає cart.items із бази

        Формує список товарів у форматі:
        { "product_id": 1, "name": "Товар", "price": 100.0, "quantity": 2, "item_total": 200.0 }
        Рахує total

        🔹 Якщо гість:
        Завантажує кошик із сесії

        Завантажує Product по ID

        Формує ті ж поля вручну
        """
        if request.user.is_authenticated:
            cart = getattr(request.user, "cart", None)
            if not cart or cart.items.count() == 0:
                return Response({"items": [], "total": 0})
            items = cart.items.select_related("product").all()
            data = [{
                "product_id": item.product.id,
                "name": item.product.name,
                "price": float(item.product.price),
                "quantity": item.quantity,
                "item_total": float(item.item_total),
            } for item in items]
            total = sum(item["item_total"] for item in data)
        else:
            cart = request.session.get(settings.CART_SESSION_ID, {})
            products = Product.objects.filter(id__in=cart.keys())
            data, total = [], 0
            for p in products:
                quantity = cart[str(p.id)]
                item_total = p.price * quantity
                total += item_total
                data.append({
                    "product_id": p.id,
                    "name": p.name,
                    "price": float(p.price),
                    "quantity": quantity,
                    "item_total": float(item_total),
                })
        return Response({"items": data, "total": total})

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        """
        🔹 Перевірка:
        Якщо кошик порожній → повертає помилку

        🔹 Створення Order:
        Використовує OrderCreateForm

        Якщо авторизований — прив'язує user

        Зберігає замовлення

        🔹 Додавання товарів до замовлення:
        Якщо авторизований — бере cart.items з БД

        Якщо гість — бере cart із сесії

        🔹 Створення OrderItem:
        Через bulk_create, щоб зберегти всі одразу

        🔹 Оплата:
        Якщо вибрано cash, змінює статус

        Інакше створює Payment зі статусом pending

        🔹 Очищення кошика:
        Якщо авторизований — очищає cart.items

        Якщо гість — очищає request.session

        🔹 Відправка email:
        send_order_confirmation_email(order)
        """
        if request.user.is_authenticated:
            cart = getattr(request.user, "cart", None)
            if not cart or cart.items.count() == 0:
                return Response({"error": "Кошик порожній"}, status=400)
        elif not request.session.get(settings.CART_SESSION_ID):
            return Response({"error": "Кошик порожній"}, status=400)

        form = OrderCreateForm(request.data)
        if not form.is_valid():
            return Response({"errors": form.errors}, status=400)

        order: Order = form.save(commit=False)
        if request.user.is_authenticated:
            order.user = request.user
        order.save()

        if request.user.is_authenticated:
            cart_items = order.user.cart.items.select_related('product').all()
        else:
            cart_data = request.session.get(settings.CART_SESSION_ID, {})
            cart_items = [{"product": Product.objects.get(id=int(pid)), "quantity": q} for pid, q in cart_data.items()]

        items = OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product=item["product"] if isinstance(item, dict) else item.product,
                quantity=item["quantity"] if isinstance(item, dict) else item.quantity,
                price=item["product"].price if isinstance(item, dict) else item.product.price
            ) for item in cart_items
        ])

        method = form.cleaned_data["payment_method"]
        total = sum(item.product.price * item.quantity for item in items)

        if method != "cash":
            Payment.objects.create(order=order, provider=method, amount=total, status="pending")
        else:
            order.status = Order.Status.PROCESSING
            order.save()

        if request.user.is_authenticated:
            cart.items.all().delete()
        request.session[settings.CART_SESSION_ID] = {}

        send_order_confirmation_email(order)

        return Response({"message": f"Замовлення №{order.id} оформлено"}, status=200)
