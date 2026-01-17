from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class EventCategory(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Event Categories"
    
    def __str__(self):
        return self.name

class CalendarEvent(models.Model):
    EVENT_TYPE_CHOICES = (
        ('class', 'Class/Lecture'),
        ('meeting', 'Meeting'),
        ('exam', 'Exam'),
        ('holiday', 'Holiday'),
        ('event', 'Special Event'),
        ('assignment', 'Assignment Due'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='class')
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Date and Time
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    
    # Location
    location = models.CharField(max_length=200, blank=True)
    room = models.CharField(max_length=50, blank=True)
    
    # Participants
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    trainers = models.ManyToManyField(User, related_name='trainer_events', blank=True, limit_choices_to={'role': 'trainer'})
    students = models.ManyToManyField(User, related_name='student_events', blank=True, limit_choices_to={'role': 'student'})
    
    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True)  # 'daily', 'weekly', 'monthly'
    recurrence_end_date = models.DateField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_date', 'start_time']
    
    def __str__(self):
        return f"{self.title} - {self.start_date}"
    
    @property
    def is_past(self):
        today = timezone.now().date()
        return self.end_date or self.start_date < today
    
    @property
    def is_today(self):
        today = timezone.now().date()
        return self.start_date == today

class CourseSchedule(models.Model):
    DAY_CHOICES = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )
    
    course_name = models.CharField(max_length=200)
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'trainer'})
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.course_name} - {self.get_day_of_week_display()} {self.start_time}"

class Attendance(models.Model):
    event = models.ForeignKey(CalendarEvent, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    attended = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['event', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.event.title}"
