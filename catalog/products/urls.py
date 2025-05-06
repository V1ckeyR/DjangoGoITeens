from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
# r — це просто спосіб вказати Python, що рядок "сирий", і в ньому не обробляти слеші.
# У випадку 'products' вона не обов’язкова, але це хороша практика при роботі з шляхами, регулярними виразами або URL.
router.register(r'products', views.ProductViewSet)
router.register(r'categories', views.CategoryViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart_add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart_detail/', views.cart_detail, name='cart_detail'),
    path('checkout/', views.checkout, name='checkout')
]

urlpatterns += router.urls
