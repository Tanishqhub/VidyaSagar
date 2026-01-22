from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, Avg
from django.core.exceptions import PermissionDenied
from courses.models import Course, Module, Session
from .models import Batch, Classroom, ClassroomEnrollment, ClassroomSession, Attendance
from .forms import (BatchForm, ClassroomForm, ClassroomEnrollmentForm, 
                   ClassroomSessionForm, AttendanceForm, CourseModuleFilterForm)

# Mixin to check if user is manager/admin
class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in ['manager', 'admin', 'superadmin']
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('dashboard')

# Mixin to check if user is trainer or manager
class TrainerOrManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in ['trainer', 'manager', 'admin', 'superadmin']

# Batch Views
class BatchListView(ManagerRequiredMixin, ListView):
    model = Batch
    template_name = 'classroom/batch_list.html'
    context_object_name = 'batches'
    ordering = ['-created_at']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_batches'] = Batch.objects.count()
        context['active_batches'] = Batch.objects.filter(is_active=True).count()
        return context

class BatchCreateView(ManagerRequiredMixin, CreateView):
    model = Batch
    form_class = BatchForm
    template_name = 'classroom/batch_form.html'
    success_url = reverse_lazy('batch_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Batch created successfully!')
        return super().form_valid(form)

class BatchDetailView(ManagerRequiredMixin, DetailView):
    model = Batch
    template_name = 'classroom/batch_detail.html'
    context_object_name = 'batch'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classrooms'] = self.object.classrooms.all()
        context['total_students'] = self.object.total_students
        return context

class BatchUpdateView(ManagerRequiredMixin, UpdateView):
    model = Batch
    form_class = BatchForm
    template_name = 'classroom/batch_form.html'
    
    def get_success_url(self):
        messages.success(self.request, 'Batch updated successfully!')
        return reverse('batch_detail', kwargs={'pk': self.object.batch_id})

