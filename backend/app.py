
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


# Application Configuration

app = Flask(__name__)

users = []
personal_infos = []
work_experiences = []
educations = []
skills = []
languages = []
projects = []
certificates = []
cvs = []

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

def next_id(items):
    return max((item["id"] for item in items), default=0) + 1


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


def validate_required_update(data, fields):
    for field in fields:
        if field in data and not required_string(data, field):
            return f"{field} cannot be empty"
    return None


def find_user_by_email(email):
    return next(
        (user for user in users if user["email"] == email),
        None,
    )


def public_user(user):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "email_verified": user["email_verified"],
    }


def current_user_id():
    return g.current_user["id"]


def owned_items(items):
    return [
        item for item in items
        if item["user_id"] == current_user_id()
    ]


def find_owned_item(items, item_id):
    return next(
        (
            item for item in items
            if item["id"] == item_id
            and item["user_id"] == current_user_id()
        ),
        None,
    )


def find_my_profile():
    return next(
        (
            profile for profile in personal_infos
            if profile["user_id"] == current_user_id()
        ),
        None,
    )


def remove_from_cv_selections(field, item_id):
    for cv in owned_items(cvs):
        cv[field] = [
            value for value in cv.get(field, [])
            if value != item_id
        ]


# OTP Helpers

def generate_otp():
    return f"{secrets.randbelow(1000000):06d}"


def hash_otp(code, salt):
    return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()


def create_otp_record(storage, email, purpose):
    code = generate_otp()
    salt = secrets.token_hex(16)

    storage[email] = {
        "salt": salt,
        "code_hash": hash_otp(code, salt),
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        "attempts": 0,
    }

    print(f"\n{purpose}")
    print(f"Email: {email}")
    print(f"OTP Code: {code}")
    print("Expires in 5 minutes\n", flush=True)


def create_otp_for_user(email):
    create_otp_record(
        pending_otps,
        email,
        "Email Verification OTP",
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

    return next(
        (
            user for user in users
            if user["id"] == session["user_id"]
        ),
        None,
    )


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        user = get_current_user()

        if user is None:
            return jsonify({
                "error": "Authentication required. Please log in."
            }), 401

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


# CV Helpers

CV_SELECTION_FIELDS = [
    ("selected_experience_ids", work_experiences),
    ("selected_education_ids", educations),
    ("selected_skill_ids", skills),
    ("selected_language_ids", languages),
    ("selected_project_ids", projects),
    ("selected_certificate_ids", certificates),
]


def validate_cv_selections(data):
    for field, collection in CV_SELECTION_FIELDS:
        if field not in data:
            continue

        values = data[field]

        if not isinstance(values, list):
            return f"{field} must be a list"

        if any(type(value) is not int for value in values):
            return f"{field} must contain integer IDs"

        valid_ids = {
            item["id"]
            for item in collection
            if item["user_id"] == current_user_id()
        }

        if any(value not in valid_ids for value in values):
            return f"{field} contains an unknown ID"

    return None


def get_cv_or_none(cv_id):
    return find_owned_item(cvs, cv_id)


def validate_cv_options(data):
    error = validate_cv_selections(data)

    if error:
        return error

    for field in ["name", "template", "color"]:
        if field in data and not required_string(data, field):
            return f"{field} must be a non-empty string"

    if "include_personal_info" in data:
        if not isinstance(data["include_personal_info"], bool):
            return "include_personal_info must be true or false"

    return None


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


# User Registration

@app.route("/api/register", methods=["POST"])
def register():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    for field in ["name", "email", "password"]:
        if not required_string(data, field):
            return jsonify({"error": f"{field} is required"}), 400

    name = data["name"].strip()
    email = data["email"].strip().lower()
    password = data["password"]

    if len(name) > 50:
        return jsonify({
            "error": "Name must be 50 characters or fewer"
        }), 400

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return jsonify({"error": "Invalid email address"}), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters"
        }), 400

    if find_user_by_email(email):
        return jsonify({
            "error": "Email is already registered"
        }), 409

    user = {
        "id": next_id(users),
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password),
        "email_verified": False,
    }

    users.append(user)
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
        return jsonify({"error": "Invalid JSON data"}), 400

    email = clean_text(data.get("email", "")).lower()
    code = str(data.get("otp", "")).strip()

    user = find_user_by_email(email)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    if user["email_verified"]:
        return jsonify({
            "message": "Email is already verified",
            "user": public_user(user),
        }), 200

    error = verify_otp_record(pending_otps, email, code)

    if error:
        return jsonify({"error": error}), 400

    user["email_verified"] = True
    pending_otps.pop(email, None)

    return jsonify({
        "message": "Email verified successfully",
        "user": public_user(user),
    }), 200


