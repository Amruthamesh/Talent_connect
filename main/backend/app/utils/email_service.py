"""
Email Service for Document Delivery
Handles sending documents via email with attachments
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional
import asyncio
from app.config import settings


class EmailService:
    """Email service for sending documents"""
    
    def __init__(self):
        # For demo purposes - in production, use proper SMTP configuration
        self.smtp_server = "smtp.gmail.com"  # Demo server
        self.smtp_port = 587
        self.sender_email = "hr@dhl-demo.com"  # Demo sender
        self.sender_password = "demo_password"  # In production, use environment variable
        
    async def send_document_email(
        self,
        recipient_email: str,
        cc_emails: Optional[List[str]] = None,
        subject: str = "Document from HR",
        document_content: str = "",
        pdf_attachment: bytes = None,
        attachment_filename: str = "document.pdf",
        sender_name: str = "HR Team"
    ) -> bool:
        """
        Send document via email with PDF attachment
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = f"{sender_name} <{self.sender_email}>"
            message["To"] = recipient_email
            if cc_emails:
                message["Cc"] = ", ".join(cc_emails)
            message["Subject"] = subject
            
            # Email body
            body = f"""
Dear Recipient,

Please find the attached document as requested.

Document Summary:
{document_content[:200]}{"..." if len(document_content) > 200 else ""}

Best regards,
{sender_name}
DHL HR Team

---
This is an automated email from the DHL Talent Connect system.
            """
            
            message.attach(MIMEText(body, "plain"))
            
            # Add PDF attachment if provided
            if pdf_attachment:
                pdf_part = MIMEApplication(pdf_attachment, _subtype="pdf")
                pdf_part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={attachment_filename}"
                )
                message.attach(pdf_part)
            
            # For demo purposes, simulate email sending
            # In production, implement actual SMTP sending
            await self._simulate_email_send(message, recipient_email, cc_emails)
            
            return True
            
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False
    
    async def _simulate_email_send(
        self, 
        message: MIMEMultipart, 
        recipient: str, 
        cc_emails: Optional[List[str]] = None
    ):
        """
        Simulate email sending for demo purposes
        In production, replace with actual SMTP implementation
        """
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        print(f"📧 DEMO EMAIL SENT:")
        print(f"   To: {recipient}")
        if cc_emails:
            print(f"   CC: {', '.join(cc_emails)}")
        print(f"   Subject: {message['Subject']}")
        print(f"   Attachment: {len(message.get_payload())} parts")
        print(f"   Status: ✅ Successfully delivered (demo)")
    
    async def _send_actual_email(
        self, 
        message: MIMEMultipart, 
        recipient: str, 
        cc_emails: Optional[List[str]] = None
    ):
        """
        Actual SMTP email sending implementation
        Use this in production with proper SMTP credentials
        """
        # Build recipient list
        recipients = [recipient]
        if cc_emails:
            recipients.extend(cc_emails)
        
        # Create SMTP session
        context = ssl.create_default_context()
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls(context=context)
            server.login(self.sender_email, self.sender_password)
            
            # Send email
            text = message.as_string()
            server.sendmail(self.sender_email, recipients, text)