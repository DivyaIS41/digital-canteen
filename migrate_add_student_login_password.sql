ALTER TABLE student
ADD COLUMN login_password VARCHAR(100) NOT NULL DEFAULT 'student123' AFTER name;

UPDATE student
SET login_password = 'student123'
WHERE login_password IS NULL OR login_password = '';
