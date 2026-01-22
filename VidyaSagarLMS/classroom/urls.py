# classroom/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.ClassroomDashboardView.as_view(), name='classroom_dashboard'),
    
    # Batch URLs
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batch/create/', views.BatchCreateView.as_view(), name='batch_create'),
    path('batch/<str:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),
    path('batch/<str:pk>/update/', views.BatchUpdateView.as_view(), name='batch_update'),
    path('batch/<str:pk>/delete/', views.BatchDeleteView.as_view(), name='batch_delete'),
    
    # Classroom URLs
    path('', views.ClassroomListView.as_view(), name='classroom_list'),
    path('create/', views.ClassroomCreateView.as_view(), name='classroom_create'),
    path('<str:pk>/', views.ClassroomDetailView.as_view(), name='classroom_detail'),
    path('<str:pk>/update/', views.ClassroomUpdateView.as_view(), name='classroom_update'),
    path('<str:pk>/delete/', views.ClassroomDeleteView.as_view(), name='classroom_delete'),
    
    # Enrollment URLs
    path('<str:classroom_id>/enroll/create/', views.EnrollmentCreateView.as_view(), name='enrollment_create'),
    path('enrollment/<int:pk>/update/', views.EnrollmentUpdateView.as_view(), name='enrollment_update'),
    path('enrollment/<int:pk>/delete/', views.EnrollmentDeleteView.as_view(), name='enrollment_delete'),
    
    # AJAX URLs
    path('ajax/get-modules/', views.get_modules_by_course, name='ajax_get_modules'),
    path('ajax/get-sessions-by-course/', views.get_sessions_by_course, name='ajax_get_sessions_by_course'),
    path('ajax/get-sessions-by-module/', views.get_sessions_by_module, name='ajax_get_sessions_by_module'),
    
    # Trainer specific
    path('trainer/my-classrooms/', views.TrainerClassroomListView.as_view(), name='trainer_classrooms'),
    
    # Student specific
    path('student/my-classrooms/', views.StudentClassroomListView.as_view(), name='student_classrooms'),
]