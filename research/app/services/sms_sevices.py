"""
SMS service abstraction
"""
from twilio.rest import Client
from flask import current_app


class SMSService:
    """SMS gateway service"""
    
    def __init__(self):
        self.account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        self.auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        self.phone_number = current_app.config.get('TWILIO_PHONE_NUMBER')
        self.client = Client(self.account_sid, self.auth_token) if self.account_sid else None
    
    def send_sms(self, to_number, message):
        """Send SMS message"""
        if not self.client:
            current_app.logger.error("Twilio client not configured")
            return False
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_number
            )
            current_app.logger.info(f"SMS sent: {message.sid}")
            return True
        except Exception as e:
            current_app.logger.error(f"SMS error: {str(e)}")
            return False
    
    def send_otp(self, to_number, otp_code):
        """Send OTP code"""
        message = f"Your verification code is: {otp_code}. Valid for 10 minutes."
        return self.send_sms(to_number, message)
    
    def send_notification(self, to_number, notification_text):
        """Send notification"""
        return self.send_sms(to_number, notification_text)