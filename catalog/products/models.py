from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator


class Category(models.Model):
    """Категорія товару"""
    name = models.CharField(max_length=255, unique=True, verbose_name="Назва категорії")
    description = models.TextField(blank=True, null=True, verbose_name="Опис")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]
        db_table = "categories"


class Product(models.Model):
    """Модель товару"""
    name = models.CharField(max_length=255, verbose_name="Назва товару")
    description = models.TextField(blank=True, null=True, verbose_name="Опис товару")

    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна (в грн)",
                                validators=[MinValueValidator(0.00)])
    discount= models.IntegerField(blank=True, null=True, verbose_name="Знижка")

    stock = models.PositiveIntegerField(default=0, verbose_name="Кількість на складі")
    available = models.BooleanField(default=True, verbose_name="Доступність товару")

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="Категорія")
    sku = models.CharField(max_length=50, unique=True, verbose_name="Артикул (SKU)")

    image_url = models.CharField(max_length=500, blank=True, null=True, verbose_name="Image URL")  # Store image as a URL

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата оновлення")

    rating = models.FloatField(default=0.0, verbose_name="Рейтинг")

    attributes = models.JSONField(default=dict, blank=True, null=True, verbose_name="Додаткові характеристики")

    class Meta:
        ordering = ["-created_at"]  # Нові товари будуть зверху
        db_table = "products"  # Назва таблиці в базі
        unique_together = ["name", "sku"]  # Гарантія унікальності комбінації "назва + артикул"

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Кошик користувача {self.user.username}"
    
    class Meta:
        db_table = "carts"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"
    
    class Meta:
        db_table = "cart_items"
        unique_together = ('cart','product')
        
    @property
    def item_total(self):
        return self.product.price * self.quantity



class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="orders",
        help_text="Користувач, який зробив замовлення (може бути порожнім для гостей)."
    )
    contact_name = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Status(models.IntegerChoices):
        NEW = 1
        PROCESSING = 2
        SHIPPED = 3
        COMPLETED = 4
        CANCELED = 5

    status = models.IntegerField(choices=Status, default=Status.NEW)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} ({self.contact_name})"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}. (order #{self.order.id})"

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    provider = models.CharField(max_length=20, choices=[
        ("liqpay", "LiqPay"),
        ("monopay", "MonoPay"),
        ("google", "Google Pay"),
        # можна додати інші, наприклад, ("paypal", "PayPal") чи ("stripe", "Stripe") якщо потрібно
    ])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ("pending", "Очікує підтвердження"),
        ("paid", "Оплачено"),
        ("failed", "Помилка")
    ], default="pending")
    transaction_id = models.CharField(max_length=100, blank=True, help_text="ID транзакції від платіжної системи")
    created_at = models.DateTimeField(auto_now_add=True)
