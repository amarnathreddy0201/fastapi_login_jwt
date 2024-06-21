import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional
import logging
from beanie import PydanticObjectId
from fastapi import Depends, Request, APIRouter, Query
from fastapi.responses import JSONResponse
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import BeanieUserDatabase, ObjectIDIDMixin
from httpx_oauth.clients.google import GoogleOAuth2
from db import User, get_user_db
import tempfile
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET = "SECRET"
google_oauth_client = GoogleOAuth2(
    os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
)

class UserManager(ObjectIDIDMixin, BaseUserManager[User, PydanticObjectId]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        logger.info(f"User {user.id} has registered.")

    async def on_after_forgot_password(self, user: User, token: str, request: Optional[Request] = None):
        # Send email to the user with the reset password token
        await self.send_reset_password_email(user.email, token)
        logger.info(f"Reset password token sent to {user.email}")
        return JSONResponse(content={"token": token})

    async def send_reset_password_email(self, email: str, token: str):
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "somemain@example.in"
        smtp_password = "ooxi zbye qrvn smpj"
        subject = "Reset Password Request"
        reset_password_url = f"http://127.0.0.1:8000/auth/reset-password?token={token}"
        body = f"Click the following link to reset your password: <a href='{reset_password_url}'>{reset_password_url}</a>"
        sender_email = "somemain@example.in"
        recipient_email = email
        msg = MIMEText(body, 'html')
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient_email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, [recipient_email], msg.as_string())
            logger.info(f"Password reset email sent to {recipient_email}.")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {recipient_email}: {e}")

    async def on_after_request_verify(self, user: User, token: str, request: Optional[Request] = None):
        logger.info(f"Verification requested for user {user.id}. Verification token: {token}")

# Add the function to send the PDF download email
async def send_pdf_download_email(email: str, s3_url: str):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "somemail@example.in"
    smtp_password = "ooxi zbye qrvn smpj"
    subject = "PDF Downloaded"
    body = "Please find the downloaded PDF attached to this email."
    sender_email = "somemain@example.in"
    recipient_email = email

    # Download the PDF file from S3
    s3_client = boto3.client('s3')
    try:
        bucket_name = s3_url.split('/')[2].split('.')[0]
        object_key = '/'.join(s3_url.split('/')[3:])
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        file_content = response['Body'].read()

        # Save the PDF file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        # Compose the email message
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg.attach(MIMEText(body))

        with open(temp_file_path, "rb") as attachment:
            part = MIMEApplication(attachment.read(), _subtype="pdf")
            part.add_header("Content-Disposition", "attachment", filename=os.path.basename(object_key))
            msg.attach(part)

        # Send the email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, [recipient_email], msg.as_string())
            logger.info(f"PDF download email sent to {recipient_email}.")
        except Exception as e:
            logger.error(f"Failed to send PDF download email to {recipient_email}: {e}")
            raise
    except Exception as e:
        logger.error(f"Failed to download the PDF file from S3: {e}")
        raise
    finally:
        # Delete the temporary PDF file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)



async def get_user_manager(user_db: BeanieUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, PydanticObjectId](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)

# Create a new router for the auth routes
auth_router = APIRouter()

@auth_router.get("/pdf-downloaded", tags=["auth"])
async def pdf_downloaded(
    user: User = Depends(current_active_user),
    s3_url: str = Query(..., description="S3 URL of the PDF file")
):
    try:
        await send_pdf_download_email(user.email, s3_url)
        return JSONResponse(content={"message": "PDF downloaded. Email sent with attachment."})
    except Exception as e:
        logger.error(f"Failed to send PDF download email: {e}")
        return JSONResponse(content={"error": "Failed to send email with attachment."}, status_code=500)

