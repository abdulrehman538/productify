from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Product


# Handles local account registration with an email address for seller contact details.
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


# Builds the product form and locks seller email to the logged-in user.
class ProductForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        user_email = getattr(user, "email", "") if user else ""
        if user_email:
            self.fields["email"].initial = user_email

        self.fields["email"].widget.attrs.update({"readonly": "readonly"})

    class Meta:
        model = Product
        fields = ["name", "price", "image", "description", "email"]
        widgets = {
            "image": forms.FileInput(attrs={"accept": "image/*"}),
        }
