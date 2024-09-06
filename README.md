# Django REST Framework Web Socket

## Project Setup

### Cài đặt Django, Django Rest Framework, Django Channels, và Daphne:
```sh
pip install django djangorestframework channels daphne
```

### Tạo một project Django mới và ứng dụng products:

```sh
# Tạo project
django-admin startproject myproject
# Di chuyển vào thư mục project
cd myproject
# Tạo app products
python manage.py startapp products
```

### Mở file settings.py và cấu hình một số phần như sau:
#### Thêm các app vào INSTALLED_APPS:

```sh
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'channels',  # Thêm Django Channels
    'products',  # Thêm app products
]
```
#### Cấu hình ASGI trong settings.py:
```sh
ASGI_APPLICATION = 'myproject.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',  # Lưu trữ trong bộ nhớ
    },
}
```
### Tạo model Product
```sh
# products/models.py

from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()

    def __str__(self):
        return self.name
```
### Chạy lệnh sau để tạo bảng trong cơ sở dữ liệu:
```sh
python manage.py makemigrations
python manage.py migrate
```
### Tạo serializer cho Product:
```sh
# products/serializers.py

from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'description']
```
### Viết API cho Product
```sh
# products/views.py

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer

class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def perform_create(self, serializer):
        product = serializer.save()

        # Gửi thông báo WebSocket sau khi tạo thành công sản phẩm
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'product_group',  # Group WebSocket client đã tham gia
            {
                'type': 'send_product_notification',
                'message': {
                    'name': product.name,
                    'price': str(product.price),  # Đảm bảo kiểu dữ liệu hợp lệ
                    'description': product.description,
                }
            }
        )
```
### Tạo routing cho API
```sh
# products/urls.py

from django.urls import path
from .views import ProductCreateView

urlpatterns = [
    path('products/create/', ProductCreateView.as_view(), name='create-product'),
]
```
#### Trong myproject/urls.py, thêm đường dẫn của app products:
```sh
# myproject/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('products.urls')),
]
```
### Cấu hình WebSocket cho sản phẩm:
```sh
# products/routing.py

from django.urls import path
from .consumers import ProductConsumer

websocket_urlpatterns = [
    path('ws/products/', ProductConsumer.as_asgi()),
]
```
#### Tạo file consumers.py trong app products:
```sh
# products/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ProductConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'product_group'

        # Tham gia nhóm 'product_group'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Rời khỏi nhóm 'product_group'
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Hàm này nhận sự kiện từ 'group_send' và gửi dữ liệu tới client
    async def send_product_notification(self, event):
        message = event['message']

        # Gửi dữ liệu sản phẩm tới WebSocket client
        await self.send(text_data=json.dumps({
            'message': message
        }))
```
### Cấu hình WebSocket trong asgi.py
```sh
# myproject/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import products.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            products.routing.websocket_urlpatterns
        )
    ),
})
```
### Cấu hình redis-server  
```sh
docker run --name redis-server -p 6379:6379 -d redis
```
### Chạy project:
```sh
daphne -b 0.0.0.0 -p 8001 myproject.asgi:application
```
### Kết nối WebSocket từ frontend:
```sh
ws://localhost:8001/ws/products/
```
