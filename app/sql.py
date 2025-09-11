import sqlite3
import datetime
import json
from typing import Any, Iterable, Optional
from zoneinfo import ZoneInfo

DB_PATH = 'app/database.db'
MOSCOW_TZ = ZoneInfo("Europe/Moscow")

def parse_to_moscow_naive(dt_input: datetime.datetime | str | None) -> datetime.datetime:
    """
    Преобразует входное значение во время Москвы (naive, без tzinfo).
    Если входное значение None или некорректно — возвращает текущее московское время.
    Строки парсятся автоматически; для naive datetime предполагается UTC; для aware — конвертация в Москву.
    """
    if not dt_input:
        return datetime.datetime.now(MOSCOW_TZ).replace(tzinfo=None)

    if isinstance(dt_input, str):
        try:
            # Если строка в формате "YYYY-MM-DD HH:MM:SS", считаем её MSK (naive)
            dt = datetime.datetime.strptime(dt_input, "%Y-%m-%d %H:%M:%S")
            return dt  # Возвращаем как есть, без преобразования
        except ValueError:
            try:
                # Пробуем ISO-формат с временной зоной
                dt = datetime.datetime.fromisoformat(dt_input.replace("Z", "+00:00"))
            except ValueError:
                return datetime.datetime.now(MOSCOW_TZ).replace(tzinfo=None)
    else:
        dt = dt_input

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(MOSCOW_TZ).replace(tzinfo=None)

def execute_query(query: str, params: tuple | None = None, fetch_one: bool = False) -> list[tuple] | tuple | None:
    """
    Выполняет SQL-запрос и возвращает результаты.
    Если fetch_one=True — возвращает одну строку или None. Иначе — все строки.
    Фиксирует изменения (commit) только для не-SELECT запросов.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        if query.strip().upper().startswith("SELECT"):
            result = cursor.fetchone() if fetch_one else cursor.fetchall()
        else:
            conn.commit()
            result = None
        return result

def create_tables():
    """
    Создает таблицы базы данных, если они еще не существуют.
    """
    users = '''
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            data_reg TEXT,
            organization TEXT,
            organization_adress TEXT,
            organization_inn TEXT,
            organization_phone TEXT,
            history_ticket TEXT,
            data_ticket TEXT,
            user_name TEXT
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

def add_user(tg_id: int, data_reg: str, organization: str, organization_adress: str,
             organization_inn: str, organization_phone: str, history_ticket: str = "",
             data_ticket: str = "", user_name: str = "") -> None:
    """Добавляет нового пользователя в базу данных."""
    query = '''INSERT INTO users (tg_id, data_reg, organization, organization_adress,
                                 organization_inn, organization_phone, history_ticket,
                                 data_ticket, user_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    execute_query(query, (tg_id, data_reg, organization, organization_adress,
                         organization_inn, organization_phone, history_ticket,
                         data_ticket, user_name))

def get_user_by_id(tg_id: int) -> dict | None:
    """Возвращает информацию о пользователе по Telegram ID."""
    query = "SELECT * FROM users WHERE tg_id = ?"
    row = execute_query(query, (tg_id,), fetch_one=True)
    if row:
        return {
            'tg_id': row[0],
            'data_reg': row[1],
            'organization': row[2],
            'organization_adress': row[3],
            'organization_inn': row[4],
            'organization_phone': row[5],
            'history_ticket': row[6],
            'data_ticket': row[7],
            'user_name': row[8]
        }
    return None

def update_user_field(tg_id: int, field_name: str, value: str) -> None:
    """Обновляет указанное поле пользователя."""
    query = f"UPDATE users SET {field_name} = ? WHERE tg_id = ?"
    execute_query(query, (value, tg_id))

def add_ticket(tg_id_ticket: int, organization: str, addres_ticket: str, message_ticket: str,
               time_ticket: str, state_ticket: str, ticket_comm: str) -> None:
    """Добавляет новый тикет в базу данных."""
    query = '''
        INSERT INTO ticket (tg_id_ticket, organization, addres_ticket, message_ticket,
                           time_ticket, state_ticket, ticket_comm)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    execute_query(query, (tg_id_ticket, organization, addres_ticket, message_ticket,
                         time_ticket, state_ticket, ticket_comm))

def get_last_ticket_number() -> int:
    """Возвращает номер последнего тикета."""
    query = "SELECT number_ticket FROM ticket ORDER BY number_ticket DESC LIMIT 1"
    row = execute_query(query, fetch_one=True)
    return row[0] if row else 0

def get_ticket_count(tg_id: int | None, status: str) -> int:
    """Возвращает количество тикетов с указанным статусом. Если tg_id=None — для всех пользователей."""
    query = "SELECT COUNT(*) FROM ticket WHERE state_ticket = ?"
    params = (status,)
    if tg_id is not None:
        query += " AND tg_id_ticket = ?"
        params = (status, tg_id)
    row = execute_query(query, params, fetch_one=True)
    return row[0] if row else 0

def get_tickets_in_progress_by_user_id(tg_id: int) -> list[tuple]:
    """Возвращает список тикетов пользователя в статусе "В работе"."""
    query = "SELECT * FROM ticket WHERE tg_id_ticket = ? AND state_ticket = ?"
    return execute_query(query, (tg_id, "В работе"))

def get_all_tickets_in_progress() -> list[tuple]:
    """Возвращает список всех тикетов в статусе "В работе"."""
    return execute_query("SELECT * FROM ticket WHERE state_ticket = ?", ("В работе",))

def get_ticket_info(ticket_id: int) -> tuple | None:
    """Возвращает информацию о тикете по его номеру."""
    return execute_query("SELECT * FROM ticket WHERE number_ticket = ?", (ticket_id,), fetch_one=True)

def update_ticket_status(ticket_id: int, new_status: str) -> None:
    """Обновляет статус тикета."""
    execute_query("UPDATE ticket SET state_ticket = ? WHERE number_ticket = ?", (new_status, ticket_id))

def get_completed_tickets_by_user(tg_id: int) -> list[tuple]:
    """Возвращает список завершенных тикетов пользователя."""
    return execute_query("SELECT * FROM ticket WHERE tg_id_ticket = ? AND state_ticket = ?",
                        (tg_id, "Завершена"))

def update_ticket_comment(ticket_id: int, ticket_comm: str) -> bool:
    """Обновляет комментарий существующего тикета."""
    execute_query("UPDATE ticket SET ticket_comm = ? WHERE number_ticket = ?", (ticket_comm, ticket_id))
    return True

def read_ticket_comment(ticket_id: int) -> str | None:
    """Читает комментарий существующего тикета."""
    row = execute_query("SELECT ticket_comm FROM ticket WHERE number_ticket = ?", (ticket_id,), fetch_one=True)
    return row[0] if row else None