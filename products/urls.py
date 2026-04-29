from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_product, name='home'),
    path('create/', views.create_product, name='create'),
    path('login/', views.user_login, name='login'),
    path('logout/',views.user_logout, name='logout'),
    path('my_products/',views.my_products, name='myproduct')
]
