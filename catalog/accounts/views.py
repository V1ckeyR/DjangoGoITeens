from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.urls import reverse
from django.http import HttpResponseBadRequest
from django.conf import settings

from products.models import Cart, CartItem, Product

from .models import Profile
from .forms import RegisterForm,  ProfileUpdateForm

def send_confirm_email(request, user, new_email):
    #  Генеруємо унікальне посилання для підтвердження
    confirm_url = request.build_absolute_uri(
        reverse('confirm_email')  # URL, який ми створимо для підтвердження
    )
    # Додамо параметри до URL: id користувача і новий email
    confirm_url += f"?user={user.id}&email={new_email}"
    # Формуємо повідомлення листа
    subject = "Підтвердження електронної пошти"
    message = f"Привіт, {user.username}!\n\n" \
            f"Ви запросили змінити адресу електронної пошти на нашому сайті.\n" \
            f"Новий email: {new_email}\n\n" \
            f"Щоб підтвердити цю адресу, перейдіть за посиланням:\n{confirm_url}\n\n" \
            f"Якщо ви не робили цю зміну, просто проігноруйте цей лист."
    # Відправляємо лист на new_email
    send_mail(subject, message, 'noreply@myshop.com', [new_email], fail_silently=False)
    # Можна показати користувачу повідомлення, що лист відправлено
    messages.info(request, "На нову адресу надіслано лист з підтвердженням. Перевірте пошту.")
    request.session['pending_email'] = new_email


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
