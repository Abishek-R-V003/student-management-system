from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# This is the function your views.py is currently looking for
def send_professional_email(user_email, user_name, reset_link):
    subject = 'Password Reset Request - Student MS'
    from_email = 'studentmanagementsystem2028@gmail.com'
    to = [user_email]

    context = {
        'user': {'first_name': user_name}, 
        'reset_link': reset_link
    }
    html_message = render_to_string('emails/password_reset_email.html', context)
    plain_message = strip_tags(html_message)

    msg = EmailMultiAlternatives(subject, plain_message, from_email, to)
    msg.attach_alternative(html_message, mimetype='text/html')
    msg.send()
    return True

# This is the function for your new OTP system
def send_otp_email(student_email, student_name, otp):
    subject = 'Your Login OTP - Student MS'
    from_email = 'studentmanagementsystem2028@gmail.com'
    
    context = {
        'name': student_name,
        'otp': otp
    }
    html_message = render_to_string('emails/otp_email.html', context)
    plain_message = strip_tags(html_message)

    msg = EmailMultiAlternatives(subject, plain_message, from_email, [student_email])
    msg.attach_alternative(html_message, mimetype='text/html')
    msg.send()
    return True

# This is the test function we used in the shell
def send_test_professional_email():
    user_email = 'abhishekvadivelrv@gmail.com' 
    user_name = 'Abhishek'
    reset_link = 'http://127.0.0.1:8000/reset-password/12345/'
    
    # Simply call the other function we already wrote
    return send_professional_email(user_email, user_name, reset_link)
