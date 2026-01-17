from django.contrib import admin
from .models import EventCategory, CalendarEvent, CourseSchedule, Attendance

class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'description']
    search_fields = ['name']

class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'start_date', 'start_time', 'location', 'created_by', 'is_active']
    list_filter = ['event_type', 'start_date', 'is_active']
    search_fields = ['title', 'description', 'location']
    filter_horizontal = ['trainers', 'students']
    
class CourseScheduleAdmin(admin.ModelAdmin):
    list_display = ['course_name', 'trainer', 'day_of_week', 'start_time', 'end_time', 'room', 'is_active']
    list_filter = ['day_of_week', 'is_active', 'trainer']
    search_fields = ['course_name', 'room']

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['event', 'student', 'attended', 'check_in_time', 'check_out_time']
    list_filter = ['attended', 'event']
    search_fields = ['student__username', 'event__title']

admin.site.register(EventCategory, EventCategoryAdmin)
admin.site.register(CalendarEvent, CalendarEventAdmin)
admin.site.register(CourseSchedule, CourseScheduleAdmin)
admin.site.register(Attendance, AttendanceAdmin)
