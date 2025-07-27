from __future__ import annotations
from typing import TYPE_CHECKING, Any
import os
import re
import json
import time
import random
import string
import logging
from pathlib import Path

from telebot.types import Message  
from telebot import Bot

if TYPE_CHECKING:
    from cardinal import Cardinal

from FunPayAPI.account import Account
from FunPayAPI.types import UserProfile, LotShortcut, LotPage

NAME = "Авто-Копирование"
VERSION = "1.0"
DESCRIPTION = "Копирует публичные лоты (RU+EN) с чужого профиля."
CREDITS = "@exfador"
UUID = "96b3d870-4bda-4025-9d46-d14a460ade30"
SETTINGS_PAGE = False

logger = logging.getLogger("FPC.auto_copy")

STATE_WAIT_LINK = "AC_WAIT_LINK"
user_data: dict[int, dict[str, Any]] = {}

def random_filename(username: str) -> str:
    """
    Возвращает имя файла вида {username}_{timestamp}_{rnd}.json
    
    Параметры:
        username (str): Имя пользователя для включения в имя файла
        
    Возвращает:
        str: Уникальное имя файла
    """
    t = int(time.time())
    r = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"{username}_{t}_{r}.json"

def extract_user_id(link: str) -> int | None:
    """
    Извлекает ID пользователя из ссылки FunPay.
    
    Параметры:
        link (str): Ссылка на профиль FunPay
        
    Возвращает:
        int | None: ID пользователя или None если не найден
    """
    pattern = re.compile(r"https?://funpay\.com/users/(\d+)/?")
    m = pattern.search(link)
    if m:
        return int(m.group(1))
    return None

def set_locale(acc: Account, locale: str) -> None:
    """
    Устанавливает локаль и обновляет аккаунт.
    
    Параметры:
        acc (Account): Аккаунт FunPay
        locale (str): Локаль для установки
    """
    acc.locale = locale
    acc.get()

def build_json_for_lot(acc: Account, lot: LotShortcut) -> dict[str, str]:
    """
    Строит JSON-структуру для лота с данными на двух языках.
    
    Параметры:
        acc (Account): Аккаунт FunPay
        lot (LotShortcut): Краткая информация о лоте
        
    Возвращает:
        dict[str, str]: JSON-структура лота
    """
    set_locale(acc, "ru")
    short_ru, desc_ru = "No RU short", "No RU full"
    try:
        pr = acc.get_lot_page(lot.id, locale="ru")
        short_ru = pr.short_description or lot.description or "No RU short"
        desc_ru = pr.full_description or "No RU full"
    except Exception as e:
        logger.warning(f"get_lot_page RU error for lot {lot.id}: {e}")

    set_locale(acc, "en")
    short_en, desc_en = "No EN short", "No EN full"
    try:
        pe = acc.get_lot_page(lot.id, locale="en")
        short_en = pe.short_description or "No EN short"
        desc_en = pe.full_description or "No EN full"
    except Exception as e:
        logger.warning(f"get_lot_page EN error for lot {lot.id}: {e}")

    set_locale(acc, "ru")

    price_ = lot.price or 0.0
    price_str = f"{price_:.6f}"
    node_id = lot.subcategory.id if lot.subcategory else 0
    sc_name_ru = lot.subcategory.name if lot.subcategory else "???"

    return {
        "query": "",
        "form_created_at": str(int(time.time())),
        "node_id": str(node_id),
        "location": "",
        "deleted": "",
        "fields[summary][ru]": short_ru,
        "fields[summary][en]": short_en,
        "fields[images]": "",
        "price": price_str,
        "amount": "999999",
        "active": "on",
        "fields[desc][ru]": desc_ru,
        "fields[desc][en]": desc_en,
        "fields[payment_msg][ru]": "",
        "fields[payment_msg][en]": "",
        "fields[type]": sc_name_ru
    }

def export_to_json(bot: Bot, chat_id: int, data: list[dict[str, str]], username: str) -> None:
    """
    Сохраняет данные в JSON и отправляет файл.
    
    Параметры:
        bot (Bot): Экземпляр Telegram бота
        chat_id (int): ID чата для отправки
        data (list[dict[str, str]]): Данные для экспорта
        username (str): Имя пользователя для имени файла
    """
    if not data:
        bot.send_message(chat_id, "❗ Нет лотов для экспорта (пустой список).")
        return
    
    filename = random_filename(username)
    cache_dir = Path("storage") / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    file_path = cache_dir / filename

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка при записи JSON в файл {file_path}: {e}")
        bot.send_message(chat_id, f"⚠️ Ошибка при создании файла экспорта: {e}")
        return

    try:
        with open(file_path, "rb") as f:
            bot.send_document(chat_id, f, caption=f"✅ Выгружено {len(data)} лот(ов).")
        
        # Удаляем временный файл после отправки
        try:
            file_path.unlink()
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл {file_path}: {e}")
            
    except Exception as e:
        logger.error(f"Ошибка при отправке файла {file_path}: {e}")
        bot.send_message(chat_id, f"⚠️ Ошибка при отправке файла экспорта: {e}")

