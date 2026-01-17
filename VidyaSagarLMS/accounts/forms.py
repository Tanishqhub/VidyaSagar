from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, StudentProfile, TrainerProfile

class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('trainer', 'Trainer'),
    )
    
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone', 'role', 'password1', 'password2')

class StudentRegistrationForm(UserCreationForm):
    student_id = forms.CharField(max_length=20, required=True)
    course = forms.CharField(max_length=100, required=True)
    enrollment_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                student_id=self.cleaned_data['student_id'],
                course=self.cleaned_data['course'],
                enrollment_date=self.cleaned_data['enrollment_date']
            )
        return user

class TrainerRegistrationForm(UserCreationForm):
    trainer_id = forms.CharField(max_length=20, required=True)
    specialization = forms.CharField(max_length=100, required=True)
    experience = forms.IntegerField(required=True)
    joining_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'trainer'
        if commit:
            user.save()
            TrainerProfile.objects.create(
                user=user,
                trainer_id=self.cleaned_data['trainer_id'],
                specialization=self.cleaned_data['specialization'],
                experience=self.cleaned_data['experience'],
                joining_date=self.cleaned_data['joining_date']
            )
        return user