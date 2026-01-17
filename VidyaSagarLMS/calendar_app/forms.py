from django import forms
from .models import CalendarEvent, EventCategory, CourseSchedule, Attendance
from django.contrib.auth import get_user_model

User = get_user_model()

class EventCategoryForm(forms.ModelForm):
    class Meta:
        model = EventCategory
        fields = ['name', 'color', 'description']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = [
            'title', 'description', 'event_type', 'category',
            'start_date', 'end_date', 'start_time', 'end_time', 'all_day',
            'location', 'room', 'trainers', 'students',
            'is_recurring', 'recurrence_pattern', 'recurrence_end_date'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'recurrence_end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'trainers': forms.SelectMultiple(attrs={'class': 'select2'}),
            'students': forms.SelectMultiple(attrs={'class': 'select2'}),
        }

class CourseScheduleForm(forms.ModelForm):
    class Meta:
        model = CourseSchedule
        fields = ['course_name', 'trainer', 'day_of_week', 'start_time', 'end_time', 'room', 'is_active']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['attended', 'check_in_time', 'check_out_time', 'remarks']
        widgets = {
            'check_in_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'check_out_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

class BulkAttendanceForm(forms.Form):
    event = forms.ModelChoiceField(queryset=CalendarEvent.objects.filter(event_type='class'))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically add fields for each student
        students = User.objects.filter(role='student')
        for student in students:
            self.fields[f'student_{student.id}'] = forms.BooleanField(
                label=student.username,
                required=False,
                initial=True
            )