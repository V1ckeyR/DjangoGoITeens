from django.urls import path
from django.contrib.auth import views as auth_views

from .views import register, login_view, logout_view, profile_view, edit_profile_view, confirm_email

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('edit_profile/', edit_profile_view, name='edit_profile'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),
    path('confirm-email/', confirm_email, name='confirm_email'),
]
