from django_filters.rest_framework import FilterSet, NumberFilter

from .models import Product


class ProductFilter(FilterSet):
    price_min = NumberFilter(field_name="price", lookup_expr="gte")
    price_max = NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ['category', 'price_min', 'price_max']
