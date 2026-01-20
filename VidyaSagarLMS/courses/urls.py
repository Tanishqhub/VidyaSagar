from django.urls import path
from . import views

urlpatterns = [
    # Course URLs
    path('', views.CourseListView.as_view(), name='course_list'),
    path('course/<str:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('course/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('course/<str:pk>/update/', views.CourseUpdateView.as_view(), name='course_update'),
    path('course/<str:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    path('access/grant/', views.grant_course_access, name='course_grant_access'),
    
    # Module URLs
    path('course/<str:cid>/modules/', views.ModuleListView.as_view(), name='module_list'),
    path('module/<int:pk>/', views.ModuleDetailView.as_view(), name='module_detail'),
    path('course/<str:cid>/module/create/', views.ModuleCreateView.as_view(), name='module_create'),
    path('module/<int:pk>/update/', views.ModuleUpdateView.as_view(), name='module_update'),
    path('module/<int:pk>/delete/', views.ModuleDeleteView.as_view(), name='module_delete'),
    
    # Session URLs
    path('course/<str:cid>/sessions/', views.SessionListView.as_view(), name='course_session_list'),
    path('module/<int:mid>/sessions/', views.SessionListView.as_view(), name='module_session_list'),
    path('session/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('module/<int:mid>/session/create/', views.SessionCreateView.as_view(), name='session_create'),
    path('session/<int:pk>/update/', views.SessionUpdateView.as_view(), name='session_update'),
    path('session/<int:pk>/delete/', views.SessionDeleteView.as_view(), name='session_delete'),
]