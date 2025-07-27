from __future__ import annotations
import os
import re
import time
import json
import sqlite3
import requests
from datetime import datetime
from typing import TYPE_CHECKING
from bs4 import BeautifulSoup
from telebot.types import Message

if TYPE_CHECKING:
    from cardinal import Cardinal

from logging import getLogger

NAME = "LZT Автовыдача"
VERSION = "1.2.0"
DESCRIPTION = "Автоматически выдает аккаунты с lzt.market и коды подтверждения Telegram"
CREDITS = "@byarix"
UUID = "f6c36100-88bc-41c0-98d4-e34f5e9a3fc4"
SETTINGS_PAGE = False

logger = getLogger("FPC.lzt_autodelivery")

# Пути
PLUGIN_STORAGE = f"storage/plugins/{UUID}/"
ACCOUNTS_DB = os.path.join(PLUGIN_STORAGE, "accounts.db")
SETTINGS_FILE = os.path.join(PLUGIN_STORAGE, "settings.json")

DEFAULT_SETTINGS = {
    "admins": [5777052726]
}

# Локализация сообщений
MESSAGES = {
    "no_rights": "❌ У вас нет прав для этой команды.",
    "account_added": "✅ Аккаунт {id} ({country}) добавлен.",
    "account_exists": "⚠️ Аккаунт {id} уже есть в базе.",
    "no_accounts": "❌ Нет доступных аккаунтов.",
    "number_issued": "📱 Ваш номер для Telegram: `{phone}`\n\nОтправьте код подтверждения, когда получите его в Telegram.\nИспользуйте команду /get_code для получения кода.",
    "code_issued": "🔐 Ваш код подтверждения: `{code}`\n\n⚠️ **Важно:**\n• Используйте код только для входа в аккаунт\n• Не передавайте код третьим лицам\n• После входа смените пароль\n\nПодтвердите получение заказа командой /confirm_order",
    "no_code": "❌ Код еще не поступил. Попробуйте позже.",
    "order_confirmed": "✅ Заказ подтвержден!\n\nСпасибо за покупку. Если возникнут вопросы - обращайтесь в поддержку.",
    "list_accounts": "Доступные аккаунты:\n{list}",
    "account_list_empty": "Нет доступных аккаунтов.",
    "active_request": "❌ У вас уже есть активный запрос. Дождитесь завершения.",
    "number_error": "❌ Не удалось получить номер телефона. Попробуйте позже.",
    "account_add_usage": "❌ Использование: /add_account ID [страна]\nПример: /add_account 179560904 RU",
    "account_add_error": "❌ Ошибка добавления аккаунта {id}.",
    "account_add_success": "✅ Аккаунт {id} ({country}) добавлен в базу.",
    "account_add_fail": "❌ Ошибка: {err}",
    "no_active_request": "❌ У вас нет активного запроса. Используйте /get_account.",
    # FunPay сообщения
    "fp_no_accounts": "❌ Нет доступных аккаунтов в базе. Ожидайте оператора.",
    "fp_number_error": "❌ Не удалось получить номер телефона. Попробуйте позже.",
    "fp_number_issued": "📱 Ваш номер для Telegram: {phone}\n\nКогда получите код подтверждения — напишите /код в этот чат.",
    "fp_code_issued": "🔐 Ваш код подтверждения: {code}\n\n⚠️ Важно:\n• Используйте код только для входа в аккаунт\n• Не передавайте код третьим лицам\n• После входа смените пароль",
    "fp_no_code": "❌ Код еще не поступил. Попробуйте позже.",
    "fp_code_command": "Отправляю код подтверждения...",
    # Уведомления для админов
    "notify_account_issued": "✅ Выдан аккаунт {lzt_id} покупателю {buyer} (заказ {order_id})",
    "notify_code_issued": "🔐 Выдан код для аккаунта {lzt_id} покупателю {buyer} (заказ {order_id})",
    "notify_no_accounts": "❌ Нет доступных аккаунтов для выдачи!",
    "notify_number_error": "❌ Не удалось получить номер для аккаунта {lzt_id}",
    "notify_code_error": "❌ Не удалось получить код для аккаунта {lzt_id}",
}

user_requests = {}  # chat_id: {"lzt_id": ..., "phone": ..., "status": ...}
order_requests = {}  # order_id: {"lzt_id": ..., "chat_id": ..., "buyer": ...}

# --- Вспомогательные функции ---
def ensure_storage():
    os.makedirs(PLUGIN_STORAGE, exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4, ensure_ascii=False)

