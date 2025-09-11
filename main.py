import asyncio
import logging
import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from app import sql
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создание бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Создание таблиц в базе данных SQLite
sql.create_tables()

# Состояния для FSM
class UserStates(StatesGroup):
    waiting_for_company_name = State()
    waiting_for_company_address = State()
    waiting_for_company_inn = State()
    waiting_for_company_phone = State()
    waiting_for_ticket_message = State()
    waiting_for_ticket_comment = State()

@dp.message(Command("start"))
async def send_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    moscow_dt = sql.parse_to_moscow_naive(message.date)
    data_reg = moscow_dt.strftime("%Y-%m-%d %H:%M:%S")
    user = sql.get_user_by_id(user_id)
    
    if not user:
        user_info = {
            'tg_id': user_id,
            'data_reg': data_reg,
            'organization': "Нет данных",
            'organization_adress': "Нет данных",
            'organization_inn': "Нет данных",
            'organization_phone': "Нет данных",
            'history_ticket': "",
            'data_ticket': "",
            'user_name': ""
        }
        sql.add_user(**user_info)
        text_no_user = "Добро пожаловать в HelpDesk компании <b>ЭниКей</b>! Для работы в сервисе необходимо заполнить данные."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏢 Моя компания", callback_data="my_company")]
        ])
        await message.answer(text_no_user, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(None)
    else:
        open_ticket = sql.get_ticket_count(user_id, "В работе")
        closed_ticket = sql.get_ticket_count(user_id, "Завершена")
        organization = user.get("organization", "Нет данных")
        organization_phone = user.get("organization_phone", "Нет данных")
        
        text_user = (
            f"<b>🧑‍💻 Главное меню</b>\n\n"
            f"<b>📋 Компания:</b> {organization}\n"
            f"<b>☎️ Контактный номер:</b> {organization_phone}\n\n"
            f"<b>📬 Открытых заявок:</b> {open_ticket}\n"
            f"<b>📭 Закрытых заявок:</b> {closed_ticket}\n"
            f"\nВыберите интересующее действие ⬇️"
        )
        
        keyboard_buttons = [
            [InlineKeyboardButton(text="🏢 Моя компания", callback_data="my_company"),
             InlineKeyboardButton(text="📥 Мои заявки", callback_data="my_ticket")],
            [InlineKeyboardButton(text="📤 Новая заявка", callback_data="new_ticket")]
        ]
        
        if user_id in config.ADMIN_USERS:
            keyboard_buttons.append([InlineKeyboardButton(text="🤘 Тикет меню", callback_data="admin_panel")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await message.answer(text_user, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(None)

def main_menu(tg_id):
    open_ticket = sql.get_ticket_count(tg_id, "В работе")
    closed_ticket = sql.get_ticket_count(tg_id, "Завершена")
    user = sql.get_user_by_id(tg_id)
    organization = user.get("organization", "Нет данных")
    organization_phone = user.get("organization_phone", "Нет данных")
    
    text = (
        f"<b>🧑‍💻 Главное меню</b>\n\n"
        f"<b>📋 Компания:</b> {organization}\n"
        f"<b>☎️ Контактный номер:</b> {organization_phone}\n\n"
        f"<b>📬 Открытых заявок:</b> {open_ticket}\n"
        f"<b>📭 Закрытых заявок:</b> {closed_ticket}\n"
        f"\nВыберите интересующее действие ⬇️"
    )
    
    keyboard_buttons = [
        [InlineKeyboardButton(text="🏢 Моя компания", callback_data="my_company"),
         InlineKeyboardButton(text="📥 Мои заявки", callback_data="my_ticket")],
        [InlineKeyboardButton(text="📤 Новая заявка", callback_data="new_ticket")]
    ]
    
    if tg_id in config.ADMIN_USERS:
        keyboard_buttons.append([InlineKeyboardButton(text="🤘 Тикет меню", callback_data="admin_panel")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return text, keyboard

def new_ticket(tg_id):
    text = (
        f"<b>📤 Создание новой заявки</b>\n\n"
        f" - 📝 Опишите вашу проблему.\n"
        f" - 🧩 Пожалуйста, опишите вашу проблему и укажите как можно больше деталей.\n\n"
        f"<b>Пример оформления заявки:</b>\n<i>Не работает принтер на 4 ПК, необходимо проверить подключение.</i>"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])
    return text, keyboard

def my_ticket(tg_id):
    user = sql.get_user_by_id(tg_id)
    user_tickets_in_progress = sql.get_tickets_in_progress_by_user_id(tg_id)
    total_user_tickets_in_progress = len(user_tickets_in_progress)
    open_ticket = str(total_user_tickets_in_progress) if total_user_tickets_in_progress else "0"
    organization = user.get("organization", "Нет данных")
    organization_address = user.get("organization_adress", "Нет данных")
    
    if user_tickets_in_progress:
        text = (
            f"<b>📥 Мои заявки в работе</b>\n\n"
            f"<b>Компания:</b> {organization}\n"
            f"<b>Адрес заявки:</b> {organization_address}\n"
            f"<b>Заявок в работе:</b> {open_ticket}\n\n"
        )
        for ticket in user_tickets_in_progress:
            text += (
                f"<b>Номер заявки:</b> <code>#{ticket[0]}</code>\n"
                f"<b>Описание:</b> {ticket[4]}\n"
                f"<b>Дата:</b> {ticket[5]}\n"
                f"<b>Статус:</b> {ticket[6]}\n"
            )
    else:
        text = (
            '<b>📥 Мои заявки</b>\n\n'
            'У вас пока нет заявок в работе.. 🤷‍♂️\n'
            '- <i>Чтобы оставить заявку, воспользуйтесь меню </i><b>"📤 Новая заявка"</b>'
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☑️ История заявок", callback_data="my_ticket_history")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])
    return text, keyboard

def my_ticket_history(tg_id, page=1, page_size=4):
    completed_tickets = sql.get_completed_tickets_by_user(tg_id)
    if completed_tickets:
        if len(completed_tickets) > page_size:
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            current_page_tickets = completed_tickets[start_index:end_index]
            text = f"<b>📨 История ваших завершенных заявок (страница {page}):</b>\n\n"
        else:
            current_page_tickets = completed_tickets
            text = "<b>📨 История ваших завершенных заявок:</b>\n\n"
        
        for ticket in current_page_tickets:
            text += (
                f"✅\n"
                f"<b>├ Номер заявки:</b> <code>#{ticket[0]}</code>\n"
                f"<b>├ Время создания:</b> {ticket[5]}\n"
                f"<b>├ Сообщение:</b> - <em>{ticket[4]}</em>\n"
                f"<b>└ Комментарий исполнителя:</b> - <em>{ticket[7]}</em>\n\n"
            )
    else:
        text = "🤷‍♂️ Упс.. У вас нет истории заявок."
        
    keyboard_buttons = []
    if len(completed_tickets) > page_size:
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(text="🔙 Предыдущая", callback_data=f"my_ticket_page_{page - 1}"))
        if end_index < len(completed_tickets):
            nav_buttons.append(InlineKeyboardButton(text="🔜 Следующая", callback_data=f"my_ticket_page_{page + 1}"))
        if nav_buttons:
            keyboard_buttons.append(nav_buttons)
    
    keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="my_ticket")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return text, keyboard

def my_company(tg_id):
    user = sql.get_user_by_id(tg_id)
    organization = user.get("organization", "Нет данных")
    organization_address = user.get("organization_adress", "Нет данных")
    organization_inn = user.get("organization_inn", "Нет данных")
    organization_phone = user.get("organization_phone", "Нет данных")
    
    text = (
        f"<b>🏢 Информация о компании</b>\n\n"
        f"<b>📋 Компания:</b> {organization}\n"
        f"<b>📍 Адрес:</b> {organization_address}\n"
        f"<b>📑 ИНН:</b> {organization_inn}\n"
        f"<b>☎️ Контактный номер:</b> <i>{organization_phone}</i>\n\n"
        f"<b>ЗАПОЛНИТЬ ДАННЫЕ О КОМПАНИИ ⬇️</b>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'✅' if organization != 'Нет данных' else '❌'} Наименование компании", callback_data="edit_company_name")],
        [InlineKeyboardButton(text=f"{'✅' if organization_address != 'Нет данных' else '❌'} Фактический адрес", callback_data="edit_company_adress")],
        [InlineKeyboardButton(text=f"{'✅' if organization_inn != 'Нет данных' else '❌'} ИНН", callback_data="edit_company_inn")],
        [InlineKeyboardButton(text=f"{'✅' if organization_phone != 'Нет данных' else '❌'} Контактный номер", callback_data="edit_company_phone")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")]
    ])
    return text, keyboard

def edit_company_name(tg_id):
    text = f"📋 Введите наименование организации.\nПример: <code>ООО РОГА И КОПЫТА</code>"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="my_company")]
    ])
    return text, keyboard

