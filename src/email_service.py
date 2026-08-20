"""
Doctor Email Notification Service.
Dispatches secure review links (/review/{token}) to doctors via SMTP or mock email logs.
Supports priority-based subjects, duplicate email prevention, environment-variable configuration,
and resilient failure handling.
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
    Modular email notification service for Doctor Review links.
    Configured via environment variables: DOCTOR_EMAIL, EMAIL_ENABLED, EMAIL_FROM, APP_BASE_URL, SMTP_HOST, etc.
    """

    def __init__(self, email_log_path: str = None):
        project_root = Path(__file__).resolve().parent.parent
        self.log_path = Path(email_log_path) if email_log_path else project_root / "data" / "sent_emails" / "doctor_emails.json"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
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

    def get_subject_for_priority(self, priority: str, is_test: bool = False) -> str:
        if is_test:
            return "TEST — Doctor Review Notification"

        p_upper = str(priority).upper()
        if p_upper == "HIGH":
            return "URGENT — Medicine Verification Required"
        elif p_upper == "MEDIUM":
            return "Medicine Verification Review Required"
        else:
            return "Medicine Prediction Confirmation Request"

    def generate_email_content(self, doctor_email: str, review_task: dict, token_record: dict, is_test: bool = False) -> dict:
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")
        token = token_record.get("token", "")
        review_url = f"{base_url}/review/{token}"

        priority = str(review_task.get("priority", "HIGH")).upper()
        brand = review_task.get("original_prediction", "Unknown")
        conf_val = float(review_task.get("original_confidence", 0.0)) * 100
        status_msg = review_task.get("prediction_status", "Doctor verification required")
        top_candidates = review_task.get("top_3_predictions", [])

        subject = self.get_subject_for_priority(priority, is_test=is_test)

        # Plain Text Body
        candidates_text = ""
        for idx, c in enumerate(top_candidates[:3], 1):
            c_name = c.get("brand_name", "Unknown")
            c_conf = float(c.get("confidence", 0.0)) * 100
            candidates_text += f"{idx}. {c_name} — {c_conf:.1f}%\n"

        plain_body = f"""Doctor,

A prescription requires verification by the AI-assisted medicine recognition system.

Priority:
{priority}

AI Prediction:
{brand}

AI Confidence:
{conf_val:.1f}%

Status:
{status_msg}

Top Predictions:
{candidates_text}
Please review the prescription using the secure link below:

[ OPEN SECURE REVIEW ]

Review link:
{review_url}

This review link expires after 24 hours.

This system is a healthcare decision-support research prototype and does not provide autonomous medical diagnosis or prescribing.
"""

        # HTML Body
        candidates_html = ""
        for idx, c in enumerate(top_candidates[:3], 1):
            c_name = c.get("brand_name", "Unknown")
            c_conf = float(c.get("confidence", 0.0)) * 100
            c_gen = c.get("generic_name") or "N/A"
            candidates_html += f"<tr><td>#{idx}</td><td><strong>{c_name}</strong></td><td>{c_gen}</td><td>{c_conf:.1f}%</td></tr>"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f7fafc; margin: 0; padding: 20px; color: #2d3748; }}
            .card {{ max-width: 600px; background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin: auto; }}
            .badge-HIGH {{ background-color: #e53e3e; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
            .badge-MEDIUM {{ background-color: #dd6b20; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
            .badge-LOW {{ background-color: #319795; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
            .btn {{ display: inline-block; background-color: #2b6cb0; color: #ffffff !important; padding: 12px 24px; font-size: 16px; font-weight: bold; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
            th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #edf2f7; }}
            th {{ background: #edf2f7; }}
          </style>
        </head>
        <body>
          <div class="card">
            <h2>Doctor Review Required</h2>
            <p><strong>Priority:</strong> <span class="badge-{priority}">{priority}</span></p>

            <p>Doctor,</p>
            <p>A prescription requires verification by the AI-assisted medicine recognition system.</p>

            <table style="margin-bottom: 20px;">
              <tr><td><strong>AI Prediction:</strong></td><td><strong>{brand}</strong> ({conf_val:.1f}% confidence)</td></tr>
              <tr><td><strong>Status:</strong></td><td>{status_msg}</td></tr>
            </table>

            <h4>Top Predictions</h4>
            <table>
              <thead><tr><th>Rank</th><th>Brand</th><th>Generic</th><th>Confidence</th></tr></thead>
              <tbody>{candidates_html}</tbody>
            </table>

            <div style="text-align: center; margin-top: 25px;">
              <a href="{review_url}" class="btn" target="_blank">OPEN SECURE REVIEW</a>
            </div>

            <p style="margin-top: 25px; font-size: 13px; color: #4a5568;">
              🔒 Review link: <a href="{review_url}">{review_url}</a><br>
              This review link expires after 24 hours.
            </p>

            <p style="font-size: 11px; color: #718096; border-top: 1px solid #edf2f7; padding-top: 15px; margin-top: 25px;">
              This system is a healthcare decision-support research prototype and does not provide autonomous medical diagnosis or prescribing.
            </p>
          </div>
        </body>
        </html>
        """

        return {
            "to": doctor_email,
            "subject": subject,
            "plain_body": plain_body,
            "html_body": html_body,
            "review_url": review_url,
            "review_id": review_task.get("review_id"),
            "priority": priority,
            "sent_at": datetime.now(timezone.utc).isoformat()
        }

    def send_doctor_review_email(
        self,
        review_task: dict,
        token_record: dict,
        doctor_email: Optional[str] = None,
        force_resend: bool = False,
        is_test: bool = False
    ) -> dict:
        """
        Sends doctor review email notification.
        Handles duplicate prevention, environment configuration, failure fallback, and test modes.
        Never crashes caller if email delivery fails.
        """
        target_email = doctor_email or os.getenv("DOCTOR_EMAIL", "doctor@example.com")
        review_id = review_task.get("review_id")

        # 1. Duplicate Email Prevention Check
        logs = self._read_logs()
        for existing in logs:
            if existing.get("review_id") == review_id and existing.get("notification_status") == "SENT" and not force_resend:
                return {
                    "email_status": "SKIPPED_DUPLICATE",
                    "notification_status": "SENT",
                    "message": f"Email notification already sent for review_id '{review_id}'. Skipped duplicate dispatch.",
                    "to": target_email,
                    "review_url": existing.get("review_url"),
                    "subject": existing.get("subject"),
                    "email_error": None
                }

        # 2. Generate Content
        content = self.generate_email_content(target_email, review_task, token_record, is_test=is_test)

        email_enabled = os.getenv("EMAIL_ENABLED", "false").lower() in ["true", "1", "yes"]

        smtp_host = os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        email_from = os.getenv("EMAIL_FROM", "no-reply@example.com")

        record = {
            "review_id": review_id,
            "to": target_email,
            "subject": content["subject"],
            "review_url": content["review_url"],
            "priority": content["priority"],
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "notification_status": "NOT_SENT",
            "email_status": "PENDING",
            "email_error": None
        }

        # 3. Handle Delivery
        if not email_enabled:
            record["notification_status"] = "DISABLED"
            record["email_status"] = "DISABLED"
            record["message"] = "EMAIL_ENABLED is false. Email notification logged in test/mock mode."
        elif smtp_host and smtp_user and smtp_pass:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = content["subject"]
                msg["From"] = email_from
                msg["To"] = target_email
                msg.attach(MIMEText(content["plain_body"], "plain"))
                msg.attach(MIMEText(content["html_body"], "html"))

                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(email_from, target_email, msg.as_string())

                record["notification_status"] = "SENT"
                record["email_status"] = "SENT"
                record["message"] = "Email notification successfully sent via SMTP."
            except Exception as e:
                record["notification_status"] = "FAILED"
                record["email_status"] = "FAILED"
                record["email_error"] = str(e)
                record["message"] = f"SMTP dispatch failed: {str(e)}"
        else:
            record["notification_status"] = "LOGGED_LOCAL_MOCK"
            record["email_status"] = "LOGGED_LOCAL_MOCK"
            record["message"] = "SMTP credentials not provided. Logged in mock mode."

        logs.append(record)
        self._write_logs(logs)

        return record
