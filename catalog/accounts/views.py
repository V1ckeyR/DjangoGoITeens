from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required

from .models import Profile
from .forms import RegisterForm,  ProfileUpdateForm

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
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
            login(request, user)
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
            user.email = new_email
            # Якщо email змінено, можна тут же запланувати відправку підтвердження (див. наступний розділ)
            user.save()
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
