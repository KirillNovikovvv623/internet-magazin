from flask import Flask, request, jsonify, send_from_directory
import sqlite3

app = Flask(__name__, static_folder='.')
DB_NAME = 'romashka.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # 1. Таблица Категория
    c.execute('''CREATE TABLE IF NOT EXISTS Категория (
        id_category INTEGER PRIMARY KEY,
        category TEXT NOT NULL
    )''')
    
    # 2. Таблица Цветы (связь 1:N с Категория)
    c.execute('''CREATE TABLE IF NOT EXISTS Цветы (
        id_flower INTEGER PRIMARY KEY,
        id_category INTEGER,
        flower_name TEXT NOT NULL,
        category TEXT,
        description TEXT,
        price INTEGER NOT NULL,
        img TEXT,
        FOREIGN KEY (id_category) REFERENCES Категория(id_category)
    )''')
    
    # 3. Таблица Клиент
    c.execute('''CREATE TABLE IF NOT EXISTS Клиент (
        id_client INTEGER PRIMARY KEY AUTOINCREMENT,
        ФИО TEXT NOT NULL,
        Телефон TEXT NOT NULL,
        email TEXT
    )''')
    
    # 4. Таблица Отзывы (связывает Клиент и Цветы по M:N)
    c.execute('''CREATE TABLE IF NOT EXISTS Отзывы (
        id_review INTEGER PRIMARY KEY AUTOINCREMENT,
        id_client INTEGER,
        id_flower INTEGER,
        name_reviewer TEXT NOT NULL,
        stars INTEGER CHECK(stars >= 1 AND stars <= 5),
        comments TEXT,
        FOREIGN KEY (id_client) REFERENCES Клиент(id_client),
        FOREIGN KEY (id_flower) REFERENCES Цветы(id_flower)
    )''')

    # Наполняем начальными данными при первом запуске
    if c.execute('SELECT COUNT(*) FROM Категория').fetchone()[0] == 0:
        c.executemany('INSERT INTO Категория VALUES (?, ?)', [
            (1, 'Полевые'), (2, 'Розы'), (3, 'Сезонные'), (4, 'В горшках')
        ])

        c.executemany('INSERT INTO Цветы VALUES (?, ?, ?, ?, ?, ?, ?)', [
            (1, 1, 'Букет «Летнее утро»', 'Полевые', 'Нежные полевые ромашки в крафтовой упаковке.', 1800, '42536-buket-letnee-utro-175766.jpg'),
            (2, 2, 'Классика «Алая страсть»', 'Розы', '15 свежих красных роз высшего сорта.', 3200, '1783702258_18491729.jpg'),
            (3, 3, 'Весенний комплимент', 'Сезонные', 'Яркий микс из разноцветных тюльпанов.', 2100, 'tulips.jpg'),
            (4, 1, 'Солнечное настроение', 'Полевые', 'Пышные подсолнухи с декоративной зеленью.', 2500, 'sunflowers.jpg'),
            (5, 2, 'Нежность облаков', 'Розы', 'Воздушные кустовые белые розы с эвкалиптом.', 3600, 'white-roses.jpg'),
            (6, 4, 'Королевская орхидея', 'В горшках', 'Цветущий фаленопсис в керамическом кашпо.', 2900, 'orchid.jpg')
        ])

        c.executemany('INSERT INTO Клиент (ФИО, Телефон, email) VALUES (?, ?, ?)', [
            ('Елена Соколова', '+79991112233', 'elena@mail.ru'),
            ('Дмитрий Волков', '+79994445566', 'dmitry@mail.ru')
        ])

        c.executemany('INSERT INTO Отзывы (id_client, id_flower, name_reviewer, stars, comments) VALUES (?, ?, ?, ?, ?)', [
            (1, 1, 'Елена Соколова', 5, 'Заказывала ромашки маме на день рождения. Цветы свежайшие, пахнут летом!'),
            (2, 2, 'Дмитрий Волков', 5, 'Шикарные свежие розы, бутоны плотные, простояли почти две недели!')
        ])

    conn.commit()
    conn.close()

# Раздача главной страницы и картинок/стилей
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

# API: Получение каталога и категорий
@app.route('/api/catalog')
def get_catalog():
    conn = get_db()
    categories = [dict(r) for r in conn.execute('SELECT * FROM Категория')]
    flowers = [dict(r) for r in conn.execute('SELECT * FROM Цветы')]
    conn.close()
    return jsonify({'categories': categories, 'flowers': flowers})

# API: Получение и добавление отзывов (с привязкой к id_client и id_flower)
@app.route('/api/reviews', methods=['GET', 'POST'])
def reviews_api():
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'POST':
        data = request.json
        # Ищем клиента по имени или создаем нового, чтобы получить id_client
        client = c.execute('SELECT id_client FROM Клиент WHERE ФИО = ?', (data['name_reviewer'],)).fetchone()
        if client:
            id_client = client['id_client']
        else:
            c.execute('INSERT INTO Клиент (ФИО, Телефон, email) VALUES (?, ?, ?)',
                      (data['name_reviewer'], 'Не указан', 'Не указан'))
            id_client = c.lastrowid

        c.execute('INSERT INTO Отзывы (id_client, id_flower, name_reviewer, stars, comments) VALUES (?, ?, ?, ?, ?)',
                  (id_client, data['id_flower'], data['name_reviewer'], data['stars'], data['comments']))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})

    query = '''
        SELECT Отзывы.*, Цветы.flower_name 
        FROM Отзывы 
        LEFT JOIN Цветы ON Отзывы.id_flower = Цветы.id_flower 
        ORDER BY Отзывы.id_review DESC
    '''
    reviews = [dict(r) for r in c.execute(query)]
    conn.close()
    return jsonify(reviews)

# API: Оформление заказа (сохранение в таблицу Клиент)
@app.route('/api/order', methods=['POST'])
def order_api():
    data = request.json
    conn = get_db()
    conn.execute('INSERT INTO Клиент (ФИО, Телефон, email) VALUES (?, ?, ?)',
                 (data['fio'], data['phone'], data['email']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    init_db()
    # host='0.0.0.0' позволяет открывать сайт не только с ПК, но и с телефона по Wi-Fi
    app.run(host='0.0.0.0', port=5000, debug=True)
