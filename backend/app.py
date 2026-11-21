
from flask import Flask, jsonify, request, send_file, g
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

import hashlib
import hmac
import re
import secrets
import time


# Flask Application and Data Storage

app = Flask(__name__)

users = []
personal_infos = []
work_experiences = []
educations = []
skills = []
cvs = []

pending_otps = {}
login_sessions = {}

OTP_EXPIRY_SECONDS = 300
SESSION_EXPIRY_SECONDS = 86400


# Helper Functions

def next_id(items):
    return max((item["id"] for item in items), default=0) + 1


def get_json_data():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def find_user_by_email(email):
    return next(
        (user for user in users if user["email"] == email),
        None
    )


def public_user(user):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "email_verified": user["email_verified"]
    }


def required_string(data, field):
    value = data.get(field)
    return isinstance(value, str) and bool(value.strip())


def clean_text(value):
    return value.strip() if isinstance(value, str) else ""


def validate_text_fields(data, fields):
    for field in fields:
        if field in data and not isinstance(data[field], str):
            return f"{field} must be a string"
    return None


# OTP Generation

def generate_otp():
    return f"{secrets.randbelow(1000000):06d}"


def hash_otp(code, salt):
    value = f"{salt}:{code}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def create_otp_for_user(email):
    code = generate_otp()
    salt = secrets.token_hex(16)

    pending_otps[email] = {
        "salt": salt,
        "code_hash": hash_otp(code, salt),
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        "attempts": 0
    }

    print(f"Email: {email}")
    print(f"OTP Code: {code}", flush=True)


# Authentication Helpers

def create_login_token(user_id):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    login_sessions[token_hash] = {
        "user_id": user_id,
        "expires_at": time.time() + SESSION_EXPIRY_SECONDS
    }

    return token


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
        None
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
        None
    )


def validate_cv_selections(data):
    fields = [
        ("selected_experience_ids", work_experiences),
        ("selected_education_ids", educations),
        ("selected_skill_ids", skills)
    ]

    for field, collection in fields:
        if field not in data:
            continue

        values = data[field]

        if not isinstance(values, list):
            return f"{field} must be a list"

        if any(type(value) is not int for value in values):
            return f"{field} must contain integer IDs"

        valid_ids = {
            item["id"] for item in collection
            if item["user_id"] == current_user_id()
        }

        if any(value not in valid_ids for value in values):
            return f"{field} contains an unknown ID"

    return None


def get_cv_or_none(cv_id):
    return find_owned_item(cvs, cv_id)


# Home and Health Check

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Welcome to CV Tool 2",
        "status": "Backend is working!"
    }), 200


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "CV Tool 2 server is running"
    }), 200


# User Registration

@app.route("/api/register", methods=["POST"])
def register():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    for field in ["name", "email", "password"]:
        if not required_string(data, field):
            return jsonify({
                "error": f"{field} is required"
            }), 400

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
        "email_verified": False
    }

    users.append(user)
    create_otp_for_user(email)

    return jsonify({
        "message": "Registration successful. Verify your email using the OTP.",
        "user": public_user(user)
    }), 201


# OTP Verification

@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    email = str(data.get("email", "")).strip().lower()
    code = str(data.get("otp", "")).strip()

    user = find_user_by_email(email)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    if user["email_verified"]:
        return jsonify({
            "message": "Email is already verified",
            "user": public_user(user)
        }), 200

    record = pending_otps.get(email)

    if record is None:
        return jsonify({
            "error": "No active OTP. Request a new code."
        }), 400

    if time.time() > record["expires_at"]:
        pending_otps.pop(email, None)
        return jsonify({
            "error": "OTP expired. Request a new code."
        }), 400

    if record["attempts"] >= 5:
        pending_otps.pop(email, None)
        return jsonify({
            "error": "Too many attempts. Request a new code."
        }), 429

    candidate_hash = hash_otp(code, record["salt"])

    if not hmac.compare_digest(candidate_hash, record["code_hash"]):
        record["attempts"] += 1
        return jsonify({"error": "Invalid OTP"}), 400

    user["email_verified"] = True
    pending_otps.pop(email, None)

    return jsonify({
        "message": "Email verified successfully",
        "user": public_user(user)
    }), 200


# Resend OTP

@app.route("/api/resend-otp", methods=["POST"])
def resend_otp():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    email = str(data.get("email", "")).strip().lower()
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


# User Login

@app.route("/api/login", methods=["POST"])
def login():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not isinstance(password, str):
        return jsonify({"error": "Invalid password"}), 400

    user = find_user_by_email(email)

    if user is None or not check_password_hash(
        user["password_hash"], password
    ):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    if not user["email_verified"]:
        return jsonify({
            "error": "Please verify your email before logging in."
        }), 403

    token = create_login_token(user["id"])

    return jsonify({
        "message": "Login successful",
        "token": token,
        "token_type": "Bearer",
        "expires_in": SESSION_EXPIRY_SECONDS,
        "user": public_user(user)
    }), 200


