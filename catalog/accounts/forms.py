from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from captcha.fields import CaptchaField
from django.core.exceptions import ValidationError

from .models import Profile  # якщо Profile у тому ж додатку


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    captcha = CaptchaField()

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
        extra_fields = ['email']



class ProfileUpdateForm(forms.Form):
    email = forms.EmailField(label="Ваша електронна пошта")
    avatar = forms.ImageField(label="Новий аватар", required=False)

    def __init__(self, *args, **kwargs):
        # Приймаємо користувача через аргументи форми
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            # Заповнюємо початкове значення полів з поточного профілю
            self.fields['email'].initial = self.user.email

    def clean_email(self):
        # За замовчуванням поле email у моделі User не є унікальним.
        email = self.cleaned_data.get('email')
        # Перевіримо, чи інший користувач вже має таку адресу
        if User.objects.filter(email=email).exclude(username=self.user.username).exists():
            raise forms.ValidationError("Ця електронна адреса вже використовується.")
        return email

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Приклад додаткової перевірки: обмеження розміру файлу (наприклад, 2MB)
            max_size = 2 * 1024 * 1024  # 2 мегабайти
            if avatar.size > max_size:
                raise forms.ValidationError("Розмір файлу занадто великий (макс. 2MB).")
        return avatar
