import time
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dotenv import load_dotenv
load_dotenv()
import smtplib
from email.mime.text import MIMEText

# DB
from db.database import FinOpsDatabase

# Fix import path

from data.synthetic.generate_data import generate_cloud_billing_data

# ================= DB INIT =================
db = FinOpsDatabase(os.getenv("DATABASE_URL"))

# ================= EMAIL CONFIG =================
SENDER_EMAIL = "ayushmali1904@gmail.com"
APP_PASSWORD = os.getenv("APP")
RECEIVER_EMAIL = "ambikashiv82@gmail.com"
print("APP_PASSWORD:", APP_PASSWORD)
def send_email_alert(message):
    msg = MIMEText(message, "html")
    msg["Subject"] = "FinOps Guardian Alert | Anomaly Detected"
    msg["From"] = f"FinOps Guardian <{SENDER_EMAIL}>"
    msg["To"] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
            print("📧 Email sent!")
    except Exception as e:
        print("❌ Email failed:", e)

# ================= ANOMALY DETECTOR =================
def simple_anomaly_detector(cost, history):
    if len(history) < 10:
        return 0
    
    mean = sum(history) / len(history)
    std = (sum((x - mean) ** 2 for x in history) / len(history)) ** 0.5
    
    if std == 0:
        return 0
    
    z_score = abs((cost - mean) / std)
    return 1 if z_score > 2.5 else 0

# ================= STREAM =================
def stream_data():
    print("🚀 Starting LIVE data stream...")

    history = []
    batch = []

    while True:
        # 🔥 generate fresh data every loop (REAL live behavior)
        df = generate_cloud_billing_data(days=1)

        for _, row in df.iterrows():
            record = row.to_dict()
            cost = record["cost_usd"]

            # detect anomaly
            is_anomaly = simple_anomaly_detector(cost, history)

            # update history
            history.append(cost)
            if len(history) > 50:
                history.pop(0)

            # ================= PRINT =================
            if is_anomaly:
                print("🚨 ANOMALY DETECTED:", record)

                # ================= EMAIL ALERT =================
                alert_msg = f"""
<html>
<body style="font-family: 'Helvetica Neue', Arial, sans-serif; color: #1a1a1a; background-color:#f9fafc; padding:30px;">

    <!-- Header -->
    <div style="text-align:center; margin-bottom:25px;">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#d9534f" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom:10px;">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <h2 style="margin:0; font-weight:500;">FinOps Guardian Alert</h2>
        <hr style="margin-top:15px; border:none; border-top:1px solid #e5e7eb; width:60%;">
    </div>

    <!-- Greeting -->
    <p style="margin-bottom:20px;"><strong>Dear Valued Customer,</strong></p>

    <!-- Description -->
    <p style="line-height:1.6; margin-bottom:25px;">
    We have detected an anomaly in your organization's cloud infrastructure usage.
    This may indicate unusual activity or inefficient resource allocation requiring attention.
    </p>

    <!-- Details Card -->
    <div style="background:white; padding:20px; border-radius:10px; border:1px solid #e5e7eb; width:70%; margin-bottom:25px;">
        <table style="width:100%; border-collapse:collapse;">
            <tr>
                <td style="padding:10px 30px 10px 0;"><strong>Provider</strong></td>
                <td>{record['provider']}</td>
            </tr>
            <tr>
                <td style="padding:10px 30px 10px 0;"><strong>Service</strong></td>
                <td>{record['service']}</td>
            </tr>
            <tr>
                <td style="padding:10px 30px 10px 0;"><strong>Team</strong></td>
                <td>{record['team']}</td>
            </tr>
            <tr>
                <td style="padding:10px 30px 10px 0;"><strong>Cost</strong></td>
                <td>${round(record['cost_usd'], 2)}</td>
            </tr>
            <tr>
                <td style="padding:10px 30px 10px 0;"><strong>Severity</strong></td>
                <td style="color:#d9534f; font-weight:500;">
                    {"HIGH" if record['cost_usd'] > 2000 else "MEDIUM" if record['cost_usd'] > 1000 else "LOW"}
                </td>
            </tr>
        </table>
    </div>

    <!-- Impact -->
    <p style="line-height:1.6; margin-bottom:20px;">
    This anomaly may impact cost efficiency and operational performance if left unaddressed.
    </p>

    <!-- Actions -->
    <div style="margin-bottom:25px;">
        <h3 style="margin-bottom:10px; font-weight:500;">Recommended Actions</h3>
        <ul style="line-height:1.8; padding-left:18px;">
            <li>Review recent deployments and configuration changes</li>
            <li>Analyze scaling behavior and resource usage</li>
            <li>Check for abnormal traffic or unexpected spikes</li>
        </ul>
    </div>

    <!-- Footer -->
    <hr style="border:none; border-top:1px solid #e5e7eb; margin:25px 0;">
    <p style="color:#6b7280;">
        Sincerely,<br>
        FinOps Guardian Team
    </p>

</body>
</html>
"""
                send_email_alert(alert_msg)

            else:
                print("✅ Normal:", record)

            # ================= DB RECORD =================
            batch.append({
                "date": record["date"],
                "provider": record["provider"],
                "service_category": record["service"],
                "team": record["team"],
                "cost_usd": record["cost_usd"],
                "is_anomaly": is_anomaly,
                "severity_label": "low",
                "severity_score": 0.1,
                "root_cause": "stream detected",
                "llm_insight": "stream data",
                "recommended_action": "check usage",
                "estimated_savings": "$0",
                "model_votes": 1,
                "impact_score": record["cost_usd"] * 0.1,
                "priority": "P3 - Low"
            })

            # slow down stream
            time.sleep(0.2)

            # ================= BATCH INSERT =================
            if len(batch) >= 100:
                df_batch = pd.DataFrame(batch)
                db.insert_anomalies(df_batch)
                batch.clear()

        # flush remaining
        if batch:
            df_batch = pd.DataFrame(batch)
            db.insert_anomalies(df_batch)
            batch.clear()

        print("🔁 Looping data again...\n")

# ================= RUN =================
if __name__ == "__main__":
    stream_data()