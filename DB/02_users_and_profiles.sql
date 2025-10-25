CREATE TABLE users (
  user_id BIGSERIAL PRIMARY KEY,
  password_hash TEXT NOT NULL,
  role user_role NOT NULL DEFAULT 'teacher',
  name VARCHAR(255) NOT NULL,
  phone_number VARCHAR(20),
  email VARCHAR(255) UNIQUE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE teacher_profiles (
  teacher_id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
  school_id BIGINT,
  teacher_name VARCHAR(255),
  teacher_email VARCHAR(255) UNIQUE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE student_profiles (
  roll_no VARCHAR(50) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  phone_number VARCHAR(20),
  email VARCHAR(255) UNIQUE,
  semester SMALLINT,
  year SMALLINT,
  school_id BIGINT,
  department_id BIGINT,
  class_id BIGINT,
  created_at TIMESTAMPTZ DEFAULT now()
);
