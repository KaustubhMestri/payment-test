from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import uuid
import os

# ===============================
# DATABASE CONFIG
# ===============================

DATABASE_URL = "sqlite:///./payments.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ===============================
# DATABASE MODEL
# ===============================

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    amount = Column(Float)
    upi_id = Column(String)
    upi_link = Column(String)
    utr_number = Column(String, nullable=True)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

# ===============================
# FASTAPI APP
# ===============================

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ⚠️ Replace with your real UPI ID if needed
UPI_ID = "7720053652@kotakbank"

# ===============================
# CREATE PAYMENT PAGE
# ===============================

@app.get("/")
def payment_page(request: Request):
    amount = 1.00  # Test amount

    order_id = str(uuid.uuid4())[:8]

    upi_link = (
        f"upi://pay?"
        f"pa={UPI_ID}"
        f"&pn=TripPilot"
        f"&am={amount}"
        f"&cu=INR"
        f"&tn=TicketBooking_{order_id}"
    )

    db = SessionLocal()

    payment = Payment(
        order_id=order_id,
        amount=amount,
        upi_id=UPI_ID,
        upi_link=upi_link,
        status="PENDING"
    )

    db.add(payment)
    db.commit()
    db.close()

    return templates.TemplateResponse(
        "payment.html",
        {
            "request": request,
            "order_id": order_id,
            "amount": amount,
            "upi_link": upi_link,
        },
    )


# ===============================
# SUBMIT UTR
# ===============================

@app.post("/submit-payment")
def submit_payment(order_id: str = Form(...), utr: str = Form(...)):

    db = SessionLocal()

    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order_id)
        .first()
    )

    if payment:
        payment.utr_number = utr
        payment.status = "UTR_SUBMITTED"
        db.commit()

    db.close()

    return RedirectResponse(url="/", status_code=303)


# ===============================
# RENDER DEPLOYMENT SUPPORT
# ===============================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
