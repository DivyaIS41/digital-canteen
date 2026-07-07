DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS order_item;
DROP TABLE IF EXISTS order_info;
DROP TABLE IF EXISTS daily_special;
DROP TABLE IF EXISTS item;
DROP TABLE IF EXISTS admin;
DROP TABLE IF EXISTS student;

CREATE TABLE admin (
  admin_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE item (
  item_id INT AUTO_INCREMENT PRIMARY KEY,
  item_name VARCHAR(255) NOT NULL UNIQUE,
  price DECIMAL(10, 2) NOT NULL,
  category VARCHAR(100) NOT NULL,
  availability_status TINYINT(1) NOT NULL DEFAULT 1
);

CREATE TABLE daily_special (
  special_id INT AUTO_INCREMENT PRIMARY KEY,
  item_id INT NOT NULL,
  date DATE NOT NULL,
  discount_percentage DECIMAL(5, 2) NOT NULL,
  UNIQUE KEY unique_item_date (item_id, date),
  CONSTRAINT fk_daily_special_item
    FOREIGN KEY (item_id) REFERENCES item(item_id)
    ON DELETE CASCADE
);

CREATE TABLE student (
  student_id VARCHAR(20) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  login_password VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  phone VARCHAR(20),
  department VARCHAR(50),
  year INT,
  balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00
);

CREATE TABLE order_info (
  order_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id VARCHAR(20) NOT NULL,
  order_date DATE NOT NULL,
  order_time TIME NOT NULL,
  total_amount DECIMAL(10, 2) NOT NULL,
  status VARCHAR(50) NOT NULL,
  CONSTRAINT fk_order_student
    FOREIGN KEY (student_id) REFERENCES student(student_id)
    ON DELETE CASCADE
);

CREATE TABLE order_item (
  order_item_id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  item_id INT NOT NULL,
  quantity INT NOT NULL,
  subtotal DECIMAL(10, 2) NOT NULL,
  CONSTRAINT fk_order_item_order
    FOREIGN KEY (order_id) REFERENCES order_info(order_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_order_item_item
    FOREIGN KEY (item_id) REFERENCES item(item_id)
    ON DELETE RESTRICT
);

CREATE TABLE payment (
  payment_id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL UNIQUE,
  payment_mode VARCHAR(50) NOT NULL,
  amount_paid DECIMAL(10, 2) NOT NULL,
  payment_status VARCHAR(50) NOT NULL,
  transaction_date DATE NOT NULL,
  CONSTRAINT fk_payment_order
    FOREIGN KEY (order_id) REFERENCES order_info(order_id)
    ON DELETE CASCADE
);
