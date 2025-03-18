from django.db import models


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

    price = models.IntegerField(verbose_name="Ціна (в грн)")
    discount_price = models.IntegerField(blank=True, null=True, verbose_name="Ціна зі знижкою")

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
