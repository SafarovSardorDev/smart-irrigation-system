# 💧 Smart Irrigation System

**Smart Irrigation System** — bu tuproq namligini avtomatik tarzda o‘lchovchi va suvni faqat kerak bo‘lganda uzatadigan aqlli sug‘orish tizimi. Ushbu loyiha orqali suv resurslarini tejash, hosildorlikni oshirish va zamonaviy qishloq xo‘jaligini targ‘ib qilish maqsad qilingan.

---

## 🎯 Loyiha Maqsadi

- Sug‘orish jarayonini avtomatlashtirish orqali suvdan oqilona foydalanish
- Dehqon va fermerlar uchun qulay, tejamkor monitoring va boshqaruv vositasini taqdim etish
- Atrof-muhitga zarar yetkazmasdan hosildorlikni oshirish

---

## ⚙️ Texnologiyalar

- **Mikrokontroller**: Arduino UNO / ESP32  
- **Sensorlar**: YL-69 (tuproq namligi), DHT11 (iqlim)  
- **Nasos va Rele**: Sug‘orish tizimini avtomatik boshqarish  
- **Dasturlash**: C/C++ (Arduino IDE)  
- **Ma'lumot uzatish (ixtiyoriy)**: Wi-Fi moduli (ESP8266/ESP32) orqali Telegram, web yoki mobil ilova integratsiyasi

---

## 📦 Asosiy funksiyalar

- 🌡️ **Tuproq namligini real vaqtli kuzatish**
- 🚿 **Avtomatik nasos boshqaruvi** (threshold asosida)
- ☁️ **Ob-havo prognozi asosida optimallashtirish** (ixtiyoriy)
- 📲 **Telegram yoki Web orqali monitoring** (ixtiyoriy)
- 🔋 **Quyosh panelli quvvat tizimi bilan moslashuvchanlik**

---

### 🔐 Foydalanuvchi Turlari

- **Fermer**: Qurilmani joylashtirib, sug‘orishni avtomatik qilish
- **Texnik shaxslar**: Monitoring va tizimni sozlash
- **Admin (ixtiyoriy holatlarda)**: Telegram yoki Web monitoring platformani kuzatish

---

## 🚀 Kelajakdagi Rivojlanishlar

- Mobil ilova (Android) orqali monitoring va ogohlantirishlar  
- Push xabarnomalar va statistik ma’lumotlar vizualizatsiyasi  
- GPS orqali har bir qurilmaning joylashuvini aniqlash  
- Sug‘orish ma’lumotlarini ma’lumotlar bazasiga yig‘ish

---

## 🚀 Ishga tushirish
1. Klonlash:
```bash
git clone https://github.com/SafarovSardorDev/smart-irrigation-system
cd smart-irrigation-system
```

### 2. Virtual muhit va kutubxonalarni o‘rnatish:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

### 4. Serverni ishga tushirish:
```bash
python manage.py runserver
```

### Brauzerda Platformani ochish:
- Brauzerda http://127.0.0.1:8000/ manziliga o'ting (yoki frontendning localhost portiga). 🌐
- Platforma ishga tushganini va barcha funksiyalarni sinab ko'ring. 🧑‍💻

### 5. Arduino IDE orqali:
-smart_irrigation.ino faylini oching
-Qurilmani USB orqali ulang
-COM portni tanlang va kodni yuklang

### 6. Qurilmani ulash:
-Sensor va nasosni tegishli pinlarga ulang (sxema asosida)
-Qurilmani ishga tushiring

## 👤 Muallif
 
Created by AutoNomous team ✨
Our Team Telegram Channel: [AutoNomousTeam](https://t.me/autonomous_flight_technologies)
Telegram: [@imsafarov](https://t.me/imsafarov)

###📜 Litsenziya
This project is licensed under the MIT License - see the LICENSE file for details. 📝

Copyright (c) 2025 Sardor
