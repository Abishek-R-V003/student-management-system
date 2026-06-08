from django import forms
from .models import Student, Course, Enrollment, Grade, Attendance, Department

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = ['user']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'course', 'semester', 'status']

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['marks', 'letter', 'remarks']

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = '__all__'
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}

class StudentSearchForm(forms.Form):
    query      = forms.CharField(required=False, label='Search')
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    status     = forms.ChoiceField(
        choices=[('', 'All')] + Student.STATUS_CHOICES, required=False
    )