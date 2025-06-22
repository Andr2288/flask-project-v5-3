from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from models import db, User, Post, Comment
from forms import LoginForm, RegisterForm, PostForm, CommentForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:1234567890@localhost/flask_crud'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db.init_app(app)
csrf = CSRFProtect(app)
jwt = JWTManager(app)


def login_required(f):
    """Simple decorator to check if user is logged in"""

    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


# Routes
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    return render_template('index.html', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username
            access_token = create_access_token(identity=user.id)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Wrong username or password!', 'error')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            # Check what caused the error
            existing_user = User.query.filter_by(username=form.username.data).first()
            existing_email = User.query.filter_by(email=form.email.data).first()

            if existing_user:
                flash('This username is already taken. Choose another one.', 'error')
            elif existing_email:
                flash('This email is already registered. Choose another one.', 'error')
            else:
                flash('Registration failed. Please try again.', 'error')
    return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


# Post CRUD
@app.route('/posts')
def posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('posts.html', posts=posts)


@app.route('/posts/create', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=session['user_id']
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
        return redirect(url_for('posts'))
    return render_template('create_post.html', form=form)


@app.route('/posts/<int:id>')
def view_post(id):
    post = Post.query.get_or_404(id)
    comments = Comment.query.filter_by(post_id=id).order_by(Comment.created_at.desc()).all()
    form = CommentForm()
    return render_template('view_post.html', post=post, comments=comments, form=form)


@app.route('/posts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)

    # Check if user owns this post
    if post.user_id != session['user_id']:
        flash('You can only edit your own posts!', 'error')
        return redirect(url_for('posts'))

    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Post updated!', 'success')
        return redirect(url_for('view_post', id=post.id))
    return render_template('edit_post.html', form=form, post=post)


@app.route('/posts/<int:id>/delete', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)

    # Check if user owns this post
    if post.user_id != session['user_id']:
        flash('You can only delete your own posts!', 'error')
        return redirect(url_for('posts'))

    db.session.delete(post)
    db.session.commit()
    flash('Post deleted!', 'success')
    return redirect(url_for('posts'))


# Comment CRUD
@app.route('/comments/create/<int:post_id>', methods=['POST'])
@login_required
def create_comment(post_id):
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            post_id=post_id,
            user_id=session['user_id']
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added!', 'success')
    return redirect(url_for('view_post', id=post_id))


@app.route('/comments/<int:id>/delete', methods=['POST'])
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    post_id = comment.post_id

    # Check if user owns this comment
    if comment.user_id != session['user_id']:
        flash('You can only delete your own comments!', 'error')
        return redirect(url_for('view_post', id=post_id))

    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted!', 'success')
    return redirect(url_for('view_post', id=post_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)