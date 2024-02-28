import sqlite3
import json

DB_PATH = 'app/database.db'

def execute_query(query, params=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.fetchall()

def create_tables():
    users = '''
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            pos TEXT,
            data_reg TEXT,
            profile TEXT
        )
    '''
    ticket = '''
        CREATE TABLE IF NOT EXISTS ticket (
            number_ticket INTEGER PRIMARY KEY AUTOINCREMENT,
            user_ticket INTEGER,
            organization TEXT,
            addres_ticket TEXT,
            message_ticket TEXT,
            time_ticket TEXT,
            state_ticket TEXT
        )
    '''
    execute_query(users)
    execute_query(ticket)

# Функция записи пользователя в базу данных
def add_user(tg_id, pos, data_reg, profile):
    query = '''INSERT INTO users (tg_id, pos, data_reg, profile) VALUES (?, ?, ?, ?)'''
    profile_json = json.dumps(profile, ensure_ascii=False)
    execute_query(query, (tg_id, pos, data_reg, profile_json))

# Функция возвращает информацию о пользователе по его tg_id
def get_user_by_id(tg_id):
    query = 'SELECT * FROM users WHERE tg_id=?'
    result = execute_query(query, (tg_id,))
    if result:
        return {
            'tg_id': result[0][0],
            'pos': result[0][1],
            'data_reg': result[0][2],
            'profile': json.loads(result[0][3])
        }
    return None

# Функция для добавления новой задачи в базу данных
def add_ticket(user_ticket, organization, addres_ticket, message_ticket, time_ticket, state_ticket):
    query = '''
        INSERT INTO ticket (user_ticket, organization, addres_ticket, message_ticket, time_ticket, state_ticket)
        VALUES (?, ?, ?, ?, ?, ?)
    '''
    execute_query(query, (user_ticket, organization, addres_ticket, message_ticket, time_ticket, state_ticket))

# Функция получения последней задачи в таблицы ticket
def get_last_ticket_number():
    query = "SELECT number_ticket FROM ticket ORDER BY number_ticket DESC LIMIT 1"
    result = execute_query(query)
    return result[0][0] if result else 0

# Функция возвращает статус задач
def get_total_tickets_by_status(tg_id, status):
    query = 'SELECT COUNT(*) FROM ticket WHERE user_ticket=? AND state_ticket=?'
    result = execute_query(query, (tg_id, status))
    return result[0][0] if result else 0

# Функция возвращает статус задач для администаротора
def get_total_tickets_by_status_admin(status):
    query = 'SELECT COUNT(*) FROM ticket WHERE state_ticket=?'
    result = execute_query(query, (status,))
    return result[0][0] if result else 0

# Функция для получения данных заявки по номеру заявки из таблицы ticket
def get_total_tickets_by_status_for_user(tg_id, status):
    total_tickets = get_total_tickets_by_status(tg_id, status)
    return str(total_tickets) if total_tickets else "0"

# Функция возвращает количество тикетов с аргументом "В работе"
def get_tickets_in_progress_by_user_id(tg_id):
    query = 'SELECT * FROM ticket WHERE user_ticket=? AND state_ticket=?'
    result = execute_query(query, (tg_id, "В работе"))
    return result

# Обновление позиции пользователя
def update_pos(pos_value, column, value):
    query = f"UPDATE users SET pos = ? WHERE {column} = ?"
    execute_query(query, (pos_value, value))

# Обновление данных пользователя внутри ячейки profile
def update_profile_data(tg_id, field_name, new_value):
    query_select = 'SELECT profile FROM users WHERE tg_id=?'
    profile_json = execute_query(query_select, (tg_id,))[0][0]
    if profile_json:
        profile_dict = json.loads(profile_json)
        profile_dict[field_name] = new_value
        query_update = "UPDATE users SET profile = ? WHERE tg_id = ?"
        execute_query(query_update, (json.dumps(profile_dict, ensure_ascii=False), tg_id))

# Чтение данных
def read_cell(column, condition_column, condition_value):
    query = f"SELECT {column} FROM users WHERE {condition_column} = ?"
    result = execute_query(query, (condition_value,))
    return str(result[0])[2:-3] if result else None

# Функция возвращает данные внутри ячейки profile
def read_profile(tg_id):
    query = "SELECT profile FROM users WHERE tg_id=?"
    result = execute_query(query, (tg_id,))
    if result:
        return json.loads(result[0][0])
    return None

# Функция возвращает данные о заявках в работе
def get_all_tickets_in_progress():
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ticket WHERE state_ticket=?', ("В работе",))
    all_tickets_in_progress = cursor.fetchall()
    conn.close()

    return all_tickets_in_progress

# Функция возвращает список тикетов с _
def get_ticket_info(ticket_id):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ticket WHERE number_ticket=?', (ticket_id,))
    ticket_info = cursor.fetchone()
    conn.close()
    return ticket_info

# Обновляет статус тикета
def update_ticket_status(ticket_id, new_status):
    conn = sqlite3.connect('app/database.db')
    cursor = conn.cursor()
    query = "UPDATE ticket SET state_ticket=? WHERE number_ticket=?"
    cursor.execute(query, (new_status, ticket_id))
    conn.commit()
