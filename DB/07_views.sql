CREATE OR REPLACE VIEW vw_student_attendance_pct AS
SELECT
  sp.roll_no,
  sp.name AS student_name,
  ar.course_code,
  COUNT(DISTINCT ar.unique_code) AS total_sessions,
  COUNT(DISTINCT al.attendance_id) FILTER (WHERE al.is_rejected = FALSE) AS present_sessions,
  ROUND(
    (COUNT(DISTINCT al.attendance_id) FILTER (WHERE al.is_rejected = FALSE) * 100.0) /
    NULLIF(COUNT(DISTINCT ar.unique_code), 0),
  2) AS attendance_percentage
FROM student_profiles sp
LEFT JOIN attendance_logs al ON al.roll_no = sp.roll_no
LEFT JOIN attendance_registers ar ON ar.unique_code = al.unique_code
GROUP BY sp.roll_no, sp.name, ar.course_code;