# Logout and Current User

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
            return jsonify({
                "error": f"{field} is required"
            }), 400

    error = validate_text_fields(
        data, ["phone", "address", "professional_summary"]
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
        )
    }

    existing = next(
        (
            item for item in personal_infos
            if item["user_id"] == current_user_id()
        ),
        None
    )

    if existing is not None:
        existing.update(profile_data)
        profile = existing
    else:
        profile = {
            "id": next_id(personal_infos),
            "user_id": current_user_id(),
            **profile_data
        }
        personal_infos.append(profile)

    return jsonify({
        "message": "Personal information saved successfully",
        "data": profile
    }), 200


@app.route("/api/personal-info", methods=["GET"])
@login_required
def get_personal_info():
    profile = next(
        (
            item for item in personal_infos
            if item["user_id"] == current_user_id()
        ),
        None
    )

    if profile is None:
        return jsonify({
            "message": "No personal information saved yet"
        }), 404

    return jsonify(profile), 200


# Work Experience

@app.route("/api/work-experience", methods=["POST"])
@login_required
def add_work_experience():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    for field in ["job_title", "company"]:
        if not required_string(data, field):
            return jsonify({
                "error": f"{field} is required"
            }), 400

    error = validate_text_fields(
        data, ["start_date", "end_date", "description"]
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
        "description": clean_text(data.get("description", ""))
    }

    work_experiences.append(experience)

    return jsonify({
        "message": "Work experience added successfully",
        "data": experience
    }), 201


