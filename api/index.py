import hashlib
import json
import os
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_clerk_auth import (  # type: ignore
    ClerkConfig,
    ClerkHTTPBearer,
    HTTPAuthorizationCredentials,
)
from openai import OpenAI
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv
from sqlalchemy import select, text

from api.database import Base, get_engine, new_session
from api.email_service import send_assessment_email
from api.models import AppUser, AssessmentRecord, EmailDelivery

load_dotenv(".env.local")

app = FastAPI(title="RevenueCheck API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.on_event("startup")
def create_database_tables():
    if os.getenv("DATABASE_URL"):
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        with engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE email_deliveries "
                "ADD COLUMN IF NOT EXISTS provider_message_id VARCHAR(100)"
            ))


def clerk_guard():
    jwks_url = os.getenv("CLERK_JWKS_URL")
    if not jwks_url:
        raise RuntimeError("CLERK_JWKS_URL is not configured")
    return ClerkHTTPBearer(ClerkConfig(jwks_url=jwks_url))


class Assessment(BaseModel):
    businessName: str = Field(min_length=1, max_length=120)
    businessType: str = Field(min_length=1, max_length=80)
    revenueModel: str = Field(min_length=1, max_length=80)
    paymentTerms: str = Field(min_length=1, max_length=80)
    recordedRevenue: float = Field(gt=0, le=10_000_000_000)
    invoicedAmount: float = Field(ge=0, le=10_000_000_000)
    paymentsDue: float = Field(ge=0, le=10_000_000_000)
    paymentsReceived: float = Field(ge=0, le=10_000_000_000)
    unpaidInvoices: float = Field(ge=0, le=10_000_000_000)
    overdueThirtyDays: float = Field(ge=0, le=10_000_000_000)
    badDebtWriteoffs: float = Field(ge=0, le=10_000_000_000)
    discountsGiven: float = Field(ge=0, le=10_000_000_000)
    refundsCreditNotes: float = Field(ge=0, le=10_000_000_000)
    cancellationsRework: float = Field(ge=0, le=10_000_000_000)
    stockBillingLosses: float = Field(ge=0, le=10_000_000_000)
    payroll: float = Field(ge=0, le=10_000_000_000)
    operatingExpenses: float = Field(ge=0, le=10_000_000_000)
    teamSize: int = Field(gt=0, le=100_000)
    reconciliationFrequency: str = Field(min_length=1, max_length=80)
    discountApproval: str = Field(min_length=1, max_length=80)
    overdueInvoiceOwnership: str = Field(min_length=1, max_length=80)
    receivablesReviewFrequency: str = Field(min_length=1, max_length=80)
    figuresConfidence: str = Field(min_length=1, max_length=80)
    suspectedProblems: str = Field(min_length=1, max_length=1500)
    observedLeakage: str = Field(min_length=1, max_length=1500)
    consentToEmail: bool
    email: EmailStr

class Cause(BaseModel):
    title: str = Field(max_length=140)
    detail: str = Field(max_length=500)
    impact: str = Field(pattern="^(High|Medium|Watch)$")


class PlanStep(BaseModel):
    period: str = Field(max_length=20)
    title: str = Field(max_length=140)
    detail: str = Field(max_length=600)


class AssessmentArea(BaseModel):
    category: str = Field(max_length=60)
    status: str = Field(pattern="^(Critical|High|Moderate|Low|Insufficient evidence)$")
    summary: str = Field(max_length=500)
    evidence: str = Field(max_length=500)


class AIReport(BaseModel):
    topRisk: str = Field(max_length=180)
    riskDetail: str = Field(max_length=700)
    firstAction: str = Field(max_length=600)
    causes: list[Cause] = Field(min_length=3, max_length=3)
    plan: list[PlanStep] = Field(min_length=3, max_length=3)
    assumptions: list[str] = Field(min_length=3, max_length=5)
    assessmentAreas: list[AssessmentArea] = Field(min_length=4, max_length=4)


