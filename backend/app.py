import os
import smtplib
import ssl
from email.message import EmailMessage

import hashlib
import hmac
import re
import secrets
import time

from functools import wraps
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from flask import Flask, g, jsonify, request, send_file, url_for
from mysql.connector import IntegrityError
from PIL import Image as PILImage, UnidentifiedImageError
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Image as PDFImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db_connection, fetch_all, fetch_one, execute_query


# Application Configuration

app = Flask(__name__)

pending_otps = {}
password_reset_otps = {}
login_sessions = {}

OTP_EXPIRY_SECONDS = 300
SESSION_EXPIRY_SECONDS = 24 * 60 * 60
REMEMBER_ME_EXPIRY_SECONDS = 30 * 24 * 60 * 60
MAX_OTP_ATTEMPTS = 5

PHOTO_DIRECTORY = Path(__file__).resolve().parent / "uploads" / "profile_photos"
PHOTO_DIRECTORY.mkdir(parents=True, exist_ok=True)

MAX_PHOTO_BYTES = 5 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_PHOTO_BYTES + 1024 * 1024


# General Helpers

def get_json_data():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def clean_text(value):
    return value.strip() if isinstance(value, str) else ""


def required_string(data, field):
    return isinstance(data.get(field), str) and bool(data[field].strip())


def validate_text_fields(data, fields):
    for field in fields:
        if field in data and not isinstance(data[field], str):
            return f"{field} must be a string"
    return None


def error_response(message, status=400):
    return jsonify({"error": message}), status


def current_user_id():
    return g.current_user["id"]


# Database User Helpers

def find_user_by_email(email):
    user = fetch_one(
        """
        SELECT user_id AS id,
               username AS name,
               email,
               password_hash,
               email_verified
        FROM users
        WHERE email = %s
        """,
        (email,)
    )

    if user:
        user["email_verified"] = bool(user["email_verified"])

    return user


def find_user_by_id(user_id):
    user = fetch_one(
        """
        SELECT user_id AS id,
               username AS name,
               email,
               password_hash,
               email_verified
        FROM users
        WHERE user_id = %s
        """,
        (user_id,)
    )

    if user:
        user["email_verified"] = bool(user["email_verified"])

    return user


def public_user(user):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "email_verified": bool(user["email_verified"]),
    }



# Email Configuration

EMAIL_ADDRESS = "cvtool60@gmail.com"
EMAIL_SENDER_NAME = "CV Tool 2"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465


class EmailDeliveryError(Exception):
    pass


def send_otp_email(recipient, code, purpose):
    password = os.environ.get(
        "CV_EMAIL_PASSWORD", ""
    ).replace(" ", "")

    if not password:
        raise EmailDeliveryError(
            "Email password is not configured"
        )

    message = EmailMessage()

    message["From"] = f"{EMAIL_SENDER_NAME} <{EMAIL_ADDRESS}>"
    message["To"] = recipient
    message["Subject"] = f"CV Tool 2 - {purpose}"

    message.set_content(
        f"""
Hello,

Your CV Tool 2 verification code is:

{code}

This code is valid for 5 minutes.

Do not share this code with anyone.

If you did not request this code,
please ignore this email.

Best regards,
CV Tool 2 Team
"""
    )

    message.add_alternative(
        f"""
        <html>
        <body style="background:#f3f4f6;padding:30px;font-family:Arial;">
            <div style="max-width:500px;margin:auto;background:white;
                        padding:30px;border-radius:12px;">

                <h1 style="color:#2563eb;text-align:center;">
                    CV Tool 2
                </h1>

                <h2 style="color:#111827;">
                    {purpose}
                </h2>

                <p>Hello,</p>

                <p>Use the verification code below to continue:</p>

                <div style="background:#eff6ff;color:#2563eb;
                            font-size:32px;font-weight:bold;
                            letter-spacing:8px;text-align:center;
                            padding:20px;border-radius:8px;">
                    {code}
                </div>

                <p>This code is valid for <strong>5 minutes</strong>.</p>

                <p>Do not share this code with anyone.</p>

                <p>If you did not request this code,
                   please ignore this email.</p>

                <hr style="border:0;border-top:1px solid #e5e7eb;">

                <p style="color:#6b7280;font-size:13px;">
                    Best regards,<br>
                    CV Tool 2 Team
                </p>

            </div>
        </body>
        </html>
        """,
        subtype="html"
    )

    try:
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(
            SMTP_SERVER,
            SMTP_PORT,
            context=context,
            timeout=15
        ) as server:

            server.login(EMAIL_ADDRESS, password)
            server.send_message(message)

    except (smtplib.SMTPException, OSError) as error:
        app.logger.error(
            "OTP email delivery failed: %s",
            type(error).__name__
        )

        raise EmailDeliveryError(
            "Unable to send verification email"
        ) from error


@app.errorhandler(EmailDeliveryError)
def handle_email_delivery_error(error):
    return jsonify({
        "error": "Unable to send verification email. Please try again."
    }), 503


# OTP Helpers

def generate_otp():
    return f"{secrets.randbelow(1000000):06d}"


def hash_otp(code, salt):
    return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()


def create_otp_record(storage, email, purpose):
    code = generate_otp()
    salt = secrets.token_hex(16)

    send_otp_email(email, code, purpose)

    storage[email] = {
        "salt": salt,
        "code_hash": hash_otp(code, salt),
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        "attempts": 0,
    }


def create_otp_for_user(email):
    create_otp_record(
        pending_otps,
        email,
        "Email Verification OTP"
    )


