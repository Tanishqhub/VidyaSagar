# classroom/forms.py
from django import forms
from django.contrib.auth import get_user_model
from courses.models import Course, Module, Session
from .models import Batch, Classroom, ClassroomEnrollment, ClassroomSession, Attendance

CustomUser = get_user_model()

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['batch_id', 'batch_name', 'description', 'start_date', 'end_date', 'is_active']
        widgets = {
            'batch_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BATCH001'}),
            'batch_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Morning Batch 2024'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance

class ClassroomForm(forms.ModelForm):
    # Use single-select fields in the form UI but map to M2M on save
    modules = forms.ModelChoiceField(
        queryset=Module.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sessions = forms.ModelChoiceField(
        queryset=Session.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter trainers only
        self.fields['trainer'].queryset = CustomUser.objects.filter(role='trainer')
        
        # Filter active courses
        self.fields['course'].queryset = Course.objects.all()
        
        # Initially empty modules and sessions (single-select)
        self.fields['modules'].queryset = Module.objects.none()
        self.fields['sessions'].queryset = Session.objects.none()
        
        if 'course' in self.data:
            try:
                course_id = self.data.get('course')
                if course_id:
                    self.fields['modules'].queryset = Module.objects.filter(course_id=course_id)
                    self.fields['sessions'].queryset = Session.objects.filter(course_id=course_id)
            except Exception:
                pass
        elif self.instance.pk:
            self.fields['modules'].queryset = self.instance.course.modules.all()
            # If the classroom already has modules/sessions, preselect the first
            existing_modules = self.instance.modules.all()
            if existing_modules.exists():
                self.initial['modules'] = existing_modules.first()
            existing_sessions = self.instance.sessions.all()
            if existing_sessions.exists():
                self.initial['sessions'] = existing_sessions.first()
            else:
                self.fields['sessions'].queryset = Session.objects.filter(course=self.instance.course)
    
    class Meta:
        model = Classroom
        fields = [
            'classroom_id', 'classroom_name', 'batch', 'course', 'trainer',
            'start_date', 'end_date', 'schedule_days', 'start_time', 'end_time',
            'status', 'max_students', 'modules', 'sessions'
        ]
        widgets = {
            'classroom_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CLS001'}),
            'classroom_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python Fundamentals Class'}),
            'batch': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'trainer': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'schedule_days': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mon, Wed, Fri'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'modules': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 5}),
            'sessions': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 8}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.created_by = self.user
        if commit:
            instance.save()
            # Map single-select fields back to M2M relations
            modules_selected = self.cleaned_data.get('modules')
            sessions_selected = self.cleaned_data.get('sessions')

            if modules_selected:
                instance.modules.set([modules_selected])
            else:
                instance.modules.clear()

            # sessions uses a through model ClassroomSession; create entries instead
            if sessions_selected:
                # ensure a ClassroomSession exists for this classroom and session
                try:
                    from datetime import date, time
                    # use classroom start_date/start_time as defaults if present
                    default_date = instance.start_date or date.today()
                    default_time = instance.start_time or time(9, 0)
                    ClassroomSession.objects.get_or_create(
                        classroom=instance,
                        session=sessions_selected,
                        defaults={
                            'scheduled_date': default_date,
                            'scheduled_time': default_time,
                            'duration_minutes': 60
                        }
                    )
                except Exception:
                    # fallback: ignore errors creating sessions to avoid breaking save
                    pass
            else:
                # don't automatically delete existing ClassroomSession entries
                pass

        return instance

class ClassroomEnrollmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.classroom = kwargs.pop('classroom', None)
        super().__init__(*args, **kwargs)
        
        if self.classroom:
            # Get students not already enrolled in this classroom
            enrolled_students = self.classroom.students.all()
            available_students = CustomUser.objects.filter(
                role='student'
            ).exclude(
                pk__in=enrolled_students.values_list('pk', flat=True)
            )
            self.fields['student'].queryset = available_students
    
    class Meta:
        model = ClassroomEnrollment
        fields = ['student', 'status', 'grade', 'comments']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A, B, C...'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        
        if self.classroom and student:
            # Check if classroom is full
            if self.classroom.is_full:
                raise forms.ValidationError("This classroom is already full.")
            
            # Check if student is already enrolled
            if ClassroomEnrollment.objects.filter(classroom=self.classroom, student=student).exists():
                raise forms.ValidationError("This student is already enrolled in this classroom.")
        
        return cleaned_data

class ClassroomSessionForm(forms.ModelForm):
    class Meta:
        model = ClassroomSession
        fields = ['session', 'scheduled_date', 'scheduled_time', 'duration_minutes', 'is_completed', 'completed_date', 'notes']
        widgets = {
            'session': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'scheduled_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 30}),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'completed_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'status', 'check_in_time', 'check_out_time', 'remarks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'check_in_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'check_out_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

# Filter forms for AJAX
class CourseModuleFilterForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_course_filter'})
    )

class ModuleSessionFilterForm(forms.Form):
    module = forms.ModelChoiceField(
        queryset=Module.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_module_filter'})
    )