@app.route("/api/resend-otp", methods=["POST"])
def resend_otp():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    email = clean_text(data.get("email", "")).lower()
    user = find_user_by_email(email)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    if user["email_verified"]:
        return jsonify({
            "message": "Email is already verified"
        }), 400

    create_otp_for_user(email)

    return jsonify({
        "message": "A new OTP has been generated."
    }), 200


# Login with Remember Me

@app.route("/api/login", methods=["POST"])
def login():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    email = clean_text(data.get("email", "")).lower()
    password = data.get("password", "")
    remember_me = data.get("remember_me", False)

    if not isinstance(password, str):
        return jsonify({"error": "Invalid password"}), 400

    if not isinstance(remember_me, bool):
        return jsonify({
            "error": "remember_me must be true or false"
        }), 400

    user = find_user_by_email(email)

    if user is None or not check_password_hash(
        user["password_hash"],
        password,
    ):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    if not user["email_verified"]:
        return jsonify({
            "error": "Please verify your email before logging in."
        }), 403

    token, duration = create_login_token(
        user["id"],
        remember_me=remember_me,
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
        return jsonify({"error": "Invalid JSON data"}), 400

    if not required_string(data, "email"):
        return jsonify({"error": "Email is required"}), 400

    email = data["email"].strip().lower()
    user = find_user_by_email(email)

    if user is not None and user["email_verified"]:
        create_otp_record(
            password_reset_otps,
            email,
            "Password Reset OTP",
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
        return jsonify({"error": "Invalid JSON data"}), 400

    email = clean_text(data.get("email", "")).lower()
    code = str(data.get("otp", "")).strip()

    if not email or not code:
        return jsonify({
            "error": "Email and OTP are required"
        }), 400

    error = verify_otp_record(
        password_reset_otps,
        email,
        code,
    )

    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "message": "Password reset OTP verified successfully"
    }), 200


@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    email = clean_text(data.get("email", "")).lower()
    code = str(data.get("otp", "")).strip()
    new_password = data.get("new_password")

    if not email or not code:
        return jsonify({
            "error": "Email and OTP are required"
        }), 400

    if not isinstance(new_password, str) or len(new_password) < 8:
        return jsonify({
            "error": "New password must be at least 8 characters"
        }), 400

    user = find_user_by_email(email)

    if user is None or not user["email_verified"]:
        return jsonify({
            "error": "Invalid password reset request"
        }), 400

    error = verify_otp_record(
        password_reset_otps,
        email,
        code,
    )

    if error:
        return jsonify({"error": error}), 400

    user["password_hash"] = generate_password_hash(new_password)

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


# Personal Information