def verify_otp_record(storage, email, code):
    record = storage.get(email)

    if record is None:
        return "No active OTP. Request a new code."

    if time.time() > record["expires_at"]:
        storage.pop(email, None)
        return "OTP expired. Request a new code."

    if record["attempts"] >= MAX_OTP_ATTEMPTS:
        storage.pop(email, None)
        return "Too many attempts. Request a new code."

    candidate = hash_otp(code, record["salt"])

    if not hmac.compare_digest(candidate, record["code_hash"]):
        record["attempts"] += 1

        if record["attempts"] >= MAX_OTP_ATTEMPTS:
            storage.pop(email, None)
            return "Too many attempts. Request a new code."

        return "Invalid OTP"

    return None


# Authentication Helpers

def create_login_token(user_id, remember_me=False):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    duration = (
        REMEMBER_ME_EXPIRY_SECONDS
        if remember_me
        else SESSION_EXPIRY_SECONDS
    )

    login_sessions[token_hash] = {
        "user_id": user_id,
        "expires_at": time.time() + duration,
    }

    return token, duration


def get_bearer_token():
    authorization = request.headers.get("Authorization", "")

    if not authorization.startswith("Bearer "):
        return None

    return authorization.split(" ", 1)[1].strip() or None


def get_current_user():
    token = get_bearer_token()

    if not token:
        return None

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = login_sessions.get(token_hash)

    if session is None:
        return None

    if time.time() > session["expires_at"]:
        login_sessions.pop(token_hash, None)
        return None

    user = find_user_by_id(session["user_id"])

    if user is None or not user["email_verified"]:
        login_sessions.pop(token_hash, None)
        return None

    return user


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        user = get_current_user()

        if user is None:
            return error_response(
                "Authentication required. Please log in.",
                401
            )

        g.current_user = user
        return function(*args, **kwargs)

    return wrapper


def invalidate_user_sessions(user_id):
    expired_tokens = [
        token_hash
        for token_hash, session in login_sessions.items()
        if session["user_id"] == user_id
    ]

    for token_hash in expired_tokens:
        login_sessions.pop(token_hash, None)


# Health Check

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Welcome to CV Tool 2",
        "status": "Backend is working!",
    }), 200


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "CV Tool 2 server is running",
    }), 200


@app.route("/api/db-health", methods=["GET"])
def database_health():
    connection = None

    try:
        connection = get_db_connection()

        return jsonify({
            "status": "ok",
            "message": "MySQL connection successful",
        }), 200

    except Exception:
        app.logger.exception("Database connection failed")

        return jsonify({
            "status": "error",
            "message": "Database connection failed",
        }), 503

    finally:
        if connection is not None:
            connection.close()


# User Registration

@app.route("/api/register", methods=["POST"])
def register():
    data = get_json_data()

    if data is None:
        return error_response("Invalid JSON data")

    for field in ["name", "email", "password"]:
        if not required_string(data, field):
            return error_response(f"{field} is required")

    name = data["name"].strip()
    email = data["email"].strip().lower()
    password = data["password"]

    if len(name) > 50:
        return error_response(
            "Name must be 50 characters or fewer"
        )

    if len(email) > 100:
        return error_response(
            "Email must be 100 characters or fewer"
        )

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return error_response("Invalid email address")

    if len(password) < 8:
        return error_response(
            "Password must be at least 8 characters"
        )

    if find_user_by_email(email):
        return error_response(
            "Email is already registered",
            409
        )

    existing_username = fetch_one(
        "SELECT user_id FROM users WHERE username = %s",
        (name,)
    )

    if existing_username:
        return error_response(
            "Username is already registered",
            409
        )

    password_hash = generate_password_hash(password)

    try:
        execute_query(
            """
            INSERT INTO users
                (username, email, password_hash, email_verified)
            VALUES (%s, %s, %s, %s)
            """,
            (name, email, password_hash, False)
        )

    except IntegrityError:
        return error_response(
            "Email or username is already registered",
            409
        )

    user = find_user_by_email(email)

    create_otp_for_user(email)

    return jsonify({
        "message": "Registration successful. Verify your email using the OTP.",
        "user": public_user(user),
    }), 201


# Email Verification

@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = get_json_data()

    if data is None:
        return error_response("Invalid JSON data")

    email = clean_text(data.get("email", "")).lower()
    code = str(data.get("otp", "")).strip()

    user = find_user_by_email(email)

    if user is None:
        return error_response("User not found", 404)

    if user["email_verified"]:
        return jsonify({
            "message": "Email is already verified",
            "user": public_user(user),
        }), 200

    error = verify_otp_record(pending_otps, email, code)

    if error:
        return error_response(error)

    execute_query(
        """
        UPDATE users
        SET email_verified = %s
        WHERE user_id = %s
        """,
        (True, user["id"])
    )

    pending_otps.pop(email, None)

    user = find_user_by_id(user["id"])

    return jsonify({
        "message": "Email verified successfully",
        "user": public_user(user),
    }), 200


@app.route("/api/resend-otp", methods=["POST"])
def resend_otp():
    data = get_json_data()

    if data is None:
        return error_response("Invalid JSON data")

    email = clean_text(data.get("email", "")).lower()

    user = find_user_by_email(email)

    if user is None:
        return error_response("User not found", 404)

    if user["email_verified"]:
        return error_response("Email is already verified")

    create_otp_for_user(email)

    return jsonify({
        "message": "A new OTP has been generated."
    }), 200


# Login with Remember Me

