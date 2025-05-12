from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from ..serializers import ProductSerializer, CategorySerializer
from ..models import Product, Category

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category']  # ?category=1
    ordering_fields = ['price', 'rating']  # ?ordering=price / -price / rating

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
