import telebot
import sqlite3
from telebot import types

bot = telebot.TeleBot('6857076342:AAGaUJyUy0xRpLcisIWIcxDRE2TLA9lngAs')
log = None
U = None  # Переменная для хранения id пользователя
B = None  # Переменная для хранения id книги


@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('library.sql')  # Подключение к базе данных
    cur = conn.cursor()

    # Создание таблицы Пользователи
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        birthdate DATA
    )
    ''')
    # Создание таблицы Книги
    cur.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        description TEXT,
        year INTEGER,
        publisher TEXT,
        age_limit INTEGER NOT NULL,
        translator TEXT
    )
    ''')
    # Создание таблицы Брони
    cur.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        book_id INTEGER,
        booking_date TEXT DEFAULT CURRENT_TIMESTAMP,
        address TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(book_id) REFERENCES books(id)
    )
    ''')
    conn.commit()
    cur.close()  # закрываем соединение с бд
    conn.close()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Регистрация 📝")
    item2 = types.KeyboardButton("Авторизация 📜")
    markup.row(item1, item2)
    bot.send_message(message.chat.id, "🖐 Здравствуй, дорогой путник! Мы рады приветствовать вас в официальном боте нашей Библиотеки! Выберите действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Регистрация 📝")
def registration(message):
    bot.send_message(message.chat.id, '🤓 О, так вы новенький? Сейчас вас зарегистрируем! Введите свое имя - ')
    bot.register_next_step_handler(message, user_log)


@bot.message_handler(func=lambda message: message.text == "Авторизация 📜") #пофиксить
def authorization(message):
    bot.send_message(message.chat.id, '🥰 Вы снова здесь, старина? Введите свой логин для авторизации - ')
    bot.register_next_step_handler(message, user_login_auth)


def user_log(message):  # заносим имя
    global log
    log = message.text.strip()
    bot.send_message(message.chat.id, 'Введите пароль - ')
    bot.register_next_step_handler(message, user_pas)


def user_pas(message):  # заносим пароль и вносим имя и пароль в бд

    global U  # глобальная переменная для хранения id пользователя

    pas = message.text.strip()

    conn = sqlite3.connect('library.sql')
    cur = conn.cursor()

    cur.execute("INSERT INTO users (login, password) VALUES ('%s', '%s')" % (log, pas))

    cur.execute("SELECT id FROM users WHERE login=?", (log,))
    user_id = cur.fetchone()

    U = user_id[0]  # id пользователя в переменной U

    conn.commit()
    cur.close()
    conn.close()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Открыть библиотеку 📔")
    item2 = types.KeyboardButton("Ваши брони 👩‍💻")

    markup.add(item1, item2)
    bot.send_message(message.chat.id, '🎉 Регистрация прошла успешно, выберите дальнейшее действие:', reply_markup=markup)


def user_login_auth(message):
   global log
   log = message.text.strip()
   bot.send_message(message.chat.id, 'Введите пароль -')
   bot.register_next_step_handler(message, user_pass_auth)


def user_pass_auth(message):
    global U

    password = message.text.strip()

    conn = sqlite3.connect('library.sql')
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE login=? AND password=?", (log, password))
    user_id = cur.fetchone()

    if user_id:
        U = user_id[0]
        bot.send_message(message.chat.id, f"Добро пожаловать, {log}!")

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item_open = types.KeyboardButton("Открыть библиотеку 📔")
        item_bookings = types.KeyboardButton("Ваши брони 👩‍💻")
        markup.add(item_open, item_bookings)
        bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)

    else:
        bot.send_message(message.chat.id, "Неправильный логин или пароль. Попробуйте снова.")

    cur.close()
    conn.close()


@bot.message_handler(func=lambda message: message.text == "Открыть библиотеку 📔")
def open_library(message):
    conn = sqlite3.connect('library.sql')
    cur = conn.cursor()

    cur.execute("SELECT id,title, author FROM books")
    books = cur.fetchall()

    if books:
        book_list = ""
        for book in books:
            book_list += f"ID: {book[0]}\nНазвание: {book[1]}\nАвтор: {book[2]}\n\n"

        bot.send_message(message.chat.id, f"Вот что у нас есть для вас!\nСписок книг в библиотеке:\n{book_list}")
        bot.send_message(message.chat.id,
                         "Приглянулось что?\n Хотите забронировать какую-то книгу или узнать про неё больше? Если да, то введите номер ID нужной книги.")
    else:
        bot.send_message(message.chat.id, "Кажется, что-то пошло не так и у нас не оказалось книг :(")

    cur.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == "Ваши брони 👩‍💻")
def user_bookings(message):
    conn = sqlite3.connect('library.sql')
    cur = conn.cursor()

    cur.execute(
        "SELECT books.title, bookings.book_id, bookings.id FROM bookings JOIN books ON bookings.book_id = books.id WHERE user_id=?",
        (U,))
    user_bookings_info = cur.fetchall()

    if user_bookings_info:
        booking_list = "👩‍💻 Ваши брони:\n"
        for book_info in user_bookings_info:
            booking_list += f"Название книги: {book_info[0]}\nID книги: {book_info[1]}\nID брони: {book_info[2]}\n\n"

        bot.send_message(message.chat.id, booking_list)
    else:
        bot.send_message(message.chat.id, "Вы уже все прочитали;)\nУ вас пока больше нет бронирований")

    cur.close()
    conn.close()



@bot.message_handler(func=lambda message: True) # функцию для обработки сообщения с id книги
def handle_book_id(message):

    global B  # глобальная переменная для хранения id книги

    conn = sqlite3.connect('library.sql')
    cur = conn.cursor()

    try:
        book_id = int(message.text)

        # Проверка существование книги с введенным id в базе данных
        cur.execute("SELECT * FROM books WHERE id=?", (book_id,))
        book = cur.fetchone()

        if book:
            B = book_id  # Сохраняем id книги в переменной B
            bot.send_message(message.chat.id,
                             f"Это точно будет вам по душе:\n   ID:  {book[0]}\n   Название:  {book[1]}\n   Автор:  {book[2]}\n   Год издания: {book[4]}\n   Описание: {book[3]}\n   Издательство:  {book[5]}\n   Переводчик:  {book[7]}\n   Возрастное ограничение:  {book[6]}")

            # Запрос пользователя о бронировании книги
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_yes = types.KeyboardButton("Да")
            item_no = types.KeyboardButton("Нет")
            markup.add(item_yes, item_no)
            bot.send_message(message.chat.id, "Хотите забронировать эту книгу?", reply_markup=markup)

            bot.register_next_step_handler(message, handle_book_booking) # Регистрация следующего шага для обработки ответа пользователя
        else:
            bot.send_message(message.chat.id, "Книги с таким ID не найдено :(")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите ID книги в виде числа")

    cur.close()
    conn.close()


def handle_book_booking(message):
    if message.text.lower() == "да":

        conn = sqlite3.connect('library.sql')
        cur = conn.cursor()

        # Создаем новую запись в таблице bookings
        cur.execute("INSERT INTO bookings (user_id, book_id) VALUES (?, ?)", (U, B))
        conn.commit()

        # Получаем id только что созданной брони
        cur.execute("SELECT id FROM bookings WHERE user_id=? AND book_id=?", (U, B))
        booking_id = cur.fetchone()

        bot.send_message(message.chat.id, f"✏️ Ура!\nБронь успешно создана. ID брони: {booking_id[0]}\nЭтот номер вам понадобится, когда вы придете к нам за книгой)")

        cur.close()
        conn.close()

        # Повторное отображение кнопок для выбора действий
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item_open = types.KeyboardButton("Открыть библиотеку 📔")
        item_bookings = types.KeyboardButton("Ваши брони 👩‍💻")
        markup.add(item_open, item_bookings)
        bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)


    elif message.text.lower() == "нет":
        bot.send_message(message.chat.id, "Давайте посмотрим что-то еще?")

        # Повторное отображение кнопок для выбора действий
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item_open = types.KeyboardButton("Открыть библиотеку 📔")
        item_bookings = types.KeyboardButton("Ваши брони 👩‍💻")
        markup.add(item_open, item_bookings)
        bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)


    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите ✅ 'Да' или ❌ 'Нет'")



bot.polling(none_stop=True)

