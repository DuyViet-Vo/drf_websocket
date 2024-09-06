from django.urls import path
from .views import ProductCreateView

urlpatterns = [
    path('products/create/', ProductCreateView.as_view(), name='create-product'),
]