def edit_company_address(tg_id):
    text = f"📍 Введите фактический адрес организации.\nПример: <code>г. Иваново, ул. Варенцовой, д. 33 оф. 1</code>"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="my_company")]
    ])
    return text, keyboard

def edit_company_inn(tg_id):
    text = f"📑 Введите ИНН организации.\nПример: <code>3700010101</code>"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="my_company")]
    ])
    return text, keyboard

def edit_company_phone(tg_id):
    text = f"☎️ Введите контактный номер телефона.\nПример: <code>+79109998188</code>"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="my_company")]
    ])
    return text, keyboard

def done_ticket(tg_id):
    last_ticket_number = sql.get_last_ticket_number()
    text = (
        f'🎉🥳 Успех, ваша заявка зарегистрирована!\n\n'
        f'<b>Номер заявки:</b> <code>#{last_ticket_number}</code>.\n\n'
        f'<i>PS: Отслеживайте статус поставленных задач в разделе</i> <b>"📥 Мои заявки"</b>'
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧑‍💻 Главное меню", callback_data="main_menu")]
    ])
    return text, keyboard

def admin_panel():
    total_open_tickets = sql.get_ticket_count(None, "В работе")
    total_closed_tickets = sql.get_ticket_count(None, "Завершена")
    all_tickets_in_progress = sql.get_all_tickets_in_progress()
    
    text = (
        f"<b>🤘 Тикет меню 💲</b>\n\n"
        f"<b>🔥 Заявок в работе:</b> {total_open_tickets}\n"
        f"<b>👍 Завершенных заявок:</b> {total_closed_tickets}\n\n"
        f"<b>⚠️ Внимание!</b> <i>Закрытые задачи не могут быть возвращены в работу. Пожалуйста, будьте внимательны при их закрытии!</i>"
    )
    
    keyboard_buttons = []
    for ticket in all_tickets_in_progress:
        ticket_info = f"Заявка #{ticket[0]} - {ticket[5]}"
        keyboard_buttons.append([InlineKeyboardButton(text=ticket_info, callback_data=f"ticket_{ticket[0]}")])
    keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return text, keyboard

