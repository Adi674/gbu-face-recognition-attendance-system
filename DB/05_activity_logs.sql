CREATE TABLE school_activities (
  activity_id BIGSERIAL PRIMARY KEY,
  activity_name activity_type NOT NULL,
  user_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
  roll_no VARCHAR(50) REFERENCES student_profiles(roll_no) ON DELETE SET NULL,
  details TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ
);
