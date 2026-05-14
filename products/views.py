from datetime import timedelta
import csv
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .forms import ProductForm, RegisterForm
from .models import Product
from .serializers import ProductSerializer


# Provides authenticated CRUD API endpoints for products through a DRF router.
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Returns only the requesting user's products and supports search/filter/sort query params.
    def get_queryset(self):
        queryset = Product.objects.filter(owner=self.request.user)
        search = self.request.query_params.get("search", "").strip()
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        ordering = self.request.query_params.get("ordering", "-created_at")
        allowed_ordering = {"name", "-name", "price", "-price", "created_at", "-created_at"}

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(email__icontains=search)
            )

        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        if ordering not in allowed_ordering:
            ordering = "-created_at"

        return queryset.order_by(ordering)

    # Saves API-created products under the current user and copies their account email.
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, email=self.request.user.email)

    # Exposes a small analytics endpoint at /api/products/stats/.
    @action(detail=False, methods=["get"])
    def stats(self, request):
        products = self.get_queryset()
        latest_product = products.order_by("-created_at").first()
        return Response(
            {
                "total_products": products.count(),
                "total_inventory_value": products.aggregate(total=Sum("price"))["total"] or 0,
                "latest_product": latest_product.name if latest_product else None,
            }
        )


# Sends a product-form question to Groq and returns a short JSON answer.
@login_required
@require_POST
def product_help(request):
    question = request.POST.get("question", "").strip()

    if not question:
        return JsonResponse({"error": "Please type a question first."}, status=400)

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return JsonResponse({"error": "GROQ_API_KEY is not set."}, status=500)

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You help users fill out a product catalog form. "
                    "Give short, practical answers about product names, prices, "
                    "descriptions, and contact email fields."
                ),
            },
            {"role": "user", "content": question},
        ],
    }

    groq_request = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(groq_request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        message = error.read().decode("utf-8") or str(error)
        return JsonResponse({"error": message}, status=502)
    except URLError as error:
        return JsonResponse({"error": str(error)}, status=502)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Groq returned invalid JSON."}, status=502)

    try:
        answer = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return JsonResponse({"error": data}, status=502)

    return JsonResponse({"answer": answer})


# Shows the dashboard with product totals, value, daily activity, and recent products.
@login_required
def home(request):
    today = timezone.localdate()
    start_date = today - timedelta(days=6)

    product_counts = (
        Product.objects.filter(owner=request.user, created_at__date__gte=start_date)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )

    counts_by_day = {item["day"]: item["total"] for item in product_counts}
    chart_days = [start_date + timedelta(days=offset) for offset in range(7)]
    chart_labels = [day.strftime("%b %d") for day in chart_days]
    chart_values = [counts_by_day.get(day, 0) for day in chart_days]
    user_products = Product.objects.filter(owner=request.user)

    return render(
        request,
        "home.html",
        {
            "chart_labels": chart_labels,
            "chart_values": chart_values,
            "products_total": user_products.count(),
            "inventory_value": user_products.aggregate(total=Sum("price"))["total"] or 0,
            "recent_products": user_products.order_by("-created_at")[:5],
        },
    )


# Creates a new product from the web form and assigns ownership to the logged-in user.
@login_required
def create_product(request):
    post_data = request.POST.copy() if request.method == "POST" else None
    if post_data is not None:
        post_data["email"] = request.user.email

    form = ProductForm(post_data, request.FILES or None, user=request.user)

    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.owner = request.user
        product.email = request.user.email
        product.save()
        return redirect("myproduct")

    return render(request, "form.html", {"form": form})


# Registers a local user account and signs the user in immediately after success.
def user_register(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.email = form.cleaned_data["email"]
        user.save(update_fields=["email"])
        login(request, user)
        return redirect("home")

    return render(
        request,
        "register.html",
        {"form": form, "google_login_enabled": settings.GOOGLE_LOGIN_ENABLED},
    )


# Authenticates an existing local user with username and password.
def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")

        return render(
            request,
            "login.html",
            {
                "error": "Invalid credentials",
                "google_login_enabled": settings.GOOGLE_LOGIN_ENABLED,
            },
        )

    return render(request, "login.html", {"google_login_enabled": settings.GOOGLE_LOGIN_ENABLED})


# Logs the current user out of the application.
def user_logout(request):
    logout(request)
    return redirect("login")


# Lists the current user's products with search, price filters, and sorting.
@login_required
def my_products(request):
    products = Product.objects.filter(owner=request.user)
    search = request.GET.get("search", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    ordering = request.GET.get("ordering", "-created_at")
    allowed_ordering = {"name", "-name", "price", "-price", "created_at", "-created_at"}

    if search:
        products = products.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(email__icontains=search)
        )

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    if ordering not in allowed_ordering:
        ordering = "-created_at"

    return render(
        request,
        "myproducts.html",
        {
            "products": products.order_by(ordering),
            "search": search,
            "min_price": min_price,
            "max_price": max_price,
            "ordering": ordering,
        },
    )


# Displays a single product record owned by the current user.
@login_required
def product_record(request, product_id):
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    return render(request, "record_page.html", {"product": product})


# Updates an existing product owned by the current user.
@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    post_data = request.POST.copy() if request.method == "POST" else None
    if post_data is not None:
        post_data["email"] = request.user.email

    form = ProductForm(
        post_data,
        request.FILES or None,
        instance=product,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.email = request.user.email
        product.save()
        return redirect("myproduct")

    return render(request, "form.html", {"form": form, "product": product})


# Deletes an existing product after a POST confirmation.
@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, owner=request.user)

    if request.method == "POST":
        product.delete()

    return redirect("myproduct")


# Downloads the current user's product list as a CSV file.
@login_required
def export_products_csv(request):
    products = Product.objects.filter(owner=request.user).order_by("-created_at")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)
    writer.writerow(["ID", "Name", "Price", "Description", "Email", "Created At"])

    for product in products:
        writer.writerow(
            [
                product.id,
                product.name,
                product.price,
                product.description,
                product.email,
                product.created_at.isoformat(),
            ]
        )

    return response
