import click
from flask.cli import with_appcontext
from models import db, User, Post, Comment


@click.command()
@with_appcontext
def init_db():
    """Ініціалізувати базу даних."""
    db.create_all()
    click.echo('База даних ініціалізована.')


@click.command()
@with_appcontext
def reset_db():
    """Скинути базу даних."""
    if click.confirm('Ви впевнені, що хочете видалити всі дані?'):
        db.drop_all()
        db.create_all()
        click.echo('База даних скинута.')


@click.command()
@with_appcontext
def seed_db():
    """Заповнити базу даних тестовими даними."""
    # Перевірити чи є дані
    if User.query.count() > 0:
        if not click.confirm('База даних вже містить дані. Продовжити?'):
            return

        # Очистити дані
        Comment.query.delete()
        Post.query.delete()
        User.query.delete()
        db.session.commit()

    # Створити користувачів
    users = [
        User(username='admin', email='admin@example.com'),
        User(username='admin2', email='admin2@example.com'),
        User(username='user1', email='user1@example.com'),
        User(username='blogger', email='blogger@example.com')
    ]

    for user in users:
        user.set_password('123456')
        db.session.add(user)

    db.session.commit()

    # Створити пости
    posts = [
        Post(title='Ласкаво просимо!',
             content='Це наш новий блог з картами та міграціями.',
             user_id=users[0].id),
        Post(title='Flask розробка',
             content='Все про Flask та його можливості.',
             user_id=users[3].id)
    ]

    for post in posts:
        db.session.add(post)

    db.session.commit()

    click.echo('Тестові дані додано успішно!')