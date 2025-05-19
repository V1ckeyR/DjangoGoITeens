from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser, AllowAny
from drf_spectacular.utils import extend_schema_view, extend_schema

from ..serializers import ProductSerializer, CategorySerializer
from ..models import Product, Category
from ..filters import ProductFilter


@extend_schema_view(
    list=extend_schema(summary="Список продуктів", tags=["Продукти"]),
    retrieve=extend_schema(summary="Один продукт", tags=["Продукт"])
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ProductFilter  # ?category=1
    ordering_fields = ['price', 'rating']  # ?ordering=price / -price / rating
    search_fields = ['name', 'description']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