def load_settings():
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def is_admin(chat_id: int) -> bool:
    settings = load_settings()
    return chat_id in settings.get("admins", [])

def notify_admins(cardinal: Cardinal, message: str):
    """Отправляет уведомление всем админам в Telegram"""
    settings = load_settings()
    for admin_id in settings.get("admins", []):
        try:
            cardinal.telegram.bot.send_message(admin_id, message)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")

def init_database():
    conn = sqlite3.connect(ACCOUNTS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            lzt_id TEXT UNIQUE,
            country TEXT,
            status TEXT DEFAULT 'available',
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_account(lzt_id: str, country: str = "RU") -> bool:
    try:
        conn = sqlite3.connect(ACCOUNTS_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT lzt_id FROM accounts WHERE lzt_id = ?", (lzt_id,))
        if cursor.fetchone():
            conn.close()
            return False  # Уже есть
        cursor.execute(
            "INSERT INTO accounts (lzt_id, country, status) VALUES (?, ?, 'available')",
            (lzt_id, country)
        )
        conn.commit()
        conn.close()
        logger.info(f"Добавлен аккаунт: {lzt_id} ({country})")
        return True
    except Exception as e:
        logger.error(f"Ошибка добавления аккаунта {lzt_id}: {e}")
        return None

def get_available_account(country: str = None):
    try:
        conn = sqlite3.connect(ACCOUNTS_DB)
        cursor = conn.cursor()
        if country:
            cursor.execute(
                "SELECT lzt_id, country, phone FROM accounts WHERE status = 'available' AND country = ? LIMIT 1",
                (country,)
            )
        else:
            cursor.execute(
                "SELECT lzt_id, country, phone FROM accounts WHERE status = 'available' LIMIT 1"
            )
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Ошибка получения аккаунта: {e}")
        return None

def mark_account_as_used(lzt_id: str):
    try:
        conn = sqlite3.connect(ACCOUNTS_DB)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE accounts SET status = 'used' WHERE lzt_id = ?",
            (lzt_id,)
        )
        conn.commit()
        conn.close()
        logger.info(f"Аккаунт {lzt_id} помечен как использованный")
        return True
    except Exception as e:
        logger.error(f"Ошибка обновления статуса аккаунта {lzt_id}: {e}")
        return False

def cache_phone_number(lzt_id: str, phone: str):
    try:
        conn = sqlite3.connect(ACCOUNTS_DB)
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET phone = ? WHERE lzt_id = ?", (phone, lzt_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка кэширования номера для {lzt_id}: {e}")

