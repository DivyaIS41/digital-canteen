INSERT INTO admin (username, password_hash) VALUES
('admin', 'set-your-admin-login-in-env-not-db');

INSERT INTO item (item_name, price, category, availability_status) VALUES
('Masala Dosa', 40.00, 'Breakfast', 1),
('Veg Sandwich', 30.00, 'Snack', 0),
('Coffee', 15.00, 'Drink', 1),
('Paneer Rice', 60.00, 'Lunch', 1),
('Veg Biryani', 85.00, 'Lunch', 1),
('Curd Rice', 45.00, 'Lunch', 0),
('French Fries', 50.00, 'Snack', 1),
('Samosa (2 pcs)', 35.00, 'Snack', 1),
('Fresh Lime Soda', 30.00, 'Drink', 1),
('Cold Coffee', 50.00, 'Drink', 1),
('Plain Uttapam', 55.00, 'Breakfast', 1),
('Gobi Manchurian', 75.00, 'Starter', 1),
('Chicken Lollypop', 120.00, 'Starter', 1),
('Masala Peanuts', 30.00, 'Starter', 1),
('Idli Sambar', 40.00, 'Breakfast', 1),
('Set Dosa', 60.00, 'Breakfast', 1),
('Vada Sambar (2 pcs)', 35.00, 'Breakfast', 0),
('Cheese Grill Sandwich', 65.00, 'Snack', 1),
('Bhel Puri', 40.00, 'Snack', 1),
('Lemon Iced Tea', 40.00, 'Drink', 0),
('Orange Juice', 60.00, 'Drink', 1),
('Egg Fried Rice', 70.00, 'Lunch', 1),
('Rajma Chawal', 80.00, 'Lunch', 1),
('Chili Paneer Dry', 100.00, 'Starter', 1),
('Prawns Fry', 150.00, 'Starter', 0),
('Gulab Jamun (2 pcs)', 45.00, 'Dessert', 1),
('Chocolate Brownie', 70.00, 'Dessert', 1),
('Fruit Salad', 60.00, 'Dessert', 1),
('Rasgulla (1 pc)', 35.00, 'Dessert', 1);

INSERT INTO student (student_id, name, email, phone, department, year, balance) VALUES
('4SF24IS402', 'Demo Student', 'demo.student@sahyadri.edu.in', '9876561066', 'IS', 2, 500.00),
('4SF23IS041', 'Divya K', 'divya.prototype@sahyadri.edu.in', '9876561022', 'IS', 3, 250.00);

INSERT INTO daily_special (item_id, date, discount_percentage) VALUES
(10, DATE('now', 'localtime'), 50.00),
(27, DATE('now', 'localtime'), 25.00);
