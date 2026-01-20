from django.contrib import admin
from .models import Course, Module, Session

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1

class SessionInline(admin.TabularInline):
    model = Session
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('cid', 'title', 'duration_days', 'duration_months', 'fees')
    search_fields = ('cid', 'title')
    inlines = [ModuleInline]

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('mid', 'm_title', 'no_of_sessions', 'course')
    list_filter = ('course',)
    search_fields = ('m_title',)
    inlines = [SessionInline]

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('sid', 'session_number', 'module', 'course', 'topics_preview')
    list_filter = ('course', 'module')
    search_fields = ('topics', 'module__m_title', 'course__title')
    ordering = ('course', 'module', 'session_number')
    
    def topics_preview(self, obj):
        return obj.topics[:100] + '...' if len(obj.topics) > 100 else obj.topics
    topics_preview.short_description = 'Topics'