@app.route("/api/login", methods=["POST"])
def login():
    data = get_json_data()

    if data is None:
        return error_response("Invalid JSON data")

    email = clean_text(data.get("email", "")).lower()
    password = data.get("password", "")
    remember_me = data.get("remember_me", False)

    if not isinstance(password, str):
        return error_response("Invalid password")

    if not isinstance(remember_me, bool):
        return error_response(
            "remember_me must be true or false"
        )

    user = find_user_by_email(email)

    if user is None or not check_password_hash(
        user["password_hash"],
        password
    ):
        return error_response(
            "Invalid email or password",
            401
        )

    if not user["email_verified"]:
        return error_response(
            "Please verify your email before logging in.",
            403
        )

    token, duration = create_login_token(
        user["id"],
        remember_me=remember_me
    )

    return jsonify({
        "message": "Login successful",
        "token": token,
        "token_type": "Bearer",
        "expires_in": duration,
        "remember_me": remember_me,
        "user": public_user(user),
    }), 200


# Forgot Password

@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    data = get_json_data()

    if data is None:
        return error_response("Invalid JSON data")

    if not required_string(data, "email"):
        return error_response("Email is required")

    email = data["email"].strip().lower()
    user = find_user_by_email(email)

    if user is not None and user["email_verified"]:
        create_otp_record(
            password_reset_otps,
            email,
            "Password Reset OTP"
        )

    return jsonify({
        "message": (
            "If the email belongs to a verified account, "
            "a password reset OTP has been generated."
        )
    }), 200


@app.route("/api/verify-reset-otp", methods=["POST"])
def verify_reset_otp():
    data = get_json_data()

    if data is None:
        return error_response("Invalid JSON data")

    email = clean_text(data.get("email", "")).lower()
    code = str(data.get("otp", "")).strip()

    if not email or not code:
        return error_response("Email and OTP are required")

    error = verify_otp_record(
        password_reset_otps,
        email,
        code
    )

    if error:
        return error_response(error)

    return jsonify({
        "message": "Password reset OTP verified successfully"
    }), 200


@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    data = get_json_data()

    if data is None:
        return error_response("Invalid JSON data")

    email = clean_text(data.get("email", "")).lower()
    code = str(data.get("otp", "")).strip()
    new_password = data.get("new_password")

    if not email or not code:
        return error_response("Email and OTP are required")

    if not isinstance(new_password, str) or len(new_password) < 8:
        return error_response(
            "New password must be at least 8 characters"
        )

    user = find_user_by_email(email)

    if user is None or not user["email_verified"]:
        return error_response("Invalid password reset request")

    error = verify_otp_record(
        password_reset_otps,
        email,
        code
    )

    if error:
        return error_response(error)

    new_password_hash = generate_password_hash(new_password)

    execute_query(
        """
        UPDATE users
        SET password_hash = %s
        WHERE user_id = %s
        """,
        (new_password_hash, user["id"])
    )

    password_reset_otps.pop(email, None)
    invalidate_user_sessions(user["id"])

    return jsonify({
        "message": "Password reset successfully. Please log in again."
    }), 200


# Logout and Account Details

@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    token = get_bearer_token()
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    login_sessions.pop(token_hash, None)

    return jsonify({
        "message": "Logged out successfully"
    }), 200


@app.route("/api/me", methods=["GET"])
@login_required
def get_my_account():
    return jsonify({
        "user": public_user(g.current_user)
    }), 200


# Personal Information Helper

def find_my_profile():
    profile = fetch_one(
        """
        SELECT profile_id AS id,
               user_id,
               full_name,
               contact_email AS email,
               phone,
               address,
               professional_summary,
               photo_url AS photo_filename
        FROM user_profiles
        WHERE user_id = %s
        ORDER BY profile_id
        LIMIT 1
        """,
        (current_user_id(),)
    )

    if profile:
        for field in ["phone", "address", "professional_summary"]:
            profile[field] = profile[field] or ""

        if profile.get("photo_filename"):
            profile["photo_url"] = url_for(
                "get_profile_photo",
                _external=True
            )
        else:
            profile.pop("photo_filename", None)

    return profile


# Personal Information

@app.route("/api/personal-info", methods=["POST"])
@login_required
def save_personal_info():
    data = get_json_data()

    if data is None:
        return error_response("Invalid JSON data")

    for field in ["full_name", "email"]:
        if not required_string(data, field):
            return error_response(f"{field} is required")

    error = validate_text_fields(
        data,
        ["phone", "address", "professional_summary"]
    )

    if error:
        return error_response(error)

    full_name = data["full_name"].strip()
    email = data["email"].strip()
    phone = clean_text(data.get("phone", ""))
    address = clean_text(data.get("address", ""))
    summary = clean_text(data.get("professional_summary", ""))

    if len(full_name) > 100:
        return error_response("Full name is too long")

    if len(email) > 100:
        return error_response("Email is too long")

    if len(phone) > 100:
        return error_response("Phone is too long")

    if len(address) > 250:
        return error_response("Address is too long")

    connection = get_db_connection()

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE user_id = %s
                FOR UPDATE
                """,
                (current_user_id(),)
            )
            cursor.fetchone()

            cursor.execute(
                """
                SELECT profile_id
                FROM user_profiles
                WHERE user_id = %s
                ORDER BY profile_id
                LIMIT 1
                """,
                (current_user_id(),)
            )

            profile = cursor.fetchone()

            if profile is None:
                cursor.execute(
                    """
                    INSERT INTO user_profiles
                        (
                            user_id,
                            full_name,
                            contact_email,
                            phone,
                            address,
                            professional_summary
                        )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        current_user_id(),
                        full_name,
                        email,
                        phone,
                        address,
                        summary
                    )
                )

            else:
                cursor.execute(
                    """
                    UPDATE user_profiles
                    SET full_name = %s,
                        contact_email = %s,
                        phone = %s,
                        address = %s,
                        professional_summary = %s
                    WHERE profile_id = %s
                    AND user_id = %s
                    """,
                    (
                        full_name,
                        email,
                        phone,
                        address,
                        summary,
                        profile["profile_id"],
                        current_user_id()
                    )
                )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return jsonify({
        "message": "Personal information saved successfully",
        "data": find_my_profile(),
    }), 200


