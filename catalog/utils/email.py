from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string

from catalog.products.models import Order

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


def send_order_confirmation_email(order: Order):
    subject = f"Підтвердження замовлення #{order.id}"
    # Згенеруємо текст листа за допомогою шаблону
    context = {"order": order}
    text_content = render_to_string("order/email_confirmation.txt", context)
    html_content = render_to_string("order/email_confirmation.html", context)
    to_email = order.contact_email
    try:
        send_mail(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,  # лист від нашого сайту
            [to_email, settings.ADMIN_EMAIL],
            html_message=html_content  # відправимо альтернативну HTML-версію
        )
        
    except Exception as e:
        # У продакшні тут можна залогувати помилку відправки
        print(f"Error sending email: {e}")
