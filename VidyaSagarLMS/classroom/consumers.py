# classroom/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import VirtualClassroom, ClassroomParticipant, ChatMessage

CustomUser = get_user_model()

class ClassroomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.room_group_name = f'classroom_{self.meeting_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Update participant status
        await self.update_participant_status(False)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'join':
            await self.handle_join(data)
        elif message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'whiteboard_update':
            await self.handle_whiteboard_update(data)
        elif message_type == 'participant_update':
            await self.handle_participant_update(data)
        elif message_type == 'screen_share':
            await self.handle_screen_share(data)
    
    async def handle_join(self, data):
        # Add user to participants
        user_id = data['user_id']
        username = data['username']
        
        await self.update_participant_status(True)
        
        # Send join notification to others
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participant_joined',
                'user_id': user_id,
                'username': username
            }
        )
    
    async def handle_chat_message(self, data):
        # Save chat message
        await self.save_chat_message(data)
        
        # Broadcast to all participants
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': data['message'],
                'user_id': data['user_id'],
                'username': data['username']
            }
        )
    
    async def handle_whiteboard_update(self, data):
        # Broadcast whiteboard update
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'whiteboard_update',
                'data': data['data'],
                'user_id': data['user_id']
            }
        )
    
    async def handle_participant_update(self, data):
        # Update participant status in database
        await self.update_participant_in_db(data)
        
        # Broadcast update
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participant_update',
                'user_id': data['user_id'],
                **{k: v for k, v in data.items() if k not in ['type', 'user_id']}
            }
        )
    
    # Handler methods for different message types
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    async def whiteboard_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'whiteboard_update',
            'data': event['data'],
            'user_id': event['user_id']
        }))
    
    async def participant_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'participant_update',
            **event
        }))
    
    async def participant_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'participant_joined',
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    async def participant_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'participant_left',
            'user_id': event['user_id']
        }))
    
    # Database operations
    @database_sync_to_async
    def update_participant_status(self, is_present):
        try:
            user = CustomUser.objects.get(id=self.scope['user'].id)
            virtual_classroom = VirtualClassroom.objects.get(meeting_id=self.meeting_id)
            
            participant, created = ClassroomParticipant.objects.get_or_create(
                virtual_classroom=virtual_classroom,
                user=user
            )
            
            participant.is_present = is_present
            participant.save()
            return True
        except:
            return False
    
    @database_sync_to_async
    def save_chat_message(self, data):
        try:
            user = CustomUser.objects.get(id=data['user_id'])
            virtual_classroom = VirtualClassroom.objects.get(meeting_id=self.meeting_id)
            
            ChatMessage.objects.create(
                virtual_classroom=virtual_classroom,
                user=user,
                message=data['message']
            )
            return True
        except:
            return False
    
    @database_sync_to_async
    def update_participant_in_db(self, data):
        try:
            user = CustomUser.objects.get(id=data['user_id'])
            virtual_classroom = VirtualClassroom.objects.get(meeting_id=self.meeting_id)
            
            participant = ClassroomParticipant.objects.get(
                virtual_classroom=virtual_classroom,
                user=user
            )
            
            if 'raise_hand' in data:
                participant.raise_hand = data['raise_hand']
            if 'is_muted' in data:
                participant.is_muted = data['is_muted']
            if 'video_enabled' in data:
                participant.video_enabled = data['video_enabled']
            
            participant.save()
            return True
        except:
            return False