from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Student, Course, Department, Enrollment, Grade, Attendance

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = ['student_id', 'full_name', 'email', 'department', 'status']
    list_filter   = ['status', 'department', 'gender']
    search_fields = ['student_id', 'first_name', 'last_name', 'email']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'credits']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'semester', 'status']

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'enrollment', 'letter', 'marks']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'date', 'status']
    list_filter  = ['status', 'date']

admin.site.register(Department)