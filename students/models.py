import random
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager

# ── USER MANAGEMENT ───────────────────────────────────────────────────────

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None # Remove username field
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email' # Use email to log in
    REQUIRED_FIELDS = [] # Email is already required

    objects = CustomUserManager()


# ── ACADEMIC MODELS ───────────────────────────────────────────────────────

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    name        = models.CharField(max_length=200)
    code        = models.CharField(max_length=20, unique=True)
    department  = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    credits     = models.PositiveSmallIntegerField(default=3)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} – {self.name}"


class Student(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'), ('graduated', 'Graduated')]

    # Relation to CustomUser
    user            = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    student_id      = models.CharField(max_length=20, unique=True)
    first_name      = models.CharField(max_length=100)
    last_name       = models.CharField(max_length=100)
    email           = models.EmailField(unique=True)
    phone           = models.CharField(max_length=15, blank=True)
    date_of_birth   = models.DateField(null=True, blank=True)
    gender          = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    address         = models.TextField(blank=True)
    photo           = models.ImageField(upload_to='students/', blank=True)
    department      = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    admission_date  = models.DateField(auto_now_add=True)
    status          = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    # OTP Authentication Fields
    otp            = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry     = models.DateTimeField(blank=True, null=True)

    def generate_otp(self):
        """Generates a 6-digit OTP and sets expiry to 5 minutes from now."""
        self.otp = str(random.randint(100000, 999999))
        self.otp_expiry = timezone.now() + timedelta(minutes=5)
        self.save()
        return self.otp

    def __str__(self):
        return f"{self.student_id} – {self.first_name} {self.last_name}"

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def gpa(self):
        grades = self.grades.all()
        if not grades:
            return None
        total_points = sum(g.grade_points() * g.enrollment.course.credits for g in grades)
        total_credits = sum(g.enrollment.course.credits for g in grades)
        return round(total_points / total_credits, 2) if total_credits else None


class Enrollment(models.Model):
    STATUS_CHOICES = [('enrolled', 'Enrolled'), ('dropped', 'Dropped'), ('completed', 'Completed')]

    student    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    semester   = models.CharField(max_length=20) 
    status     = models.CharField(max_length=15, choices=STATUS_CHOICES, default='enrolled')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course', 'semester')

    def __str__(self):
        return f"{self.student} → {self.course} ({self.semester})"


class Grade(models.Model):
    LETTER_CHOICES = [
        ('A+', 'A+'), ('A', 'A'), ('A-', 'A-'),
        ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'),
        ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
        ('D', 'D'), ('F', 'F'),
    ]
    GRADE_POINTS = {
        'A+': 4.0, 'A': 4.0, 'A-': 3.7,
        'B+': 3.3, 'B': 3.0, 'B-': 2.7,
        'C+': 2.3, 'C': 2.0, 'C-': 1.7,
        'D': 1.0, 'F': 0.0,
    }

    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='grade')
    student    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    marks      = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    letter     = models.CharField(max_length=2, choices=LETTER_CHOICES, blank=True)
    remarks    = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def grade_points(self):
        return self.GRADE_POINTS.get(self.letter, 0.0)

    def __str__(self):
        return f"{self.student} – {self.enrollment.course.code}: {self.letter}"


class Attendance(models.Model):
    STATUS_CHOICES = [('present', 'Present'), ('absent', 'Absent'), ('late', 'Late')]

    student    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    course     = models.ForeignKey(Course, on_delete=models.CASCADE)
    date       = models.DateField()
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    note       = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('student', 'course', 'date')

    def __str__(self):
        return f"{self.student} | {self.course.code} | {self.date} – {self.status}"