@app.route("/api/personal-info", methods=["GET"])
@login_required
def get_personal_info():
    profile = find_my_profile()

    if profile is None:
        return jsonify({
            "message": "No personal information saved yet"
        }), 404

    return jsonify(profile), 200


# Profile Photo Helpers

def get_photo_path(filename):
    if not filename:
        return None

    if not re.fullmatch(
        rf"user_{current_user_id()}_[a-f0-9]{{24}}\.jpg",
        filename
    ):
        return None

    return PHOTO_DIRECTORY / filename


def remove_photo_file(filename):
    path = get_photo_path(filename)

    if path:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            app.logger.exception("Could not remove profile photo")


# Profile Photo Upload

@app.route("/api/personal-info/photo", methods=["POST"])
@login_required
def upload_profile_photo():
    profile = find_my_profile()

    if profile is None:
        return error_response(
            "Save personal information before uploading a photo",
            404
        )

    photo = request.files.get("photo")

    if photo is None or not photo.filename:
        return error_response(
            "Upload an image using the 'photo' field"
        )

    image_bytes = photo.read(MAX_PHOTO_BYTES + 1)

    if len(image_bytes) > MAX_PHOTO_BYTES:
        return error_response(
            "Photo must be 5 MB or smaller",
            413
        )

    filename = (
        f"user_{current_user_id()}_"
        f"{secrets.token_hex(12)}.jpg"
    )

    photo_path = PHOTO_DIRECTORY / filename

    try:
        with PILImage.open(BytesIO(image_bytes)) as image:
            if image.format not in ("JPEG", "PNG"):
                return error_response(
                    "Only JPEG and PNG photos are allowed"
                )

            image.load()
            image = image.convert("RGB")
            image.thumbnail((800, 800))
            image.save(photo_path, format="JPEG", quality=90)

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        PILImage.DecompressionBombError,
    ):
        remove_photo_file(filename)
        return error_response("Invalid or corrupted image")

    old_filename = profile.get("photo_filename")

    try:
        execute_query(
            """
            UPDATE user_profiles
            SET photo_url = %s
            WHERE profile_id = %s
            AND user_id = %s
            """,
            (
                filename,
                profile["id"],
                current_user_id()
            )
        )

    except Exception:
        remove_photo_file(filename)
        raise

    remove_photo_file(old_filename)

    return jsonify({
        "message": "Profile photo uploaded successfully",
        "photo_url": url_for(
            "get_profile_photo",
            _external=True
        ),
    }), 200


@app.route("/api/personal-info/photo", methods=["GET"])
@login_required
def get_profile_photo():
    profile = find_my_profile()

    if profile is None or not profile.get("photo_filename"):
        return error_response("No profile photo uploaded", 404)

    photo_path = get_photo_path(profile["photo_filename"])

    if photo_path is None or not photo_path.is_file():
        return error_response("Photo file not found", 404)

    return send_file(photo_path, mimetype="image/jpeg")


@app.route("/api/personal-info/photo", methods=["DELETE"])
@login_required
def delete_profile_photo():
    profile = find_my_profile()

    if profile is None or not profile.get("photo_filename"):
        return error_response("No profile photo uploaded", 404)

    filename = profile["photo_filename"]

    execute_query(
        """
        UPDATE user_profiles
        SET photo_url = NULL
        WHERE profile_id = %s
        AND user_id = %s
        """,
        (profile["id"], current_user_id())
    )

    remove_photo_file(filename)

    return jsonify({
        "message": "Profile photo deleted successfully"
    }), 200


# Repository Configuration

REPOSITORIES = {
    "work_experiences": {
        "route": "/api/work-experience",
        "id": "experience_id",
        "label": "Work experience",
        "fields": {
            "job_title": "job_title",
            "company": "company",
            "start_date": "start_date",
            "end_date": "end_date",
            "description": "description",
        },
        "required": ["job_title", "company"],
        "limits": {
            "job_title": 100,
            "company": 100,
            "start_date": 20,
            "end_date": 20,
        },
    },

    "educations": {
        "route": "/api/education",
        "id": "education_id",
        "label": "Education",
        "fields": {
            "degree": "degree_qualification",
            "school": "school_university",
            "start_date": "start_date",
            "end_date": "end_date",
            "description": "description",
        },
        "required": ["degree", "school"],
        "limits": {
            "degree": 100,
            "school": 100,
            "start_date": 20,
            "end_date": 20,
        },
    },

    "skills": {
        "route": "/api/skills",
        "id": "skill_id",
        "label": "Skill",
        "fields": {
            "name": "skill_name",
            "level": "level",
        },
        "required": ["name"],
        "limits": {
            "name": 50,
            "level": 50,
        },
    },

    "languages": {
        "route": "/api/languages",
        "id": "language_id",
        "label": "Language",
        "fields": {
            "name": "language_name",
            "level": "proficiency",
        },
        "required": ["name"],
        "limits": {
            "name": 50,
            "level": 50,
        },
    },

    "projects": {
        "route": "/api/projects",
        "id": "project_id",
        "label": "Project",
        "fields": {
            "title": "project_title",
            "description": "description",
            "start_date": "start_date",
            "end_date": "end_date",
            "url": "project_url",
        },
        "required": ["title"],
        "limits": {
            "title": 100,
            "start_date": 20,
            "end_date": 20,
            "url": 255,
        },
    },

    "certificates": {
        "route": "/api/certificates",
        "id": "certificate_id",
        "label": "Certificate",
        "fields": {
            "name": "certificate_name",
            "issuer": "issuing_organization",
            "issue_date": "issue_date",
            "expiry_date": "expiry_date",
            "credential_url": "credential_url",
        },
        "required": ["name"],
        "limits": {
            "name": 100,
            "issuer": 100,
            "issue_date": 20,
            "expiry_date": 20,
            "credential_url": 255,
        },
    },
}


