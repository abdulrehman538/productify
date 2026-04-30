from django.db import models
from django.conf import settings


class Product(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    description = models.TextField()
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name
