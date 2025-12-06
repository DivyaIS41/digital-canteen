-- Digital Canteen - Database schema
-- Generated from provided DB descriptions/screenshots
-- Use this file to create the `canteen` database tables

-- Safety: disable FK checks while creating/dropping tables
SET FOREIGN_KEY_CHECKS = 0;

-- Drop tables if they exist (safe to run multiple times)
DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS order_item;
DROP TABLE IF EXISTS order_info;
DROP TABLE IF EXISTS daily_special;
DROP TABLE IF EXISTS item;
DROP TABLE IF EXISTS admin;
DROP TABLE IF EXISTS student;

-- Create admin table
CREATE TABLE admin (
  admin_id INT NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (admin_id),
  UNIQUE KEY uq_admin_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create item table
CREATE TABLE item (
  item_id INT NOT NULL AUTO_INCREMENT,
  item_name VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  category VARCHAR(50) NOT NULL,
  availability_status TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (item_id),
  UNIQUE KEY uq_item_name (item_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create daily_special table
CREATE TABLE daily_special (
  special_id INT NOT NULL AUTO_INCREMENT,
  item_id INT NOT NULL,
  date DATE NOT NULL,
  discount_percentage DECIMAL(5,2) NOT NULL,
  PRIMARY KEY (special_id),
  KEY idx_daily_special_item (item_id),
  CONSTRAINT fk_daily_special_item FOREIGN KEY (item_id) REFERENCES item(item_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create student table
CREATE TABLE student (
  student_id VARCHAR(20) NOT NULL,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  phone VARCHAR(15) DEFAULT NULL,
  department VARCHAR(50) DEFAULT NULL,
  year INT DEFAULT NULL,
  balance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (student_id),
  UNIQUE KEY uq_student_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create order_info table
CREATE TABLE order_info (
  order_id INT NOT NULL AUTO_INCREMENT,
  student_id VARCHAR(20) NOT NULL,
  order_date DATE NOT NULL,
  order_time TIME NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  status VARCHAR(20) NOT NULL,
  PRIMARY KEY (order_id),
  KEY idx_order_info_student (student_id),
  CONSTRAINT fk_order_info_student FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create order_item table
CREATE TABLE order_item (
  order_item_id INT NOT NULL AUTO_INCREMENT,
  order_id INT NOT NULL,
  item_id INT NOT NULL,
  quantity INT NOT NULL,
  subtotal DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (order_item_id),
  KEY idx_order_item_order (order_id),
  KEY idx_order_item_item (item_id),
  CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES order_info(order_id) ON DELETE CASCADE,
  CONSTRAINT fk_order_item_item FOREIGN KEY (item_id) REFERENCES item(item_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create payment table
CREATE TABLE payment (
  payment_id INT NOT NULL AUTO_INCREMENT,
  order_id INT NOT NULL,
  payment_mode VARCHAR(50) NOT NULL,
  amount_paid DECIMAL(10,2) NOT NULL,
  payment_status VARCHAR(20) NOT NULL,
  transaction_date DATETIME NOT NULL,
  PRIMARY KEY (payment_id),
  UNIQUE KEY uq_payment_order (order_id),
  CONSTRAINT fk_payment_order FOREIGN KEY (order_id) REFERENCES order_info(order_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- End of schema
