from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Настройка веб-драйвера Chrome"""
        chrome_options = Options()
        
        # Опции для стабильной работы
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Инициализация драйвера
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)
        
        logger.info("Веб-драйвер успешно инициализирован")
        
    def navigate_to_bot(self):
        """Переход к боту"""
        url = "https://web.telegram.org/k/#@FunPayAssistantBot"
        logger.info(f"Переходим по адресу: {url}")
        
        try:
            self.driver.get(url)
            logger.info("Страница загружена")
            
            # Ждем загрузки страницы
            time.sleep(5)
            
            # Ждем появления поля ввода сообщения
            message_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )
            logger.info("Поле ввода сообщения найдено")
            
            return message_input
            
        except Exception as e:
            logger.error(f"Ошибка при переходе к боту: {e}")
            return None
    
    def send_message(self, message_input, message):
        """Отправка сообщения"""
        try:
            # Очищаем поле ввода
            message_input.clear()
            
            # Вводим сообщение
            message_input.send_keys(message)
            time.sleep(0.5)
            
            # Отправляем сообщение (Enter)
            message_input.send_keys(Keys.ENTER)
            
            logger.info(f"Сообщение отправлено: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            return False
    
    def run_automation(self):
        """Основная функция автоматизации"""
        try:
            logger.info("Запуск автоматизации Telegram бота")
            
            # Настройка драйвера
            self.setup_driver()
            
            # Переход к боту
            message_input = self.navigate_to_bot()
            
            if not message_input:
                logger.error("Не удалось найти поле ввода сообщения")
                return
            
            # Основной цикл отправки сообщений
            message = "/delete_lots"
            counter = 0
            
            logger.info(f"Начинаем отправку сообщений '{message}' каждую секунду")
            
            while True:
                try:
                    counter += 1
                    success = self.send_message(message_input, message)
                    
                    if success:
                        logger.info(f"Сообщение #{counter} отправлено успешно")
                    else:
                        logger.warning(f"Ошибка при отправке сообщения #{counter}")
                    
                    # Пауза 1 секунда
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    logger.info("Автоматизация остановлена пользователем")
                    break
                except Exception as e:
                    logger.error(f"Неожиданная ошибка: {e}")
                    time.sleep(5)  # Пауза перед повторной попыткой
                    
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
        finally:
            if self.driver:
                logger.info("Закрытие браузера")
                self.driver.quit()

def main():
    """Главная функция"""
    print("=" * 50)
    print("Telegram Bot Automation Script")
    print("=" * 50)
    print("Скрипт будет:")
    print("1. Открывать Telegram Web")
    print("2. Переходить к @FunPayAssistantBot")
    print("3. Отправлять '/delete_lots' каждую секунду")
    print("=" * 50)
    print("Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    bot = TelegramBot()
    bot.run_automation()

if __name__ == "__main__":
    main()
