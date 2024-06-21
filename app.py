import logging
from beanie import init_beanie
from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from db import User, db
from schemas import UserCreate, UserRead, UserUpdate
from users import auth_backend, current_active_user, fastapi_users, google_oauth_client, auth_router
from typing import List, Dict
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from PIL import Image
import cv2
import base64
import uuid
from datetime import datetime, date, timedelta
import numpy as np
import os
# from aws_config import AWSConfig
from utils.system_logger import log_request_stats as log_system_stats

app = FastAPI()

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_request_stats(request: Request, call_next):
    logger.info(f"Request {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status code: {response.status_code}")

    # Call the imported function to log request stats using system_logger's functionality
    log_system_stats(request.method, str(request.url))
    
    return response

# Mount the static directory for serving images
# app.mount("/static", StaticFiles(directory="../static"), name="static")

# Jinja2 templates for HTML rendering
templates = Jinja2Templates(directory="../templates")


# aws_config = AWSConfig()





class CountRequest(BaseModel):
    base64_image: str

async def get_current_admin_user(user: User = Depends(current_active_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden: Requires admin role")
    return user

@app.post("/doubt")
async def doubt(
    request: Request,
    count_request: CountRequest,
    user: User = Depends(get_current_admin_user)
):
    
    

    current_utc_datetime = datetime.utcnow()
    ist_offset = timedelta(hours=5, minutes=30)
    current_ist_datetime = current_utc_datetime + ist_offset
    ist_date = current_ist_datetime.date().isoformat()
    ist_time = current_ist_datetime.time().isoformat(timespec='seconds')
    count_text ="doubts"
    count_info = {
        "ID": str(uuid.uuid4()),
        "Date": ist_date,
        "Time": ist_time,
        "Doubt": count_text,
        
    }
    user.counts.append(count_info)

    # Update the count_requests field for the user
    current_date = current_ist_datetime.date()
    count_request_entry = next((entry for entry in user.count_requests if entry["date"] == current_date.isoformat()), None)
    if count_request_entry:
        count_request_entry["doubt"] += 1
    else:
        user.count_requests.append({"date": current_date.isoformat(), "doubt": 1})

    await user.update({"$set": {"doubts": user.counts, "count_requests": user.count_requests}})
    logger.info("doubt and data is valid")

    # os.remove(processed_image_path)
    
    return {"Doubt": count_text}

@app.get("/user-doubts", response_model=List[Dict])
async def get_user_counts(user: User = Depends(current_active_user)):
    logger.info("Retrieving user doubts")
    return user.counts

# @app.get("/user-counts/{date}", response_model=List[Dict])
# async def get_user_counts_by_date(date: date, user: User = Depends(current_active_user)):
#     filtered_counts = [count for count in user.counts if count["Date"] == date.isoformat()]
#     logger.info(f"Retrieving user counts for date: {date}")
#     return filtered_counts

@app.get("/no-of-requests")
async def get_no_of_requests(date: date):
    users = await User.find().to_list()
    total_count = sum(entry["doubt"] for user in users for entry in user.count_requests if entry.get("date") == date.isoformat())
    return {"date": date.isoformat(), "total_count": total_count}

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])
app.include_router(fastapi_users.get_oauth_router(google_oauth_client, auth_backend, "SECRET", associate_by_email=True, is_verified_by_default=True), prefix="/auth/google", tags=["auth"])

@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    logger.info(f"Authenticated route accessed by {user.email}")
    return {"message": f"Hello {user.email}!"}

@app.get("/logs")
async def get_logs():
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    logs_path = os.path.join(current_file_dir, 'utils', 'logs.txt')
    
    if not os.path.isfile(logs_path):
        logger.warning("Log file not found")
        return {"error": "Log file not found."}
    
    logger.info("Logs retrieved")
    return FileResponse(logs_path)

@app.on_event("startup")
async def on_startup():
    logger.info("Application startup")
    await init_beanie(database=db, document_models=[User])

@app.get("/")
async def health_check():
    logger.debug("Health check endpoint called")
    return {"status": "UP"}



import uvicorn

if __name__ == "__main__":
    uvicorn.run(app,host="0.0.0.0",port=8000)
