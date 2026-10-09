#!/usr/bin/env python3
"""
Telegram-бот для мастерской LUMIÈRE (Анжела Бачерикова, г. Киров).
Отправляет уведомления о заказах:
- Мастеру: @Angisept
- Владельцу (дублирование): @Cr1mnsx (Chat ID: 7452781280)
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
        "bot_token": "8998636215:AAGsFx26TwgAKvxr_zUwFRLns738Mkjvffs",
        "bot_username": "lumiere_kirov_bot",
        "owner_chat_id": "7452781280",
        "owner_username": "Cr1mnsx",
        "angela_chat_id": "",
        "angela_username": "Angisept",
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

def send_message(token, chat_id, text, reply_markup=None):
    if not chat_id:
        return False
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    res = api_call(token, "sendMessage", payload)
    return res and res.get("ok", False)

def format_order_message(order_data):
    order_id = order_data.get("order_id", "LK-8419")
    client_name = order_data.get("name", "Мария Смирнова")
    phone = order_data.get("phone", "+7 (912) 820-45-67")
    tg = order_data.get("tg", "@mariya_k")
    address = order_data.get("address", "г. Киров, Октябрьский пр-т, 24 / ПВЗ СДЭК")
    shipping = order_data.get("shipping", "Курьер по Кирову (Яндекс Доставка, 250 ₽)")
    comment = order_data.get("comment", "Крафтовая упаковка и открытка")
    items = order_data.get("items", [
        {"name": "Свеча «Кашемир & Теплая Ваниль» (200 мл)", "qty": 1, "price": 1490},
        {"name": "Овальный поднос из гипса «L'Ovale»", "qty": 1, "price": 590}
    ])
    total = order_data.get("total", 2330)
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
        f"🕒 <i>{date_str}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👩‍🎨 Мастер: @Angisept | 📋 Контроль: @Cr1mnsx"
    )

def broadcast_order(cfg, order_data):
    token = cfg.get("bot_token")
    msg = format_order_message(order_data)

    # 1. Отправка Анжеле (@Angisept)
    angela_id = cfg.get("angela_chat_id")
    if angela_id:
        send_message(token, angela_id, msg)
        print(f"✅ Заказ #{order_data.get('order_id')} отправлен Анжеле (@Angisept)")
    else:
        print("⚠️ Chat ID Анжелы (@Angisept) пока не зарегистрирован (нужно нажать /start в боте).")

    # 2. Дублирование владельцу (@Cr1mnsx)
    owner_id = cfg.get("owner_chat_id", "7452781280")
    if owner_id:
        send_message(token, owner_id, msg)
        print(f"✅ Заказ #{order_data.get('order_id')} продублирован владельцу (@Cr1mnsx)")

def send_test_order(cfg):
    test_data = {
        "order_id": "LK-TEST",
        "name": "Елена (Тестовый заказ)",
        "phone": "+7 (912) 820-11-22",
        "tg": "@elena_kirov",
        "address": "г. Киров, ул. Ленина, 105",
        "shipping": "Курьер по Кирову (Яндекс Доставка, 250 ₽)",
        "comment": "Тестовый заказ для проверки маршрутизации @Angisept и @Cr1mnsx",
        "items": [
            {"name": "Свеча «Кашемир & Теплая Ваниль» (200 мл)", "qty": 1, "price": 1490},
            {"name": "Овальный поднос из гипса «L'Ovale»", "qty": 1, "price": 590}
        ],
        "total": 2330
    }
    broadcast_order(cfg, test_data)

def run_polling(cfg):
    token = cfg.get("bot_token")
    bot_info = api_call(token, "getMe")
    if not bot_info or not bot_info.get("ok"):
        print("❌ Неверный токен бота.")
        return

    bot_username = bot_info["result"]["username"]
    print("="*60)
    print(f"✅ Бот @{bot_username} запущен и слушает события!")
    print(f"Владелец (@Cr1mnsx): Chat ID = {cfg.get('owner_chat_id')}")
    print(f"Мастер (@Angisept): Chat ID = {cfg.get('angela_chat_id') or 'Ожидает /start'}")
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
                    username = (msg["from"].get("username") or "").lower()
                    first_name = msg["from"].get("first_name", "Гость")

                    # Автоматическое распознавание Анжелы (@Angisept)
                    if username == "angisept" or text.startswith("/im_angela"):
                        cfg["angela_chat_id"] = chat_id
                        save_config(cfg)
                        welcome_angela = (
                            f"🌸 <b>Здравствуйте, Анжела!</b>\n\n"
                            f"Бот <b>@{bot_username}</b> успешно подключен к вашей мастерской LUMIÈRE (г. Киров).\n\n"
                            f"Теперь каждый заказ с сайта и Telegram Mini App будет мгновенно приходить прямо сюда в ваш личный чат со всеми деталями, составом изделий, номером телефона и адресом покупателя!"
                        )
                        send_message(token, chat_id, welcome_angela)

                        # Уведомляем владельца @Cr1mnsx
                        owner_id = cfg.get("owner_chat_id")
                        if owner_id and owner_id != chat_id:
                            send_message(token, owner_id, f"🎉 <b>Анжела (@Angisept) активировала бота!</b>\nЕё Chat ID (<code>{chat_id}</code>) сохранён. Теперь заказы уходят сразу ей и дублируются вам.")
                        print(f"✅ Зарегистрирован Chat ID Анжелы: {chat_id}")
                        continue

                    # Автоматическое распознавание владельца (@Cr1mnsx)
                    if username == "cr1mnsx" or chat_id == str(cfg.get("owner_chat_id")):
                        cfg["owner_chat_id"] = chat_id
                        save_config(cfg)
                        if text.startswith("/test"):
                            send_test_order(cfg)
                            continue
                        elif text.startswith("/status"):
                            angela_status = f"✅ подключена (<code>{cfg.get('angela_chat_id')}</code>)" if cfg.get('angela_chat_id') else "⏳ ожидает перехода в бота @Angisept"
                            send_message(token, chat_id, f"📊 <b>Статус заказов LUMIÈRE</b>:\n\n• Дублирование @Cr1mnsx: ✅ подключено\n• Мастер @Angisept: {angela_status}\n\nКоманда /test — отправить тестовый заказ.")
                            continue

                    if text.startswith("/start"):
                        send_message(token, chat_id, (
                            f"👋 Здравствуйте, <b>{first_name}</b>!\n\n"
                            f"Это бот авторской мастерской свечей <b>LUMIÈRE</b> (Анжела Бачерикова, г. Киров).\n\n"
                            f"Сайт мастерской: https://crimnsx-alt.github.io/lumiere-candles/\n"
                            f"Связь с мастером: @Angisept"
                        ))

            time.sleep(1)
        except KeyboardInterrupt:
            print("\nБот остановлен.")
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
