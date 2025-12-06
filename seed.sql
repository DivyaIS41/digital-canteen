USE canteen;

-- Sample items
INSERT INTO item (item_name, price, category, availability_status) VALUES
('Biryani', 80.00, 'Lunch', 1),
('Veg Sandwich', 45.00, 'Snacks', 1),
('Masala Dosa', 50.00, 'Breakfast', 1),
('Tea', 10.00, 'Beverages', 1);

-- Sample student
INSERT INTO student (student_id, name, email, phone, department, year, balance) VALUES
('IS2101', 'John Doe', 'john@example.com', '9876543210', 'IS', 2, 100.00);

-- Sample daily special (applies discount to first item)
INSERT INTO daily_special (item_id, date, discount_percentage) VALUES
(1, CURDATE(), 10.00);
