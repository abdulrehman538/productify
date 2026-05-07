from django import forms
from .models import Product

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
