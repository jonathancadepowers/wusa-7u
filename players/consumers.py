import json
from channels.generic.websocket import AsyncWebsocketConsumer


class DraftConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join draft updates group
        self.group_name = 'draft_updates'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave draft updates group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # We don't expect to receive messages from clients in this implementation
        pass

    # Receive message from group
    async def draft_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'draft_update',
            'player_id': event['player_id'],
            'player_name': event['player_name'],
            'team_name': event['team_name'],
            'round': event['round'],
            'pick': event['pick']
        }))
