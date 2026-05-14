from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    # Stores the next response handler when Django builds the middleware chain.
    def __init__(self, get_response):
        self.get_response = get_response

    # Redirects anonymous web users to login while allowing public/system routes.
    def __call__(self, request):
        login_url = reverse("login")
        register_url = reverse("register")

        public_prefixes = (
            "/admin/",
            "/api/",
            "/accounts/",
            "/media/",
            "/static/",
        )

        if request.path.startswith(public_prefixes):
            return self.get_response(request)

        if not request.user.is_authenticated and request.path not in {login_url, register_url}:
            return redirect("login")

        if request.user.is_authenticated and request.path in {login_url, register_url}:
            return redirect("home")

        return self.get_response(request)
