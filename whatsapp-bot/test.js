const axios = require('axios');

async function testWhatsAppAPI() {
    try {
        // Тест 1: Проверка статуса
        console.log('🔍 Проверка статуса сервера...');
        const statusResponse = await axios.get('http://localhost:3000/status');
        console.log('✅ Статус сервера:', statusResponse.data);
        
        // Тест 2: Отправка тестового сообщения
        console.log('\n📱 Отправка тестового сообщения...');
        const testNumber = '996999999999'; // Замените на реальный номер для тестирования
        const testMessage = '🧪 Тестовое сообщение от WhatsApp Bot\n\nЭто сообщение отправлено для проверки работы API.';
        
        const sendResponse = await axios.post('http://localhost:3000/send', {
            number: testNumber,
            message: testMessage
        });
        
        console.log('✅ Результат отправки:', sendResponse.data);
        
    } catch (error) {
        console.error('❌ Ошибка:', error.response?.data || error.message);
    }
}

// Запускаем тест
testWhatsAppAPI(); 