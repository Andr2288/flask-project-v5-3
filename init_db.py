from main import app
from models import db, User, Post, Comment
from datetime import datetime


def init_database():
    """Ініціалізує базу даних з тестовими даними"""
    with app.app_context():
        # Перевірити чи є дані
        user_count = User.query.count()
        if user_count > 0:
            print(f"База даних вже містить дані ({user_count} користувачів)")
            choice = input("Видалити всі дані та створити заново? (y/n): ").lower().strip()

            if choice in ['y', 'yes', 'так', 'т']:
                print("Видаляємо всі дані...")
                # Видалити всі дані
                Comment.query.delete()
                Post.query.delete()
                User.query.delete()
                db.session.commit()
                print("Дані видалено!")
            else:
                print("Операція скасована. Дані залишаються без змін.")
                return

        print("Створюємо тестові дані...")

        # Створити тестових користувачів
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

        # Створити тестові пости
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

        # Отримати створені пости
        posts = Post.query.all()

        # Створити тестові коментарі
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

        print("База даних успішно ініціалізована з тестовими даними!")
        print("\nТестові користувачі:")
        print("- admin:admin@example.com (пароль: 123456)")
        print("- admin2:admin2@example.com (пароль: 123456)")
        print("- user1:user1@example.com (пароль: 123456)")
        print("- blogger:blogger@example.com (пароль: 123456)")
        print(
            f"\nСтворено: {User.query.count()} користувачів, {Post.query.count()} постів, {Comment.query.count()} коментарів")


if __name__ == '__main__':
    init_database()