@dp.callback_query(F.data.startswith('ticket_'))
async def handle_ticket_callback(query: CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    ticket_id = int(query.data.split('_')[1])
    ticket_info = sql.get_ticket_info(ticket_id)
    await state.set_state(UserStates.waiting_for_ticket_comment)
    await state.update_data(ticket_id=ticket_id)
    
    text = (
        f"<b>Детали заявки:</b> <code>#{ticket_info[0]}</code>\n\n"
        f"<b>Пользователь ID:</b> <a href='tg://user?id={ticket_info[1]}'>{ticket_info[1]}</a>\n"
        f"<b>Организация:</b> {ticket_info[2]}\n"
        f"<b>Адрес:</b> {ticket_info[3]}\n\n"
        f"<b>Сообщение от пользователя:</b> - <em>{ticket_info[4]}</em>\n\n"
        f"<b>Время создания:</b> {ticket_info[5]}\n"
        f"<b>Статус:</b> {ticket_info[6]}\n\n"
        f"<em>⚠️ Для завершения задачи введите комментарий. В ответ вам придет сообщение с подтвержением!</em>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")]
    ])
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await query.answer()

@dp.callback_query(F.data.startswith('my_ticket_page_'))
async def handle_ticket_page_callback(query: CallbackQuery):
    page = int(query.data.split('_')[3])
    await query.answer()
    text, keyboard = my_ticket_history(query.from_user.id, page)
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query()
async def inline_kb_answer_callback_handler(query: CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    
    if query.data == 'admin_panel':
        await state.set_state(None)
        await query.answer()
        text, keyboard = admin_panel()
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

    elif query.data == 'main_menu':
        await state.set_state(None)
        await query.answer()
        text, keyboard = main_menu(user_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    elif query.data.startswith('complete_'):
        ticket_id = int(query.data.split('_')[1])
        await query.answer()
        sql.update_ticket_status(ticket_id, "Завершена")
        ticket_comm_done = sql.read_ticket_comment(ticket_id)
        ticket_info = sql.get_ticket_info(ticket_id)
        
        current_time = sql.parse_to_moscow_naive(None)
        time_ticket = sql.parse_to_moscow_naive(ticket_info[5])  
        time_difference = current_time - time_ticket
        hours = int(time_difference.total_seconds() // 3600)

        user_id = ticket_info[1]
        completion_message = (
            f"🎉 Задача <code>#{ticket_id}</code> выполнена!\n"
            f"<b>Время выполнения:</b> {hours} часа(ов).\n\n"
            f"<b>Ответ исполнителя:</b> - <em>{ticket_comm_done}</em>\n\n"
            f"<em>⚠️ Пожалуйста, проверьте корректность исполнения задачи.</em>"
        )
        
        keyboard_markup_user = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="☑️ История заявок", callback_data="my_ticket_history"),
            InlineKeyboardButton(text="🧑‍💻 Главное меню", callback_data="main_menu")]
        ])
        
        keyboard_markup_admin = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤘 Тикет меню", callback_data="admin_panel")]
        ])
        
        await bot.send_message(user_id, completion_message, reply_markup=keyboard_markup_user, parse_mode="HTML")
        await bot.send_message(query.from_user.id, completion_message, reply_markup=keyboard_markup_admin, parse_mode="HTML")
        await state.set_state(None)
        
    elif query.data == 'my_company':
        await state.set_state(None)
        await query.answer()
        text, keyboard = my_company(user_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
       
    elif query.data == 'edit_company_name':
        await state.set_state(UserStates.waiting_for_company_name)
        await query.answer()
        text, keyboard = edit_company_name(user_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    elif query.data == 'edit_company_adress':
        await state.set_state(UserStates.waiting_for_company_address)
        await query.answer()
        text, keyboard = edit_company_address(user_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    elif query.data == 'edit_company_inn':
        await state.set_state(UserStates.waiting_for_company_inn)
        await query.answer()
        text, keyboard = edit_company_inn(user_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    elif query.data == 'edit_company_phone':
        await state.set_state(UserStates.waiting_for_company_phone)
        await query.answer()
        text, keyboard = edit_company_phone(user_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    elif query.data == 'new_ticket':
        await state.set_state(UserStates.waiting_for_ticket_message)
        await query.answer()
        text, keyboard = new_ticket(user_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    elif query.data == 'my_ticket':
        await state.set_state(None)
        await query.answer()
        text, keyboard = my_ticket(user_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    elif query.data == 'my_ticket_history':
        await state.set_state(None)
        await query.answer()
        text, keyboard = my_ticket_history(user_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@dp.message(UserStates.waiting_for_company_name)
async def handle_company_name(message: Message, state: FSMContext):
    sql.update_user_field(message.from_user.id, 'organization', message.text)
    text, keyboard = my_company(message.from_user.id)
    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(None)

@dp.message(UserStates.waiting_for_company_address)
async def handle_company_address(message: Message, state: FSMContext):
    sql.update_user_field(message.from_user.id, 'organization_adress', message.text)
    text, keyboard = my_company(message.from_user.id)
    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(None)

@dp.message(UserStates.waiting_for_company_inn)
async def handle_company_inn(message: Message, state: FSMContext):
    sql.update_user_field(message.from_user.id, 'organization_inn', message.text)
    text, keyboard = my_company(message.from_user.id)
    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(None)

@dp.message(UserStates.waiting_for_company_phone)
async def handle_company_phone(message: Message, state: FSMContext):
    sql.update_user_field(message.from_user.id, 'organization_phone', message.text)
    text, keyboard = my_company(message.from_user.id)
    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(None)

@dp.message(UserStates.waiting_for_ticket_message)
async def handle_ticket_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    user = sql.get_user_by_id(user_id)
    organization = user.get("organization", "Нет данных")
    addres_ticket = user.get("organization_adress", "Нет данных")
    organization_phone = user.get("organization_phone", "Нет данных")
    message_ticket = message.text
    time_ticket_dt = sql.parse_to_moscow_naive(message.date)
    time_ticket = time_ticket_dt.strftime("%Y-%m-%d %H:%M:%S")
    state_ticket = "В работе"
    ticket_comm = ""

    sql.add_ticket(user_id, organization, addres_ticket, message_ticket, time_ticket, state_ticket, ticket_comm)
    last_ticket_number = sql.get_last_ticket_number()

    if last_ticket_number:
        sql.update_user_field(user_id, 'history_ticket', str(last_ticket_number))
        sql.update_user_field(user_id, 'data_ticket', time_ticket)
        sql.update_user_field(user_id, 'user_name', username)
        
        text, keyboard = done_ticket(user_id)
        await message.reply(text, reply_markup=keyboard, parse_mode="HTML")
        
        admin_text = (
            f"📬❗️\nПользователь @{username} создал новую заявку с номером <code>#{last_ticket_number}</code>.\n\n"
            f"<b>Сообщение от пользователя:</b>\n - <em>{message_ticket}</em>\n\n"
            f"<b>Телефон:</b> {organization_phone}\n"
            f"<b>Компания:</b> {organization}\n"
            f"<b>Адрес:</b> {addres_ticket}\n"
        )
        keyboard_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤘 Тикет меню 🫰", callback_data="admin_panel")]
        ])
        await bot.send_message(config.ADMIN_MESSAGE, admin_text, parse_mode="HTML", reply_markup=keyboard_markup)
    else:
        await message.reply("Ошибка при получении заявки.")
    await state.set_state(None)

@dp.message(UserStates.waiting_for_ticket_comment)
async def handle_ticket_comment(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    ticket_id = data.get('ticket_id')
    
    if ticket_id:
        comment_text = message.text
        sql.update_ticket_comment(ticket_id, comment_text)
        
        success_message = (
            f"<b>Комментарий к тикету <code>#{ticket_id}</code> успешно записан!</b>\n\n"
            f"<b>Ответ исполнителя:</b> - <em>{comment_text}</em>\n\n"
            f"<em>⚠️ Если вы допустили ошибку, просто отправьте исправленное сообщение еще раз.</em>"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Завершить задачу", callback_data=f"complete_{ticket_id}")]
        ])
        await message.reply(success_message, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.reply("Ошибка: не указан номер тикета.", parse_mode="HTML")
    # Состояние не сбрасываем, чтобы пользователь мог отправить новый комментарий

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())