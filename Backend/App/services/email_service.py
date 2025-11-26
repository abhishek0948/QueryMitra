from flask import current_app
from flask_mail import Message
import random
from datetime import datetime, timedelta

class EmailService:
    def __init__(self):
        self.db = current_app.db
        self.otp_collection = self.db['otp_verification']
    
    def generate_otp(self):
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    def store_otp(self, email, otp):
        """Store OTP in database with expiration time"""
        expiry_time = datetime.utcnow() + timedelta(minutes=current_app.config['OTP_EXPIRY_MINUTES'])
        
        # Delete any existing OTP for this email
        self.otp_collection.delete_many({'email': email})
        
        # Store new OTP
        otp_data = {
            'email': email,
            'otp': otp,
            'expires_at': expiry_time,
            'created_at': datetime.utcnow()
        }
        self.otp_collection.insert_one(otp_data)
    
    def verify_otp(self, email, otp):
        """Verify if OTP is valid and not expired"""
        otp_data = self.otp_collection.find_one({'email': email, 'otp': otp})
        
        if not otp_data:
            return False, "Invalid OTP"
        
        # Check if OTP is expired
        if datetime.utcnow() > otp_data['expires_at']:
            self.otp_collection.delete_one({'_id': otp_data['_id']})
            return False, "OTP has expired"
        
        # OTP is valid, delete it
        self.otp_collection.delete_one({'_id': otp_data['_id']})
        return True, "OTP verified successfully"
    
    def send_otp_email(self, email, otp):
        """Send OTP to user's email"""
        try:
            # Get mail instance from app extensions
            from flask_mail import Mail
            mail = current_app.extensions.get('mail')
            
            if not mail:
                return False, "Email service not configured"
            
            msg = Message(
                subject="Your Query Mitra Verification Code",
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email]
            )
            
            msg.body = f"""
Hello,

Your verification code for Query Mitra is: {otp}

This code will expire in {current_app.config['OTP_EXPIRY_MINUTES']} minutes.

If you didn't request this code, please ignore this email.

Best regards,
Query Mitra Team
            """
            
            msg.html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .otp-box {{ background: white; border: 2px solid #667eea; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0; }}
        .otp-code {{ font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Query Mitra</h1>
            <p>Email Verification</p>
        </div>
        <div class="content">
            <h2>Welcome!</h2>
            <p>Thank you for signing up. Please use the verification code below to complete your registration:</p>
            
            <div class="otp-box">
                <div class="otp-code">{otp}</div>
            </div>
            
            <p><strong>This code will expire in {current_app.config['OTP_EXPIRY_MINUTES']} minutes.</strong></p>
            
            <p>If you didn't request this code, please ignore this email.</p>
            
            <div class="footer">
                <p>© 2025 Query Mitra. All rights reserved.</p>
            </div>
        </div>
    </div>
</body>
</html>
            """
            
            mail.send(msg)
            return True, "OTP sent successfully"
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False, f"Failed to send email: {str(e)}"
    
    def delete_expired_otps(self):
        """Clean up expired OTPs from database"""
        self.otp_collection.delete_many({'expires_at': {'$lt': datetime.utcnow()}})
