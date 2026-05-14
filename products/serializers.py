from rest_framework import serializers
from .models import Product


# Serializes product records for the REST API and keeps ownership server-controlled.
class ProductSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "owner",
            "owner_username",
            "name",
            "image",
            "price",
            "description",
            "email",
            "created_at",
        ]
        read_only_fields = ["id", "owner", "owner_username", "email", "created_at"]
