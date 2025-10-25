CREATE TABLE schools (
  school_id BIGSERIAL PRIMARY KEY,
  school_name VARCHAR(255) NOT NULL,
  school_dean VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE departments (
  department_id BIGSERIAL PRIMARY KEY,
  department_name VARCHAR(255) NOT NULL,
  hod VARCHAR(255),
  school_id BIGINT REFERENCES schools(school_id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE classes (
  class_id BIGSERIAL PRIMARY KEY,
  class_name VARCHAR(255) NOT NULL,
  department_id BIGINT REFERENCES departments(department_id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE subjects (
  course_code VARCHAR(50) PRIMARY KEY,
  subject_name VARCHAR(255) NOT NULL,
  school_id BIGINT REFERENCES schools(school_id) ON DELETE SET NULL,
  semester SMALLINT,
  class_id BIGINT REFERENCES classes(class_id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