# Repository Database Helpers

def repository_select_columns(table):
    config = REPOSITORIES[table]

    columns = [
        f"{config['id']} AS id",
        "user_id"
    ]

    for api_field, db_field in config["fields"].items():
        columns.append(f"{db_field} AS {api_field}")

    return ", ".join(columns)


def normalize_repository_item(table, item):
    if item is not None:
        for field in REPOSITORIES[table]["fields"]:
            if item[field] is None:
                item[field] = ""

    return item


def owned_items(table):
    config = REPOSITORIES[table]
    columns = repository_select_columns(table)

    items = fetch_all(
        f"""
        SELECT {columns}
        FROM {table}
        WHERE user_id = %s
        ORDER BY {config['id']}
        """,
        (current_user_id(),)
    )

    return [
        normalize_repository_item(table, item)
        for item in items
    ]


def find_owned_item(table, item_id):
    config = REPOSITORIES[table]
    columns = repository_select_columns(table)

    item = fetch_one(
        f"""
        SELECT {columns}
        FROM {table}
        WHERE {config['id']} = %s
        AND user_id = %s
        """,
        (item_id, current_user_id())
    )

    return normalize_repository_item(table, item)


def validate_repository_data(table, data, updating=False):
    config = REPOSITORIES[table]

    if table == "skills":
        if "name" not in data and "skill_name" in data:
            data["name"] = data["skill_name"]

    error = validate_text_fields(data, config["fields"])

    if error:
        return error

    for field in config["required"]:
        if updating and field not in data:
            continue

        if not required_string(data, field):
            return f"{field} is required and cannot be empty"

    for field, limit in config["limits"].items():
        if field in data and len(data[field].strip()) > limit:
            return f"{field} must be {limit} characters or fewer"

    return None


# Add Repository Record

def add_repository_item(table):
    config = REPOSITORIES[table]
    data = get_json_data()

    if data is None:
        return error_response("Invalid JSON data")

    error = validate_repository_data(table, data)

    if error:
        return error_response(error)

    columns = ["user_id"]
    values = [current_user_id()]

    for api_field, db_field in config["fields"].items():
        columns.append(db_field)
        values.append(clean_text(data.get(api_field, "")))

    column_sql = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(values))

    item_id = execute_query(
        f"""
        INSERT INTO {table} ({column_sql})
        VALUES ({placeholders})
        """,
        tuple(values)
    )

    return jsonify({
        "message": f"{config['label']} added successfully",
        "data": find_owned_item(table, item_id),
    }), 201


# List Repository Records

def list_repository_items(table):
    items = owned_items(table)

    return jsonify({
        "data": items,
        "count": len(items),
    }), 200


# Update Repository Record

def update_repository_item(table, item_id):
    config = REPOSITORIES[table]

    item = find_owned_item(table, item_id)

    if item is None:
        return error_response(
            f"{config['label']} not found",
            404
        )

    data = get_json_data()

    if data is None:
        return error_response("Invalid JSON data")

    error = validate_repository_data(
        table,
        data,
        updating=True
    )

    if error:
        return error_response(error)

    assignments = []
    values = []

    for api_field, db_field in config["fields"].items():
        if api_field in data:
            assignments.append(f"{db_field} = %s")
            values.append(data[api_field].strip())

    if assignments:
        values.extend([item_id, current_user_id()])

        execute_query(
            f"""
            UPDATE {table}
            SET {", ".join(assignments)}
            WHERE {config['id']} = %s
            AND user_id = %s
            """,
            tuple(values)
        )

    return jsonify({
        "message": f"{config['label']} updated successfully",
        "data": find_owned_item(table, item_id),
    }), 200


# Delete Repository Record

def delete_repository_item(table, item_id):
    config = REPOSITORIES[table]

    item = find_owned_item(table, item_id)

    if item is None:
        return error_response(
            f"{config['label']} not found",
            404
        )

    execute_query(
        f"""
        DELETE FROM {table}
        WHERE {config['id']} = %s
        AND user_id = %s
        """,
        (item_id, current_user_id())
    )

    return jsonify({
        "message": f"{config['label']} deleted successfully"
    }), 200


# Work Experience

@app.route("/api/work-experience", methods=["POST"])
@login_required
def add_work_experience():
    return add_repository_item("work_experiences")


@app.route("/api/work-experience", methods=["GET"])
@login_required
def get_work_experiences():
    return list_repository_items("work_experiences")


@app.route("/api/work-experience/<int:item_id>", methods=["PUT"])
@login_required
def update_work_experience(item_id):
    return update_repository_item("work_experiences", item_id)


@app.route("/api/work-experience/<int:item_id>", methods=["DELETE"])
@login_required
def delete_work_experience(item_id):
    return delete_repository_item("work_experiences", item_id)


# Education

@app.route("/api/education", methods=["POST"])
@login_required
def add_education():
    return add_repository_item("educations")


@app.route("/api/education", methods=["GET"])
@login_required
def get_educations():
    return list_repository_items("educations")


@app.route("/api/education/<int:item_id>", methods=["PUT"])
@login_required
def update_education(item_id):
    return update_repository_item("educations", item_id)


@app.route("/api/education/<int:item_id>", methods=["DELETE"])
@login_required
def delete_education(item_id):
    return delete_repository_item("educations", item_id)


# Skills

