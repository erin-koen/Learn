from django.urls import path
from .views import ProductDetailView, ProductListView

urlpatterns = [
    path("", ProductListView.as_view(), name="product-list"),
    #specifiy the primary key of the Product in the url below
    path("products/<int:pk>", ProductDetailView.as_view(), name="product-detail")
]