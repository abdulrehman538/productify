from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("products", views.ProductViewSet, basename="product")

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('create/', views.create_product, name='create'),
    path('edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('logout/', views.user_logout, name='logout'),
    path('my_products/', views.my_products, name='myproduct'),
    path('product/<int:product_id>/', views.product_record, name='product_record'),
    path('export/products.csv', views.export_products_csv, name='export_products_csv'),
    path('product-help/', views.product_help, name='product_help'),
    path('api/', include(router.urls)),
]
