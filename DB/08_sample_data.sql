INSERT INTO schools (school_name, school_dean) VALUES ('Engineering College', 'Dr. A Dean');
INSERT INTO departments (department_name, hod, school_id) VALUES ('Computer Science', 'Prof. HOD', 1);
INSERT INTO classes (class_name, department_id) VALUES ('BCS III A', 1);
INSERT INTO subjects (course_code, subject_name, school_id, semester, class_id)
VALUES ('CSE301', 'Operating Systems', 1, 5, 1);

INSERT INTO users (password_hash, role, name, email)
VALUES ('hash_admin_123', 'admin', 'Admin', 'admin@example.com');

INSERT INTO teacher_profiles (user_id, school_id, teacher_name, teacher_email)
VALUES (1, 1, 'John Teacher', 'john.teacher@example.com');

INSERT INTO student_profiles (roll_no, name, email, semester, year, school_id, department_id, class_id)
VALUES
('CS2022-001','Vikas Kumar','vikas@example.com',5,3,1,1,1),
('CS2022-002','Aman Sharma','aman@example.com',5,3,1,1,1);
