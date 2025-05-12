from rest_framework import serializers
from .models import *


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(read_only=True)  # read_only=True — для вкладених моделей, які не мають редагуватися через цей серіалізатор
    discount_price = serializers.SerializerMethodField()  # SerializerMethodField дозволяє робити прості обчислення прямо в серіалізаторі

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'discount', 'stock',
            'available', 'category', 'rating', 'attributes', 'image_url', 'created_at'
        ]
        
    def get_discount_price(self, obj):
        if obj.discount:
            discounted = obj.price * (1 - obj.discount / 100)
            return round(discounted, 2)
        return obj.price
    
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Ціна не може бути від’ємною")
        return value


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    # в DRF-серіалізаторі @property не працює автоматично — потрібно явно додати поле:
    item_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'item_total']

    def get_item_total(self, obj):
        """📌 Переваги:
            Модель залишається зручною й читабельною.
            Серіалізатор гнучко керує логікою представлення (можна форматувати, округляти, додавати знижку).
        """
        return obj.item_total  # property item_total from model


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cart_items', many=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price']

    def get_total_price(self, obj):
        return sum([
            (item.product.discount_price or item.product.price) * item.quantity
            for item in obj.cart_items.all()
        ])
        
        
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'contact_name', 'contact_email', 'contact_phone', 'address',
            'status', 'status_display', 'is_paid', 'created_at', 'items'
        ]
        