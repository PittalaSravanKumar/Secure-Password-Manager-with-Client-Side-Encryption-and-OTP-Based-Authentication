import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

def send_otp(email, otp):
    try:
        subject = "Your OTP Code - Secure Password Storage System"
        body = f"""Dear User,

Your One-Time Password (OTP) for secure access to your Password Storage System is: {otp}

This OTP is valid for the next 10 minutes only. Please use it to verify your identity and proceed with secure password management.

Security Notice:
- Never share this OTP with anyone, including support staff
- Our system will never ask for your OTP via phone or email
- If you didn't request this code, please ignore this email and secure your account

This verification ensures your sensitive password data remains protected at all times.

Best regards,
Secure Password Storage Team"""
        
        em = EmailMessage()
        em['From'] = EMAIL_SENDER
        em['To'] = email
        em['Subject'] = subject
        em.set_content(body)
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_SENDER, email, em.as_string())
        
        return True
    except:
        return False

def send_wrong_password_alert(email):
    try:
        subject = "⚠️ Security Alert: Data Breach Detected - Immediate Action Required"
        body = """Dear User,

URGENT SECURITY NOTICE

We have detected that your password may have been compromised in a recent data breach. Your account security is at risk.

⚠️ IMMEDIATE ACTION REQUIRED ⚠️

For your protection, we strongly recommend you:
1. Register again with a new, strong password
2. Use a unique password that you haven't used elsewhere
3. Enable two-factor authentication if available

Password Security Tips:
• Use at least 12 characters
• Mix uppercase, lowercase, numbers, and special characters
• Avoid common words or personal information
• Never reuse passwords across different platforms

Your stored passwords remain encrypted and secure, but we urge you to take immediate action to protect your account.

If you have any questions or concerns, please contact our security team immediately.

Stay safe,
Secure Password Storage Security Team

This is an automated security alert. Please do not reply to this email."""
        
        em = EmailMessage()
        em['From'] = EMAIL_SENDER
        em['To'] = email
        em['Subject'] = subject
        em.set_content(body)
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_SENDER, email, em.as_string())
        
        return True
    except:
        return False