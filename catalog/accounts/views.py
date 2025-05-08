from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from utils.email import send_confirm_email
from products.models import Cart, CartItem, Product

from .models import Profile
from .forms import RegisterForm,  ProfileUpdateForm
from .serializers import UserSerializer, ProfileSerializer


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save()

            login(request, user)
            send_confirm_email(request, user=user, new_email=user.email)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            session_cart = request.session.get(settings.CART_SESSION_ID)
            login(request, user)
            if session_cart:
                # перенести кожен товар із сесії в БД
                cart, _ = Cart.objects.get_or_create(user=user)
                for prod_id, quantity in session_cart.items():
                    product = Product.objects.get(id=prod_id)
                    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                    if not created:
                        cart_item.quantity += quantity
                    else:
                        cart_item.quantity = quantity
                    cart_item.save()
                # очистити кошик в сесії, оскільки він вже перенесений
                request.session[settings.CART_SESSION_ID] = {}

            next_url = request.GET.get('next')
            return redirect(next_url or 'home')
        else:
            return render(request, 'login.html', {'error': 'Невірні дані'})
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'profile.html')


@login_required
def edit_profile_view(request):
    user = request.user
    # Отримуємо пов'язаний профіль або створюємо, якщо його нема
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            # Оновлюємо email користувача
            new_email = form.cleaned_data['email']
            if new_email != user.email:
                send_confirm_email(request, user=user, new_email=new_email)
            # решту збереження робимо, тільки НЕ оновлюємо user.email тут, залишимо старий до підтвердження

            # Оновлюємо аватар профілю, якщо завантажено новий
            avatar = form.cleaned_data.get('avatar')
            if avatar:
                profile.avatar = avatar
            # Збережемо профіль (якщо аватар змінено або навіть якщо ні, на всяк випадок)
            profile.save()
            # Можна додати повідомлення успіху через messages
            messages.success(request, "Профіль успішно оновлено!")
            return redirect('profile') 
    else:
        form = ProfileUpdateForm(user=user)  # початкове заповнення форми

    return render(request, 'edit_profile.html', {'form': form, 'profile': profile})

def confirm_email(request):
    user_id = request.GET.get('user')
    new_email = request.GET.get('email')
    # Можна також мати token = request.GET.get('token') для безпеки, але припустимо поки що не потрібен
    if not user_id or not new_email:
        return HttpResponseBadRequest("Недійсний запит.")
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponseBadRequest("Користувача не знайдено.")
    # Можна перевірити, що new_email ніким не зайнятий (на випадок, якщо поки підтверджували, хтось зареєстрував)
    if user.is_active and User.objects.filter(email=new_email).exists():
        return HttpResponseBadRequest("Ця електронна адреса вже використовується іншим обліковим записом.")
    # Оновлюємо email
    old_email = user.email
    user.email = new_email
    user.is_active = True
    user.save()
    # За бажанням, тут можна помітити в профілі, що email підтверджений, або інший флаг.
    # Повідомлення користувачу
    return render(request, 'email_confirmed.html', {'new_email': new_email, 'old_email': old_email})

class AccountViewSet(viewsets.ViewSet):  # ViewSet: використовується замість звичайних функцій view для групування пов’язаних дій в один клас.
    permission_classes = [AllowAny]  # за замовчуванням дозволяє доступ усім, але конкретні методи можуть перевизначати це (наприклад, @action(..., permission_classes=[IsAuthenticated])).
    
    @action(detail=False, methods=["post"])
    def register(self, request):
        form = RegisterForm(request.data)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save()
            login(request, user)
            send_confirm_email(request, user=user, new_email=user.email)
            return Response({"message": "Користувача зареєстровано"}, status=201)
        return Response(form.errors, status=400)

    @action(detail=False, methods=["post"])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            session_cart = request.session.get(settings.CART_SESSION_ID)
            login(request, user)
            if session_cart:
                cart, _ = Cart.objects.get_or_create(user=user)
                for prod_id, quantity in session_cart.items():
                    product = Product.objects.get(id=prod_id)
                    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                    cart_item.quantity = cart_item.quantity + quantity if not created else quantity
                    cart_item.save()
                request.session[settings.CART_SESSION_ID] = {}
            return Response({"message": "Успішний вхід"})
        return Response({"error": "Невірні дані"}, status=400)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        logout(request)
        return Response({"message": "Вихід виконано"})

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def profile(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def edit_profile(self, request):
        user = request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        form = ProfileUpdateForm(request.data, request.FILES, user=user)
        if form.is_valid():
            new_email = form.cleaned_data['email']
            if new_email != user.email:
                send_confirm_email(request, user=user, new_email=new_email)
            avatar = form.cleaned_data.get("avatar")
            if avatar:
                profile.avatar = avatar
            profile.save()
            return Response({"message": "Профіль оновлено"})
        return Response(form.errors, status=400)

    @action(detail=False, methods=["get"])
    def confirm_email(self, request):
        user_id = request.GET.get('user')
        new_email = request.GET.get('email')
        if not user_id or not new_email:
            return Response({"error": "Недійсний запит."}, status=400)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "Користувача не знайдено."}, status=400)

        if user.is_active and User.objects.filter(email=new_email).exists():
            return Response({"error": "Цей email вже використовується."}, status=400)

        old_email = user.email
        user.email = new_email
        user.is_active = True
        user.save()

        return Response({"message": "Email підтверджено", "old_email": old_email, "new_email": new_email})
