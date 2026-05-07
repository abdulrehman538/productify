from datetime import timedelta
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ProductSerializer
from .forms import ProductForm
from .models import Product
from rest_framework import generics



# ---------------- API ENDPOINTS ---------------- #

@api_view(['GET'])
def api_products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def api_product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    serializer = ProductSerializer(product)
    return Response(serializer.data)


# ---------------- GROQ AI FUNCTION ---------------- #

@login_required
@require_POST
def product_help(request):
    question = request.POST.get("question", "").strip()

    if not question:
        return JsonResponse({"error": "Please type a question first."}, status=400)

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return JsonResponse({"error": "GROQ_API_KEY is not set."}, status=500)

    url = "https://api.groq.com/openai/v1/chat/completions"

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
            {
                "role": "user",
                "content": question,
            },
        ],
    }

    request_data = json.dumps(payload).encode("utf-8")

    groq_request = Request(
        url,
        data=request_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Mozilla/5.0",   # 🔥 Fixes 1010 error
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


# ---------------- MAIN VIEWS ---------------- #

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

    products_total = Product.objects.filter(owner=request.user).count()
    recent_products = Product.objects.filter(owner=request.user).order_by("-created_at")[:5]

    return render(
        request,
        "home.html",
        {
            "chart_labels": chart_labels,
            "chart_values": chart_values,
            "products_total": products_total,
            "recent_products": recent_products,
        },
    )


@login_required
def create_product(request):
    post_data = request.POST.copy() if request.method == "POST" else None
    if post_data is not None:
        post_data["email"] = request.user.email

    form = ProductForm(post_data, request.FILES or None, user=request.user)

    if request.method == "POST":
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.email = request.user.email
            product.save()
            return redirect("myproduct")

    return render(request, "form.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            return render(request, "login.html", {"error": "Invalid credentials"})

    return render(request, "login.html")


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def my_products(request):
    products = Product.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "myproducts.html", {"products": products})


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


@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, owner=request.user)

    if request.method == "POST":
        product.delete()

    return redirect("myproduct")

class ProductCreateAPIView(
    generics.CreateAPIView

):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
