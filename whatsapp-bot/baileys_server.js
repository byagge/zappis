const { default: makeWASocket, DisconnectReason } = require('@whiskeysockets/baileys');
const { useMultiFileAuthState } = require('@whiskeysockets/baileys/lib/Utils/use-multi-file-auth-state');
const express = require('express');
const qrcode = require('qrcode-terminal');
const app = express();

app.use(express.json());

let sock;
let authState;

async function startSock() {
    authState = await useMultiFileAuthState('./auth');
    
    sock = makeWASocket({ 
        auth: authState.state, 
        defaultQueryTimeoutMs: undefined
    });

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr) {
            console.log('QR Code received:');
            qrcode.generate(qr, { small: true });
        }
        
        if (connection === 'close') {
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            if (shouldReconnect) startSock();
        }
        
        if (connection === 'open') {
            console.log('Connected to WhatsApp!');
        }
    });

    sock.ev.on('creds.update', authState.saveCreds);
}

startSock();

// Функция для форматирования номера телефона
function formatPhoneNumber(number) {
    // Убираем все нецифровые символы
    let cleanNumber = number.replace(/\D/g, '');
    
    // Если номер начинается с 996, оставляем как есть
    if (cleanNumber.startsWith('996')) {
        return cleanNumber;
    }
    
    // Если номер начинается с 0, заменяем на 996
    if (cleanNumber.startsWith('0')) {
        return '996' + cleanNumber.substring(1);
    }
    
    // Если номер 9 цифр (без кода страны), добавляем 996
    if (cleanNumber.length === 9) {
        return '996' + cleanNumber;
    }
    
    // Если номер 10 цифр (с кодом страны), добавляем 996
    if (cleanNumber.length === 10) {
        return '996' + cleanNumber;
    }
    
    return cleanNumber;
}

app.post('/send', async (req, res) => {
    const { number, message } = req.body;
    
    if (!number || !message) {
        return res.status(400).send({ 
            status: 'error', 
            message: 'Number and message are required' 
        });
    }
    
    try {
        // Форматируем номер телефона
        const formattedNumber = formatPhoneNumber(number);
        const jid = `${formattedNumber}@s.whatsapp.net`;
        
        console.log(`📱 Отправка WhatsApp сообщения:`);
        console.log(`   Номер: ${number} -> ${formattedNumber}`);
        console.log(`   JID: ${jid}`);
        console.log(`   Сообщение: ${message.substring(0, 50)}...`);
        
        await sock.sendMessage(jid, { text: message });
        
        console.log(`✅ WhatsApp сообщение успешно отправлено на ${formattedNumber}`);
        res.send({ 
            status: 'sent', 
            original_number: number,
            formatted_number: formattedNumber,
            jid: jid
        });
        
    } catch (e) {
        console.error(`❌ Ошибка отправки WhatsApp сообщения:`, e);
        res.status(500).send({ 
            status: 'error', 
            message: e.toString(),
            original_number: number
        });
    }
});

// Добавляем endpoint для проверки статуса подключения
app.get('/status', (req, res) => {
    res.send({ 
        status: 'connected',
        whatsapp_connected: sock && sock.user ? true : false,
        user: sock && sock.user ? sock.user : null
    });
});

app.listen(3000, () => console.log('Baileys API is running on port 3000'));
