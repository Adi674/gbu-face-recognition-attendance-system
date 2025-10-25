CREATE TYPE user_role AS ENUM ('admin', 'school', 'teacher');
CREATE TYPE activity_type AS ENUM (
  'add_student',
  'add_teacher',
  'remove_teacher',
  'remove_student',
  'update_teacher',
  'update_student'
);
