from django.urls import path
from . import views

urlpatterns = [
     path('login-otp/', views.login_request_otp, name='login_request_otp'),
    path('login-verify/', views.login_verify_otp, name='login_verify_otp'),
    path('',                              views.dashboard,       name='dashboard'),
    path('students/',                     views.student_list,    name='student_list'),
    path('students/new/',                 views.student_create,  name='student_create'),
    path('students/<int:pk>/',            views.student_detail,  name='student_detail'),
    path('students/<int:pk>/edit/',       views.student_edit,    name='student_edit'),
    path('students/<int:pk>/delete/',     views.student_delete,  name='student_delete'),
    path('courses/',                      views.course_list,     name='course_list'),
    path('courses/new/',                  views.course_create,   name='course_create'),
    path('enroll/',                       views.enroll_student,  name='enroll_student'),
    path('grades/<int:enrollment_id>/',   views.grade_entry,     name='grade_entry'),
    path('attendance/',                   views.mark_attendance, name='mark_attendance'),
    path('students/export/', views.export_students_csv, name='export_students_csv'),
     path('logout/', views.custom_logout, name='logout'), 
]