@app.route("/api/skills", methods=["POST"])
@login_required
def add_skill():
    return add_repository_item("skills")


@app.route("/api/skills", methods=["GET"])
@login_required
def get_skills():
    return list_repository_items("skills")


@app.route("/api/skills/<int:item_id>", methods=["PUT"])
@login_required
def update_skill(item_id):
    return update_repository_item("skills", item_id)


@app.route("/api/skills/<int:item_id>", methods=["DELETE"])
@login_required
def delete_skill(item_id):
    return delete_repository_item("skills", item_id)


# Languages

@app.route("/api/languages", methods=["POST"])
@login_required
def add_language():
    return add_repository_item("languages")


@app.route("/api/languages", methods=["GET"])
@login_required
def get_languages():
    return list_repository_items("languages")


@app.route("/api/languages/<int:item_id>", methods=["PUT"])
@login_required
def update_language(item_id):
    return update_repository_item("languages", item_id)


@app.route("/api/languages/<int:item_id>", methods=["DELETE"])
@login_required
def delete_language(item_id):
    return delete_repository_item("languages", item_id)


# Projects

@app.route("/api/projects", methods=["POST"])
@login_required
def add_project():
    return add_repository_item("projects")


@app.route("/api/projects", methods=["GET"])
@login_required
def get_projects():
    return list_repository_items("projects")


@app.route("/api/projects/<int:item_id>", methods=["PUT"])
@login_required
def update_project(item_id):
    return update_repository_item("projects", item_id)


@app.route("/api/projects/<int:item_id>", methods=["DELETE"])
@login_required
def delete_project(item_id):
    return delete_repository_item("projects", item_id)


# Certificates

@app.route("/api/certificates", methods=["POST"])
@login_required
def add_certificate():
    return add_repository_item("certificates")


@app.route("/api/certificates", methods=["GET"])
@login_required
def get_certificates():
    return list_repository_items("certificates")


@app.route("/api/certificates/<int:item_id>", methods=["PUT"])
@login_required
def update_certificate(item_id):
    return update_repository_item("certificates", item_id)


@app.route("/api/certificates/<int:item_id>", methods=["DELETE"])
@login_required
def delete_certificate(item_id):
    return delete_repository_item("certificates", item_id)


# CV Selection Configuration

CV_SELECTION_FIELDS = [
    (
        "selected_experience_ids",
        "work_experiences"
    ),
    (
        "selected_education_ids",
        "educations"
    ),
    (
        "selected_skill_ids",
        "skills"
    ),
    (
        "selected_language_ids",
        "languages"
    ),
    (
        "selected_project_ids",
        "projects"
    ),
    (
        "selected_certificate_ids",
        "certificates"
    ),
]


# CV Validation Helpers

def validate_cv_selections(data):
    for field, table in CV_SELECTION_FIELDS:
        if field not in data:
            continue

        values = data[field]

        if not isinstance(values, list):
            return f"{field} must be a list"

        if any(type(value) is not int for value in values):
            return f"{field} must contain integer IDs"

        valid_ids = {
            item["id"]
            for item in owned_items(table)
        }

        if any(value not in valid_ids for value in values):
            return f"{field} contains an unknown ID"

    return None


def validate_cv_options(data):
    error = validate_cv_selections(data)

    if error:
        return error

    limits = {
        "name": 100,
        "template": 50,
        "color": 30,
    }

    for field, limit in limits.items():
        if field in data:
            if not required_string(data, field):
                return f"{field} must be a non-empty string"

            if len(data[field].strip()) > limit:
                return f"{field} must be {limit} characters or fewer"

    if "include_personal_info" in data:
        if not isinstance(data["include_personal_info"], bool):
            return "include_personal_info must be true or false"

    return None


# CV Database Helpers

def load_cv_selections(cv):
    cv["include_personal_info"] = bool(
        cv["include_personal_info"]
    )

    for field, table in CV_SELECTION_FIELDS:
        id_column = REPOSITORIES[table]["id"]
        mapping_table = f"cv_{table}"

        rows = fetch_all(
            f"""
            SELECT mapping.{id_column} AS id
            FROM {mapping_table} AS mapping
            INNER JOIN {table} AS item
                ON mapping.{id_column} = item.{id_column}
            WHERE mapping.cv_id = %s
            AND item.user_id = %s
            ORDER BY mapping.{id_column}
            """,
            (cv["id"], current_user_id())
        )

        cv[field] = [row["id"] for row in rows]

    return cv


def get_cv_or_none(cv_id):
    cv = fetch_one(
        """
        SELECT cv_id AS id,
               user_id,
               cv_title AS name,
               template,
               color,
               include_personal_info
        FROM cvs
        WHERE cv_id = %s
        AND user_id = %s
        """,
        (cv_id, current_user_id())
    )

    if cv is None:
        return None

    return load_cv_selections(cv)


def save_cv_selections(cursor, cv_id, data):
    for field, table in CV_SELECTION_FIELDS:
        if field not in data:
            continue

        mapping_table = f"cv_{table}"
        id_column = REPOSITORIES[table]["id"]

        cursor.execute(
            f"""
            DELETE FROM {mapping_table}
            WHERE cv_id = %s
            """,
            (cv_id,)
        )

        selected_ids = list(dict.fromkeys(data[field]))

        for item_id in selected_ids:
            cursor.execute(
                f"""
                INSERT INTO {mapping_table}
                    (cv_id, {id_column})
                SELECT %s, {id_column}
                FROM {table}
                WHERE {id_column} = %s
                AND user_id = %s
                """,
                (cv_id, item_id, current_user_id())
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    f"{field} contains an unknown ID"
                )


