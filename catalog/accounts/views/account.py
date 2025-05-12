from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from utils.email import send_confirm_email
from products.models import Cart, CartItem, Product

from ..models import Profile
from ..forms import RegisterForm,  ProfileUpdateForm
from ..serializers import ProfileSerializer

class AccountViewSet(viewsets.ViewSet):  # ViewSet: використовується замість звичайних функцій view для групування пов’язаних дій в один клас.
    permission_classes = [AllowAny]  # за замовчуванням дозволяє доступ усім, але конкретні методи можуть перевизначати це (наприклад, @action(..., permission_classes=[IsAuthenticated])).
    
    @action(detail=False, methods=["post"])
    def register(self, request):
        """
        Приймає POST-запит з формою реєстрації.

        Якщо form.is_valid():

            Створює нового користувача.

            Робить його неактивним (user.is_active = False), чекає на підтвердження email.

            Авторизує його (login(request, user)).

            Відправляє email на підтвердження (send_confirm_email(...)).

        Якщо форма невалідна — повертає помилки.
        """
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
        """
        Отримує логін і пароль з тіла запиту.

        authenticate(...) перевіряє облікові дані.

        Якщо успішно:

            Копіює кошик із сесії до бази (для авторизованого користувача).

            Авторизує користувача.

            Повертає повідомлення успіху.

        Якщо неуспішно — повертає помилку.
        """
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
        """
        Видаляє сесію користувача через logout(request)

        Повертає відповідь { "message": "Вихід виконано" }

        Доступ тільки для авторизованих користувачів (IsAuthenticated)
        """
        logout(request)
        return Response({"message": "Вихід виконано"})

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """
        Отримує або створює об'єкт Profile для користувача.

        Повертає його через ProfileSerializer.
        """
        profile = Profile.objects.get(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def edit_profile(self, request):
        """
        Отримує форму ProfileUpdateForm (включає email та аватар).

        Якщо email змінено — відправляє запит на підтвердження нового email.

        Зберігає аватар у профілі.

        Повертає повідомлення або помилки форми.
        """
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
        """
        Приймає user_id і new_email з GET-запиту.

        Якщо ці параметри відсутні — помилка.

        Перевіряє, що email ще не зайнятий.

        Оновлює email користувача і активує акаунт.

        Повертає повідомлення про успішне підтвердження.
        """
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
