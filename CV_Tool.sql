CREATE DATABASE IF NOT EXISTS CV_Tool;
USE CV_Tool;
CREATE TABLE users (
user_id INT PRIMARY KEY,
username VARCHAR(50) NOT NULL UNIQUE,
email VARCHAR(100) NOT NULL UNIQUE,
password_hash varchar(150) NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE user_profiles (
profile_id INT PRIMARY KEY,
user_id INT NOT NULL,
full_name VARCHAR(100) NOT NULL,
contact_email VARCHAR(100) NOT NULL,
phone VARCHAR(100),
address VARCHAR(250),
phone_url VARCHAR(250),
professional_summary TEXT,
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

USE CV_Tool;
CREATE TABLE work_experiences (
    experience_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    company VARCHAR(100) NOT NULL,
    start_date VARCHAR(20), -- Format: MM/YYYY[cite: 4]
    end_date VARCHAR(20),   -- Format: MM/YYYY[cite: 4]
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE educations (
    education_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    degree_qualification VARCHAR(100) NOT NULL,
    school_university VARCHAR(100) NOT NULL,
    start_end_year VARCHAR(50), -- Format: Year (From-To)[cite: 5]
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE skills (
    skill_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    skill_name VARCHAR(50) NOT NULL, -- e.g., Excel, Java, Teamwork[cite: 5]
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE cvs (
    cv_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    cv_title VARCHAR(100) NOT NULL, -- e.g., "Software Engineer CV"
    file_name VARCHAR(100),         -- e.g., Name-CV.pdf[cite: 8]
    save_location VARCHAR(255),     -- e.g., This PC/Documents[cite: 8]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE cv_work_experiences (
    cv_id INT,
    experience_id INT,
    PRIMARY KEY (cv_id, experience_id),
    FOREIGN KEY (cv_id) REFERENCES cvs(cv_id) ON DELETE CASCADE,
    FOREIGN KEY (experience_id) REFERENCES work_experiences(experience_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE cv_educations (
    cv_id INT,
    education_id INT,
    PRIMARY KEY (cv_id, education_id),
    FOREIGN KEY (cv_id) REFERENCES cvs(cv_id) ON DELETE CASCADE,
    FOREIGN KEY (education_id) REFERENCES educations(education_id) ON DELETE CASCADE
) ENGINE=InnoDB;

USE CV_Tool;
CREATE TABLE cv_skills (
    cv_id INT NOT NULL,
    skill_id INT NOT NULL,
    PRIMARY KEY (cv_id, skill_id),
    FOREIGN KEY (cv_id) REFERENCES cvs(cv_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
) ENGINE=InnoDB;
