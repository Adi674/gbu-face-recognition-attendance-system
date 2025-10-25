CREATE TABLE attendance_registers (
  unique_code VARCHAR(100) PRIMARY KEY,
  created_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
  course_code VARCHAR(50) REFERENCES subjects(course_code) ON DELETE SET NULL,
  class_id BIGINT REFERENCES classes(class_id) ON DELETE SET NULL,
  teacher_id BIGINT REFERENCES teacher_profiles(teacher_id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  start_time TIMESTAMPTZ,
  end_time TIMESTAMPTZ
);

CREATE TABLE attendance_logs (
  attendance_id BIGSERIAL PRIMARY KEY,
  unique_code VARCHAR(100) REFERENCES attendance_registers(unique_code) ON DELETE CASCADE,
  roll_no VARCHAR(50) REFERENCES student_profiles(roll_no) ON DELETE SET NULL,
  is_manual BOOLEAN DEFAULT FALSE,
  is_rejected BOOLEAN DEFAULT FALSE,
  is_proxy BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT uq_attendance_unique_roll UNIQUE (unique_code, roll_no)
);
