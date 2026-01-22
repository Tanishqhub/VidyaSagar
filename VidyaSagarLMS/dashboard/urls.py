from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('grant-access/<int:user_id>/', views.grant_user_course_access, name='dashboard_grant_access'),
]