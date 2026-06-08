import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login,logout
from django.db.models import Q, Count, Avg
from django.http import HttpResponse
from django.utils import timezone

# Import models and forms
from .models import Student, Course, Enrollment, Grade, Attendance, Department
from .forms import (StudentForm, CourseForm, EnrollmentForm,
                    GradeForm, AttendanceForm, StudentSearchForm)

# Import utility functions
from .utils import send_professional_email, send_otp_email

# ── EXPORT ───────────────────────────────────────────────────────────────────

@login_required
def export_students_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Student ID', 'First Name', 'Last Name', 'Email', 'GPA'])
    students = Student.objects.all()
    for s in students:
        writer.writerow([s.student_id, s.first_name, s.last_name, s.email, s.gpa()])
    return response

# ── DASHBOARD ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    context = {
        'total_students':   Student.objects.count(),
        'active_students':  Student.objects.filter(status='active').count(),
        'total_courses':    Course.objects.count(),
        'total_enrollments': Enrollment.objects.filter(status='enrolled').count(),
        'departments':      Department.objects.annotate(student_count=Count('student')),
        'recent_students':  Student.objects.order_by('-admission_date')[:5],
    }
    return render(request, 'students/dashboard.html', context)

# ── STUDENTS ─────────────────────────────────────────────────────────────────

@login_required
def student_list(request):
    form = StudentSearchForm(request.GET)
    students = Student.objects.select_related('department').all()
    if form.is_valid():
        q = form.cleaned_data.get('query')
        dept = form.cleaned_data.get('department')
        status = form.cleaned_data.get('status')
        if q:
            students = students.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) |
                Q(student_id__icontains=q) | Q(email__icontains=q)
            )
        if dept:
            students = students.filter(department=dept)
        if status:
            students = students.filter(status=status)
    return render(request, 'students/student_list.html', {'students': students, 'form': form})

@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    enrollments = student.enrollments.select_related('course').all()
    attendance  = student.attendance.select_related('course').order_by('-date')[:20]
    return render(request, 'students/student_detail.html', {
        'student': student, 'enrollments': enrollments, 'attendance': attendance
    })

@login_required
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student {student.full_name()} created.')
            return redirect('student_detail', pk=student.pk)
    else:
        form = StudentForm()
    return render(request, 'students/student_form.html', {'form': form, 'action': 'Create'})

@login_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated.')
            return redirect('student_detail', pk=pk)
    else:
        form = StudentForm(instance=student)
    return render(request, 'students/student_form.html', {'form': form, 'action': 'Edit'})

@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student deleted.')
        return redirect('student_list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})

# ── COURSES ───────────────────────────────────────────────────────────────────

@login_required
def course_list(request):
    courses = Course.objects.select_related('department').annotate(
        enrolled=Count('enrollments', filter=Q(enrollments__status='enrolled'))
    )
    return render(request, 'students/course_list.html', {'courses': courses})

@login_required
def course_create(request):
    form = CourseForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Course created.')
        return redirect('course_list')
    return render(request, 'students/course_form.html', {'form': form, 'action': 'Create'})

# ── ENROLLMENTS ───────────────────────────────────────────────────────────────

@login_required
def enroll_student(request):
    form = EnrollmentForm(request.POST or None)
    if form.is_valid():
        enrollment = form.save()
        messages.success(request, f'{enrollment.student.full_name()} enrolled in {enrollment.course}.')
        return redirect('student_detail', pk=enrollment.student.pk)
    return render(request, 'students/enrollment_form.html', {'form': form})

# ── GRADES ────────────────────────────────────────────────────────────────────

@login_required
def grade_entry(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, pk=enrollment_id)
    grade, _ = Grade.objects.get_or_create(
        enrollment=enrollment, defaults={'student': enrollment.student}
    )
    form = GradeForm(request.POST or None, instance=grade)
    if form.is_valid():
        form.save()
        messages.success(request, 'Grade saved.')
        return redirect('student_detail', pk=enrollment.student.pk)
    return render(request, 'students/grade_form.html', {'form': form, 'enrollment': enrollment})

# ── ATTENDANCE ────────────────────────────────────────────────────────────────

@login_required
def mark_attendance(request):
    form = AttendanceForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Attendance recorded.')
        return redirect('dashboard')
    return render(request, 'students/attendance_form.html', {'form': form})

# ── OTP AUTHENTICATION VIEWS ────────────────────────────────────────────────

def login_request_otp(request):
    if request.method == 'POST':
        reg_no = request.POST.get('student_id')
        try:
            student = Student.objects.get(student_id=reg_no)
            otp = student.generate_otp()
            send_otp_email(student.email, student.full_name(), otp)
            request.session['otp_student_id'] = reg_no 
            messages.success(request, f"OTP sent to {student.email}")
            return redirect('login_verify_otp')
        except Student.DoesNotExist:
            messages.error(request, "Invalid Register Number!")
    return render(request, 'students/otp_request.html')

def login_verify_otp(request):
    student_id = request.session.get('otp_student_id')
    if not student_id:
        return redirect('login_request_otp')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        try:
            student = Student.objects.get(student_id=student_id)
            if student.otp == entered_otp and student.otp_expiry > timezone.now():
                user = student.user 
                if user:
                    login(request, user)
                    messages.success(request, "Welcome back!")
                    return redirect('dashboard')
                else:
                    messages.error(request, "Student has no user account linked. Please contact Admin.")
            else:
                messages.error(request, "Invalid or Expired OTP!")
        except Student.DoesNotExist:
            messages.error(request, "Student not found.")

    return render(request, 'students/otp_verify.html')

def custom_logout(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login_request_otp')
