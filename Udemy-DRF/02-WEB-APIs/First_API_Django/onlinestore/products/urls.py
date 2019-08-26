from django.urls import path
from .views import product_list, product_detail, manufacturer_detail, active_manufacturers

urlpatterns = [
    path("products/", product_list, name="product-list"),
    path("products/<int:pk>", product_detail, name="product-detail"),
    path("manufacturers/<int:pk>", manufacturer_detail, name="manufacturer-detail"),
    path("manufacturers/active", active_manufacturers, name = "active-mfgs")
]
