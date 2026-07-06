from db_config import initialize_database


if __name__ == '__main__':
    if initialize_database():
        print('SQLite database initialized successfully.')
    else:
        print('Failed to initialize SQLite database.')
