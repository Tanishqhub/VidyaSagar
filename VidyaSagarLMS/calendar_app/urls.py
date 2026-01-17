from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('events/json/', views.calendar_events_json, name='calendar_events_json'),
    path('day/<int:year>/<int:month>/<int:day>/', views.day_view, name='day_view'),
    path('day/', views.day_view, name='today_view'),
    
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/add/', views.add_event, name='add_event'),
    path('event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('event/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    
    path('categories/', views.manage_categories, name='manage_categories'),
    path('schedules/', views.course_schedules, name='course_schedules'),
    
    path('attendance/<int:event_id>/', views.take_attendance, name='take_attendance'),
    path('attendance/report/', views.attendance_report, name='attendance_report'),
]