class BatchDeleteView(ManagerRequiredMixin, DeleteView):
    model = Batch
    template_name = 'classroom/batch_confirm_delete.html'
    success_url = reverse_lazy('batch_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Batch deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Classroom Views
class ClassroomListView(LoginRequiredMixin, ListView):
    model = Classroom
    template_name = 'classroom/classroom_list.html'
    context_object_name = 'classrooms'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role in ['manager', 'admin', 'superadmin']:
            return Classroom.objects.all().order_by('-created_at')
        elif user.role == 'trainer':
            return Classroom.objects.filter(trainer=user).order_by('-created_at')
        elif user.role == 'student':
            return Classroom.objects.filter(students=user).order_by('-created_at')
        
        return Classroom.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_classrooms'] = Classroom.objects.count()
        context['ongoing_classrooms'] = Classroom.objects.filter(status='ongoing').count()
        context['upcoming_classrooms'] = Classroom.objects.filter(status='planned').count()
        return context

class ClassroomCreateView(ManagerRequiredMixin, CreateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = 'classroom/classroom_form.html'
    success_url = reverse_lazy('classroom_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batches'] = Batch.objects.filter(is_active=True)
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Classroom created successfully!')
        return super().form_valid(form)

class ClassroomDetailView(LoginRequiredMixin, DetailView):
    model = Classroom
    template_name = 'classroom/classroom_detail.html'
    context_object_name = 'classroom'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classroom = self.object
        
        # Add enrollment data
        context['enrollments'] = classroom.enrollments.select_related('student').all()
        context['available_seats'] = classroom.available_seats
        
        # Add sessions
        context['sessions'] = classroom.classroom_sessions.all()
        
        # Add trainer profile
        context['trainer_profile'] = classroom.get_trainer_profile()
        
        # Add student profiles
        context['student_profiles'] = classroom.get_student_profiles()
        
        return context
    
    def dispatch(self, request, *args, **kwargs):
        classroom = self.get_object()
        user = request.user
        
        # Check access permissions
        if user.role in ['manager', 'admin', 'superadmin']:
            return super().dispatch(request, *args, **kwargs)
        elif user.role == 'trainer' and classroom.trainer == user:
            return super().dispatch(request, *args, **kwargs)
        elif user.role == 'student' and classroom.students.filter(pk=user.pk).exists():
            return super().dispatch(request, *args, **kwargs)
        
        messages.error(request, "You don't have permission to view this classroom.")
        return redirect('classroom_list')

class ClassroomUpdateView(ManagerRequiredMixin, UpdateView):
    model = Classroom
    form_class = ClassroomForm
    template_name = 'classroom/classroom_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        messages.success(self.request, 'Classroom updated successfully!')
        return reverse('classroom_detail', kwargs={'pk': self.object.classroom_id})

class ClassroomDeleteView(ManagerRequiredMixin, DeleteView):
    model = Classroom
    template_name = 'classroom/classroom_confirm_delete.html'
    success_url = reverse_lazy('classroom_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Classroom deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Enrollment Views
class EnrollmentCreateView(ManagerRequiredMixin, CreateView):
    model = ClassroomEnrollment
    form_class = ClassroomEnrollmentForm
    template_name = 'classroom/enrollment_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        classroom_id = self.kwargs.get('classroom_id')
        classroom = get_object_or_404(Classroom, classroom_id=classroom_id)
        kwargs['classroom'] = classroom
        return kwargs
    
    def form_valid(self, form):
        classroom_id = self.kwargs.get('classroom_id')
        classroom = get_object_or_404(Classroom, classroom_id=classroom_id)
        form.instance.classroom = classroom
        
        # Update enrollment status
        if form.instance.status == 'attending':
            classroom.students.add(form.instance.student)
        
        messages.success(self.request, 'Student enrolled successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        classroom_id = self.kwargs.get('classroom_id')
        return reverse('classroom_detail', kwargs={'pk': classroom_id})

class EnrollmentUpdateView(ManagerRequiredMixin, UpdateView):
    model = ClassroomEnrollment
    form_class = ClassroomEnrollmentForm
    template_name = 'classroom/enrollment_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['classroom'] = self.object.classroom
        return kwargs
    
    def get_success_url(self):
        messages.success(self.request, 'Enrollment updated successfully!')
        return reverse('classroom_detail', kwargs={'pk': self.object.classroom.classroom_id})

class EnrollmentDeleteView(ManagerRequiredMixin, DeleteView):
    model = ClassroomEnrollment
    template_name = 'classroom/enrollment_confirm_delete.html'
    
    def delete(self, request, *args, **kwargs):
        enrollment = self.get_object()
        classroom = enrollment.classroom
        
        # Remove student from classroom
        classroom.students.remove(enrollment.student)
        
        messages.success(request, 'Enrollment removed successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        classroom = self.get_object().classroom
        return reverse('classroom_detail', kwargs={'pk': classroom.classroom_id})

# AJAX Views for dynamic filtering
@require_POST
def get_modules_by_course(request):
    course_id = request.POST.get('course_id')
    modules = Module.objects.filter(course_id=course_id).values('mid', 'm_title')
    return JsonResponse(list(modules), safe=False)

@require_POST
def get_sessions_by_course(request):
    course_id = request.POST.get('course_id')
    sessions = Session.objects.filter(course_id=course_id).values('sid', 'session_number', 'topics')
    return JsonResponse(list(sessions), safe=False)

@require_POST
def get_sessions_by_module(request):
    module_id = request.POST.get('module_id')
    sessions = Session.objects.filter(module_id=module_id).values('sid', 'session_number', 'topics')
    return JsonResponse(list(sessions), safe=False)

# Dashboard Views
class ClassroomDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'classroom/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.role in ['manager', 'admin', 'superadmin']:
            # Manager dashboard
            context['total_classrooms'] = Classroom.objects.count()
            context['ongoing_classrooms'] = Classroom.objects.filter(status='ongoing').count()
            context['total_batches'] = Batch.objects.count()
            context['total_trainers'] = user.__class__.objects.filter(role='trainer').count()
            context['total_students'] = user.__class__.objects.filter(role='student').count()
            context['recent_classrooms'] = Classroom.objects.all().order_by('-created_at')[:5]
            
        elif user.role == 'trainer':
            # Trainer dashboard
            context['my_classrooms'] = Classroom.objects.filter(trainer=user).count()
            context['ongoing_classes'] = Classroom.objects.filter(trainer=user, status='ongoing').count()
            context['total_students'] = ClassroomEnrollment.objects.filter(
                classroom__trainer=user
            ).values('student').distinct().count()
            context['upcoming_sessions'] = ClassroomSession.objects.filter(
                classroom__trainer=user,
                is_completed=False
            ).order_by('scheduled_date')[:5]
            
        elif user.role == 'student':
            # Student dashboard
            context['my_classrooms'] = Classroom.objects.filter(students=user).count()
            context['active_classes'] = Classroom.objects.filter(students=user, status='ongoing').count()
            context['upcoming_sessions'] = ClassroomSession.objects.filter(
                classroom__students=user,
                is_completed=False
            ).order_by('scheduled_date')[:5]
            context['recent_attendance'] = Attendance.objects.filter(
                student=user
            ).order_by('-classroom_session__scheduled_date')[:10]
        
        return context

# Trainer specific views
class TrainerClassroomListView(TrainerOrManagerRequiredMixin, ListView):
    template_name = 'classroom/trainer_classrooms.html'
    context_object_name = 'classrooms'
    
    def get_queryset(self):
        return Classroom.objects.filter(trainer=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trainer_profile'] = self.request.user.trainerprofile
        return context

# Student specific views
class StudentClassroomListView(LoginRequiredMixin, ListView):
    template_name = 'classroom/student_classrooms.html'
    context_object_name = 'classrooms'
    
    def get_queryset(self):
        return Classroom.objects.filter(students=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student_profile'] = self.request.user.studentprofile
        return context
