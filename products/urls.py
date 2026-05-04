from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('create/', views.create_product, name='create'),
    path('edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('logout/', views.user_logout, name='logout'),
    path('my_products/', views.my_products, name='myproduct'),
    path('api/products/', views.api_products),
    path('api/products/<int:product_id>/', views.api_product_detail),
]
