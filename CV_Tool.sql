CREATE DATABASE IF NOT EXISTS CV_Tool;
USE CV_Tool;

# Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

# User Profiles / Personal Information
USE CV_Tool;
CREATE TABLE IF NOT EXISTS user_profiles (
    profile_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    contact_email VARCHAR(100) NOT NULL,
    phone VARCHAR(100),
    address VARCHAR(250),
    photo_url VARCHAR(255),
    professional_summary TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

# Work Experience Repository
USE CV_Tool;
CREATE TABLE IF NOT EXISTS work_experiences (
    experience_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    company VARCHAR(100) NOT NULL,
    start_date VARCHAR(20),
    end_date VARCHAR(20),
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

# Education Repository
USE CV_Tool;
CREATE TABLE IF NOT EXISTS educations (
    education_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    degree_qualification VARCHAR(100) NOT NULL,
    school_university VARCHAR(100) NOT NULL,
    start_date VARCHAR(20),
    end_date VARCHAR(20),
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

# Skills Repository
USE CV_Tool;
CREATE TABLE IF NOT EXISTS skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_name VARCHAR(50) NOT NULL,
    level VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

# Languages Repository
USE CV_Tool;
CREATE TABLE IF NOT EXISTS languages (
    language_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    language_name VARCHAR(50) NOT NULL,
    proficiency VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

# Projects Repository
USE CV_Tool;
CREATE TABLE IF NOT EXISTS projects (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    project_title VARCHAR(100) NOT NULL,
    description TEXT,
    project_url VARCHAR(255),
    start_date VARCHAR(20),
    end_date VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

# Certificates Repository
USE CV_Tool;
CREATE TABLE IF NOT EXISTS certificates (
    certificate_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    certificate_name VARCHAR(100) NOT NULL,
    issuing_organization VARCHAR(100),
    issue_date VARCHAR(20),
    credential_url VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

# CV Instances Table
USE CV_Tool;
CREATE TABLE IF NOT EXISTS cvs (
    cv_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    cv_title VARCHAR(100) NOT NULL,
    template VARCHAR(50) DEFAULT 'default',
    color VARCHAR(30) DEFAULT '#000000',
    include_personal_info BOOLEAN DEFAULT TRUE,
    file_name VARCHAR(100),
    save_location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

# CV Selection Mapping Tables
USE CV_Tool;
CREATE TABLE IF NOT EXISTS cv_work_experiences (
    cv_id INT,
    experience_id INT,
    PRIMARY KEY (cv_id, experience_id),
    FOREIGN KEY (cv_id) REFERENCES cvs(cv_id) ON DELETE CASCADE,
    FOREIGN KEY (experience_id) REFERENCES work_experiences(experience_id) ON DELETE CASCADE
) ENGINE=InnoDB;

USE CV_Tool;
CREATE TABLE IF NOT EXISTS cv_educations (
    cv_id INT,
    education_id INT,
    PRIMARY KEY (cv_id, education_id),
    FOREIGN KEY (cv_id) REFERENCES cvs(cv_id) ON DELETE CASCADE,
    FOREIGN KEY (education_id) REFERENCES educations(education_id) ON DELETE CASCADE
) ENGINE=InnoDB;

USE CV_Tool;
CREATE TABLE IF NOT EXISTS cv_skills (
    cv_id INT,
    skill_id INT,
    PRIMARY KEY (cv_id, skill_id),
    FOREIGN KEY (cv_id) REFERENCES cvs(cv_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
) ENGINE=InnoDB;

USE CV_Tool;
CREATE TABLE IF NOT EXISTS cv_languages (
    cv_id INT,
    language_id INT,
    PRIMARY KEY (cv_id, language_id),
    FOREIGN KEY (cv_id) REFERENCES cvs(cv_id) ON DELETE CASCADE,
    FOREIGN KEY (language_id) REFERENCES languages(language_id) ON DELETE CASCADE
) ENGINE=InnoDB;

USE CV_Tool;
CREATE TABLE IF NOT EXISTS cv_projects (
    cv_id INT,
    project_id INT,
    PRIMARY KEY (cv_id, project_id),
    FOREIGN KEY (cv_id) REFERENCES cvs(cv_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
) ENGINE=InnoDB;

USE CV_Tool;
CREATE TABLE IF NOT EXISTS cv_certificates (
    cv_id INT,
    certificate_id INT,
    PRIMARY KEY (cv_id, certificate_id),
    FOREIGN KEY (cv_id) REFERENCES cvs(cv_id) ON DELETE CASCADE,
    FOREIGN KEY (certificate_id) REFERENCES certificates(certificate_id) ON DELETE CASCADE
) ENGINE=InnoDB;
