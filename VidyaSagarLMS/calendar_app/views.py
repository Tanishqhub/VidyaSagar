from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Q
from datetime import date, datetime, time, timedelta
from django.utils import timezone
from .models import CalendarEvent, EventCategory, CourseSchedule, Attendance
from .forms import CalendarEventForm, EventCategoryForm, CourseScheduleForm, AttendanceForm, BulkAttendanceForm
from accounts.models import CustomUser
import calendar

@login_required
def calendar_view(request):
    """Main calendar view"""
    user = request.user
    today = date.today()
    
    # Get month and year from request or use current
    year = request.GET.get('year', today.year)
    month = request.GET.get('month', today.month)
    
    try:
        year = int(year)
        month = int(month)
    except (ValueError, TypeError):
        year = today.year
        month = today.month
    
    # Calculate previous and next month
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    # Get events for the month
    events = CalendarEvent.objects.filter(
        Q(start_date__year=year, start_date__month=month) |
        Q(end_date__year=year, end_date__month=month) |
        (Q(is_recurring=True) & Q(start_date__lte=date(year, month, 1)))
    ).filter(is_active=True)
    
    # Filter events based on user role
    if user.role == 'student':
        events = events.filter(students=user)
    elif user.role == 'trainer':
        events = events.filter(trainers=user)
    
    # Generate proper month calendar grid
    cal = calendar.monthcalendar(year, month)
    month_calendar = []
    
    # Get month name and year for display
    month_name_full = date(year, month, 1).strftime('%B')
    
    for week_num, week in enumerate(cal):
        week_days = []
        for day in week:
            if day == 0:
                # Empty day (from previous/next month)
                week_days.append({
                    'date': None,
                    'day': '',
                    'events': [],
                    'is_today': False,
                    'is_current_month': False
                })
            else:
                day_date = date(year, month, day)
                day_events = []
                
                # Find events for this day
                for event in events:
                    if event.start_date == day_date:
                        day_events.append(event)
                    elif event.end_date and event.start_date <= day_date <= event.end_date:
                        day_events.append(event)
                    elif event.is_recurring and event.start_date <= day_date:
                        # Simple recurrence check (for demo - implement proper recurrence logic)
                        if event.recurrence_pattern == 'daily':
                            day_events.append(event)
                        elif event.recurrence_pattern == 'weekly' and event.start_date.weekday() == day_date.weekday():
                            day_events.append(event)
                        elif event.recurrence_pattern == 'monthly' and event.start_date.day == day:
                            day_events.append(event)
                
                week_days.append({
                    'date': day_date,
                    'day': day,
                    'events': day_events,
                    'is_today': day_date == today,
                    'is_current_month': True
                })
        month_calendar.append(week_days)
    
    # Get event counts for statistics
    event_counts = {
        'total': events.count(),
        'classes': events.filter(event_type='class').count(),
        'meetings': events.filter(event_type='meeting').count(),
        'exams': events.filter(event_type='exam').count(),
        'holidays': events.filter(event_type='holiday').count(),
    }
    
    context = {
        'user': user,
        'events': events,
        'current_year': year,
        'current_month': month,
        'current_month_name': month_name_full,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'today': today,
        'month_calendar': month_calendar,
        'event_counts': event_counts,
        'weekdays': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    }
    
    return render(request, 'calendar_app/calendar.html', context)

@login_required
def calendar_events_json(request):
    """API endpoint for calendar events (FullCalendar integration)"""
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    try:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        start_date = date.today()
        end_date = start_date + timedelta(days=30)
    
    events = CalendarEvent.objects.filter(
        Q(start_date__range=[start_date, end_date]) |
        Q(end_date__range=[start_date, end_date]) |
        (Q(is_recurring=True) & Q(start_date__lte=end_date))
    ).filter(is_active=True)
    
    # Filter based on user role
    user = request.user
    if user.role == 'student':
        events = events.filter(students=user)
    elif user.role == 'trainer':
        events = events.filter(trainers=user)
    
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'start': f"{event.start_date}T{event.start_time}" if event.start_time else str(event.start_date),
            'end': f"{event.end_date or event.start_date}T{event.end_time}" if event.end_time else str(event.end_date or event.start_date),
            'allDay': event.all_day,
            'color': event.category.color if event.category else '#007bff',
            'description': event.description,
            'location': event.location,
            'type': event.get_event_type_display(),
        })
    
    return JsonResponse(events_data, safe=False)

