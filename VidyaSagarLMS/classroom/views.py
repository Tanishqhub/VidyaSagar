from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from courses.models import Course, Module, Session
from .models import (
    Batch, Classroom, ClassroomEnrollment, ClassroomSession, Attendance,
    VirtualClassroom, ClassroomParticipant, Whiteboard, ChatMessage, BreakoutRoom
)
from .forms import (
    BatchForm, ClassroomForm, ClassroomEnrollmentForm,
    ClassroomSessionForm, AttendanceForm, CourseModuleFilterForm,
    VirtualClassroomForm, JoinMeetingForm
)

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
# Virtual Classroom Views
class VirtualClassroomCreateView(ManagerRequiredMixin, CreateView):
    model = VirtualClassroom
    form_class = VirtualClassroomForm
    template_name = 'classroom/virtual_classroom_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        classroom_id = self.kwargs.get('pk')
        self.classroom = get_object_or_404(Classroom, classroom_id=classroom_id)
        # If a virtual classroom already exists for this classroom, redirect to its detail
        try:
            existing = self.classroom.virtual_classroom
        except VirtualClassroom.DoesNotExist:
            existing = None

        if existing:
            if existing.status == 'live':
                return redirect('virtual_classroom_live', pk=existing.meeting_id)
            return redirect('virtual_classroom_detail', pk=existing.meeting_id)

        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classroom'] = self.classroom
        return context
    
    def form_valid(self, form):
        form.instance.classroom = self.classroom
        form.instance.meeting_url = f"/classroom/virtual/{form.instance.meeting_id}/join/"
        
        # Create default meeting password if not provided
        if not form.instance.meeting_password:
            import random
            form.instance.meeting_password = str(random.randint(1000, 9999))
        
        messages.success(self.request, 'Virtual classroom created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('virtual_classroom_detail', kwargs={'pk': self.object.meeting_id})

class VirtualClassroomDetailView(LoginRequiredMixin, DetailView):
    model = VirtualClassroom
    template_name = 'classroom/virtual_classroom_detail.html'
    context_object_name = 'virtual_classroom'
    slug_field = 'meeting_id'
    slug_url_kwarg = 'pk'
    # Override get_object to reliably lookup by meeting_id (UUID)
    def get_object(self, queryset=None):
        lookup = self.kwargs.get(self.slug_url_kwarg) or self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(VirtualClassroom, meeting_id=lookup)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        virtual_classroom = self.object
        
        # Check if user is participant
        is_participant = ClassroomParticipant.objects.filter(
            virtual_classroom=virtual_classroom,
            user=self.request.user
        ).exists()
        
        context['is_participant'] = is_participant
        context['is_trainer'] = virtual_classroom.classroom.trainer == self.request.user
        context['can_join'] = self.can_join_classroom(virtual_classroom)
        context['participants'] = virtual_classroom.participants.filter(is_present=True)
        context['upcoming_sessions'] = virtual_classroom.classroom.classroom_sessions.filter(
            is_completed=False,
            scheduled_date__gte=timezone.now().date()
        ).order_by('scheduled_date')[:5]
        
        return context
    
    def can_join_classroom(self, virtual_classroom):
        user = self.request.user
        
        # Check if user is trainer of this classroom
        if virtual_classroom.classroom.trainer == user:
            return True
        
        # Check if user is enrolled student
        if user.role == 'student' and virtual_classroom.classroom.students.filter(pk=user.pk).exists():
            return True
        
        # Check if user is manager/admin
        if user.role in ['manager', 'admin', 'superadmin']:
            return True
        
        return False

class JoinVirtualClassroomView(LoginRequiredMixin, View):
    template_name = 'classroom/join_meeting.html'
    
    def get(self, request, pk):
        virtual_classroom = get_object_or_404(VirtualClassroom, meeting_id=pk)
        
        # Check if user can join
        if not self.can_join(virtual_classroom, request.user):
            messages.error(request, "You don't have permission to join this classroom.")
            return redirect('classroom_list')
        
        # Check if meeting requires password
        form = JoinMeetingForm()
        
        context = {
            'virtual_classroom': virtual_classroom,
            'form': form,
            'requires_password': bool(virtual_classroom.meeting_password)
        }
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        virtual_classroom = get_object_or_404(VirtualClassroom, meeting_id=pk)
        form = JoinMeetingForm(request.POST)
        
        if not self.can_join(virtual_classroom, request.user):
            messages.error(request, "You don't have permission to join this classroom.")
            return redirect('classroom_list')
        
        # Validate password if required
        if virtual_classroom.meeting_password:
            if not form.is_valid() or form.cleaned_data['meeting_password'] != virtual_classroom.meeting_password:
                messages.error(request, "Invalid meeting password.")
                return render(request, self.template_name, {
                    'virtual_classroom': virtual_classroom,
                    'form': form,
                    'requires_password': True
                })
        
        # Create or update participant record
        participant, created = ClassroomParticipant.objects.get_or_create(
            virtual_classroom=virtual_classroom,
            user=request.user
        )
        
        # Set participant role
        if request.user == virtual_classroom.classroom.trainer:
            participant.role = 'host'
        else:
            participant.role = 'participant'
        
        participant.join_time = timezone.now()
        participant.is_present = True
        participant.save()
        
        # Start meeting if not already live
        if virtual_classroom.status == 'scheduled':
            virtual_classroom.status = 'live'
            virtual_classroom.actual_start = timezone.now()
            virtual_classroom.save()
        
        return redirect('virtual_classroom_live', pk=pk)

    def can_join(self, virtual_classroom, user):
        # Check if user is trainer of this classroom
        if virtual_classroom.classroom.trainer == user:
            return True

        # Check if user is enrolled student
        if user.role == 'student' and virtual_classroom.classroom.students.filter(pk=user.pk).exists():
            return True

        # Check if user is manager/admin
        if user.role in ['manager', 'admin', 'superadmin']:
            return True

        return False



class LiveClassroomView(LoginRequiredMixin, TemplateView):
    template_name = 'classroom/live_classroom.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.virtual_classroom = get_object_or_404(VirtualClassroom, meeting_id=kwargs['pk'])
        
        # Check if user is participant
        try:
            self.participant = ClassroomParticipant.objects.get(
                virtual_classroom=self.virtual_classroom,
                user=request.user,
                is_present=True
            )
        except ClassroomParticipant.DoesNotExist:
            messages.error(request, "You are not in this meeting.")
            return redirect('join_virtual_classroom', pk=kwargs['pk'])
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get whiteboard data
        whiteboard, created = Whiteboard.objects.get_or_create(
            virtual_classroom=self.virtual_classroom
        )
        
        # Get chat messages
        chat_messages_qs = ChatMessage.objects.filter(
            virtual_classroom=self.virtual_classroom
        ).order_by('timestamp')[:50]
        
        # Get active participants
        participants = ClassroomParticipant.objects.filter(
            virtual_classroom=self.virtual_classroom,
            is_present=True
        ).select_related('user')
        
        # Get breakout rooms
        breakout_rooms = BreakoutRoom.objects.filter(
            virtual_classroom=self.virtual_classroom,
            ended_at__isnull=True
        )
        
        context.update({
            'virtual_classroom': self.virtual_classroom,
            'participant': self.participant,
            'whiteboard': whiteboard,
            'chat_messages': chat_messages_qs,
            'participants': participants,
            'breakout_rooms': breakout_rooms,
            'is_host': self.participant.role in ['host', 'co-host'],
            'is_trainer': self.virtual_classroom.classroom.trainer == user,
            'whiteboard_enabled': self.virtual_classroom.whiteboard_enabled,
            'current_user': user,
            'current_session': self.get_current_session(),
        })
        
        return context
    
    def get_current_session(self):
        """Get the current classroom session if any"""
        now = timezone.now()
        today = now.date()
        
        try:
            return self.virtual_classroom.classroom.classroom_sessions.filter(
                scheduled_date=today,
                scheduled_time__lte=now.time(),
                is_completed=False
            ).first()
        except:
            return None

class EndMeetingView(LoginRequiredMixin, View):
    def post(self, request, pk):
        virtual_classroom = get_object_or_404(VirtualClassroom, meeting_id=pk)
        
        # Only host or admin can end meeting
        participant = ClassroomParticipant.objects.filter(
            virtual_classroom=virtual_classroom,
            user=request.user,
            role__in=['host', 'co-host']
        ).first()
        
        if not participant and request.user.role not in ['admin', 'superadmin', 'manager']:
            messages.error(request, "Only host can end the meeting.")
            return redirect('virtual_classroom_live', pk=pk)
        
        # Update all participants
        ClassroomParticipant.objects.filter(
            virtual_classroom=virtual_classroom,
            is_present=True
        ).update(
            leave_time=timezone.now(),
            is_present=False
        )
        
        # Update virtual classroom status
        virtual_classroom.status = 'ended'
        virtual_classroom.actual_end = timezone.now()
        virtual_classroom.save()
        
        messages.success(request, "Meeting ended successfully.")
        return redirect('classroom_detail', pk=virtual_classroom.classroom.classroom_id)

# AJAX Views for Real-time Features
@require_POST
def update_whiteboard(request, pk):
    virtual_classroom = get_object_or_404(VirtualClassroom, meeting_id=pk)
    
    # Check if user is in the meeting
    try:
        participant = ClassroomParticipant.objects.get(
            virtual_classroom=virtual_classroom,
            user=request.user,
            is_present=True
        )
    except ClassroomParticipant.DoesNotExist:
        return JsonResponse({'error': 'Not in meeting'}, status=403)

    # Check if whiteboard is enabled for this meeting
    if not virtual_classroom.whiteboard_enabled:
        return JsonResponse({'error': 'Whiteboard disabled for this meeting'}, status=403)

    # Only the trainer may update the whiteboard
    if request.user != virtual_classroom.classroom.trainer:
        return JsonResponse({'error': 'Only the trainer can modify the whiteboard'}, status=403)
    
    # Get or create whiteboard
    whiteboard, created = Whiteboard.objects.get_or_create(
        virtual_classroom=virtual_classroom
    )
    
    # Update whiteboard data
    canvas_data = request.POST.get('canvas_data', '')
    if canvas_data:
        whiteboard.canvas_data = canvas_data
        whiteboard.last_modified_by = request.user
        whiteboard.save()
    
    return JsonResponse({'status': 'success'})

@require_POST
def send_chat_message(request, pk):
    virtual_classroom = get_object_or_404(VirtualClassroom, meeting_id=pk)
    
    # Check if user is in the meeting
    try:
        participant = ClassroomParticipant.objects.get(
            virtual_classroom=virtual_classroom,
            user=request.user,
            is_present=True
        )
    except ClassroomParticipant.DoesNotExist:
        return JsonResponse({'error': 'Not in meeting'}, status=403)
    
    message_text = request.POST.get('message', '').strip()
    if message_text:
        ChatMessage.objects.create(
            virtual_classroom=virtual_classroom,
            user=request.user,
            message=message_text
        )
    
    return JsonResponse({'status': 'success'})

@require_POST
def update_participant_status(request, pk):
    virtual_classroom = get_object_or_404(VirtualClassroom, meeting_id=pk)
    
    # Check if user is in the meeting
    try:
        participant = ClassroomParticipant.objects.get(
            virtual_classroom=virtual_classroom,
            user=request.user,
            is_present=True
        )
    except ClassroomParticipant.DoesNotExist:
        return JsonResponse({'error': 'Not in meeting'}, status=403)
    
    # Update participant status
    raise_hand = request.POST.get('raise_hand') == 'true'
    is_muted = request.POST.get('is_muted') == 'true'
    video_enabled = request.POST.get('video_enabled') == 'true'
    
    participant.raise_hand = raise_hand
    participant.is_muted = is_muted
    participant.video_enabled = video_enabled
    participant.save()
    
    return JsonResponse({'status': 'success'})

@require_POST
def create_breakout_room(request, pk):
    virtual_classroom = get_object_or_404(VirtualClassroom, meeting_id=pk)
    
    # Check if user is host
    try:
        participant = ClassroomParticipant.objects.get(
            virtual_classroom=virtual_classroom,
            user=request.user,
            role__in=['host', 'co-host']
        )
    except ClassroomParticipant.DoesNotExist:
        return JsonResponse({'error': 'Only host can create breakout rooms'}, status=403)
    
    room_name = request.POST.get('room_name', '')
    if room_name:
        breakout_room = BreakoutRoom.objects.create(
            virtual_classroom=virtual_classroom,
            room_name=room_name,
            host=request.user
        )
        
        # Add host to breakout room
        breakout_room.participants.add(request.user)
        
        return JsonResponse({
            'status': 'success',
            'room_id': str(breakout_room.room_id),
            'room_name': breakout_room.room_name
        })
    
    return JsonResponse({'error': 'Room name required'}, status=400)

@login_required
def get_chat_messages(request, pk):
    virtual_classroom = get_object_or_404(VirtualClassroom, meeting_id=pk)
    
    chat_msgs = ChatMessage.objects.filter(
        virtual_classroom=virtual_classroom
    ).order_by('timestamp')[:100]
    
    data = []
    for msg in chat_msgs:
        data.append({
            'id': msg.id,
            'user': {
                'username': msg.user.username,
                'role': msg.user.role,
            },
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%H:%M'),
            'is_system': msg.is_system,
        })
    
    return JsonResponse({'messages': data})

@login_required
def get_participants(request, pk):
    virtual_classroom = get_object_or_404(VirtualClassroom, meeting_id=pk)
    
    participants = ClassroomParticipant.objects.filter(
        virtual_classroom=virtual_classroom,
        is_present=True
    ).select_related('user')
    
    data = []
    for participant in participants:
        data.append({
            'id': participant.id,
            'user': {
                'username': participant.user.username,
                'full_name': participant.user.get_full_name() or participant.user.username,
                'role': participant.user.role,
            },
            'participant_role': participant.role,
            'raise_hand': participant.raise_hand,
            'is_muted': participant.is_muted,
            'video_enabled': participant.video_enabled,
            'is_host': participant.role in ['host', 'co-host'],
        })
    
    return JsonResponse({'participants': data})