def insert_cv(data):
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO cvs
                    (
                        user_id,
                        cv_title,
                        template,
                        color,
                        include_personal_info
                    )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    current_user_id(),
                    data.get("name", "Untitled CV").strip(),
                    data.get("template", "classic").strip(),
                    data.get("color", "blue").strip(),
                    data.get("include_personal_info", True)
                )
            )

            cv_id = cursor.lastrowid

            save_cv_selections(
                cursor,
                cv_id,
                data
            )

        connection.commit()

        return cv_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# CV Creation

@app.route("/api/cvs", methods=["POST"])
@login_required
def create_cv():
    data = get_json_data()

    if data is None:
        return error_response("Invalid JSON data")

    if "name" not in data:
        data["name"] = "Untitled CV"

    error = validate_cv_options(data)

    if error:
        return error_response(error)

    try:
        cv_id = insert_cv(data)

    except ValueError as error:
        return error_response(str(error))

    return jsonify({
        "message": "CV created successfully",
        "data": get_cv_or_none(cv_id),
    }), 201


# List Saved CVs

@app.route("/api/cvs", methods=["GET"])
@login_required
def list_cvs():
    items = fetch_all(
        """
        SELECT cv_id AS id,
               user_id,
               cv_title AS name,
               template,
               color,
               include_personal_info
        FROM cvs
        WHERE user_id = %s
        ORDER BY cv_id
        """,
        (current_user_id(),)
    )

    items = [
        load_cv_selections(cv)
        for cv in items
    ]

    return jsonify({
        "data": items,
        "count": len(items),
    }), 200


# Open Saved CV

@app.route("/api/cvs/<int:cv_id>", methods=["GET"])
@login_required
def get_cv(cv_id):
    cv = get_cv_or_none(cv_id)

    if cv is None:
        return error_response("CV not found", 404)

    return jsonify(cv), 200


# CV Editing