@login_required
def day_view(request, year=None, month=None, day=None):
    """Daily schedule view"""
    user = request.user
    today = date.today()
    
    if year and month and day:
        try:
            view_date = date(year, month, day)
        except ValueError:
            view_date = today
    else:
        view_date = today
    
    # Get events for the day
    events = CalendarEvent.objects.filter(
        Q(start_date=view_date) |
        Q(end_date=view_date) |
        (Q(start_date__lte=view_date) & Q(end_date__gte=view_date)) |
        (Q(is_recurring=True) & Q(start_date__lte=view_date))
    ).filter(is_active=True)
    
    # Filter based on user role
    if user.role == 'student':
        events = events.filter(students=user)
    elif user.role == 'trainer':
        events = events.filter(trainers=user)
    
    # Get previous and next day
    prev_day = view_date - timedelta(days=1)
    next_day = view_date + timedelta(days=1)
    
    context = {
        'user': user,
        'events': events.order_by('start_time'),
        'view_date': view_date,
        'prev_day': prev_day,
        'next_day': next_day,
        'today': today,
    }
    
    return render(request, 'calendar_app/day_view.html', context)

@login_required
def event_detail(request, event_id):
    """Event detail view"""
    event = get_object_or_404(CalendarEvent, id=event_id, is_active=True)
    user = request.user
    
    # Check if user has permission to view this event
    if user.role == 'student' and user not in event.students.all():
        return redirect('calendar')
    elif user.role == 'trainer' and user not in event.trainers.all():
        return redirect('calendar')
    
    # Get attendance for this event if it's a class
    attendance = None
    if event.event_type == 'class' and user.role in ['trainer', 'manager', 'admin', 'superadmin']:
        attendance = Attendance.objects.filter(event=event)
    
    context = {
        'event': event,
        'attendance': attendance,
        'can_edit': user.role in ['manager', 'admin', 'superadmin'] or user == event.created_by,
    }
    
    return render(request, 'calendar_app/event_detail.html', context)

@login_required
def add_event(request):
    """Add new event (only for managers, admins, and trainers)"""
    user = request.user
    
    if user.role not in ['trainer', 'manager', 'admin', 'superadmin']:
        return redirect('calendar')
    
    if request.method == 'POST':
        form = CalendarEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = user
            event.save()
            form.save_m2m()  # Save many-to-many relationships
            return redirect('event_detail', event_id=event.id)
    else:
        form = CalendarEventForm()
        # Pre-select current user if they're a trainer
        if user.role == 'trainer':
            form.fields['trainers'].initial = [user]
    
    context = {
        'form': form,
        'title': 'Add New Event',
    }
    
    return render(request, 'calendar_app/event_form.html', context)

@login_required
def edit_event(request, event_id):
    """Edit event (only for managers, admins, and event creator)"""
    event = get_object_or_404(CalendarEvent, id=event_id)
    user = request.user
    
    if not (user.role in ['manager', 'admin', 'superadmin'] or user == event.created_by):
        return redirect('event_detail', event_id=event_id)
    
    if request.method == 'POST':
        form = CalendarEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('event_detail', event_id=event.id)
    else:
        form = CalendarEventForm(instance=event)
    
    context = {
        'form': form,
        'title': 'Edit Event',
        'event': event,
    }
    
    return render(request, 'calendar_app/event_form.html', context)

@login_required
def delete_event(request, event_id):
    """Delete event (soft delete)"""
    event = get_object_or_404(CalendarEvent, id=event_id)
    user = request.user
    
    if not (user.role in ['manager', 'admin', 'superadmin'] or user == event.created_by):
        return redirect('event_detail', event_id=event_id)
    
    if request.method == 'POST':
        event.is_active = False
        event.save()
        return redirect('calendar')
    
    return render(request, 'calendar_app/confirm_delete.html', {'event': event})

@login_required
def manage_categories(request):
    """Manage event categories (only for managers and admins)"""
    user = request.user
    
    if user.role not in ['manager', 'admin', 'superadmin']:
        return redirect('calendar')
    
    categories = EventCategory.objects.all()
    
    if request.method == 'POST':
        form = EventCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_categories')
    else:
        form = EventCategoryForm()
    
    context = {
        'categories': categories,
        'form': form,
    }
    
    return render(request, 'calendar_app/manage_categories.html', context)

