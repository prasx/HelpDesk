import sqlite3
import json

DB_PATH = 'app/database.db'

def execute_query(query, params=None):
    """
    Выполняет SQL-запрос к базе данных.

    Parameters:
        query (str): SQL-запрос.
        params (tuple): Параметры для запроса (по умолчанию None).

    Returns:
        list: Результат выполнения запроса.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.fetchall()

def create_tables():
    """
    Создает таблицы в базе данных, если они не существуют.
    """
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
            tg_id_ticket INTEGER,
            organization TEXT,
            addres_ticket TEXT,
            message_ticket TEXT,
            time_ticket TEXT,
            state_ticket TEXT,
            ticket_comm TEXT
        )
    '''
    execute_query(users)
    execute_query(ticket)


def add_user(tg_id, pos, data_reg, profile):
    """
    Добавляет нового пользователя в базу данных.

    Parameters:
        tg_id (int): Telegram ID пользователя.
        pos (str): Позиция пользователя.
        data_reg (str): Дата регистрации пользователя.
        profile (dict): Профиль пользователя в формате словаря.
    """
    query = '''INSERT INTO users (tg_id, pos, data_reg, profile) VALUES (?, ?, ?, ?)'''
    profile_json = json.dumps(profile, ensure_ascii=False)
    execute_query(query, (tg_id, pos, data_reg, profile_json))


def get_user_by_id(tg_id):
    """
    Возвращает информацию о пользователе по его Telegram ID.

    Parameters:
        tg_id (int): Telegram ID пользователя.

    Returns:
        dict: Информация о пользователе.
    """
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


def add_ticket(tg_id_ticket, organization, addres_ticket, message_ticket, time_ticket, state_ticket, ticket_comm):
    """
    Добавляет новую задачу в базу данных.

    Parameters:
        tg_id_ticket (int): Telegram ID пользователя, создавшего задачу.
        organization (str): Название организации.
        addres_ticket (str): Адрес задачи.
        message_ticket (str): Сообщение задачи.
        time_ticket (str): Время создания задачи.
        state_ticket (str): Статус задачи.
        ticket_comm (str): Комментарий к задаче.
    """
    query = '''
        INSERT INTO ticket (tg_id_ticket, organization, addres_ticket, message_ticket, time_ticket, state_ticket, ticket_comm)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    execute_query(query, (tg_id_ticket, organization, addres_ticket, message_ticket, time_ticket, state_ticket, ticket_comm))


def get_last_ticket_number():
    """
    Возвращает номер последней задачи в таблице ticket.

    Returns:
        int: Номер последней задачи.
    """
    query = "SELECT number_ticket FROM ticket ORDER BY number_ticket DESC LIMIT 1"
    result = execute_query(query)
    return result[0][0] if result else 0


def get_total_tickets_by_status(tg_id, status):
    """
    Возвращает общее количество задач с указанным статусом для заданного пользователя.

    Parameters:
        tg_id (int): Telegram ID пользователя.
        status (str): Статус задачи.

    Returns:
        int: Общее количество задач с указанным статусом.
    """
    query = 'SELECT COUNT(*) FROM ticket WHERE tg_id_ticket=? AND state_ticket=?'
    result = execute_query(query, (tg_id, status))
    return result[0][0] if result else 0


def get_total_tickets_by_status_admin(status):
    """
    Возвращает общее количество задач с указанным статусом для администратора.

    Parameters:
        status (str): Статус задачи.

    Returns:
        int: Общее количество задач с указанным статусом.
    """
    query = 'SELECT COUNT(*) FROM ticket WHERE state_ticket=?'
    result = execute_query(query, (status,))
    return result[0][0] if result else 0


def get_total_tickets_by_status_for_user(tg_id, status):
    """
    Возвращает общее количество задач с указанным статусом для заданного пользователя.

    Parameters:
        tg_id (int): Telegram ID пользователя.
        status (str): Статус задачи.

    Returns:
        str: Общее количество задач с указанным статусом (в виде строки).
    """
    total_tickets = get_total_tickets_by_status(tg_id, status)
    return str(total_tickets) if total_tickets else "0"


def get_tickets_in_progress_by_user_id(tg_id):
    """
    Возвращает список задач в работе для указанного пользователя.

    Parameters:
        tg_id (int): Telegram ID пользователя.

    Returns:
        list: Список задач в работе.
    """
    query = 'SELECT * FROM ticket WHERE tg_id_ticket=? AND state_ticket=?'
    result = execute_query(query, (tg_id, "В работе"))
    return result


def update_pos(pos_value, column, value):
    """
    Обновляет позицию пользователя в базе данных.

    Parameters:
        pos_value (str): Новое значение позиции.
        column (str): Название столбца, в котором нужно обновить значение.
        value (int): Значение, по которому происходит обновление.

    Returns:
        None
    """
    query = f"UPDATE users SET pos = ? WHERE {column} = ?"
    execute_query(query, (pos_value, value))


def update_profile_data(tg_id, field_name, new_value):
    """
    Обновляет данные профиля пользователя внутри ячейки profile.

    Parameters:
        tg_id (int): Telegram ID пользователя.
        field_name (str): Название поля, которое нужно обновить.
        new_value: Новое значение для поля.

    Returns:
        None
    """
    query_select = 'SELECT profile FROM users WHERE tg_id=?'
    profile_json = execute_query(query_select, (tg_id,))[0][0]
    if profile_json:
        profile_dict = json.loads(profile_json)
        profile_dict[field_name] = new_value
        query_update = "UPDATE users SET profile = ? WHERE tg_id = ?"
        execute_query(query_update, (json.dumps(profile_dict, ensure_ascii=False), tg_id))


def read_cell(column, condition_column, condition_value):
    """
    Читает данные из указанной ячейки в таблице пользователей.

    Parameters:
        column (str): Название столбца, из которого нужно прочитать данные.
        condition_column (str): Название столбца для условия выборки.
        condition_value: Значение, по которому происходит выборка.

    Returns:
        str: Значение ячейки (в виде строки).
    """
    query = f"SELECT {column} FROM users WHERE {condition_column} = ?"
    result = execute_query(query, (condition_value,))
    return str(result[0])[2:-3] if result else None


def read_profile(tg_id):
    """
    Возвращает данные профиля пользователя из ячейки profile.

    Parameters:
        tg_id (int): Telegram ID пользователя.

    Returns:
        dict: Данные профиля пользователя.
    """
    query = "SELECT profile FROM users WHERE tg_id=?"
    result = execute_query(query, (tg_id,))
    if result:
        return json.loads(result[0][0])
    return None


def get_all_tickets_in_progress():
    """
    Возвращает список всех тикетов, находящихся в процессе выполнения.

    Returns:
        list: Список кортежей с данными о тикетах.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ticket WHERE state_ticket=?', ("В работе",))
    all_tickets_in_progress = cursor.fetchall()
    conn.close()
    return all_tickets_in_progress


