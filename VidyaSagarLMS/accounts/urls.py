from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/choice/', views.register_choice, name='register_choice'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/trainer/', views.register_trainer, name='register_trainer'),
    path('logout/', views.logout_view, name='logout'),
]