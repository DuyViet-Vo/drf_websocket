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