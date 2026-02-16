"""
Custom SMTP service for tenant-specific email configuration
"""
from flask import current_app
from flask_mail import Message
from app.extensions import mail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class SMTPService:
    """Custom SMTP service"""
    
    @staticmethod
    def send_email(to, subject, body, html_body=None, sender=None):
        """Send email using Flask-Mail"""
        try:
            msg = Message(
                subject=subject,
                recipients=[to] if isinstance(to, str) else to,
                sender=sender or current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            
            msg.body = body
            if html_body:
                msg.html = html_body
            
            mail.send(msg)
            current_app.logger.info(f"Email sent to {to}")
            return True
        except Exception as e:
            current_app.logger.error(f"Email error: {str(e)}")
            return False
    
    @staticmethod
    def send_custom_smtp(to, subject, body, smtp_config):
        """Send email using custom SMTP configuration"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_config.get('from_email')
            msg['To'] = to
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(
                smtp_config.get('server'),
                smtp_config.get('port')
            )
            server.starttls()
            server.login(
                smtp_config.get('username'),
                smtp_config.get('password')
            )
            
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            current_app.logger.error(f"Custom SMTP error: {str(e)}")
            return False
    
    @staticmethod
    def send_verification_email(to, verification_url, user_name=None):
        """Send email verification"""
        subject = "Verify Your Email Address"
        body = f"""
        Hello {user_name or ''},
        
        Please verify your email address by clicking the link below:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        
        Best regards,
        {current_app.config.get('APP_NAME')}
        """
        
        return SMTPService.send_email(to, subject, body)
    
    @staticmethod
    def send_password_reset_email(to, reset_url, user_name=None):
        """Send password reset email"""
        subject = "Reset Your Password"
        body = f"""
        Hello {user_name or ''},
        
        You requested to reset your password. Click the link below to proceed:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        {current_app.config.get('APP_NAME')}
        """
        
        return SMTPService.send_email(to, subject, body)