from django.db import models
from django.contrib.auth import get_user_model
from courses.models import Course, Module, Session

CustomUser = get_user_model()

class Batch(models.Model):
    batch_id = models.CharField(max_length=20, unique=True, primary_key=True)
    batch_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_batches')
    
    class Meta:
        verbose_name_plural = "Batches"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.batch_id} - {self.batch_name}"
    
    @property
    def total_classrooms(self):
        return self.classrooms.count()
    
    @property
    def total_students(self):
        from django.db.models import Count
        return StudentProfile.objects.filter(
            user__classroomenrollment__classroom__batch=self
        ).distinct().count()

class Classroom(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    classroom_id = models.CharField(max_length=20, unique=True, primary_key=True)
    classroom_name = models.CharField(max_length=200)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='classrooms')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='classrooms')
    trainer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='classrooms_as_trainer', 
                              limit_choices_to={'role': 'trainer'})
    students = models.ManyToManyField(CustomUser, related_name='classrooms_as_student', 
                                    through='ClassroomEnrollment',
                                    limit_choices_to={'role': 'student'})
    
    # Course structure
    modules = models.ManyToManyField(Module, related_name='classrooms')
    sessions = models.ManyToManyField(Session, related_name='classrooms', through='ClassroomSession')
    
    # Schedule
    start_date = models.DateField()
    end_date = models.DateField()
    schedule_days = models.CharField(max_length=100, help_text="e.g., Mon, Wed, Fri")
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    max_students = models.IntegerField(default=30)
    
    # Manager info
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, 
                                 related_name='created_classrooms',
                                 limit_choices_to={'role__in': ['manager', 'admin', 'superadmin']})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.classroom_id} - {self.classroom_name}"
    
    @property
    def current_students(self):
        return self.students.count()
    
    @property
    def available_seats(self):
        return self.max_students - self.current_students
    
    @property
    def is_full(self):
        return self.current_students >= self.max_students
    
    @property
    def duration_weeks(self):
        from datetime import timedelta
        weeks = (self.end_date - self.start_date).days // 7
        return f"{weeks} weeks"
    
    @property
    def total_sessions(self):
        return self.sessions.count()
    
    def get_trainer_profile(self):
        try:
            return self.trainer.trainerprofile
        except:
            return None
    
    def get_student_profiles(self):
        return StudentProfile.objects.filter(user__in=self.students.all())

class ClassroomEnrollment(models.Model):
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('attending', 'Attending'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('pending', 'Pending'),
    ]
    
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrollments',
                              limit_choices_to={'role': 'student'})
    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    grade = models.CharField(max_length=5, blank=True, null=True)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    comments = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['classroom', 'student']
        ordering = ['enrollment_date']
    
    def __str__(self):
        return f"{self.student.username} in {self.classroom.classroom_name}"
    
    @property
    def student_profile(self):
        try:
            return self.student.studentprofile
        except:
            return None

class ClassroomSession(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='classroom_sessions')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='classroom_sessions')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.IntegerField(default=60)
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    attendance_taken = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['classroom', 'session']
        ordering = ['scheduled_date', 'scheduled_time']
    
    def __str__(self):
        return f"{self.session} in {self.classroom} on {self.scheduled_date}"

class Attendance(models.Model):
    classroom_session = models.ForeignKey(ClassroomSession, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='classroom_attendances',
                              limit_choices_to={'role': 'student'})
    status_choices = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='present')
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['classroom_session', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.status} - {self.classroom_session}"
