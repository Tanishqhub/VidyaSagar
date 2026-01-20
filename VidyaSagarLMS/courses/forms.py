from django import forms
from .models import Module, Session

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['m_title', 'no_of_sessions']
        widgets = {
            'm_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter module title'
            }),
            'no_of_sessions': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Number of sessions'
            }),
        }
        labels = {
            'm_title': 'Module Title',
            'no_of_sessions': 'Number of Sessions'
        }

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['session_number', 'topics']
        widgets = {
            'session_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Session number'
            }),
            'topics': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter topics covered in this session'
            }),
        }
        labels = {
            'session_number': 'Session Number',
            'topics': 'Topics'
        }
    
    def clean_session_number(self):
        session_number = self.cleaned_data.get('session_number')
        if session_number < 1:
            raise forms.ValidationError("Session number must be at least 1")
        return session_number