@app.route("/api/personal-info", methods=["POST"])
@login_required
def save_personal_info():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    for field in ["full_name", "email"]:
        if not required_string(data, field):
            return jsonify({"error": f"{field} is required"}), 400

    error = validate_text_fields(
        data,
        ["phone", "address", "professional_summary"],
    )

    if error:
        return jsonify({"error": error}), 400

    profile_data = {
        "full_name": data["full_name"].strip(),
        "email": data["email"].strip(),
        "phone": clean_text(data.get("phone", "")),
        "address": clean_text(data.get("address", "")),
        "professional_summary": clean_text(
            data.get("professional_summary", "")
        ),
    }

    profile = find_my_profile()

    if profile is None:
        profile = {
            "id": next_id(personal_infos),
            "user_id": current_user_id(),
            **profile_data,
        }
        personal_infos.append(profile)
    else:
        profile.update(profile_data)

    return jsonify({
        "message": "Personal information saved successfully",
        "data": profile,
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


# Profile Photo Upload

@app.route("/api/personal-info/photo", methods=["POST"])
@login_required
def upload_profile_photo():
    profile = find_my_profile()

    if profile is None:
        return jsonify({
            "error": "Save personal information before uploading a photo"
        }), 404

    photo = request.files.get("photo")

    if photo is None or not photo.filename:
        return jsonify({
            "error": "Upload an image using the 'photo' field"
        }), 400

    image_bytes = photo.read(MAX_PHOTO_BYTES + 1)

    if len(image_bytes) > MAX_PHOTO_BYTES:
        return jsonify({
            "error": "Photo must be 5 MB or smaller"
        }), 413

    try:
        with PILImage.open(BytesIO(image_bytes)) as image:
            if image.format not in ("JPEG", "PNG"):
                return jsonify({
                    "error": "Only JPEG and PNG photos are allowed"
                }), 400

            image.load()
            image = image.convert("RGB")
            image.thumbnail((800, 800))

            filename = (
                f"user_{current_user_id()}_"
                f"{secrets.token_hex(12)}.jpg"
            )

            photo_path = PHOTO_DIRECTORY / filename
            image.save(photo_path, format="JPEG", quality=90)

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        PILImage.DecompressionBombError,
    ):
        return jsonify({
            "error": "Invalid or corrupted image"
        }), 400

    old_filename = profile.get("photo_filename")

    profile["photo_filename"] = filename
    profile["photo_url"] = url_for(
        "get_profile_photo",
        _external=True,
    )

    if old_filename:
        (PHOTO_DIRECTORY / old_filename).unlink(missing_ok=True)

    return jsonify({
        "message": "Profile photo uploaded successfully",
        "photo_url": profile["photo_url"],
    }), 200


@app.route("/api/personal-info/photo", methods=["GET"])
@login_required
def get_profile_photo():
    profile = find_my_profile()

    if profile is None or not profile.get("photo_filename"):
        return jsonify({
            "error": "No profile photo uploaded"
        }), 404

    photo_path = PHOTO_DIRECTORY / profile["photo_filename"]

    if not photo_path.is_file():
        return jsonify({
            "error": "Photo file not found"
        }), 404

    return send_file(photo_path, mimetype="image/jpeg")


@app.route("/api/personal-info/photo", methods=["DELETE"])
@login_required
def delete_profile_photo():
    profile = find_my_profile()

    if profile is None or not profile.get("photo_filename"):
        return jsonify({
            "error": "No profile photo uploaded"
        }), 404

    filename = profile.pop("photo_filename")
    profile.pop("photo_url", None)

    (PHOTO_DIRECTORY / filename).unlink(missing_ok=True)

    return jsonify({
        "message": "Profile photo deleted successfully"
    }), 200


# Work Experience

@app.route("/api/work-experience", methods=["POST"])
@login_required
def add_work_experience():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    for field in ["job_title", "company"]:
        if not required_string(data, field):
            return jsonify({"error": f"{field} is required"}), 400

    error = validate_text_fields(
        data,
        ["start_date", "end_date", "description"],
    )

    if error:
        return jsonify({"error": error}), 400

    experience = {
        "id": next_id(work_experiences),
        "user_id": current_user_id(),
        "job_title": data["job_title"].strip(),
        "company": data["company"].strip(),
        "start_date": clean_text(data.get("start_date", "")),
        "end_date": clean_text(data.get("end_date", "")),
        "description": clean_text(data.get("description", "")),
    }

    work_experiences.append(experience)

    return jsonify({
        "message": "Work experience added successfully",
        "data": experience,
    }), 201


@app.route("/api/work-experience", methods=["GET"])
@login_required
def get_work_experiences():
    items = owned_items(work_experiences)

    return jsonify({
        "data": items,
        "count": len(items),
    }), 200


@app.route("/api/work-experience/<int:item_id>", methods=["PUT"])
@login_required
def update_work_experience(item_id):
    experience = find_owned_item(work_experiences, item_id)

    if experience is None:
        return jsonify({
            "error": "Work experience not found"
        }), 404

    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    allowed = [
        "job_title",
        "company",
        "start_date",
        "end_date",
        "description",
    ]

    error = validate_text_fields(data, allowed)

    if error:
        return jsonify({"error": error}), 400

    error = validate_required_update(
        data,
        ["job_title", "company"],
    )

    if error:
        return jsonify({"error": error}), 400

    for field in allowed:
        if field in data:
            experience[field] = data[field].strip()

    return jsonify({
        "message": "Work experience updated successfully",
        "data": experience,
    }), 200


@app.route("/api/work-experience/<int:item_id>", methods=["DELETE"])
@login_required
def delete_work_experience(item_id):
    experience = find_owned_item(work_experiences, item_id)

    if experience is None:
        return jsonify({
            "error": "Work experience not found"
        }), 404

    work_experiences.remove(experience)
    remove_from_cv_selections("selected_experience_ids", item_id)

    return jsonify({
        "message": "Work experience deleted successfully"
    }), 200


# Education

@app.route("/api/education", methods=["POST"])
@login_required
def add_education():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    for field in ["degree", "school"]:
        if not required_string(data, field):
            return jsonify({"error": f"{field} is required"}), 400

    error = validate_text_fields(
        data,
        ["start_date", "end_date", "description"],
    )

    if error:
        return jsonify({"error": error}), 400

    education = {
        "id": next_id(educations),
        "user_id": current_user_id(),
        "degree": data["degree"].strip(),
        "school": data["school"].strip(),
        "start_date": clean_text(data.get("start_date", "")),
        "end_date": clean_text(data.get("end_date", "")),
        "description": clean_text(data.get("description", "")),
    }

    educations.append(education)

    return jsonify({
        "message": "Education added successfully",
        "data": education,
    }), 201


@app.route("/api/education", methods=["GET"])
@login_required
def get_educations():
    items = owned_items(educations)

    return jsonify({
        "data": items,
        "count": len(items),
    }), 200


@app.route("/api/education/<int:item_id>", methods=["PUT"])
@login_required
def update_education(item_id):
    education = find_owned_item(educations, item_id)

    if education is None:
        return jsonify({"error": "Education not found"}), 404

    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    allowed = [
        "degree",
        "school",
        "start_date",
        "end_date",
        "description",
    ]

    error = validate_text_fields(data, allowed)

    if error:
        return jsonify({"error": error}), 400

    error = validate_required_update(
        data,
        ["degree", "school"],
    )

    if error:
        return jsonify({"error": error}), 400

    for field in allowed:
        if field in data:
            education[field] = data[field].strip()

    return jsonify({
        "message": "Education updated successfully",
        "data": education,
    }), 200


@app.route("/api/education/<int:item_id>", methods=["DELETE"])
@login_required
def delete_education(item_id):
    education = find_owned_item(educations, item_id)

    if education is None:
        return jsonify({"error": "Education not found"}), 404

    educations.remove(education)
    remove_from_cv_selections("selected_education_ids", item_id)

    return jsonify({
        "message": "Education deleted successfully"
    }), 200


# Skills

@app.route("/api/skills", methods=["POST"])
@login_required
def add_skill():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    name = data.get("name", data.get("skill_name"))

    if not isinstance(name, str) or not name.strip():
        return jsonify({
            "error": "Skill name is required"
        }), 400

    error = validate_text_fields(data, ["level"])

    if error:
        return jsonify({"error": error}), 400

    skill = {
        "id": next_id(skills),
        "user_id": current_user_id(),
        "name": name.strip(),
        "level": clean_text(data.get("level", "")),
    }

    skills.append(skill)

    return jsonify({
        "message": "Skill added successfully",
        "data": skill,
    }), 201


@app.route("/api/skills", methods=["GET"])
@login_required
def get_skills():
    items = owned_items(skills)

    return jsonify({
        "data": items,
        "count": len(items),
    }), 200


@app.route("/api/skills/<int:item_id>", methods=["PUT"])
@login_required
def update_skill(item_id):
    skill = find_owned_item(skills, item_id)

    if skill is None:
        return jsonify({"error": "Skill not found"}), 404

    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    name = data.get("name", data.get("skill_name"))

    if name is not None:
        if not isinstance(name, str) or not name.strip():
            return jsonify({
                "error": "Skill name cannot be empty"
            }), 400

        skill["name"] = name.strip()

    if "level" in data:
        if not isinstance(data["level"], str):
            return jsonify({
                "error": "level must be a string"
            }), 400

        skill["level"] = data["level"].strip()

    return jsonify({
        "message": "Skill updated successfully",
        "data": skill,
    }), 200


@app.route("/api/skills/<int:item_id>", methods=["DELETE"])
@login_required
def delete_skill(item_id):
    skill = find_owned_item(skills, item_id)

    if skill is None:
        return jsonify({"error": "Skill not found"}), 404

    skills.remove(skill)
    remove_from_cv_selections("selected_skill_ids", item_id)

    return jsonify({
        "message": "Skill deleted successfully"
    }), 200


# Languages

@app.route("/api/languages", methods=["POST"])
@login_required
def add_language():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    name = data.get("name")
    level = data.get("level", "")

    if not isinstance(name, str) or not name.strip():
        return jsonify({
            "error": "Language name is required"
        }), 400

    if not isinstance(level, str):
        return jsonify({
            "error": "Level must be a string"
        }), 400

    language = {
        "id": next_id(languages),
        "user_id": current_user_id(),
        "name": name.strip(),
        "level": level.strip(),
    }

    languages.append(language)

    return jsonify({
        "message": "Language added successfully",
        "data": language,
    }), 201


@app.route("/api/languages", methods=["GET"])
@login_required
def get_languages():
    items = owned_items(languages)

    return jsonify({
        "data": items,
        "count": len(items),
    }), 200


@app.route("/api/languages/<int:item_id>", methods=["PUT"])
@login_required
def update_language(item_id):
    language = find_owned_item(languages, item_id)

    if language is None:
        return jsonify({"error": "Language not found"}), 404

    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    if "name" in data:
        if not required_string(data, "name"):
            return jsonify({
                "error": "Language name cannot be empty"
            }), 400

        language["name"] = data["name"].strip()

    if "level" in data:
        if not isinstance(data["level"], str):
            return jsonify({
                "error": "Level must be a string"
            }), 400

        language["level"] = data["level"].strip()

    return jsonify({
        "message": "Language updated successfully",
        "data": language,
    }), 200


@app.route("/api/languages/<int:item_id>", methods=["DELETE"])
@login_required
def delete_language(item_id):
    language = find_owned_item(languages, item_id)

    if language is None:
        return jsonify({"error": "Language not found"}), 404

    languages.remove(language)
    remove_from_cv_selections("selected_language_ids", item_id)

    return jsonify({
        "message": "Language deleted successfully"
    }), 200


# Projects

@app.route("/api/projects", methods=["POST"])
@login_required
def add_project():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    if not required_string(data, "title"):
        return jsonify({
            "error": "Project title is required"
        }), 400

    error = validate_text_fields(
        data,
        ["description", "start_date", "end_date", "url"],
    )

    if error:
        return jsonify({"error": error}), 400

    project = {
        "id": next_id(projects),
        "user_id": current_user_id(),
        "title": data["title"].strip(),
        "description": clean_text(data.get("description", "")),
        "start_date": clean_text(data.get("start_date", "")),
        "end_date": clean_text(data.get("end_date", "")),
        "url": clean_text(data.get("url", "")),
    }

    projects.append(project)

    return jsonify({
        "message": "Project added successfully",
        "data": project,
    }), 201


@app.route("/api/projects", methods=["GET"])
@login_required
def get_projects():
    items = owned_items(projects)

    return jsonify({
        "data": items,
        "count": len(items),
    }), 200


@app.route("/api/projects/<int:item_id>", methods=["PUT"])
@login_required
def update_project(item_id):
    project = find_owned_item(projects, item_id)

    if project is None:
        return jsonify({"error": "Project not found"}), 404

    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    allowed = [
        "title",
        "description",
        "start_date",
        "end_date",
        "url",
    ]

    error = validate_text_fields(data, allowed)

    if error:
        return jsonify({"error": error}), 400

    error = validate_required_update(data, ["title"])

    if error:
        return jsonify({"error": error}), 400

    for field in allowed:
        if field in data:
            project[field] = data[field].strip()

    return jsonify({
        "message": "Project updated successfully",
        "data": project,
    }), 200


@app.route("/api/projects/<int:item_id>", methods=["DELETE"])
@login_required
def delete_project(item_id):
    project = find_owned_item(projects, item_id)

    if project is None:
        return jsonify({"error": "Project not found"}), 404

    projects.remove(project)
    remove_from_cv_selections("selected_project_ids", item_id)

    return jsonify({
        "message": "Project deleted successfully"
    }), 200


# Certificates

@app.route("/api/certificates", methods=["POST"])
@login_required
def add_certificate():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    if not required_string(data, "name"):
        return jsonify({
            "error": "Certificate name is required"
        }), 400

    error = validate_text_fields(
        data,
        ["issuer", "issue_date", "expiry_date", "credential_url"],
    )

    if error:
        return jsonify({"error": error}), 400

    certificate = {
        "id": next_id(certificates),
        "user_id": current_user_id(),
        "name": data["name"].strip(),
        "issuer": clean_text(data.get("issuer", "")),
        "issue_date": clean_text(data.get("issue_date", "")),
        "expiry_date": clean_text(data.get("expiry_date", "")),
        "credential_url": clean_text(data.get("credential_url", "")),
    }

    certificates.append(certificate)

    return jsonify({
        "message": "Certificate added successfully",
        "data": certificate,
    }), 201


@app.route("/api/certificates", methods=["GET"])
@login_required
def get_certificates():
    items = owned_items(certificates)

    return jsonify({
        "data": items,
        "count": len(items),
    }), 200


@app.route("/api/certificates/<int:item_id>", methods=["PUT"])
@login_required
def update_certificate(item_id):
    certificate = find_owned_item(certificates, item_id)

    if certificate is None:
        return jsonify({
            "error": "Certificate not found"
        }), 404

    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    allowed = [
        "name",
        "issuer",
        "issue_date",
        "expiry_date",
        "credential_url",
    ]

    error = validate_text_fields(data, allowed)

    if error:
        return jsonify({"error": error}), 400

    error = validate_required_update(data, ["name"])

    if error:
        return jsonify({"error": error}), 400

    for field in allowed:
        if field in data:
            certificate[field] = data[field].strip()

    return jsonify({
        "message": "Certificate updated successfully",
        "data": certificate,
    }), 200


@app.route("/api/certificates/<int:item_id>", methods=["DELETE"])
@login_required
def delete_certificate(item_id):
    certificate = find_owned_item(certificates, item_id)

    if certificate is None:
        return jsonify({
            "error": "Certificate not found"
        }), 404

    certificates.remove(certificate)
    remove_from_cv_selections("selected_certificate_ids", item_id)

    return jsonify({
        "message": "Certificate deleted successfully"
    }), 200


# CV Creation

@app.route("/api/cvs", methods=["POST"])
@login_required
def create_cv():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    if "name" not in data:
        data["name"] = "Untitled CV"

    error = validate_cv_options(data)

    if error:
        return jsonify({"error": error}), 400

    cv = {
        "id": next_id(cvs),
        "user_id": current_user_id(),
        "name": data["name"].strip(),
        "template": clean_text(data.get("template", "classic")),
        "color": clean_text(data.get("color", "blue")),
        "include_personal_info": data.get("include_personal_info", True),
    }

    for field, _ in CV_SELECTION_FIELDS:
        cv[field] = list(data.get(field, []))

    cvs.append(cv)

    return jsonify({
        "message": "CV created successfully",
        "data": cv,
    }), 201


@app.route("/api/cvs", methods=["GET"])
@login_required
def list_cvs():
    items = owned_items(cvs)

    return jsonify({
        "data": items,
        "count": len(items),
    }), 200


@app.route("/api/cvs/<int:cv_id>", methods=["GET"])
@login_required
def get_cv(cv_id):
    cv = get_cv_or_none(cv_id)

    if cv is None:
        return jsonify({"error": "CV not found"}), 404

    return jsonify(cv), 200


# CV Editing

@app.route("/api/cvs/<int:cv_id>", methods=["PUT"])
@login_required
def update_cv(cv_id):
    cv = get_cv_or_none(cv_id)

    if cv is None:
        return jsonify({"error": "CV not found"}), 404

    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    error = validate_cv_options(data)

    if error:
        return jsonify({"error": error}), 400

    for field in ["name", "template", "color"]:
        if field in data:
            cv[field] = data[field].strip()

    if "include_personal_info" in data:
        cv["include_personal_info"] = data["include_personal_info"]

    for field, _ in CV_SELECTION_FIELDS:
        if field in data:
            cv[field] = list(data[field])

    return jsonify({
        "message": "CV updated successfully",
        "data": cv,
    }), 200


@app.route("/api/cvs/<int:cv_id>", methods=["DELETE"])
@login_required
def delete_cv(cv_id):
    cv = get_cv_or_none(cv_id)

    if cv is None:
        return jsonify({"error": "CV not found"}), 404

    cvs.remove(cv)

    return jsonify({
        "message": "CV deleted successfully"
    }), 200


# CV Duplication

@app.route("/api/cvs/<int:cv_id>/duplicate", methods=["POST"])
@login_required
def duplicate_cv(cv_id):
    original = get_cv_or_none(cv_id)

    if original is None:
        return jsonify({"error": "CV not found"}), 404

    duplicate = {
        "id": next_id(cvs),
        "user_id": current_user_id(),
        "name": original["name"] + " (Copy)",
        "template": original["template"],
        "color": original["color"],
        "include_personal_info": original["include_personal_info"],
    }

    for field, _ in CV_SELECTION_FIELDS:
        duplicate[field] = list(original.get(field, []))

    cvs.append(duplicate)

    return jsonify({
        "message": "CV duplicated successfully",
        "data": duplicate,
    }), 201


# CV Preview

def build_cv_preview(cv_id):
    cv = get_cv_or_none(cv_id)

    if cv is None:
        return None

    profile = find_my_profile()

    def selected_items(collection, field):
        selected_ids = set(cv.get(field, []))

        return [
            item for item in owned_items(collection)
            if item["id"] in selected_ids
        ]

    return {
        "cv": cv,
        "personal_info": (
            profile if cv["include_personal_info"] else None
        ),
        "work_experiences": selected_items(
            work_experiences,
            "selected_experience_ids",
        ),
        "educations": selected_items(
            educations,
            "selected_education_ids",
        ),
        "skills": selected_items(
            skills,
            "selected_skill_ids",
        ),
        "languages": selected_items(
            languages,
            "selected_language_ids",
        ),
        "projects": selected_items(
            projects,
            "selected_project_ids",
        ),
        "certificates": selected_items(
            certificates,
            "selected_certificate_ids",
        ),
    }


@app.route("/api/cvs/<int:cv_id>/preview", methods=["GET"])
@login_required
def preview_cv(cv_id):
    preview = build_cv_preview(cv_id)

    if preview is None:
        return jsonify({"error": "CV not found"}), 404

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
        requested_name,
    )

    requested_name = requested_name.strip(" .")

    if not requested_name:
        requested_name = f"cv_{cv['id']}"

    return f"{requested_name[:100]}.pdf"


