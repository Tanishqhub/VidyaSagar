from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser, StudentProfile, TrainerProfile
from django.contrib import messages
from django.shortcuts import get_object_or_404

@login_required
def dashboard_view(request):
    user = request.user
    
    if user.role == 'superadmin':
        # Super Admin can see all users
        users = CustomUser.objects.all()
        return render(request, 'dashboard/superadmin_dashboard.html', {
            'user': user,
            'users': users,
            'total_users': users.count(),
            'student_count': CustomUser.objects.filter(role='student').count(),
            'trainer_count': CustomUser.objects.filter(role='trainer').count(),
            'manager_count': CustomUser.objects.filter(role='manager').count(),
            'admin_count': CustomUser.objects.filter(role='admin').count(),
            'superadmin_count': CustomUser.objects.filter(role='superadmin').count(),
        })
    
    elif user.role == 'admin':
        # Admin can see all users except superadmins
        users = CustomUser.objects.exclude(role='superadmin')
        return render(request, 'dashboard/admin_dashboard.html', {
            'user': user,
            'users': users,
            'total_users': users.count(),
            'student_count': CustomUser.objects.filter(role='student').count(),
            'trainer_count': CustomUser.objects.filter(role='trainer').count(),
            'manager_count': CustomUser.objects.filter(role='manager').count(),
            'admin_count': CustomUser.objects.filter(role='admin').count(),
        })
    
    elif user.role == 'manager':
        # Managers can see trainers and students
        trainers = CustomUser.objects.filter(role='trainer')
        students = CustomUser.objects.filter(role='student')
        
        return render(request, 'dashboard/manager_dashboard.html', {
            'user': user,
            'trainers': trainers,
            'students': students,
            'trainer_count': trainers.count(),
            'student_count': students.count(),
        })
    
    elif user.role == 'trainer':
        # Trainers can see their students
        students = CustomUser.objects.filter(role='student')
        
        return render(request, 'dashboard/trainer_dashboard.html', {
            'user': user,
            'students': students,
            'student_count': students.count(),
        })
    
    elif user.role == 'student':
        # Students see their own dashboard
        return render(request, 'dashboard/student_dashboard.html', {
            'user': user
        })
    
    else:
        return redirect('login')


@login_required
def grant_user_course_access(request, user_id):
    """Allow superadmin to grant or revoke persistent course access for a user."""
    if request.method != 'POST':
        return redirect('dashboard')

    if getattr(request.user, 'role', None) != 'superadmin':
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')

    target = get_object_or_404(CustomUser, pk=user_id)
    # Toggle access based on posted action, default to grant
    action = request.POST.get('action', 'grant')
    if action == 'revoke':
        target.course_access = False
        messages.success(request, f'Course access revoked for {target.username}.')
    else:
        target.course_access = True
        messages.success(request, f'Course access granted for {target.username}.')

    target.save()
    return redirect('dashboard')