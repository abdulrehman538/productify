from django.contrib import admin
from .models import Product


# Adds product search, filtering, and helpful columns to the Django admin.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "owner", "price", "email", "created_at"]
    search_fields = ["name", "description", "email", "owner__username"]
    list_filter = ["created_at", "price"]

    readonly_fields = ["email", "created_at"]
