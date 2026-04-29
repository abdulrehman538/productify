from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import ProductForm

def create_product(request):
    form = ProductForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("create")
    
    return render(request, "form.html", {"form": form})

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('create')   
        else:
            return render(request, "login.html", {"error": "Invalid credentials"})

    return render(request, "login.html")

def user_logout(request):
    logout(request)
    return redirect('login')

def my_products(request):
        return render(redirect,"myproducts.html")