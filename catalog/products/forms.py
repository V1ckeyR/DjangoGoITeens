from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["contact_name", "contact_email", "contact_phone", "address"]
        labels = {
            "contact_name": "Client's name",
            "contact_email": "Email",
            "contact_phone": "Phone number",
            "address": "Delivery address",
        }