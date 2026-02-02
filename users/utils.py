# ==================== users/utils.py ====================
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_otp_email(email, otp, purpose='registration', user_name='User'):
    """
    Send OTP email to user
    
    Args:
        email: Recipient email
        otp: OTP code
        purpose: Purpose of OTP (registration, login, password_reset, email_change)
        user_name: User's name
    """
    
    # Subject based on purpose
    subjects = {
        'registration': 'Verify Your Email - Healthcare Platform',
        'login': 'Your Login OTP - Healthcare Platform',
        'password_reset': 'Reset Your Password - Healthcare Platform',
        'email_change': 'Verify Your New Email - Healthcare Platform',
    }
    
    subject = subjects.get(purpose, 'Your OTP - Healthcare Platform')
    
    # Email content based on purpose
    messages = {
        'registration': f'''
            <h2>Welcome to Healthcare Platform!</h2>
            <p>Hi {user_name},</p>
            <p>Thank you for registering with us. Please use the following OTP to verify your email address:</p>
            <div style="background-color: #f5f5f5; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                {otp}
            </div>
            <p>This OTP is valid for 10 minutes.</p>
            <p>If you didn't request this, please ignore this email.</p>
        ''',
        'login': f'''
            <h2>Login Verification</h2>
            <p>Hi {user_name},</p>
            <p>Someone is trying to login to your account. Please use the following OTP to complete the login:</p>
            <div style="background-color: #f5f5f5; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                {otp}
            </div>
            <p>This OTP is valid for 10 minutes.</p>
            <p>If you didn't try to login, please secure your account immediately.</p>
        ''',
        'password_reset': f'''
            <h2>Password Reset Request</h2>
            <p>Hi {user_name},</p>
            <p>You requested to reset your password. Please use the following OTP to proceed:</p>
            <div style="background-color: #f5f5f5; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                {otp}
            </div>
            <p>This OTP is valid for 10 minutes.</p>
            <p>If you didn't request this, please ignore this email.</p>
        ''',
        'email_change': f'''
            <h2>Email Change Verification</h2>
            <p>Hi {user_name},</p>
            <p>You requested to change your email address. Please use the following OTP to verify this new email:</p>
            <div style="background-color: #f5f5f5; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                {otp}
            </div>
            <p>This OTP is valid for 10 minutes.</p>
            <p>If you didn't request this, please secure your account immediately.</p>
        ''',
    }
    
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            {messages.get(purpose, messages['registration'])}
            <div class="footer">
                <p>Best regards,<br>Healthcare Platform Team</p>
                <p>This is an automated email. Please do not reply to this message.</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def send_welcome_email(user):
    """Send welcome email after successful verification"""
    subject = 'Welcome to Healthcare Platform!'
    
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Welcome to Healthcare Platform!</h2>
            <p>Hi {user.first_name},</p>
            <p>Your email has been successfully verified. Welcome to our platform!</p>
            <p>You can now:</p>
            <ul>
                <li>Search for doctors and specialists</li>
                <li>Book appointments online</li>
                <li>Use our AI symptom checker</li>
                <li>Access health tips and resources</li>
            </ul>
            <p>Thank you for choosing Healthcare Platform.</p>
            <br>
            <p>Best regards,<br>Healthcare Platform Team</p>
        </div>
    </body>
    </html>
    '''
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        return False