def cmd_steal_lots(m: Message, cardinal: Cardinal) -> None:
    """
    Обрабатывает команду /steal_lots и начинает процесс.
    
    Параметры:
        m (Message): Telegram сообщение
        cardinal (Cardinal): Экземпляр Cardinal
    """
    bot = cardinal.telegram.bot
    chat_id = m.chat.id
    user_data[chat_id] = {"step": STATE_WAIT_LINK}
    bot.send_message(
        chat_id,
        "🔎 Пришлите ссылку на профиль FunPay, с которого копировать лоты.\n"
        "Например: https://funpay.com/users/11506286/\n\n"
        "/cancel — отмена."
    )
    logger.info(f"[Авто-Копирование] Пользователь {chat_id} начал процесс копирования.")

def cmd_cancel(m: Message) -> None:
    """
    Обрабатывает команду /cancel и отменяет текущий процесс.
    
    Параметры:
        m (Message): Telegram сообщение
    """
    bot = m.bot
    chat_id = m.chat.id
    if chat_id in user_data:
        user_data.pop(chat_id, None)
        bot.send_message(chat_id, "🚫 Действие отменено.")
        logger.info(f"[Авто-Копирование] Пользователь {chat_id} отменил процесс.")
    else:
        bot.send_message(chat_id, "🚫 Нет активного процесса для отмены.")

def handle_text(m: Message, cardinal: Cardinal) -> None:
    """
    Обрабатывает текстовые сообщения от пользователя.
    
    Параметры:
        m (Message): Telegram сообщение
        cardinal (Cardinal): Экземпляр Cardinal
    """
    bot = cardinal.telegram.bot
    chat_id = m.chat.id

    if chat_id not in user_data:
        return

    step = user_data[chat_id]["step"]
    if step == STATE_WAIT_LINK:
        link_ = m.text.strip()
        user_id = extract_user_id(link_)
        if not user_id:
            bot.send_message(chat_id, "❗ Не удалось извлечь ID из ссылки. /cancel — отмена.")
            logger.warning(f"[Авто-Копирование] Пользователь {chat_id} прислал некорректную ссылку: {link_}")
            user_data.pop(chat_id, None)
            return

        try:
            set_locale(cardinal.account, "ru")
            profile = cardinal.account.get_user(user_id)
            logger.info(f"[Авто-Копирование] Получен профиль пользователя {user_id} (чат {chat_id}).")
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ Ошибка get_user({user_id}): {e}")
            logger.error(f"[Авто-Копирование] Ошибка get_user({user_id}) для чата {chat_id}: {e}")
            user_data.pop(chat_id, None)
            return

        lots = list(profile.get_lots())
        logger.info(f"[Авто-Копирование] Найдено {len(lots)} лотов у пользователя {user_id} (чат {chat_id}).")
        if not lots:
            bot.send_message(chat_id, "🙁 У пользователя нет публичных лотов.")
            logger.info(f"[Авто-Копирование] У пользователя {user_id} нет публичных лотов (чат {chat_id}).")
            user_data.pop(chat_id, None)
            return

        bot.send_message(chat_id, f"⏳ Обрабатываю {len(lots)} лотов, пожалуйста, подождите...")
        out_list = []
        
        for i, lot in enumerate(lots, 1):
            logger.info(f"[Авто-Копирование] Обрабатывается лот {lot.id} ({i}/{len(lots)})...")

            # Уменьшаем задержку для лучшей производительности
            delay = random.uniform(5, 15)
            time.sleep(delay)

            try:
                out_list.append(build_json_for_lot(cardinal.account, lot))
            except Exception as e:
                logger.error(f"Ошибка при обработке лота {lot.id}: {e}")

        export_to_json(bot, chat_id, out_list, profile.username)
        logger.info(f"[Авто-Копирование] Пользователь {chat_id} выгрузил все лоты.")
        user_data.pop(chat_id, None)

def pingtest_cmd(m: Message, cardinal: Cardinal) -> None:
    """
    Тестовый хендлер для проверки работы бота.
    
    Параметры:
        m (Message): Telegram сообщение
        cardinal (Cardinal): Экземпляр Cardinal
    """
    bot = cardinal.telegram.bot
    chat_id = m.chat.id
    bot.send_message(chat_id, "🏓 Pong!")
    logger.info(f"[Авто-Копирование] Пользователь {chat_id} выполнил /pingtest.")

def init_plugin(cardinal: Cardinal, *args: Any) -> None:
    """
    Инициализирует плагин.
    
    Параметры:
        cardinal (Cardinal): Экземпляр Cardinal
        *args: Дополнительные аргументы
    """
    bot = cardinal.telegram.bot

    cardinal.add_telegram_commands(UUID, [
        ("steal_lots", "🤖 Авто-Копирование лотов (RU+EN)", True),
        ("cancel", "🚫 Отмена", True),
    ])

    @bot.message_handler(commands=["steal_lots"])
    def steal_cmd(m: Message) -> None:
        cmd_steal_lots(m, cardinal)

    @bot.message_handler(commands=["cancel"])
    def cancel_cmd(m: Message) -> None:
        cmd_cancel(m)

    @bot.message_handler(content_types=["text"])
    def text_msgs(m: Message) -> None:
        handle_text(m, cardinal)

BIND_TO_PRE_INIT = [init_plugin]
BIND_TO_DELETE = None
