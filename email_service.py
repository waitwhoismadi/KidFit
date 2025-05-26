from flask import current_app, render_template_string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional

class EmailService:
    """Email service for sending notifications"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize email service with Flask app"""
        # Email configuration
        app.config.setdefault('MAIL_SERVER', 'smtp.gmail.com')
        app.config.setdefault('MAIL_PORT', 587)
        app.config.setdefault('MAIL_USE_TLS', True)
        app.config.setdefault('MAIL_USERNAME', os.environ.get('MAIL_USERNAME'))
        app.config.setdefault('MAIL_PASSWORD', os.environ.get('MAIL_PASSWORD'))
        app.config.setdefault('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_DEFAULT_SENDER'))
        
    def send_email(self, to_emails: List[str], subject: str, html_body: str, 
                   text_body: Optional[str] = None, attachments: Optional[List] = None):
        """Send email to recipients"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
            msg['To'] = ', '.join(to_emails)
            
            # Add text version if provided
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    with open(attachment, "rb") as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment)}'
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
                server.starttls()
                if current_app.config['MAIL_USERNAME'] and current_app.config['MAIL_PASSWORD']:
                    server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
                
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_enrollment_confirmation(self, enrollment):
        """Send enrollment confirmation to parent"""
        parent_email = enrollment.child.parent.user.email
        child_name = enrollment.child.name
        program_name = enrollment.schedule.program.name
        center_name = enrollment.schedule.program.center.center_name
        schedule_info = f"{enrollment.schedule.get_day_name()} {enrollment.schedule.get_time_range()}"
        
        subject = f"Enrollment Confirmation - {child_name} in {program_name}"
        
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #4f46e5; color: white; padding: 20px; text-align: center;">
                    <h1>Enrollment Confirmation</h1>
                </div>
                
                <div style="padding: 20px;">
                    <p>Dear {enrollment.child.parent.user.name},</p>
                    
                    <p>Great news! Your child <strong>{child_name}</strong> has been successfully enrolled in:</p>
                    
                    <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #4f46e5; margin-top: 0;">{program_name}</h3>
                        <p><strong>Center:</strong> {center_name}</p>
                        <p><strong>Schedule:</strong> {schedule_info}</p>
                        <p><strong>Status:</strong> {"Active" if enrollment.status == "active" else "Pending Approval"}</p>
                    </div>
                    
                    <p>What's next?</p>
                    <ul>
                        {"<li>Your enrollment is confirmed and classes can begin!</li>" if enrollment.status == "active" else "<li>Please wait for center approval. You'll receive another email once approved.</li>"}
                        <li>Contact the center if you have any questions</li>
                        <li>Check your dashboard for enrollment details</li>
                    </ul>
                    
                    <div style="margin: 30px 0; padding: 15px; background-color: #e0f2fe; border-radius: 8px;">
                        <h4>Center Contact Information:</h4>
                        <p><strong>{center_name}</strong></p>
                        <p>{enrollment.schedule.program.center.address}</p>
                        {f"<p>Phone: {enrollment.schedule.program.center.user.phone}</p>" if enrollment.schedule.program.center.user.phone else ""}
                        <p>Email: {enrollment.schedule.program.center.user.email}</p>
                    </div>
                    
                    <p>Thank you for choosing KidFit Astana!</p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="{current_app.config.get('BASE_URL', 'http://localhost:5000')}/parent/enrollments" 
                           style="background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                            View My Enrollments
                        </a>
                    </div>
                </div>
                
                <div style="background-color: #f1f5f9; padding: 15px; text-align: center; color: #64748b;">
                    <p>KidFit Astana - Connecting families with quality education</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email([parent_email], subject, html_body)
    
    def send_teacher_invitation(self, center, teacher_email, invite_code):
        """Send teacher invitation email"""
        subject = f"Invitation to Join {center.center_name} as a Teacher"
        
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #10b981; color: white; padding: 20px; text-align: center;">
                    <h1>Teacher Invitation</h1>
                </div>
                
                <div style="padding: 20px;">
                    <p>Hello!</p>
                    
                    <p>You've been invited to join <strong>{center.center_name}</strong> as a teacher on the KidFit Astana platform.</p>
                    
                    <div style="background-color: #f0fdf4; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
                        <h3 style="color: #10b981; margin-top: 0;">Your Invite Code</h3>
                        <div style="font-size: 24px; font-weight: bold; color: #059669; letter-spacing: 2px;">
                            {invite_code}
                        </div>
                    </div>
                    
                    <p>To complete your registration:</p>
                    <ol>
                        <li>Visit the teacher registration page</li>
                        <li>Enter the invite code above</li>
                        <li>Fill in your details</li>
                        <li>Start teaching!</li>
                    </ol>
                    
                    <div style="margin: 30px 0; padding: 15px; background-color: #eff6ff; border-radius: 8px;">
                        <h4>About {center.center_name}:</h4>
                        <p>{center.description or "A quality education center focused on providing excellent programs for children and teenagers."}</p>
                        <p><strong>Location:</strong> {center.address}</p>
                        {f"<p><strong>Contact:</strong> {center.user.phone}</p>" if center.user.phone else ""}
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="{current_app.config.get('BASE_URL', 'http://localhost:5000')}/register/teacher" 
                           style="background-color: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                            Register as Teacher
                        </a>
                    </div>
                </div>
                
                <div style="background-color: #f1f5f9; padding: 15px; text-align: center; color: #64748b;">
                    <p>KidFit Astana - Empowering educators and students</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email([teacher_email], subject, html_body)
    
    def send_enrollment_status_update(self, enrollment, new_status):
        """Send enrollment status update to parent"""
        parent_email = enrollment.child.parent.user.email
        child_name = enrollment.child.name
        program_name = enrollment.schedule.program.name
        center_name = enrollment.schedule.program.center.center_name
        
        status_messages = {
            'active': {
                'title': 'Enrollment Approved!',
                'message': 'Your enrollment has been approved and is now active.',
                'color': '#10b981'
            },
            'cancelled': {
                'title': 'Enrollment Cancelled',
                'message': 'Your enrollment has been cancelled.',
                'color': '#ef4444'
            },
            'paused': {
                'title': 'Enrollment Paused',
                'message': 'Your enrollment has been temporarily paused.',
                'color': '#f59e0b'
            }
        }
        
        status_info = status_messages.get(new_status, {
            'title': 'Enrollment Status Updated',
            'message': f'Your enrollment status has been updated to {new_status}.',
            'color': '#6b7280'
        })
        
        subject = f"{status_info['title']} - {child_name} in {program_name}"
        
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: {status_info['color']}; color: white; padding: 20px; text-align: center;">
                    <h1>{status_info['title']}</h1>
                </div>
                
                <div style="padding: 20px;">
                    <p>Dear {enrollment.child.parent.user.name},</p>
                    
                    <p>{status_info['message']}</p>
                    
                    <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #4f46e5; margin-top: 0;">{program_name}</h3>
                        <p><strong>Child:</strong> {child_name}</p>
                        <p><strong>Center:</strong> {center_name}</p>
                        <p><strong>New Status:</strong> {new_status.title()}</p>
                    </div>
                    
                    <p>If you have any questions about this status change, please contact the center directly.</p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="{current_app.config.get('BASE_URL', 'http://localhost:5000')}/parent/enrollments" 
                           style="background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                            View My Enrollments
                        </a>
                    </div>
                </div>
                
                <div style="background-color: #f1f5f9; padding: 15px; text-align: center; color: #64748b;">
                    <p>KidFit Astana - Connecting families with quality education</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email([parent_email], subject, html_body)

# Initialize email service
email_service = EmailService()