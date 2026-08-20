"""
Doctor Email Notification Service.
Dispatches secure review links (/review/{token}) to doctors via SMTP or mock email logs.
"""

import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict

class DoctorEmailNotifier:
    """
    Handles generation of doctor review email notifications and delivery via SMTP / mock logger.
    """

    def __init__(self, email_log_path: str = None, base_url: str = "http://127.0.0.1:8000"):
        project_root = Path(__file__).resolve().parent.parent
        self.log_path = Path(email_log_path) if email_log_path else project_root / "data" / "sent_emails" / "doctor_emails.json"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url.rstrip("/")
        self._init_log()

    def _init_log(self):
        if not self.log_path.exists():
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_logs(self) -> list:
        with open(self.log_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_logs(self, logs: list):
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)

    def generate_email_template(self, doctor_email: str, review_task: dict, token_record: dict) -> dict:
        review_url = f"{self.base_url}{token_record['review_url']}"
        priority = review_task.get("priority", "HIGH")
        brand = review_task.get("original_prediction", "Unknown")
        conf = float(review_task.get("original_confidence", 0.0)) * 100

        subject = f"[{priority} PRIORITY] Doctor Review Required: Prescription #{review_task['prescription_id']}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin: auto; }}
            .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 20px; }}
            .priority-high {{ background-color: #e53e3e; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
            .priority-medium {{ background-color: #dd6b20; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
            .priority-low {{ background-color: #319795; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
            .btn {{ display: inline-block; background-color: #2b6cb0; color: #ffffff !important; padding: 12px 24px; font-size: 16px; font-weight: bold; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #718096; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h2>Prescription Verification Request</h2>
              <p>Priority: <span class="priority-{priority.lower()}">{priority}</span> | Task ID: <code>{review_task['review_id']}</code></p>
            </div>

            <p>Hello Doctor,</p>
            <p>A new handwritten prescription has been processed by the AI system and requires your review.</p>

            <table style="width:100%; border-collapse: collapse; margin-top: 15px;">
              <tr><td><strong>Prescription ID:</strong></td><td>{review_task['prescription_id']}</td></tr>
              <tr><td><strong>AI Top Prediction:</strong></td><td>{brand} ({conf:.1f}% confidence)</td></tr>
            </table>

            <div style="text-align: center; margin-top: 25px;">
              <a href="{review_url}" class="btn" target="_blank">Open Secure Doctor Review Portal</a>
            </div>

            <p style="margin-top: 25px; font-size: 13px; color: #4a5568;">
              🔒 <strong>Security Notice:</strong> This review link is personalized, cryptographically secured, and valid for 24 hours.
            </p>

            <div class="footer">
              <p>AI-Based Handwritten Medicine Recognition & Continuous Learning System</p>
            </div>
          </div>
        </body>
        </html>
        """
        return {
            "to": doctor_email,
            "subject": subject,
            "html_body": html_body,
            "review_url": review_url,
            "review_id": review_task['review_id'],
            "priority": priority,
            "sent_at": datetime.now(timezone.utc).isoformat()
        }

    def send_doctor_review_email(self, doctor_email: str, review_task: dict, token_record: dict) -> dict:
        email_data = self.generate_email_template(doctor_email, review_task, token_record)

        # Log to file DB
        logs = self._read_logs()
        logs.append(email_data)
        self._write_logs(logs)

        # Optional Real SMTP Sending if configured in ENV
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD")

        if smtp_server and smtp_user and smtp_pass:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = email_data["subject"]
                msg["From"] = smtp_user
                msg["To"] = doctor_email
                msg.attach(MIMEText(email_data["html_body"], "html"))

                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_user, doctor_email, msg.as_string())
                email_data["delivery_status"] = "SENT_VIA_SMTP"
            except Exception as e:
                email_data["delivery_status"] = f"SMTP_FAILED: {str(e)}"
        else:
            email_data["delivery_status"] = "LOGGED_LOCAL_MOCK"

        return email_data
