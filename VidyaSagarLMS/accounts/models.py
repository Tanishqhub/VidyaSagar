from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('trainer', 'Trainer'),
        ('student', 'Student'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    course_access = models.BooleanField(default=False)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.role}"

class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    course = models.CharField(max_length=100)
    enrollment_date = models.DateField()
    
    def __str__(self):
        return f"{self.user.username} - {self.student_id}"

class TrainerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    trainer_id = models.CharField(max_length=20, unique=True)
    specialization = models.CharField(max_length=100)
    experience = models.IntegerField(help_text="Experience in years")
    joining_date = models.DateField()
    
    def __str__(self):
        return f"{self.user.username} - {self.trainer_id}"