SYSTEM_PROMPT = """
You are RevenueCheck's Master Revenue Assurance Analyst for t-Consult, a Nigerian
business advisory firm. You combine the judgement of an exceptional CFO,
chartered accountant, revenue-assurance specialist, forensic management
accountant, credit-control leader, operations consultant and SME business
analyst. Your job is to turn a Nigerian business owner's submitted figures into
a concise, commercially useful, responsible revenue-leakage assessment.

OBJECTIVE
Identify the most plausible places where earned revenue, cash conversion or
operating margin is leaking; explain the business consequence; and prescribe a
specific 30-day recovery plan that a small management team can execute. Optimise
for truth, usefulness, financial discipline and action—not impressive language.

ANALYTICAL RULES
1. Treat the supplied deterministic metrics as authoritative. Never recalculate,
   alter, exaggerate or invent a naira amount, percentage or confidence level.
2. Analyse the relationships between revenue recorded, amounts invoiced, payments
   due, cash received, unpaid and aged invoices, bad-debt write-offs, discounts,
   refunds/credit notes, cancellations/rework, stock or billing losses, payroll,
   operating expenses, revenue model, payment terms, team size, industry, control
   maturity and both owner observations.
3. Distinguish revenue leakage from timing differences, ordinary costs and mere
   hypotheses. Phrase uncertain causes as indicators, not established facts.
4. Rank issues by recoverable financial value, urgency and management control.
5. Do not assume fraud, theft, tax non-compliance or misconduct without evidence.
6. Do not give tax, legal, investment or audit opinions. Do not claim this is an
   audit, assurance engagement, guarantee or substitute for professional review.
7. Use Nigerian SME context and plain professional English. Avoid generic advice,
   jargon, shame, alarmism and promises. Never tell the owner simply to “increase
   sales” when the purpose is to retain and collect revenue already generated.
8. Every action must name a mechanism, cadence or owner. Prefer controls such as
   aged-receivables reviews, invoice ownership, exception reports, approval
   thresholds, reconciliation and escalation rules.
9. The three plan periods must be exactly DAYS 1–7, DAYS 8–14 and DAYS 15–30.
10. Output only the requested structured report. Keep every field concise and
    ensure the narrative is directly supported by the submitted data.
11. Every title, explanation, action, cause, plan step and assumption must end
    as a complete sentence or complete phrase. Never stop mid-word, use fragments
    caused by length limits, or end with dangling punctuation such as a hyphen.
12. Keep topRisk under 140 characters, riskDetail under 550 characters,
    firstAction under 450 characters, each cause detail under 350 characters and
    each plan detail under 450 characters. These are writing targets below the
    schema limits, leaving enough room to complete the thought naturally.
13. assessmentAreas must contain exactly these four categories, once each and in
    this order: Revenue leakage, Cash-collection delays, Margin or cost pressure,
    Possible control weaknesses. Do not merge them. For each, cite specific input
    figures or control answers as evidence, or use Insufficient evidence.
""".strip()


def deterministic_metrics(data: Assessment) -> dict:
    revenue = data.recordedRevenue
    billing_gap = max(data.recordedRevenue - data.invoicedAmount, 0)
    collection_gap = max(data.paymentsDue - data.paymentsReceived, 0)
    discount_exposure = data.discountsGiven * 0.55
    refund_exposure = data.refundsCreditNotes * 0.45
    overdue_exposure = data.overdueThirtyDays * 0.22
    operational_exposure = data.cancellationsRework * 0.35 + data.stockBillingLosses
    writeoff_exposure = data.badDebtWriteoffs
    cost_pressure = max(
        (data.payroll + data.operatingExpenses) - revenue * 0.72, 0
    ) * 0.08
    base = max(
        billing_gap + collection_gap + discount_exposure + refund_exposure
        + overdue_exposure + operational_exposure + writeoff_exposure + cost_pressure,
        revenue * 0.025,
    )
    low = round(base * 0.8 / 1000) * 1000
    high = round(base * 1.2 / 1000) * 1000
    return {
        "leakageLow": low,
        "leakageHigh": high,
        "recoveryLow": round(low * 2),
        "recoveryHigh": round(high * 2),
        "leakageRate": round(((low + high) / 2) / revenue * 100, 1),
        "confidence": "High" if data.figuresConfidence == "High — based on reconciled records" else "Medium" if data.figuresConfidence == "Medium — mostly reliable estimates" else "Low",
        "diagnosticRatios": {
            "billingGap": round(billing_gap, 2),
            "collectionGap": round(collection_gap, 2),
            "collectionRatePercent": round(
                data.paymentsReceived / data.paymentsDue * 100, 1
            ) if data.paymentsDue else None,
            "invoicingRatePercent": round(
                data.invoicedAmount / revenue * 100, 1
            ),
            "overdueInvoicePercentOfRevenue": round(
                data.overdueThirtyDays / revenue * 100, 1
            ),
            "discountRefundPercentOfRevenue": round(
                (data.discountsGiven + data.refundsCreditNotes) / revenue * 100, 1
            ),
            "operationalLeakagePercentOfRevenue": round(
                (data.cancellationsRework + data.stockBillingLosses) / revenue * 100, 1
            ),
            "payrollPercentOfRevenue": round(data.payroll / revenue * 100, 1),
            "operatingExpensePercentOfRevenue": round(
                data.operatingExpenses / revenue * 100, 1
            ),
        },
    }