# PDF Export

@app.route("/api/cvs/<int:cv_id>/export-pdf", methods=["GET"])
@login_required
def export_cv_pdf(cv_id):
    preview = build_cv_preview(cv_id)

    if preview is None:
        return jsonify({"error": "CV not found"}), 404

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

    accent_color = color_options.get(
        str(cv.get("color", "blue")).lower(),
        color_options["blue"],
    )

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

        safe_text = escape(str(value)).replace("\n", "<br/>")

        story.append(Paragraph(safe_text, styles[style]))
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

    # Personal Information

    personal = preview.get("personal_info") or {}
    photo_filename = personal.get("photo_filename")

    if photo_filename:
        photo_path = PHOTO_DIRECTORY / photo_filename

        if photo_path.is_file():
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
        "CVName",
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
            add_text(experience.get("job_title"), "Heading3")
            add_text(experience.get("company"))

            start = experience.get("start_date", "")
            end = experience.get("end_date", "")

            if start or end:
                add_text(f"{start} - {end}")

            add_text(experience.get("description"))
            story.append(Spacer(1, 8))

    # Education

    education_items = preview.get("educations") or []

    if education_items:
        add_section("Education")

        for education in education_items:
            add_text(education.get("degree"), "Heading3")
            add_text(education.get("school"))

            start = education.get("start_date", "")
            end = education.get("end_date", "")

            if start or end:
                add_text(f"{start} - {end}")

            add_text(education.get("description"))
            story.append(Spacer(1, 8))

    # Skills

    selected_skills = preview.get("skills") or []

    if selected_skills:
        add_section("Skills")

        for skill in selected_skills:
            name = skill.get("name", "")
            level = skill.get("level", "")

            add_text(f"{name} - {level}" if level else name)

    # Languages

    selected_languages = preview.get("languages") or []

    if selected_languages:
        add_section("Languages")

        for language in selected_languages:
            name = language.get("name", "")
            level = language.get("level", "")

            add_text(f"{name} - {level}" if level else name)

    # Projects

    selected_projects = preview.get("projects") or []

    if selected_projects:
        add_section("Projects")

        for project in selected_projects:
            add_text(project.get("title"), "Heading3")

            start = project.get("start_date", "")
            end = project.get("end_date", "")

            if start or end:
                add_text(f"{start} - {end}")

            add_text(project.get("description"))
            add_text(project.get("url"))
            story.append(Spacer(1, 8))

    # Certificates

    selected_certificates = preview.get("certificates") or []

    if selected_certificates:
        add_section("Certificates")

        for certificate in selected_certificates:
            add_text(certificate.get("name"), "Heading3")
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

    return send_file(
        buffer,
        as_attachment=True,
        download_name=get_pdf_filename(cv),
        mimetype="application/pdf",
    )


# Run Flask Application

if __name__ == "__main__":
    app.run(debug=True)
