from main import app
from models import db, User, Post, Comment
from datetime import datetime


def init_database():
    """Ініціалізує базу даних з тестовими даними"""
    with app.app_context():
        # Створити таблиці якщо їх немає
        db.create_all()

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

        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.add(user4)
        db.session.commit()

        # Створити тестові пости
        post1 = Post(
            title='Ласкаво просимо до нашого блогу!',
            content='Це перший пост у нашому блозі. Тут ми будемо ділитися цікавими думками та ідеями.',
            user_id=user1.id
        )

        post2 = Post(
            title='Про Flask та веб-розробку',
            content='Flask - це мікрофреймворк для Python, який дозволяє швидко створювати веб-додатки. Він простий у використанні та дуже гнучкий.',
            user_id=user4.id
        )

        post3 = Post(
            title='Майбутнє веб-технологій',
            content='Веб-технології розвиваються дуже швидко. Кожного дня з\'являються нові інструменти та підходи до розробки.',
            user_id=user3.id
        )

        post4 = Post(
            title='Новий пост від admin2',
            content='Це пост створений користувачем admin2 для тестування системи.',
            user_id=user2.id
        )

        db.session.add(post1)
        db.session.add(post2)
        db.session.add(post3)
        db.session.add(post4)
        db.session.commit()

        # Створити тестові коментарі
        comment1 = Comment(
            content='Дуже цікавий пост! Дякую за інформацію.',
            post_id=post1.id,
            user_id=user3.id
        )

        comment2 = Comment(
            content='Згоден! Flask справді простий у використанні.',
            post_id=post2.id,
            user_id=user1.id
        )

        comment3 = Comment(
            content='Було б цікаво почитати більше про нові технології.',
            post_id=post3.id,
            user_id=user4.id
        )

        comment4 = Comment(
            content='Відмінний пост від admin2!',
            post_id=post4.id,
            user_id=user1.id
        )

        db.session.add(comment1)
        db.session.add(comment2)
        db.session.add(comment3)
        db.session.add(comment4)
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