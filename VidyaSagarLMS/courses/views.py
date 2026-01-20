from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate
from django.views.generic.edit import FormView
from django.contrib import messages
from .models import Course, Module, Session
from .forms import ModuleForm, SessionForm

# Course Views (already created)
class CoursePermissionMixin:
    """Allow full access to superadmin/admin, or to users who have been granted course access via dashboard."""
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if getattr(user, 'role', None) in ('superadmin', 'admin'):
            return super().dispatch(request, *args, **kwargs)

        # Allow if session flag set (granted via dashboard button)
        if request.session.get('course_access'):
            return super().dispatch(request, *args, **kwargs)

        messages.error(request, 'You do not have permission to access courses. Request access from your dashboard.')
        return redirect('dashboard')

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    ordering = ['-created_at']

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modules'] = self.object.modules.all().order_by('mid')
        return context

class CourseCreateView(LoginRequiredMixin, CoursePermissionMixin, CreateView):
    model = Course
    template_name = 'courses/course_form.html'
    fields = ['cid', 'title', 'duration_days', 'duration_months', 'fees']
    success_url = reverse_lazy('course_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Course created successfully!')
        return super().form_valid(form)

class CourseUpdateView(LoginRequiredMixin, CoursePermissionMixin, UpdateView):
    model = Course
    template_name = 'courses/course_form.html'
    fields = ['title', 'duration_days', 'duration_months', 'fees']
    
    def get_success_url(self):
        messages.success(self.request, 'Course updated successfully!')
        return reverse('course_detail', kwargs={'pk': self.object.cid})

class CourseDeleteView(LoginRequiredMixin, CoursePermissionMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('course_list')
    
    def post(self, request, *args, **kwargs):
        # For superadmin/admin require re-authentication
        user = request.user
        if getattr(user, 'role', None) in ('superadmin', 'admin'):
            username = request.POST.get('confirm_username')
            password = request.POST.get('confirm_password')
            if not username or not password:
                messages.error(request, 'Please enter username and password to confirm deletion.')
                return self.get(request, *args, **kwargs)

            auth_user = authenticate(username=username, password=password)
            if auth_user is None or auth_user.pk != user.pk:
                messages.error(request, 'Invalid credentials. Deletion cancelled.')
                return self.get(request, *args, **kwargs)

        messages.success(self.request, 'Course deleted successfully!')
        return super().post(request, *args, **kwargs)


def grant_course_access(request):
    """Grant temporary course access to non-admin users via dashboard button."""
    if not request.user.is_authenticated:
        messages.error(request, 'Login required to request access.')
        return redirect('login')

    # Only non-admins need the button; admins already have access
    if getattr(request.user, 'role', None) in ('superadmin', 'admin'):
        messages.info(request, 'You already have full course access.')
        return redirect('dashboard')

    # Set a session flag granting access for the session
    request.session['course_access'] = True
    messages.success(request, 'Course access granted for this session.')
    return redirect('dashboard')

# Module Views
class ModuleListView(ListView):
    model = Module
    template_name = 'courses/module_list.html'
    context_object_name = 'modules'
    ordering = ['mid']
    
    def get_queryset(self):
        course_id = self.kwargs.get('cid')
        if course_id:
            return Module.objects.filter(course__cid=course_id).order_by('mid')
        return Module.objects.all().order_by('mid')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('cid')
        if course_id:
            context['course'] = get_object_or_404(Course, cid=course_id)
        return context

class ModuleDetailView(DetailView):
    model = Module
    template_name = 'courses/module_detail.html'
    context_object_name = 'module'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sessions'] = self.object.sessions.all().order_by('session_number')
        return context

class ModuleCreateView(LoginRequiredMixin, CreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'courses/module_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        course_id = self.kwargs.get('cid')
        if course_id:
            course = get_object_or_404(Course, cid=course_id)
            initial['course'] = course
        return initial
    
    def form_valid(self, form):
        course_id = self.kwargs.get('cid')
        if course_id:
            course = get_object_or_404(Course, cid=course_id)
            form.instance.course = course
        messages.success(self.request, 'Module created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('course_detail', kwargs={'pk': self.object.course.cid})

class ModuleUpdateView(LoginRequiredMixin, UpdateView):
    model = Module
    form_class = ModuleForm
    template_name = 'courses/module_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Module updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('course_detail', kwargs={'pk': self.object.course.cid})

class ModuleDeleteView(LoginRequiredMixin, DeleteView):
    model = Module
    template_name = 'courses/module_confirm_delete.html'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Module deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('course_detail', kwargs={'pk': self.object.course.cid})

# Session Views
class SessionCreateView(LoginRequiredMixin, CreateView):
    model = Session
    form_class = SessionForm
    template_name = 'courses/session_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        module_id = self.kwargs.get('mid')
        if module_id:
            module = get_object_or_404(Module, mid=module_id)
            initial['module'] = module
            initial['course'] = module.course
        return initial
    
    def form_valid(self, form):
        module_id = self.kwargs.get('mid')
        if module_id:
            module = get_object_or_404(Module, mid=module_id)
            form.instance.module = module
            form.instance.course = module.course
        messages.success(self.request, 'Session created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('module_detail', kwargs={'pk': self.object.module.mid})

class SessionUpdateView(LoginRequiredMixin, UpdateView):
    model = Session
    form_class = SessionForm
    template_name = 'courses/session_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Session updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('module_detail', kwargs={'pk': self.object.module.mid})

class SessionDeleteView(LoginRequiredMixin, DeleteView):
    model = Session
    template_name = 'courses/session_confirm_delete.html'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Session deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('module_detail', kwargs={'pk': self.object.module.mid})
    

class SessionListView(ListView):
    model = Session
    template_name = 'courses/session_list.html'
    context_object_name = 'sessions'
    ordering = ['session_number']
    
    def get_queryset(self):
        course_id = self.kwargs.get('cid')
        module_id = self.kwargs.get('mid')
        
        if module_id:
            return Session.objects.filter(module__mid=module_id).order_by('session_number')
        elif course_id:
            return Session.objects.filter(course__cid=course_id).order_by('session_number')
        
        return Session.objects.all().order_by('session_number')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('cid')
        module_id = self.kwargs.get('mid')
        
        if module_id:
            context['module'] = get_object_or_404(Module, mid=module_id)
            context['course'] = context['module'].course
        elif course_id:
            context['course'] = get_object_or_404(Course, cid=course_id)
        
        return context

class SessionDetailView(DetailView):
    model = Session
    template_name = 'courses/session_detail.html'
    context_object_name = 'session'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all sessions in the same module
        all_sessions = Session.objects.filter(
            module=self.object.module
        ).order_by('session_number')
        
        # Find previous and next sessions
        session_list = list(all_sessions)
        current_index = None
        
        for i, session in enumerate(session_list):
            if session.sid == self.object.sid:
                current_index = i
                break
        
        if current_index is not None:
            if current_index > 0:
                context['previous_session'] = session_list[current_index - 1]
            if current_index < len(session_list) - 1:
                context['next_session'] = session_list[current_index + 1]
        
        context['related_sessions'] = all_sessions.exclude(sid=self.object.sid)
        context['total_sessions_in_module'] = all_sessions.count()
        
        return context