@app.route("/api/cvs/<int:cv_id>", methods=["PUT"])
@login_required
def update_cv(cv_id):
    data = get_json_data()

    if data is None:
        return error_response("Invalid JSON data")

    error = validate_cv_options(data)

    if error:
        return error_response(error)

    connection = get_db_connection()

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT cv_id
                FROM cvs
                WHERE cv_id = %s
                AND user_id = %s
                FOR UPDATE
                """,
                (cv_id, current_user_id())
            )

            if cursor.fetchone() is None:
                connection.rollback()
                return error_response("CV not found", 404)

            fields = {
                "name": "cv_title",
                "template": "template",
                "color": "color",
                "include_personal_info": "include_personal_info",
            }

            assignments = []
            values = []

            for api_field, db_field in fields.items():
                if api_field in data:
                    value = data[api_field]

                    if isinstance(value, str):
                        value = value.strip()

                    assignments.append(f"{db_field} = %s")
                    values.append(value)

            if assignments:
                values.extend([cv_id, current_user_id()])

                cursor.execute(
                    f"""
                    UPDATE cvs
                    SET {", ".join(assignments)}
                    WHERE cv_id = %s
                    AND user_id = %s
                    """,
                    tuple(values)
                )

            save_cv_selections(
                cursor,
                cv_id,
                data
            )

        connection.commit()

    except ValueError as error:
        connection.rollback()
        return error_response(str(error))

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return jsonify({
        "message": "CV updated successfully",
        "data": get_cv_or_none(cv_id),
    }), 200


# CV Deletion

@app.route("/api/cvs/<int:cv_id>", methods=["DELETE"])
@login_required
def delete_cv(cv_id):
    cv = get_cv_or_none(cv_id)

    if cv is None:
        return error_response("CV not found", 404)

    execute_query(
        """
        DELETE FROM cvs
        WHERE cv_id = %s
        AND user_id = %s
        """,
        (cv_id, current_user_id())
    )

    return jsonify({
        "message": "CV deleted successfully"
    }), 200


# CV Duplication

@app.route("/api/cvs/<int:cv_id>/duplicate", methods=["POST"])
@login_required
def duplicate_cv(cv_id):
    original = get_cv_or_none(cv_id)

    if original is None:
        return error_response("CV not found", 404)

    duplicate = {
        "name": original["name"][:93] + " (Copy)",
        "template": original["template"],
        "color": original["color"],
        "include_personal_info": original["include_personal_info"],
    }

    for field, table in CV_SELECTION_FIELDS:
        duplicate[field] = list(original.get(field, []))

    try:
        duplicate_id = insert_cv(duplicate)

    except ValueError as error:
        return error_response(str(error))

    return jsonify({
        "message": "CV duplicated successfully",
        "data": get_cv_or_none(duplicate_id),
    }), 201


# CV Preview

def build_cv_preview(cv_id):
    cv = get_cv_or_none(cv_id)

    if cv is None:
        return None

    preview = {
        "cv": cv,
        "personal_info": (
            find_my_profile()
            if cv["include_personal_info"]
            else None
        ),
    }

    for field, table in CV_SELECTION_FIELDS:
        selected_ids = set(cv.get(field, []))

        preview[table] = [
            item
            for item in owned_items(table)
            if item["id"] in selected_ids
        ]

    return preview


@app.route("/api/cvs/<int:cv_id>/preview", methods=["GET"])
@login_required
def preview_cv(cv_id):
    preview = build_cv_preview(cv_id)

    if preview is None:
        return error_response("CV not found", 404)

    return jsonify(preview), 200


# PDF Filename Helper

def get_pdf_filename(cv):
    requested_name = request.args.get("filename", "").strip()

    if not requested_name:
        requested_name = f"cv_{cv['id']}"

    if requested_name.lower().endswith(".pdf"):
        requested_name = requested_name[:-4]

    requested_name = re.sub(
        r'[<>:"/\\|?*\x00-\x1f]',
        "_",
        requested_name
    )

    requested_name = requested_name.strip(" .")

    if not requested_name:
        requested_name = f"cv_{cv['id']}"

    reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        *[f"COM{i}" for i in range(1, 10)],
        *[f"LPT{i}" for i in range(1, 10)],
    }

    if requested_name.split(".")[0].upper() in reserved_names:
        requested_name = "_" + requested_name

    return f"{requested_name[:96]}.pdf"


# PDF Export

@app.route("/api/cvs/<int:cv_id>/export-pdf", methods=["GET"])
@login_required
def export_cv_pdf(cv_id):
    preview = build_cv_preview(cv_id)

    if preview is None:
        return error_response("CV not found", 404)

    cv = preview["cv"]
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45,
    )

    color_options = {
        "blue": colors.HexColor("#2563EB"),
        "green": colors.HexColor("#15803D"),
        "red": colors.HexColor("#B91C1C"),
        "purple": colors.HexColor("#7C3AED"),
        "black": colors.HexColor("#111827"),
        "gray": colors.HexColor("#4B5563"),
    }

    selected_color = str(
        cv.get("color", "blue")
    ).lower()

    accent_color = color_options.get(
        selected_color,
        color_options["blue"]
    )

    if re.fullmatch(r"#[0-9a-fA-F]{6}", selected_color):
        accent_color = colors.HexColor(selected_color)

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="CVName",
            parent=styles["Title"],
            fontSize=22,
            leading=27,
            alignment=TA_CENTER,
            textColor=accent_color,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CVSection",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=accent_color,
            spaceAfter=8,
        )
    )

    story = []

    def add_text(value, style="Normal"):
        if value is None or not str(value).strip():
            return

        safe_text = escape(str(value)).replace(
            "\n",
            "<br/>"
        )

        story.append(
            Paragraph(safe_text, styles[style])
        )

        story.append(Spacer(1, 6))

    def add_section(title):
        story.append(Spacer(1, 12))

        add_text(title, "CVSection")

        story.append(
            HRFlowable(
                width="100%",
                thickness=1,
                color=accent_color,
            )
        )

        story.append(Spacer(1, 8))

    def add_dates(item):
        start = item.get("start_date", "")
        end = item.get("end_date", "")

        if start or end:
            add_text(f"{start} - {end}")

    # Personal Information

    personal = preview.get("personal_info") or {}

    photo_filename = personal.get("photo_filename")
    photo_path = get_photo_path(photo_filename)

    if photo_path and photo_path.is_file():
        try:
            with PILImage.open(photo_path) as image:
                width, height = image.size

            scale = min(100 / width, 100 / height)

            pdf_photo = PDFImage(
                str(photo_path),
                width=width * scale,
                height=height * scale,
            )

            pdf_photo.hAlign = "CENTER"

            story.append(pdf_photo)
            story.append(Spacer(1, 12))

        except (OSError, ValueError):
            pass

    add_text(
        personal.get("full_name", "Curriculum Vitae"),
        "CVName"
    )

    add_text(personal.get("email"))
    add_text(personal.get("phone"))
    add_text(personal.get("address"))

    if personal.get("professional_summary"):
        add_section("Professional Summary")
        add_text(personal["professional_summary"])

    # Work Experience

    experiences = preview.get("work_experiences") or []

    if experiences:
        add_section("Work Experience")

        for experience in experiences:
            add_text(
                experience.get("job_title"),
                "Heading3"
            )

            add_text(experience.get("company"))
            add_dates(experience)
            add_text(experience.get("description"))

            story.append(Spacer(1, 8))

    # Education

    education_items = preview.get("educations") or []

    if education_items:
        add_section("Education")

        for education in education_items:
            add_text(
                education.get("degree"),
                "Heading3"
            )

            add_text(education.get("school"))
            add_dates(education)
            add_text(education.get("description"))

            story.append(Spacer(1, 8))

    # Skills

    selected_skills = preview.get("skills") or []

    if selected_skills:
        add_section("Skills")

        for skill in selected_skills:
            name = skill.get("name", "")
            level = skill.get("level", "")

            add_text(
                f"{name} - {level}"
                if level
                else name
            )

    # Languages

    selected_languages = preview.get("languages") or []

    if selected_languages:
        add_section("Languages")

        for language in selected_languages:
            name = language.get("name", "")
            level = language.get("level", "")

            add_text(
                f"{name} - {level}"
                if level
                else name
            )

    # Projects

    selected_projects = preview.get("projects") or []

    if selected_projects:
        add_section("Projects")

        for project in selected_projects:
            add_text(
                project.get("title"),
                "Heading3"
            )

            add_dates(project)
            add_text(project.get("description"))
            add_text(project.get("url"))

            story.append(Spacer(1, 8))

    # Certificates

    selected_certificates = preview.get("certificates") or []

    if selected_certificates:
        add_section("Certificates")

        for certificate in selected_certificates:
            add_text(
                certificate.get("name"),
                "Heading3"
            )

            add_text(certificate.get("issuer"))

            issued = certificate.get("issue_date", "")
            expires = certificate.get("expiry_date", "")

            if issued:
                add_text(f"Issued: {issued}")

            if expires:
                add_text(f"Expires: {expires}")

            add_text(certificate.get("credential_url"))

            story.append(Spacer(1, 8))

    document.build(story)
    buffer.seek(0)

    filename = get_pdf_filename(cv)

    execute_query(
        """
        UPDATE cvs
        SET file_name = %s
        WHERE cv_id = %s
        AND user_id = %s
        """,
        (filename, cv_id, current_user_id())
    )

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )


# Run Flask Application

if __name__ == "__main__":
    app.run(debug=True)