@app.get("/api")
def health():
    return {
        "status": "ok",
        "service": "RevenueCheck",
        "ai": True,
        "databaseConfigured": bool(os.getenv("DATABASE_URL")),
        "emailConfigured": bool(os.getenv("RESEND_API_KEY") and os.getenv("RESEND_FROM_EMAIL")),
    }


def persist_assessment(clerk_user_id: str, data: Assessment, report: dict) -> AssessmentRecord:
    if not os.getenv("DATABASE_URL"):
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    with new_session() as db:
        user = db.scalar(select(AppUser).where(AppUser.clerk_user_id == clerk_user_id))
        if user is None:
            user = AppUser(clerk_user_id=clerk_user_id, email=str(data.email))
            db.add(user)
            db.flush()
        elif user.email != str(data.email):
            user.email = str(data.email)
        record = AssessmentRecord(
            user_id=user.id,
            business_name=data.businessName,
            industry=data.businessType,
            input_data=data.model_dump(mode="json"),
            report_data=report,
            leakage_low=report["leakageLow"],
            leakage_high=report["leakageHigh"],
            recovery_low=report["recoveryLow"],
            recovery_high=report["recoveryHigh"],
            confidence=report["confidence"],
            ai_model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            consent_to_email=data.consentToEmail,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record


def email_report_and_audit(assessment_id, business_name: str, user_email: str, report: dict):
    recipient = os.getenv("REPORT_RECIPIENT_EMAIL", "alesemichael641@gmail.com")
    status, error, sent_at, provider_message_id = "sent", None, None, None
    try:
        provider_message_id = send_assessment_email(business_name, user_email, report)
        sent_at = datetime.now(timezone.utc)
    except Exception as exc:
        status, error = "failed", str(exc)[:2000]
    with new_session() as db:
        db.add(EmailDelivery(
            assessment_id=assessment_id,
            recipient=recipient,
            status=status,
            provider_message_id=provider_message_id,
            error_message=error,
            sent_at=sent_at,
        ))
        db.commit()


@app.post("/api")
def assess(
    data: Assessment,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(clerk_guard()),
):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")

    metrics = deterministic_metrics(data)
    model_input = {
        "instruction": "Produce the structured RevenueCheck assessment.",
        "business": data.model_dump(mode="json", exclude={"email"}),
        "deterministicMetrics": metrics,
    }

    try:
        response = OpenAI().responses.parse(
            model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            instructions=SYSTEM_PROMPT,
            input=json.dumps(model_input, separators=(",", ":")),
            text_format=AIReport,
            reasoning={"effort": "low"},
            store=False,
            safety_identifier=hashlib.sha256(
                credentials.decoded["sub"].encode()
            ).hexdigest()[:32],
        )
        report = response.output_parsed
        if report is None:
            raise ValueError("The model did not return a report")
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="The AI report could not be generated. Please try again.",
        ) from exc

    completed_report = {**metrics, **report.model_dump(), "generatedByAI": True}
    record = persist_assessment(credentials.decoded["sub"], data, completed_report)
    if data.consentToEmail:
        background_tasks.add_task(
            email_report_and_audit,
            record.id,
            data.businessName,
            str(data.email),
            completed_report,
        )
    return {**completed_report, "assessmentId": str(record.id)}