@app.route("/api/work-experience", methods=["GET"])
@login_required
def get_work_experiences():
    items = owned_items(work_experiences)

    return jsonify({
        "data": items,
        "count": len(items)
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
        "job_title", "company", "start_date",
        "end_date", "description"
    ]

    error = validate_text_fields(data, allowed)

    if error:
        return jsonify({"error": error}), 400

    for field in allowed:
        if field in data:
            if field in ["job_title", "company"] and not data[field].strip():
                return jsonify({
                    "error": f"{field} cannot be empty"
                }), 400

            experience[field] = data[field].strip()

    return jsonify({
        "message": "Work experience updated successfully",
        "data": experience
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

    for cv in owned_items(cvs):
        cv["selected_experience_ids"] = [
            value for value in cv["selected_experience_ids"]
            if value != item_id
        ]

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
            return jsonify({
                "error": f"{field} is required"
            }), 400

    error = validate_text_fields(
        data, ["start_date", "end_date", "description"]
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
        "description": clean_text(data.get("description", ""))
    }

    educations.append(education)

    return jsonify({
        "message": "Education added successfully",
        "data": education
    }), 201


@app.route("/api/education", methods=["GET"])
@login_required
def get_educations():
    items = owned_items(educations)

    return jsonify({
        "data": items,
        "count": len(items)
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
        "degree", "school", "start_date",
        "end_date", "description"
    ]

    error = validate_text_fields(data, allowed)

    if error:
        return jsonify({"error": error}), 400

    for field in allowed:
        if field in data:
            if field in ["degree", "school"] and not data[field].strip():
                return jsonify({
                    "error": f"{field} cannot be empty"
                }), 400

            education[field] = data[field].strip()

    return jsonify({
        "message": "Education updated successfully",
        "data": education
    }), 200


@app.route("/api/education/<int:item_id>", methods=["DELETE"])
@login_required
def delete_education(item_id):
    education = find_owned_item(educations, item_id)

    if education is None:
        return jsonify({"error": "Education not found"}), 404

    educations.remove(education)

    for cv in owned_items(cvs):
        cv["selected_education_ids"] = [
            value for value in cv["selected_education_ids"]
            if value != item_id
        ]

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

    skill_name = data.get("name", data.get("skill_name"))

    if not isinstance(skill_name, str) or not skill_name.strip():
        return jsonify({
            "error": "Skill name is required"
        }), 400

    error = validate_text_fields(data, ["level"])

    if error:
        return jsonify({"error": error}), 400

    skill = {
        "id": next_id(skills),
        "user_id": current_user_id(),
        "name": skill_name.strip(),
        "level": clean_text(data.get("level", ""))
    }

    skills.append(skill)

    return jsonify({
        "message": "Skill added successfully",
        "data": skill
    }), 201


@app.route("/api/skills", methods=["GET"])
@login_required
def get_skills():
    items = owned_items(skills)

    return jsonify({
        "data": items,
        "count": len(items)
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
        "data": skill
    }), 200


@app.route("/api/skills/<int:item_id>", methods=["DELETE"])
@login_required
def delete_skill(item_id):
    skill = find_owned_item(skills, item_id)

    if skill is None:
        return jsonify({"error": "Skill not found"}), 404

    skills.remove(skill)

    for cv in owned_items(cvs):
        cv["selected_skill_ids"] = [
            value for value in cv["selected_skill_ids"]
            if value != item_id
        ]

    return jsonify({
        "message": "Skill deleted successfully"
    }), 200


# CV Creation

@app.route("/api/cvs", methods=["POST"])
@login_required
def create_cv():
    data = get_json_data()

    if data is None:
        return jsonify({"error": "Invalid JSON data"}), 400

    name = data.get("name", "Untitled CV")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "CV name is required"}), 400

    error = validate_cv_selections(data)

    if error:
        return jsonify({"error": error}), 400

    for field in ["template", "color"]:
        if field in data and not isinstance(data[field], str):
            return jsonify({
                "error": f"{field} must be a string"
            }), 400

    if "include_personal_info" in data:
        if not isinstance(data["include_personal_info"], bool):
            return jsonify({
                "error": "include_personal_info must be true or false"
            }), 400

    cv = {
        "id": next_id(cvs),
        "user_id": current_user_id(),
        "name": name.strip(),
        "template": data.get("template", "classic"),
        "color": data.get("color", "blue"),
        "include_personal_info": data.get(
            "include_personal_info", True
        ),
        "selected_experience_ids": list(
            data.get("selected_experience_ids", [])
        ),
        "selected_education_ids": list(
            data.get("selected_education_ids", [])
        ),
        "selected_skill_ids": list(
            data.get("selected_skill_ids", [])
        )
    }

    cvs.append(cv)

    return jsonify({
        "message": "CV created successfully",
        "data": cv
    }), 201


# CV Listing

@app.route("/api/cvs", methods=["GET"])
@login_required
def list_cvs():
    items = owned_items(cvs)

    return jsonify({
        "data": items,
        "count": len(items)
    }), 200


# CV Details

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

    error = validate_cv_selections(data)

    if error:
        return jsonify({"error": error}), 400

    for field in ["name", "template", "color"]:
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return jsonify({
                    "error": f"{field} must be a non-empty string"
                }), 400

    if "include_personal_info" in data:
        if not isinstance(data["include_personal_info"], bool):
            return jsonify({
                "error": "include_personal_info must be true or false"
            }), 400

    for field in ["name", "template", "color"]:
        if field in data:
            cv[field] = data[field].strip()

    if "include_personal_info" in data:
        cv["include_personal_info"] = data["include_personal_info"]

    for field in [
        "selected_experience_ids",
        "selected_education_ids",
        "selected_skill_ids"
    ]:
        if field in data:
            cv[field] = list(data[field])

    return jsonify({
        "message": "CV updated successfully",
        "data": cv
    }), 200


# CV Deletion

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
        "selected_experience_ids": list(
            original["selected_experience_ids"]
        ),
        "selected_education_ids": list(
            original["selected_education_ids"]
        ),
        "selected_skill_ids": list(
            original["selected_skill_ids"]
        )
    }

    cvs.append(duplicate)

    return jsonify({
        "message": "CV duplicated successfully",
        "data": duplicate
    }), 201


# CV Preview

def build_cv_preview(cv_id):
    cv = get_cv_or_none(cv_id)

    if cv is None:
        return None

    profile = next(
        (
            item for item in personal_infos
            if item["user_id"] == current_user_id()
        ),
        None
    )

    selected_experiences = [
        item for item in owned_items(work_experiences)
        if item["id"] in cv["selected_experience_ids"]
    ]

    selected_educations = [
        item for item in owned_items(educations)
        if item["id"] in cv["selected_education_ids"]
    ]

    selected_skills = [
        item for item in owned_items(skills)
        if item["id"] in cv["selected_skill_ids"]
    ]

    return {
        "cv": cv,
        "personal_info": (
            profile if cv["include_personal_info"] else None
        ),
        "work_experiences": selected_experiences,
        "educations": selected_educations,
        "skills": selected_skills
    }


@app.route("/api/cvs/<int:cv_id>/preview", methods=["GET"])
@login_required
def preview_cv(cv_id):
    preview = build_cv_preview(cv_id)

    if preview is None:
        return jsonify({"error": "CV not found"}), 404

    return jsonify(preview), 200


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
        bottomMargin=45
    )

    color_options = {
        "blue": colors.HexColor("#2563EB"),
        "green": colors.HexColor("#15803D"),
        "red": colors.HexColor("#B91C1C"),
        "purple": colors.HexColor("#7C3AED"),
        "black": colors.HexColor("#111827"),
        "gray": colors.HexColor("#4B5563")
    }

    accent_color = color_options.get(
        str(cv.get("color", "blue")).lower(),
        color_options["blue"]
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
            spaceAfter=12
        )
    )

    styles.add(
        ParagraphStyle(
            name="CVSection",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=accent_color,
            spaceAfter=8
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
                color=accent_color
            )
        )

        story.append(Spacer(1, 8))

    personal = preview.get("personal_info") or {}

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

    selected_skills = preview.get("skills") or []

    if selected_skills:
        add_section("Skills")

        for skill in selected_skills:
            skill_name = skill.get("name", "")
            level = skill.get("level", "")

            if level:
                add_text(f"{skill_name} - {level}")
            else:
                add_text(skill_name)

    if not story:
        add_text("Curriculum Vitae", "CVName")

    document.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"cv_{cv_id}.pdf",
        mimetype="application/pdf"
    )


# Run Flask Application

if __name__ == "__main__":
    app.run(debug=True)
