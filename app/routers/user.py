from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import hash_password, verify_password, create_access_token
from app.dependencies import get_db, get_current_user
router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):

    existing = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login", response_model=schemas.Token)
def login(
    user: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        user.password,
        db_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "sub": str(db_user.id)
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/", response_model=list[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()
@router.get("/me", response_model=schemas.UserResponse)
def get_me(
    current_user: models.User = Depends(get_current_user)
):
    return current_user


@router.post("/forgot-password")
def forgot_password(user: schemas.UserLogin):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    sender_email = "ingrelens1app@gmail.com"
    app_password = "sfunuwxviqglzvvg"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "IngreLens - Reset Your Password"
        msg["From"] = f"IngreLens Support <{sender_email}>"
        msg["To"] = user.email

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; rounded: 12px;">
            <h2 style="color: #00C853; text-align: center;">IngreLens Password Reset</h2>
            <p>Hello,</p>
            <p>We received a request to reset your password for your <strong>IngreLens</strong> health shield account.</p>
            <p>Click the link below to set a new password:</p>
            <div style="text-align: center; margin: 25px 0;">
                <a href="http://localhost:5173/reset-password?email={user.email}" 
                   style="background-color: #00C853; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p style="color: #777; font-size: 12px;">If you did not request this password reset, please ignore this email.</p>
        </div>
        """

        msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, user.email, msg.as_string())
        server.quit()

        return {"message": f"Password reset email sent successfully to {user.email}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
