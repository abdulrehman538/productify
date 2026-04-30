from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ProductForm
from .models import Product


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
    form = ProductForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
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
    form = ProductForm(request.POST or None, instance=product)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("myproduct")

    return render(request, "form.html", {"form": form, "product": product})


@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, owner=request.user)

    if request.method == "POST":
        product.delete()

    return redirect("myproduct")
