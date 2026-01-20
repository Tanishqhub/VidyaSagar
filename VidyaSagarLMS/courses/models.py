from django.db import models

class Course(models.Model):
    cid = models.CharField(max_length=10, unique=True, primary_key=True)
    title = models.CharField(max_length=200)
    duration_days = models.IntegerField()
    duration_months = models.DecimalField(max_digits=5, decimal_places=2)
    fees = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.cid} - {self.title}"

class Module(models.Model):
    mid = models.AutoField(primary_key=True)
    m_title = models.CharField(max_length=200)
    no_of_sessions = models.IntegerField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    
    def __str__(self):
        return f"{self.mid} - {self.m_title}"

class Session(models.Model):
    sid = models.AutoField(primary_key=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='sessions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    topics = models.TextField()
    session_number = models.IntegerField()
    
    class Meta:
        ordering = ['session_number']
    
    def __str__(self):
        return f"Session {self.session_number}: {self.topics[:50]}..."
