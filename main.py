from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_migrate import Migrate
from flask_restful import Api as RestfulApi
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import folium
import threading
import asyncio
import time

# Import our modules
from models import db, User, Post, Comment
from forms import LoginForm, RegisterForm, PostForm, CommentForm
from api_resources import api as restful_api
from async_service import run_async_server
from websocket_service import init_socketio
from admin import init_basic_admin
from template_helpers import init_template_helpers

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:1234567890@localhost/flask_crud'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
jwt = JWTManager(app)

# Initialize Flask-RESTful
restful_api.init_app(app)
print("✓ Flask-RESTful API initialized")

# Initialize Flask-SocketIO
socketio = init_socketio(app)
print("✓ Flask-SocketIO initialized")

# Initialize Flask-Admin
admin = init_basic_admin(app)
print("✓ Flask-Admin initialized")

# Initialize template helpers
init_template_helpers(app)
print("✓ Template helpers initialized")


def login_required(f):
    """Simple decorator to check if user is logged in"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# JWT API Authentication endpoint
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """JWT authentication for API"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'message': 'JSON data required'}), 400

        if 'username' not in data or 'password' not in data:
            return jsonify({'message': 'Username and password required'}), 400

        user = User.query.filter_by(username=data['username']).first()
        if user and user.check_password(data['password']):
            access_token = create_access_token(identity=user.id)
            return jsonify({
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        else:
            return jsonify({'message': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'message': f'Login error: {str(e)}'}), 500


# API endpoint for testing different technologies
@app.route('/api/test/technologies')
def test_technologies():
    """Test endpoint to show all integrated technologies"""
    return jsonify({
        'message': 'Technologies integration status',
        'technologies': {
            'Flask': 'Web framework - ✓',
            'MySQL': 'Database - ✓',
            'Flask-SQLAlchemy': 'ORM - ✓',
            'Flask-WTF': 'Forms - ✓',
            'Flask-JWT-Extended': 'Authentication - ✓',
            'Flask-RESTful': 'REST API - ✓ (check /api/posts)',
            'Flask-Migrate': 'Database migrations - ✓',
            'Flask-SocketIO': 'WebSocket - ✓ (check /websocket)',
            'Flask-Admin': 'Administration - ✓ (check /admin)',
            'Jinja2': 'Template engine - ✓',
            'Folium': 'Interactive maps - ✓ (check /map)',
            'aiohttp': 'Async HTTP - ✓ (running on port 8080)',
            'asyncio': 'Async operations - ✓'
        },
        'endpoints': {
            'Web Interface': {
                'Home': '/',
                'Posts': '/posts',
                'Login': '/login',
                'Register': '/register',
                'Map': '/map',
                'WebSocket Test': '/websocket',
                'Admin Panel': '/admin'
            },
            'REST API (Flask-RESTful)': {
                'Users': '/api/users',
                'Posts': '/api/posts',
                'Auth': '/api/auth/login'
            },
            'Async Service (aiohttp)': {
                'Base URL': 'http://localhost:8080',
                'Posts': '/async/posts',
                'External Data': '/async/external',
                'Analytics': '/async/analytics',
                'Health': '/async/health'
            },
            'WebSocket (Flask-SocketIO)': {
                'Test Page': '/websocket',
                'Socket.IO endpoint': '/socket.io/'
            },
            'Admin Panel (Flask-Admin)': {
                'Dashboard': '/admin',
                'Users Management': '/admin/user',
                'Posts Management': '/admin/post',
                'Comments Management': '/admin/comment'
            }
        }
    })


# Routes (keeping existing ones)
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    return render_template('index.html', posts=posts)


@app.route('/map')
def map_view():
    """Show map using folium"""
    # Create map centered on Kyiv
    m = folium.Map(location=[50.4501, 30.5234], zoom_start=10)

    # Add markers
    folium.Marker(
        [50.4501, 30.5234],
        popup="Kyiv - Capital of Ukraine",
        tooltip="Click for information"
    ).add_to(m)

    folium.Marker(
        [49.2331, 28.4682],
        popup="Vinnytsia",
        tooltip="Vinnytsia"
    ).add_to(m)

    # Convert map to HTML
    map_html = m._repr_html_()

    return render_template('map.html', map_html=map_html)


@app.route('/websocket')
def websocket_test():
    """WebSocket test page"""
    return render_template('websocket_test.html')


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

    if comment.user_id != session['user_id']:
        flash('You can only delete your own comments!', 'error')
        return redirect(url_for('view_post', id=post_id))

    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted!', 'success')
    return redirect(url_for('view_post', id=post_id))


def start_async_server():
    """Start the async server in a separate thread"""
    def run_async():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            print("🚀 Starting async server...")
            loop.run_until_complete(run_async_server())
            loop.run_forever()
        except Exception as e:
            print(f"❌ Async server error: {e}")

    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()
    print("✓ Async server thread started")

    # Give it time to start
    time.sleep(2)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # Start async server
    start_async_server()

    print("\n" + "=" * 60)
    print("FLASK CRUD APP - ESSENTIAL TECHNOLOGIES")
    print("=" * 60)
    print("Main Flask app: http://localhost:5000")
    print("Admin Panel: http://localhost:5000/admin")
    print("API endpoints: http://localhost:5000/api/test/technologies")
    print("WebSocket test: http://localhost:5000/websocket")
    print("Async service: http://localhost:8080")
    print("=" * 60)

    # Run with SocketIO support - removed allow_unsafe_werkzeug
    socketio.run(app, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)