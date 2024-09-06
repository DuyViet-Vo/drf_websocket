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