def get_phone_number(lzt_id: str) -> str | None:
    try:
        conn = sqlite3.connect(ACCOUNTS_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM accounts WHERE lzt_id = ?", (lzt_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return row[0]
        # Если не закэшировано — парсим
        url = f"https://lzt.market/{lzt_id}/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        span = soup.find("span", {"id": "loginData--login"})
        if span:
            phone = span.text.strip()
            cache_phone_number(lzt_id, phone)
            logger.info(f"Получен номер {phone} для аккаунта {lzt_id}")
            return phone
        else:
            logger.warning(f"Не найден номер для аккаунта {lzt_id}")
            return None
    except Exception as e:
        logger.error(f"Ошибка получения номера для {lzt_id}: {e}")
        return None

def get_telegram_code(lzt_id: str) -> str | None:
    try:
        url = f"https://lzt.market/{lzt_id}/telegram-login-code"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        today = datetime.now().strftime("%d %b %Y")
        code_blocks = soup.find_all("div", class_="mn-0-0-15")
        for block in code_blocks:
            date_span = block.find("span", class_="DateTime")
            if date_span and date_span.get("title", "").startswith(today):
                input_tag = block.find("input", {"id": "confirmationCode"})
                if input_tag and input_tag.get("value"):
                    code = input_tag["value"]
                    logger.info(f"Получен код {code} для аккаунта {lzt_id}")
                    return code
        logger.warning(f"Не найден код для аккаунта {lzt_id}")
        return None
    except Exception as e:
        logger.error(f"Ошибка получения кода для {lzt_id}: {e}")
        return None

def extract_country_from_description(description: str) -> str | None:
    patterns = [
        r'tg:\s*(\w+)',
        r'страна:\s*(\w+)',
        r'country:\s*(\w+)',
        r'(\w{2,3})',
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            country = match.group(1).upper()
            logger.info(f"Извлечена страна: {country} из описания")
            return country
    return None

# --- Telegram команды (для админов) ---
def cmd_add_account(m: Message, cardinal: Cardinal):
    bot = cardinal.telegram.bot
    chat_id = m.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, MESSAGES["no_rights"])
        return
    try:
        parts = m.text.split()
        if len(parts) < 2:
            bot.send_message(chat_id, MESSAGES["account_add_usage"])
            return
        lzt_id = parts[1]
        country = parts[2] if len(parts) > 2 else "RU"
        result = add_account(lzt_id, country)
        if result is True:
            bot.send_message(chat_id, MESSAGES["account_add_success"].format(id=lzt_id, country=country))
        elif result is False:
            bot.send_message(chat_id, MESSAGES["account_exists"].format(id=lzt_id))
        else:
            bot.send_message(chat_id, MESSAGES["account_add_error"].format(id=lzt_id))
    except Exception as e:
        logger.error(f"Ошибка добавления аккаунта: {e}")
        bot.send_message(chat_id, MESSAGES["account_add_fail"].format(err=str(e)))

def cmd_list_accounts(m: Message, cardinal: Cardinal):
    bot = cardinal.telegram.bot
    chat_id = m.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, MESSAGES["no_rights"])
        return
    try:
        conn = sqlite3.connect(ACCOUNTS_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT lzt_id, country, status FROM accounts WHERE status = 'available'")
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            bot.send_message(chat_id, MESSAGES["account_list_empty"])
            return
        acc_list = "\n".join([f"ID: {row[0]}, Страна: {row[1]}, Статус: {row[2]}" for row in rows])
        bot.send_message(chat_id, MESSAGES["list_accounts"].format(list=acc_list))
    except Exception as e:
        logger.error(f"Ошибка вывода списка аккаунтов: {e}")
        bot.send_message(chat_id, f"Ошибка: {e}")

# --- FunPay обработчики ---
def on_new_order(cardinal: Cardinal, event):
    """Обработчик новых заказов на FunPay"""
    try:
        order = event.order
        chat_id = order.chat_id
        buyer = order.buyer_username
        order_id = order.id
        
        # Получаем описание товара
        description = ""
        if hasattr(order, 'full_description') and order.full_description:
            description = order.full_description
        elif hasattr(order, 'description') and order.description:
            description = order.description
        
        # Извлекаем страну из описания
        country = extract_country_from_description(description)
        if not country:
            logger.info(f"Страна не найдена в описании заказа {order_id}, пропускаем")
            return
        
        # Получаем доступный аккаунт
        account_data = get_available_account(country)
        if not account_data:
            cardinal.send_message(chat_id, MESSAGES["fp_no_accounts"])
            notify_admins(cardinal, MESSAGES["notify_no_accounts"])
            return
        
        lzt_id, account_country, phone = account_data
        
        # Получаем номер телефона
        if not phone:
            phone = get_phone_number(lzt_id)
        
        if not phone:
            cardinal.send_message(chat_id, MESSAGES["fp_number_error"])
            notify_admins(cardinal, MESSAGES["notify_number_error"].format(lzt_id=lzt_id))
            return
        
        # Сохраняем связь заказа с аккаунтом
        order_requests[order_id] = {
            "lzt_id": lzt_id,
            "chat_id": chat_id,
            "buyer": buyer,
            "country": account_country
        }
        
        # Отправляем номер покупателю
        cardinal.send_message(chat_id, MESSAGES["fp_number_issued"].format(phone=phone))
        
        # Уведомляем админов
        notify_admins(cardinal, MESSAGES["notify_account_issued"].format(
            lzt_id=lzt_id, buyer=buyer, order_id=order_id
        ))
        
        logger.info(f"Выдан аккаунт {lzt_id} покупателю {buyer} (заказ {order_id})")
        
    except Exception as e:
        logger.error(f"Ошибка обработки нового заказа: {e}")

def on_new_message(cardinal: Cardinal, event):
    """Обработчик новых сообщений в FunPay-чатах"""
    try:
        message = event.message
        chat_id = message.chat_id
        text = message.text.strip().lower() if message.text else ""
        
        # Проверяем команду /код
        if text == '/код':
            # Ищем заказ для этого чата
            order_id = None
            for oid, req in order_requests.items():
                if req["chat_id"] == chat_id:
                    order_id = oid
                    break
            
            if not order_id:
                cardinal.send_message(chat_id, "❌ У вас нет активного заказа с аккаунтом.")
                return
            
            req = order_requests[order_id]
            lzt_id = req["lzt_id"]
            buyer = req["buyer"]
            
            # Получаем код
            code = get_telegram_code(lzt_id)
            if not code:
                cardinal.send_message(chat_id, MESSAGES["fp_no_code"])
                return
            
            # Отправляем код покупателю
            cardinal.send_message(chat_id, MESSAGES["fp_code_issued"].format(code=code))
            
            # Помечаем аккаунт как использованный
            mark_account_as_used(lzt_id)
            
            # Уведомляем админов
            notify_admins(cardinal, MESSAGES["notify_code_issued"].format(
                lzt_id=lzt_id, buyer=buyer, order_id=order_id
            ))
            
            # Удаляем связь заказа
            del order_requests[order_id]
            
            logger.info(f"Выдан код для аккаунта {lzt_id} покупателю {buyer} (заказ {order_id})")
            
    except Exception as e:
        logger.error(f"Ошибка обработки нового сообщения: {e}")

# --- Устаревшие Telegram команды (оставляем для совместимости) ---
def cmd_get_account(m: Message, cardinal: Cardinal):
    bot = cardinal.telegram.bot
    chat_id = m.chat.id
    if chat_id in user_requests:
        bot.send_message(chat_id, MESSAGES["active_request"])
        return
    country = None
    if hasattr(m, 'text') and m.text:
        country = extract_country_from_description(m.text)
    account_data = get_available_account(country)
    if not account_data:
        bot.send_message(chat_id, MESSAGES["no_accounts"])
        return
    lzt_id, account_country, phone = account_data
    if not phone:
        phone = get_phone_number(lzt_id)
    if not phone:
        bot.send_message(chat_id, MESSAGES["number_error"])
        return
    user_requests[chat_id] = {
        "lzt_id": lzt_id,
        "phone": phone,
        "status": "waiting_code",
        "country": account_country
    }
    bot.send_message(
        chat_id,
        MESSAGES["number_issued"].format(phone=phone),
        parse_mode='Markdown'
    )
    logger.info(f"Выдан аккаунт {lzt_id} пользователю {chat_id}")

def cmd_get_code(m: Message, cardinal: Cardinal):
    bot = cardinal.telegram.bot
    chat_id = m.chat.id
    if chat_id not in user_requests:
        bot.send_message(chat_id, MESSAGES["no_active_request"])
        return
    user_data = user_requests[chat_id]
    lzt_id = user_data["lzt_id"]
    code = get_telegram_code(lzt_id)
    if not code:
        bot.send_message(chat_id, MESSAGES["no_code"])
        return
    mark_account_as_used(lzt_id)
    bot.send_message(
        chat_id,
        MESSAGES["code_issued"].format(code=code),
        parse_mode='Markdown'
    )
    user_requests.pop(chat_id, None)
    logger.info(f"Выдан код {code} пользователю {chat_id} для аккаунта {lzt_id}")

def cmd_confirm_order(m: Message, cardinal: Cardinal):
    bot = cardinal.telegram.bot
    chat_id = m.chat.id
    bot.send_message(chat_id, MESSAGES["order_confirmed"])
    logger.info(f"Заказ подтвержден пользователем {chat_id}")

def init_plugin(cardinal: Cardinal, *args):
    ensure_storage()
    init_database()
    bot = cardinal.telegram.bot
    cardinal.add_telegram_commands(UUID, [
        ("add_account", "Добавить аккаунт в базу (админ)", True),
        ("list_accounts", "Список доступных аккаунтов (админ)", True),
        ("get_account", "Получить аккаунт (устарело)", True),
        ("get_code", "Получить код подтверждения (устарело)", True),
        ("confirm_order", "Подтвердить заказ (устарело)", True),
    ])
    @bot.message_handler(commands=["add_account"])
    def add_account_cmd(m: Message):
        cmd_add_account(m, cardinal)
    @bot.message_handler(commands=["list_accounts"])
    def list_accounts_cmd(m: Message):
        cmd_list_accounts(m, cardinal)
    @bot.message_handler(commands=["get_account"])
    def get_account_cmd(m: Message):
        cmd_get_account(m, cardinal)
    @bot.message_handler(commands=["get_code"])
    def get_code_cmd(m: Message):
        cmd_get_code(m, cardinal)
    @bot.message_handler(commands=["confirm_order"])
    def confirm_order_cmd(m: Message):
        cmd_confirm_order(m, cardinal)
    logger.info(f"[{NAME}] Плагин инициализирован")

BIND_TO_PRE_INIT = [init_plugin]
BIND_TO_NEW_ORDER = [on_new_order]
BIND_TO_NEW_MESSAGE = [on_new_message]
BIND_TO_DELETE = None 