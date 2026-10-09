#!/usr/bin/env python3
"""
Telegram-бот для мастерской свечей LUMIÈRE (Анжела Бачерикова, г. Киров).
Принимает заказы с сайта и рассылает их:
1) Владельцу (тебе) для мониторинга и тестов
2) Анжеле в личку для приёма и обработки
"""

import sys
import os
import json
import time
import urllib.request
import urllib.parse

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "bot_config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка чтения config: {e}")
    return {
        "bot_token": "",
        "owner_chat_id": "",
        "angela_chat_id": "",
        "master_name": "Бачерикова Анжела Александровна",
        "city": "Киров"
    }

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def api_call(token, method, data=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    if data:
        json_data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=json_data, headers={"Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        print(f"HTTP Error {e.code}: {error_body}")
        return None
    except Exception as e:
        print(f"Ошибка вызова Telegram API: {e}")
        return None

def send_message(token, chat_id, text):
    if not chat_id:
        return False
    res = api_call(token, "sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })
    return res and res.get("ok", False)

def format_order_message(order_data):
    order_id = order_data.get("order_id", "LK-TEST")
    client_name = order_data.get("name", "Екатерина")
    phone = order_data.get("phone", "+7 (912) 820-00-00")
    tg = order_data.get("tg", "@test_user")
    address = order_data.get("address", "г. Киров, Октябрьский пр-т, 24")
    shipping = order_data.get("shipping", "Самовывоз в г. Киров (Бесплатно)")
    comment = order_data.get("comment", "Подарочная открытка")
    items = order_data.get("items", [
        {"name": "Свеча «Кашемир & Теплая Ваниль» (200 мл)", "qty": 1, "price": 1490},
        {"name": "Овальный поднос из гипса «L'Ovale»", "qty": 1, "price": 590}
    ])
    total = order_data.get("total", 2080)
    date_str = time.strftime("%d.%m.%Y %H:%M")

    items_text = "\n".join([
        f"{i+1}. <b>{it['name']}</b> — {it['qty']} шт. × {it['price']} ₽ = <b>{it['qty'] * it['price']} ₽</b>"
        for i, it in enumerate(items)
    ])

    return (
        f"🕯 <b>НОВЫЙ ЗАКАЗ С САЙТА #{order_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Клиент:</b> {client_name}\n"
        f"📞 <b>Телефон:</b> <code>{phone}</code>\n"
        f"✈️ <b>Telegram:</b> {tg}\n"
        f"📍 <b>Адрес / ПВЗ:</b> {address}\n"
        f"🚚 <b>Доставка:</b> {shipping}\n"
        f"💌 <b>Пожелание:</b> {comment}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Состав заказа:</b>\n{items_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Итого к оплате:</b> <b>{total:,} ₽</b>\n"
        f"🕒 <i>{date_str}</i>"
    )

def send_test_order(cfg):
    token = cfg.get("bot_token")
    if not token:
        print("❌ Ошибка: В bot_config.json не указан bot_token!")
        return

    test_data = {
        "order_id": "LK-TEST",
        "name": "Елена (Тестовый заказ)",
        "phone": "+7 (912) 820-11-22",
        "tg": "@elena_kirov",
        "address": "г. Киров, ул. Ленина, 105",
        "shipping": "Курьер по Кирову (Яндекс Доставка, 250 ₽)",
        "comment": "Тестовое сообщение о заказе для проверки работы бота",
        "items": [
            {"name": "Свеча «Кашемир & Теплая Ваниль» (200 мл)", "qty": 1, "price": 1490},
            {"name": "Овальный поднос из гипса «L'Ovale»", "qty": 1, "price": 590}
        ],
        "total": 2330
    }
    msg = format_order_message(test_data)

    recipients = []
    if cfg.get("owner_chat_id"):
        recipients.append(("Владелец", cfg["owner_chat_id"]))
    if cfg.get("angela_chat_id"):
        recipients.append(("Анжела (мастер)", cfg["angela_chat_id"]))

    if not recipients:
        print("⚠️ Ни один chat_id пока не зарегистрирован! Запусти бота и напиши ему /start.")
        return

    for role, chat_id in recipients:
        ok = send_message(token, chat_id, msg)
        status = "✅ доставлено" if ok else "❌ ошибка отправки"
        print(f"Отправка тестового заказа ({role}, id {chat_id}): {status}")

def run_polling(cfg):
    token = cfg.get("bot_token")
    if not token:
        print("="*60)
        print("⚠️ ВНИМАНИЕ: Не указан токен бота в bot_config.json!")
        print("1. Открой Telegram и напиши боту @BotFather")
        print("2. Введи команду /newbot и выбери имя (например, LumiereCandlesKirovBot)")
        print("3. Скопируй полученный токен и запиши в bot_config.json или укажи через аргументы.")
        print("="*60)
        token = input("Введите токен бота (или Enter для выхода): ").strip()
        if not token:
            return
        cfg["bot_token"] = token
        save_config(cfg)

    bot_info = api_call(token, "getMe")
    if not bot_info or not bot_info.get("ok"):
        print("❌ Неверный токен бота. Проверьте правильность токена.")
        return

    bot_username = bot_info["result"]["username"]
    print("="*60)
    print(f"✅ Бот @{bot_username} успешно запущен!")
    print(f"Ссылка на бота: https://t.me/{bot_username}")
    print("Команды в чате бота:")
    print("  /start    — Регистрация (выбор роли: Владелец / Анжела)")
    print("  /test     — Отправить тестовый заказ всем зарегистрированным")
    print("  /status   — Проверить текущий статус и подключенные чаты")
    print("="*60)

    last_update_id = 0
    while True:
        try:
            updates = api_call(token, "getUpdates", {
                "offset": last_update_id + 1,
                "timeout": 15
            })
            if updates and updates.get("ok"):
                for u in updates.get("result", []):
                    last_update_id = u["update_id"]
                    msg = u.get("message")
                    if not msg:
                        continue
                    
                    chat_id = str(msg["chat"]["id"])
                    text = msg.get("text", "").strip()
                    user_first_name = msg["from"].get("first_name", "Гость")
                    user_username = msg["from"].get("username", "")

                    if text.startswith("/start"):
                        welcome_text = (
                            f"👋 Здравствуйте, <b>{user_first_name}</b>!\n\n"
                            f"Это бот заказов мастерской <b>LUMIÈRE | Авторские свечи</b> (г. Киров).\n\n"
                            f"Ваш Telegram Chat ID: <code>{chat_id}</code>\n\n"
                            f"Чтобы настроить получение заказов:\n"
                            f"• Отправьте <code>/im_owner</code> — зарегистрироваться как Владелец (тесты и контроль)\n"
                            f"• Отправьте <code>/im_angela</code> — зарегистрироваться как Анжела (приём заказов в личку)\n"
                            f"• Отправьте <code>/test</code> — отправить тестовый заказ"
                        )
                        send_message(token, chat_id, welcome_text)

                    elif text.startswith("/im_owner"):
                        cfg["owner_chat_id"] = chat_id
                        save_config(cfg)
                        send_message(token, chat_id, "✅ Вы успешно зарегистрированы как <b>Владелец</b>!\nСюда будут приходить все заказы с сайта для тестирования и контроля.")
                        print(f"Зарегистрирован владелец: chat_id={chat_id} (@{user_username})")

                    elif text.startswith("/im_angela"):
                        cfg["angela_chat_id"] = chat_id
                        save_config(cfg)
                        send_message(token, chat_id, "🌸 Вы успешно зарегистрированы как <b>Анжела Бачерикова</b>!\nСюда будут поступать все новые заказы клиентов с сайта LUMIÈRE.")
                        print(f"Зарегистрирована Анжела: chat_id={chat_id} (@{user_username})")

                    elif text.startswith("/test"):
                        send_test_order(cfg)

                    elif text.startswith("/status"):
                        owner_st = f"подключен (<code>{cfg.get('owner_chat_id', '')}</code>)" if cfg.get("owner_chat_id") else "не подключен"
                        angela_st = f"подключена (<code>{cfg.get('angela_chat_id', '')}</code>)" if cfg.get("angela_chat_id") else "не подключена"
                        status_msg = (
                            f"📊 <b>Статус бота LUMIÈRE</b>\n\n"
                            f"• Владелец: {owner_st}\n"
                            f"• Анжела: {angela_st}\n"
                            f"• Город: {cfg.get('city', 'Киров')}\n\n"
                            f"Для проверки напишите /test"
                        )
                        send_message(token, chat_id, status_msg)

            time.sleep(1)
        except KeyboardInterrupt:
            print("\nБот остановлен пользователем.")
            break
        except Exception as e:
            print(f"Ошибка в цикле: {e}")
            time.sleep(2)

if __name__ == "__main__":
    config = load_config()
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        send_test_order(config)
    else:
        run_polling(config)
