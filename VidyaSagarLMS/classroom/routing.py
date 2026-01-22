# classroom/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/classroom/(?P<meeting_id>[^/]+)/$', consumers.ClassroomConsumer.as_asgi()),
]