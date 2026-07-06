PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS order_item;
DROP TABLE IF EXISTS order_info;
DROP TABLE IF EXISTS daily_special;
DROP TABLE IF EXISTS item;
DROP TABLE IF EXISTS admin;
DROP TABLE IF EXISTS student;

CREATE TABLE admin (
  admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE item (
  item_id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_name TEXT NOT NULL UNIQUE,
  price REAL NOT NULL,
  category TEXT NOT NULL,
  availability_status INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE daily_special (
  special_id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL,
  date TEXT NOT NULL,
  discount_percentage REAL NOT NULL,
  UNIQUE (item_id, date),
  FOREIGN KEY (item_id) REFERENCES item(item_id) ON DELETE CASCADE
);

CREATE TABLE student (
  student_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT,
  department TEXT,
  year INTEGER,
  balance REAL NOT NULL DEFAULT 0.00
);

CREATE TABLE order_info (
  order_id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id TEXT NOT NULL,
  order_date TEXT NOT NULL,
  order_time TEXT NOT NULL,
  total_amount REAL NOT NULL,
  status TEXT NOT NULL,
  FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE
);

CREATE TABLE order_item (
  order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  item_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  subtotal REAL NOT NULL,
  FOREIGN KEY (order_id) REFERENCES order_info(order_id) ON DELETE CASCADE,
  FOREIGN KEY (item_id) REFERENCES item(item_id) ON DELETE RESTRICT
);

CREATE TABLE payment (
  payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL UNIQUE,
  payment_mode TEXT NOT NULL,
  amount_paid REAL NOT NULL,
  payment_status TEXT NOT NULL,
  transaction_date TEXT NOT NULL,
  FOREIGN KEY (order_id) REFERENCES order_info(order_id) ON DELETE CASCADE
);

PRAGMA foreign_keys = ON;
