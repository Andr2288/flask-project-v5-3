from main import app
from models import db, User, Post, Comment
from sqlalchemy import create_engine, text
from urllib.parse import urlparse
import time


def check_database_exists(uri):
    parsed = urlparse(uri)
    db_name = parsed.path.lstrip('/')

    base_uri = f"{parsed.scheme}://"
    if parsed.username:
        base_uri += parsed.username
        if parsed.password:
            base_uri += f":{parsed.password}"
        base_uri += "@"
    if parsed.hostname:
        base_uri += parsed.hostname
    if parsed.port:
        base_uri += f":{parsed.port}"
    base_uri += "/"

    try:
        engine = create_engine(base_uri)
        with engine.connect() as conn:
            result = conn.execute(text("SHOW DATABASES"))
            databases = [row[0] for row in result]
            return db_name in databases, db_name, base_uri
    except Exception as e:
        print(f"❌ Помилка підключення до MySQL: {e}")
        return False, db_name, base_uri


def delete_database():
    """Видаляє базу даних, якщо вона існує"""
    uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    if not uri or not uri.startswith('mysql'):
        print("❌ Неправильна конфігурація бази даних")
        return False

    db_exists, db_name, base_uri = check_database_exists(uri)
    if not db_exists:
        print(f"ℹ️ База даних `{db_name}` не існує — нічого видаляти")
        return True

    print(f"🗑️  Видаляємо базу даних `{db_name}`...")

    try:
        engine = create_engine(base_uri, isolation_level="AUTOCOMMIT", echo=True)
        with engine.connect() as conn:
            # Завершуємо активні з'єднання
            active_connections = conn.execute(text(f"""
                SELECT id FROM information_schema.processlist WHERE db = :dbname
            """), {'dbname': db_name}).fetchall()

            for row in active_connections:
                conn.execute(text(f"KILL {row[0]}"))

            conn.execute(text(f"DROP DATABASE `{db_name}`"))
            print(f"✅ База даних `{db_name}` видалена")
        engine.dispose()
        return True
    except Exception as e:
        print(f"❌ Помилка при видаленні бази даних: {e}")
        return False


def create_and_fill_database():
    """Створює базу, таблиці та наповнює тестовими даними"""
    uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    if not uri or not uri.startswith('mysql'):
        print("❌ Неправильна конфігурація бази даних")
        return False

    db_exists, db_name, base_uri = check_database_exists(uri)
    if db_exists:
        print(f"ℹ️ База даних `{db_name}` вже існує — не створюємо з нуля")
        return False

    print(f"📝 Створюємо базу даних `{db_name}`...")
    try:
        engine = create_engine(base_uri, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        engine.dispose()
        print(f"✅ База даних `{db_name}` створена")
    except Exception as e:
        print(f"❌ Помилка при створенні бази даних: {e}")
        return False

    time.sleep(1)  # даємо час серверу

    with app.app_context():
        print("📝 Створюємо таблиці...")
        try:
            db.create_all()
            db.session.remove()
            db.engine.dispose()
            print("✅ Таблиці створені")
        except Exception as e:
            print(f"❌ Помилка при створенні таблиць: {e}")
            return False

        print("📝 Створюємо тестові дані...")
        try:
            user1 = User(username='admin', email='admin@example.com')
            user1.set_password('123456')

            user2 = User(username='admin2', email='admin2@example.com')
            user2.set_password('123456')

            user3 = User(username='user1', email='user1@example.com')
            user3.set_password('123456')

            user4 = User(username='blogger', email='blogger@example.com')
            user4.set_password('123456')

            db.session.add_all([user1, user2, user3, user4])
            db.session.commit()

            posts_data = [
                {
                    'title': 'Ласкаво просимо до нашого блогу!',
                    'content': 'Це перший пост у нашому блозі. Тут ми будемо ділитися цікавими думками та ідеями. Також тепер у нас є інтерактивні карти!',
                    'user_id': user1.id
                },
                {
                    'title': 'Про Flask та веб-розробку',
                    'content': 'Flask - це мікрофреймворк для Python, який дозволяє швидко створювати веб-додатки. Він простий у використанні та дуже гнучкий. З Flask-Migrate можна легко керувати змінами в базі даних.',
                    'user_id': user4.id
                },
                {
                    'title': 'Інтерактивні карти з Folium',
                    'content': 'Folium дозволяє створювати красиві інтерактивні карти безпосередньо в Python. Це дуже корисно для візуалізації географічних даних.',
                    'user_id': user3.id
                },
                {
                    'title': 'Міграції Flask-Migrate',
                    'content': 'Flask-Migrate спрощує управління змінами схеми бази даних. Тепер можна легко оновлювати структуру БД без втрати даних.',
                    'user_id': user2.id
                }
            ]

            for post_data in posts_data:
                post = Post(**post_data)
                db.session.add(post)

            db.session.commit()

            posts = Post.query.all()

            comments_data = [
                {
                    'content': 'Дуже цікавий пост! Дякую за інформацію про нові можливості.',
                    'post_id': posts[0].id,
                    'user_id': user3.id
                },
                {
                    'content': 'Згоден! Flask справді простий у використанні. Migrate теж дуже корисний.',
                    'post_id': posts[1].id,
                    'user_id': user1.id
                },
                {
                    'content': 'Folium виглядає дуже цікаво! Спробую використати в своєму проекті.',
                    'post_id': posts[2].id,
                    'user_id': user4.id
                },
                {
                    'content': 'Відмінний пост про міграції! Дуже корисна інформація.',
                    'post_id': posts[3].id,
                    'user_id': user1.id
                }
            ]

            for comment_data in comments_data:
                comment = Comment(**comment_data)
                db.session.add(comment)

            db.session.commit()
            print("✅ Тестові дані створені")
            return True

        except Exception as e:
            print(f"❌ Помилка при створенні тестових даних: {e}")
            return False


if __name__ == '__main__':
    print("Оберіть дію:")
    print("1 - Видалити базу даних")
    print("2 - Створити базу та наповнити тестовими даними")
    choice = input("Введіть номер опції (1/2): ").strip()

    if choice == '1':
        success = delete_database()
        if success:
            print("✅ Видалення бази даних завершено успішно.")
        else:
            print("❌ Видалення бази даних завершилося з помилкою.")
    elif choice == '2':
        success = create_and_fill_database()
        if success:
            print("✅ Створення та наповнення бази завершено успішно.")
        else:
            print("❌ Створення бази або наповнення тестовими даними завершилося з помилкою.")
    else:
        print("❌ Невірна опція. Будь ласка, запустіть скрипт знову та оберіть 1 або 2.")