def get_ticket_info(ticket_id):
    """
    Возвращает информацию о заданном тикете.

    Parameters:
        ticket_id (int): Номер тикета.

    Returns:
        tuple: Кортеж с данными о тикете.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ticket WHERE number_ticket=?', (ticket_id,))
    ticket_info = cursor.fetchone()
    conn.close()
    return ticket_info


def update_ticket_status(ticket_id, new_status):
    """
    Обновляет статус заданного тикета.

    Parameters:
        ticket_id (int): Номер тикета.
        new_status (str): Новый статус.

    Returns:
        None
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "UPDATE ticket SET state_ticket=? WHERE number_ticket=?"
    cursor.execute(query, (new_status, ticket_id))
    conn.commit()
    conn.close()


def get_completed_tickets_by_user(tg_id):
    """
    Возвращает список завершенных тикетов для указанного пользователя.

    Parameters:
        tg_id (int): Telegram ID пользователя.

    Returns:
        list: Список кортежей с данными о завершенных тикетах.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ticket WHERE tg_id_ticket=? AND state_ticket=?', (tg_id, "Завершена"))
    completed_tickets = cursor.fetchall()
    conn.close()
    return completed_tickets


def update_ticket_comment(ticket_id, ticket_comm):
    """
    Обновляет комментарий в существующем тикете.

    Parameters:
        ticket_id (int): Номер тикета.
        ticket_comm (str): Новый комментарий.

    Returns:
        bool: Флаг успешного выполнения операции (True - успешно, False - ошибка).
    """
    query = 'UPDATE ticket SET ticket_comm = ? WHERE number_ticket = ?'
    execute_query(query, (ticket_comm, ticket_id))
    return True


def read_ticket_comment(ticket_id):
    """
    Читает комментарий из существующего тикета.

    Parameters:
        ticket_id (int): Номер тикета.

    Returns:
        str: Комментарий к тикету.
    """
    query = 'SELECT ticket_comm FROM ticket WHERE number_ticket = ?'
    result = execute_query(query, (ticket_id,))
    if result:
        return result[0][0]
    else:
        return None