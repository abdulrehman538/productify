from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_url = reverse("login")

        # ✅ FIX: allow ALL admin URLs properly
        if request.path.startswith("/admin/"):
            return self.get_response(request)

        if request.path.startswith("/static/"):
            return self.get_response(request)

        if not request.user.is_authenticated:
            if request.path != login_url:
                return redirect("login")

        if request.user.is_authenticated and request.path == login_url:
            return redirect("home")

        return self.get_response(request)