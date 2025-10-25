CREATE OR REPLACE FUNCTION trg_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_attendance_logs_updated_at
BEFORE UPDATE ON attendance_logs
FOR EACH ROW
EXECUTE FUNCTION trg_set_updated_at();

CREATE OR REPLACE FUNCTION mark_attendance(
  p_unique_code VARCHAR,
  p_roll_no VARCHAR,
  p_is_manual BOOLEAN DEFAULT FALSE,
  p_is_proxy BOOLEAN DEFAULT FALSE
) RETURNS VOID AS $$
BEGIN
  LOOP
    UPDATE attendance_logs
    SET is_manual = p_is_manual,
        is_proxy = p_is_proxy,
        is_rejected = FALSE,
        updated_at = now()
    WHERE unique_code = p_unique_code AND roll_no = p_roll_no;
    IF FOUND THEN RETURN; END IF;
    BEGIN
      INSERT INTO attendance_logs (unique_code, roll_no, is_manual, is_proxy)
      VALUES (p_unique_code, p_roll_no, p_is_manual, p_is_proxy);
      RETURN;
    EXCEPTION WHEN unique_violation THEN
    END;
  END LOOP;
END;
$$ LANGUAGE plpgsql;
