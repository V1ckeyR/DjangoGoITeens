from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    payment_method = forms.ChoiceField(choices=[
        ("liqpay", "Онлайн карткою (LiqPay)"),
        ("monopay", "Онлайн карткою (MonoPay)"),
        ("google", "Google Pay"),
        ("cash", "Готівкою при отриманні")
    ], label="Спосіб оплати")

    class Meta:
        model = Order
        fields = ["contact_name", "contact_email", "contact_phone", "address", "payment_method"]
        labels = {
            "contact_name": "Client's name",
            "contact_email": "Email",
            "contact_phone": "Phone number",
            "address": "Delivery address",
        }