@login_required
def course_schedules(request):
    """Manage course schedules"""
    user = request.user
    
    if user.role not in ['trainer', 'manager', 'admin', 'superadmin']:
        return redirect('calendar')
    
    schedules = CourseSchedule.objects.filter(is_active=True)
    
    if request.method == 'POST' and user.role in ['manager', 'admin', 'superadmin']:
        form = CourseScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('course_schedules')
    else:
        form = CourseScheduleForm()
    
    context = {
        'schedules': schedules,
        'form': form,
        'can_edit': user.role in ['manager', 'admin', 'superadmin'],
    }
    
    return render(request, 'calendar_app/course_schedules.html', context)

@login_required
def take_attendance(request, event_id):
    """Take attendance for a class event"""
    event = get_object_or_404(CalendarEvent, id=event_id, event_type='class')
    user = request.user
    
    # Only trainers, managers, and admins can take attendance
    if user.role not in ['trainer', 'manager', 'admin', 'superadmin']:
        return redirect('event_detail', event_id=event_id)
    
    # Check if user is a trainer for this event
    if user.role == 'trainer' and user not in event.trainers.all():
        return redirect('event_detail', event_id=event_id)
    
    students = event.students.all()
    
    if request.method == 'POST':
        for student in students:
            attended = request.POST.get(f'attended_{student.id}') == 'on'
            check_in = request.POST.get(f'check_in_{student.id}')
            check_out = request.POST.get(f'check_out_{student.id}')
            remarks = request.POST.get(f'remarks_{student.id}', '')
            
            # Parse datetime strings
            check_in_time = None
            check_out_time = None
            
            if check_in:
                try:
                    check_in_time = datetime.strptime(check_in, '%Y-%m-%dT%H:%M')
                except ValueError:
                    pass
            
            if check_out:
                try:
                    check_out_time = datetime.strptime(check_out, '%Y-%m-%dT%H:%M')
                except ValueError:
                    pass
            
            # Update or create attendance record
            attendance, created = Attendance.objects.update_or_create(
                event=event,
                student=student,
                defaults={
                    'attended': attended,
                    'check_in_time': check_in_time,
                    'check_out_time': check_out_time,
                    'remarks': remarks,
                }
            )
        
        return redirect('event_detail', event_id=event_id)
    
    # Get existing attendance records
    attendance_records = {}
    for student in students:
        try:
            record = Attendance.objects.get(event=event, student=student)
            attendance_records[student.id] = record
        except Attendance.DoesNotExist:
            attendance_records[student.id] = None
    
    context = {
        'event': event,
        'students': students,
        'attendance_records': attendance_records,
        'today': date.today().isoformat(),
    }
    
    return render(request, 'calendar_app/take_attendance.html', context)

@login_required
def attendance_report(request):
    """Attendance report for managers and admins"""
    user = request.user
    
    if user.role not in ['manager', 'admin', 'superadmin']:
        return redirect('calendar')
    
    # Filter parameters
    event_type = request.GET.get('event_type', 'class')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    events = CalendarEvent.objects.filter(event_type='class', is_active=True)
    
    if start_date:
        try:
            events = events.filter(start_date__gte=start_date)
        except ValueError:
            pass
    
    if end_date:
        try:
            events = events.filter(start_date__lte=end_date)
        except ValueError:
            pass
    
    # Calculate attendance statistics
    total_events = events.count()
    attendance_data = []
    
    for event in events:
        total_students = event.students.count()
        attended = Attendance.objects.filter(event=event, attended=True).count()
        percentage = (attended / total_students * 100) if total_students > 0 else 0
        
        attendance_data.append({
            'event': event,
            'total_students': total_students,
            'attended': attended,
            'percentage': round(percentage, 1),
        })
    
    context = {
        'attendance_data': attendance_data,
        'total_events': total_events,
        'event_type': event_type,
        'start_date': start_date,
        'end_date': end_date,
        'today': date.today().isoformat(),
    }
    
    return render(request, 'calendar_app/attendance_report.html', context)