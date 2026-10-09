#!/usr/bin/env python3
"""
Telegram-бот для авторской мастерской LUMIÈRE (Анжела Бачерикова, г. Киров).
Поддерживает:
1. Запуск нативного Telegram Mini App магазина через меню и инлайн-кнопки.
2. Маршрутизацию заказов:
   - Мастеру: @Angisept
   - Владельцу (дублирование): @Cr1mnsx (Chat ID: 7452781280)
3. Автоматическую регистрацию ролей по username (@Angisept, @Cr1mnsx).
4. Команды /start, /catalog, /shipping, /contact, /status, /test.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.parse

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "bot_config.json")
MINI_APP_URL = "https://crimnsx-alt.github.io/lumiere-candles/webapp.html"
WEBSITE_URL = "https://crimnsx-alt.github.io/lumiere-candles/"

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
        print(f"Ошибка вызова Telegram API ({method}): {e}")
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

def get_main_keyboard():
    """Основная клавиатура с кнопкой запуска Telegram Mini App прямо внутри Telegram"""
    return {
        "inline_keyboard": [
            [
                {
                    "text": "🕯 Открыть бутик LUMIÈRE (Mini App)",
                    "web_app": {"url": MINI_APP_URL}
                }
            ],
            [
                {
                    "text": "👩‍🎨 Написать Анжеле @Angisept",
                    "url": "https://t.me/Angisept"
                },
                {
                    "text": "🌐 Веб-сайт мастерской",
                    "url": WEBSITE_URL
                }
            ],
            [
                {
                    "text": "🚚 Доставка в Кирове и по РФ",
                    "callback_data": "shipping"
                },
                {
                    "text": "🌿 О соевом воске и уходе",
                    "callback_data": "about"
                }
            ]
        ]
    }

def setup_bot_ui(token):
    """Настройка нативной кнопки меню (Menu Button) и команд бота в Telegram"""
    print("⚙️ Регистрация кнопки меню Telegram Mini App...")
    # Нативная кнопка "🛍 Открыть бутик" возле поля ввода сообщения
    menu_res = api_call(token, "setChatMenuButton", {
        "menu_button": {
            "type": "web_app",
            "text": "🛍 Открыть бутик",
            "web_app": {"url": MINI_APP_URL}
        }
    })
    if menu_res and menu_res.get("ok"):
        print("✅ Menu Button успешно зарегистрирована!")

    # Список команд для всплывающего меню [/]
    cmd_res = api_call(token, "setMyCommands", {
        "commands": [
            {"command": "start", "description": "✨ Главное меню и каталог свечей"},
            {"command": "catalog", "description": "🕯 Открыть Telegram Mini App бутик"},
            {"command": "shipping", "description": "🚚 Условия доставки в Кирове и по РФ"},
            {"command": "contact", "description": "👩‍🎨 Связаться с мастером Анжелой"},
            {"command": "status", "description": "📊 Статус мастерской и уведомлений"}
        ]
    })
    if cmd_res and cmd_res.get("ok"):
        print("✅ Команды бота успешно настроены!")

def format_order_message(order_data):
    order_id = order_data.get("order_id", "LK-8419")
    client_name = order_data.get("name", "Мария Смирнова")
    phone = order_data.get("phone", "+7 (912) 820-45-67")
    tg = order_data.get("tg", "@mariya_k")
    address = order_data.get("address", "г. Киров, Октябрьский пр-т, 24 / ПВЗ СДЭК")
    shipping = order_data.get("shipping", "Курьер по Кирову (Яндекс Доставка, 250 ₽)")
    comment = order_data.get("comment", "")
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

    comment_line = f"💌 <b>Пожелание / открытка:</b> {comment}\n" if comment else ""

    return (
        f"🕯 <b>НОВЫЙ ЗАКАЗ ИЗ MINI APP #{order_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Клиент:</b> {client_name}\n"
        f"📞 <b>Телефон:</b> <code>{phone}</code>\n"
        f"✈️ <b>Telegram:</b> {tg}\n"
        f"📍 <b>Адрес / ПВЗ:</b> {address}\n"
        f"🚚 <b>Доставка:</b> {shipping}\n"
        f"{comment_line}"
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

    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": "🛍 Открыть каталог",
                    "web_app": {"url": MINI_APP_URL}
                }
            ]
        ]
    }

    # 1. Отправка Анжеле (@Angisept)
    angela_id = cfg.get("angela_chat_id")
    if angela_id:
        send_message(token, angela_id, msg, reply_markup=reply_markup)
        print(f"✅ Заказ #{order_data.get('order_id')} отправлен мастеру Анжеле (@Angisept)")
    else:
        print("⚠️ Chat ID Анжелы (@Angisept) пока не зарегистрирован (нужно нажать /start в боте).")

    # 2. Дублирование владельцу (@Cr1mnsx)
    owner_id = cfg.get("owner_chat_id", "7452781280")
    if owner_id:
        send_message(token, owner_id, msg, reply_markup=reply_markup)
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

    # Инициализация интерфейса WebApp в Telegram
    setup_bot_ui(token)

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

                    # 1. Обработка нажатий на инлайн-кнопки (Callback Query)
                    cb = u.get("callback_query")
                    if cb:
                        cb_id = cb["id"]
                        cb_data = cb.get("data", "")
                        cb_chat_id = str(cb["message"]["chat"]["id"])
                        api_call(token, "answerCallbackQuery", {"callback_query_id": cb_id})

                        if cb_data == "shipping":
                            shipping_text = (
                                "🚚 <b>Условия доставки мастерской LUMIÈRE</b>\n\n"
                                "• <b>Самовывоз в Кирове:</b> Бесплатно (центр города, по предварительному согласованию)\n"
                                "• <b>Курьер по Кирову:</b> 250 ₽ (Яндекс Доставка до двери)\n"
                                "• <b>СДЭК и Почта России:</b> 350 ₽ (<b>Бесплатно</b> при заказе от 3 500 ₽)\n\n"
                                "📦 Каждое изделие бережно упаковывается в крафтовый бокс с наполнителем, тишью и льняной лентой."
                            )
                            send_message(token, cb_chat_id, shipping_text, reply_markup=get_main_keyboard())
                        elif cb_data == "about":
                            about_text = (
                                "🕯 <b>О мастерской LUMIÈRE (г. Киров)</b>\n\n"
                                "Создатель и мастер: <b>Бачерикова Анжела Александровна</b>.\n\n"
                                "🌿 <b>100% соевый воск:</b> Без парафина, продуктов нефтепереработки и вредных примесей.\n"
                                "🪵 <b>Деревянный фитиль:</b> При горении издаёт медитативный треск домашнего камина.\n"
                                "✨ <b>Масла из Грасса:</b> Селективные парфюмерные композиции из столицы французской парфюмерии.\n"
                                "🏺 <b>Гипсовый декор:</b> Подносы и кашпо ручной отливки с влагозащитным матовым покрытием."
                            )
                            send_message(token, cb_chat_id, about_text, reply_markup=get_main_keyboard())
                        continue

                    # 2. Обработка текстовых сообщений и WebApp данных
                    msg = u.get("message")
                    if not msg:
                        continue

                    chat_id = str(msg["chat"]["id"])
                    text = msg.get("text", "").strip()
                    username = (msg["from"].get("username") or "").lower()
                    first_name = msg["from"].get("first_name", "Гость")

                    # Проверяем отправку данных из WebApp (если через sendData)
                    if "web_app_data" in msg:
                        data_str = msg["web_app_data"].get("data", "{}")
                        try:
                            order_obj = json.loads(data_str)
                            broadcast_order(cfg, order_obj)
                            send_message(token, chat_id, f"✅ <b>Ваш заказ #{order_obj.get('order_id')} принят!</b>\nМастер @Angisept уже собирает его в Кирове.")
                        except Exception as ex:
                            print(f"Ошибка парсинга web_app_data: {ex}")
                        continue

                    # Автоматическое распознавание Анжелы (@Angisept)
                    if username == "angisept" or text.startswith("/im_angela"):
                        cfg["angela_chat_id"] = chat_id
                        save_config(cfg)
                        welcome_angela = (
                            f"🌸 <b>Здравствуйте, Анжела!</b>\n\n"
                            f"Бот <b>@{bot_username}</b> успешно подключен к вашей мастерской LUMIÈRE (г. Киров).\n\n"
                            f"Теперь каждый заказ с сайта и Telegram Mini App будет мгновенно приходить прямо сюда в ваш личный чат со всеми деталями, составом изделий, номером телефона и адресом покупателя!"
                        )
                        send_message(token, chat_id, welcome_angela, reply_markup=get_main_keyboard())

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
                            angela_status = f"✅ подключена (<code>{cfg.get('angela_chat_id')}</code>)" if cfg.get('angela_chat_id') else "⏳ ожидает первого перехода в бота @Angisept"
                            send_message(token, chat_id, (
                                f"📊 <b>Статус заказов LUMIÈRE</b>:\n\n"
                                f"• Дублирование @Cr1mnsx: ✅ подключено (<code>{chat_id}</code>)\n"
                                f"• Мастер @Angisept: {angela_status}\n"
                                f"• Mini App: <code>{MINI_APP_URL}</code>\n\n"
                                f"Команда /test — отправить тестовый заказ в оба чата."
                            ), reply_markup=get_main_keyboard())
                            continue

                    # Команда /catalog
                    if text.startswith("/catalog"):
                        send_message(token, chat_id, (
                            "🕯 <b>Каталог свечей и декора LUMIÈRE</b>\n\n"
                            "Нажмите кнопку ниже, чтобы открыть бутик внутри Telegram:"
                        ), reply_markup=get_main_keyboard())
                        continue

                    # Команда /shipping
                    if text.startswith("/shipping"):
                        shipping_text = (
                            "🚚 <b>Условия доставки мастерской LUMIÈRE</b>\n\n"
                            "• <b>Самовывоз в Кирове:</b> Бесплатно\n"
                            "• <b>Курьер по Кирову:</b> 250 ₽\n"
                            "• <b>СДЭК и Почта по РФ:</b> 350 ₽ (бесплатно от 3 500 ₽)"
                        )
                        send_message(token, chat_id, shipping_text, reply_markup=get_main_keyboard())
                        continue

                    # Команда /contact
                    if text.startswith("/contact"):
                        send_message(token, chat_id, (
                            "👩‍🎨 <b>Контакты мастерской LUMIÈRE</b>\n\n"
                            "• Мастер: <b>Бачерикова Анжела Александровна</b>\n"
                            "• Личный Telegram мастера: @Angisept\n"
                            "• Город: г. Киров\n"
                            f"• Веб-сайт: {WEBSITE_URL}"
                        ), reply_markup=get_main_keyboard())
                        continue

                    # Команда /start или любое первое сообщение
                    if text.startswith("/start") or text:
                        welcome_msg = (
                            f"✨ Здравствуйте, <b>{first_name}</b>!\n\n"
                            f"Добро пожаловать в авторскую мастерскую свечей и гипсового декора <b>LUMIÈRE</b> "
                            f"(мастер Анжела Бачерикова, г. Киров).\n\n"
                            f"🕯 100% соевый воск & селективные ароматы из Грасса\n"
                            f"🪵 Деревянные трескучие фитили\n"
                            f"🏺 Эстетичный интерьерный декор из гипса\n"
                            f"📦 Самовывоз в Кирове и доставка СДЭК по всей России\n\n"
                            f"Нажмите кнопку <b>«🕯 Открыть бутик LUMIÈRE»</b> или <b>«🛍 Открыть бутик»</b> внизу экрана, "
                            f"чтобы выбрать свечи прямо в Telegram:"
                        )
                        send_message(token, chat_id, welcome_msg, reply_markup=get_main_keyboard())

            time.sleep(1)
        except KeyboardInterrupt:
            print("\nБот остановлен.")
            break
        except Exception as e:
            print(f"Ошибка в цикле polling: {e}")
            time.sleep(2)

if __name__ == "__main__":
    config = load_config()
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        send_test_order(config)
    else:
        run_polling(config)
