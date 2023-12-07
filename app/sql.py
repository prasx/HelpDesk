import sqlite3
import json

# Функция для создания таблиц в базе данных SQLite
def create_tables():
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            pos TEXT,
            data_reg TEXT,
            profile TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticket (
            number_ticket INTEGER PRIMARY KEY AUTOINCREMENT,
            user_ticket INTEGER,
            organization TEXT,
            addres_ticket TEXT,
            message_ticket TEXT,
            time_ticket TEXT,
            state_ticket TEXT
        )
    ''')

    conn.commit()
    conn.close()

# Функция для добавления пользователя в базу данных
def add_user(tg_id, pos, data_reg, profile):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()

    profile_json = json.dumps(profile, ensure_ascii=False)
    cursor.execute('''INSERT INTO users (tg_id, pos, data_reg, profile)VALUES (?, ?, ?, ?)''', (tg_id, pos, data_reg, profile_json))

    conn.commit()
    conn.close()

# Функция для получения информации о пользователе по его tg_id
def get_user_by_id(tg_id):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE tg_id=?', (tg_id,))
    user = cursor.fetchone()

    conn.close()

    if user:
        return {
            'tg_id': user[0],
            'pos': user[1],
            'data_reg': user[2],
            'profile': json.loads(user[3])
        }
    return None

# Функция для добавления билета в базу данных
def add_ticket(user_ticket, organization, addres_ticket, message_ticket, time_ticket, state_ticket):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO ticket (user_ticket, organization, addres_ticket, message_ticket, time_ticket, state_ticket)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_ticket, organization, addres_ticket, message_ticket, time_ticket, state_ticket))

    conn.commit()
    conn.close()

# Функция для получения всех заявок
def get_all_tickets():
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM ticket')
    tickets = cursor.fetchall()

    conn.close()

    return tickets



def get_last_ticket_number():
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()

    try:
        # Используем SQL-запрос для получения номера последней добавленной заявки
        cursor.execute("SELECT number_ticket FROM ticket ORDER BY number_ticket DESC LIMIT 1")
        last_ticket_number = cursor.fetchone()

        if last_ticket_number:
            return last_ticket_number[0]  # Возвращаем номер последней добавленной заявки

        return 0  # Если таблица пустая, возвращаем 0

    except sqlite3.Error as e:
        print("Ошибка при получении последнего номера заявки:", e)
        return None

    finally:
        cursor.close()
        conn.close()


# Функция для получения данных заявки по номеру заявки из таблицы ticket
def get_ticket_message_by_number(user_ticket):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT message_ticket FROM ticket WHERE user_ticket = ?', (user_ticket,))
    message_ticket = cursor.fetchone()
    conn.close()
    return message_ticket[0] if message_ticket else None


# Функция возвращает общее количество заявок для данного пользователя
def get_total_tickets_by_user_id(user_id):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM ticket WHERE user_ticket=?', (user_id,))
    total_tickets = cursor.fetchone()[0]
    conn.close()
    return total_tickets

# Функция возвращает статус задач
def get_total_tickets_by_status(user_id, status):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM ticket WHERE user_ticket=? AND state_ticket=?', (user_id, status))
    total_tickets = cursor.fetchone()[0]
    conn.close()
    return total_tickets

# Функция возвращает заявки "в работе" для пользователя
def get_tickets_in_progress_by_user_id(user_id):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ticket WHERE user_ticket=? AND state_ticket=?', (user_id, "В работе"))
    user_tickets_in_progress = cursor.fetchall()
    conn.close()
    return user_tickets_in_progress


# Функция для получения заявок по ID пользователя
def get_tickets_by_user_id(user_id):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM ticket WHERE user_ticket=?', (user_id,))
    tickets = cursor.fetchall()

    conn.close()

    return tickets


# Функция для обновления значения поля 'pos' для определенного пользователя по его tg_id
def update_pos(pos_value, column, value):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()

    update_query = f"UPDATE users SET pos = ? WHERE {column} = ?"
    cursor.execute(update_query, (pos_value, value))

    conn.commit()
    conn.close()


def update_profile_data(tg_id, field_name, new_value):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT profile FROM users WHERE tg_id=?', (tg_id,))
        profile_json = cursor.fetchone()[0]  # Получаем JSON из базы данных
        
        if profile_json:
            profile_dict = json.loads(profile_json)
            profile_dict[field_name] = new_value  # Обновляем значение в словаре
            cursor.execute("UPDATE users SET profile = ? WHERE tg_id = ?", (json.dumps(profile_dict, ensure_ascii=False), tg_id))
            conn.commit()

    except sqlite3.Error as e:
        print("Ошибка при работе с базой данных:", e)
        conn.rollback()  # Откатываем транзакцию в случае ошибки

    finally:
        cursor.close()  # Закрываем курсор
        conn.close()    # Закрываем соединение


# Функция для чтения ячейки из базы данных
def read_cell(column, condition_column, condition_value):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT {column} FROM users WHERE {condition_column} = ?", (condition_value,))
    result = str(cursor.fetchone())[2:-3]

    conn.close()
    return result

# Функция для чтения JSON-строки профиля пользователя
def read_profile(user_id):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT profile FROM users WHERE tg_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    # Если есть результат, преобразуйте его из строки JSON в словарь и верните
    if result:
        profile_data = json.loads(result[0])
        return profile_data
    else:
        return None