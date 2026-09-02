import html
import os

import resend


def send_assessment_email(business_name: str, user_email: str, report: dict) -> str:
    required = ["RESEND_API_KEY", "RESEND_FROM_EMAIL"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing Resend configuration: {', '.join(missing)}")

    recipient = os.getenv("REPORT_RECIPIENT_EMAIL", "alesemichael641@gmail.com")
    causes = "".join(
        f"<li><strong>{html.escape(c['title'])}</strong>: {html.escape(c['detail'])}</li>"
        for c in report["causes"]
    )
    plan = "".join(
        f"<li><strong>{html.escape(step['period'])} — {html.escape(step['title'])}</strong>: "
        f"{html.escape(step['detail'])}</li>" for step in report["plan"]
    )
    body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#123c32;line-height:1.55">
      <h1>RevenueCheck assessment</h1>
      <p><strong>Business:</strong> {html.escape(business_name)}<br>
      <strong>Submitted by:</strong> {html.escape(user_email)}</p>
      <h2>Estimated monthly leakage</h2>
      <p>₦{report['leakageLow']:,.0f} – ₦{report['leakageHigh']:,.0f}</p>
      <h2>Top risk</h2><p><strong>{html.escape(report['topRisk'])}</strong></p>
      <p>{html.escape(report['riskDetail'])}</p>
      <h2>Recommended first action</h2><p>{html.escape(report['firstAction'])}</p>
      <h2>Likely leakage points</h2><ol>{causes}</ol>
      <h2>30-day plan</h2><ol>{plan}</ol>
    </body></html>
    """
    resend.api_key = os.environ["RESEND_API_KEY"]
    result = resend.Emails.send({
        "from": os.environ["RESEND_FROM_EMAIL"],
        "to": [recipient],
        "reply_to": user_email,
        "subject": f"RevenueCheck assessment — {business_name}",
        "html": body,
    })
    message_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)
    if not message_id:
        raise RuntimeError("Resend accepted no message ID")
    return str(message_id)
