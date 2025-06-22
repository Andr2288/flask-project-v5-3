from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_migrate import Migrate
from flask_restful import Api as RestfulApi
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import folium
import threading
import asyncio
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# Import our modules
from models import db, User, Post, Comment
from forms import LoginForm, RegisterForm, PostForm, CommentForm
from api_resources import api as restful_api
from async_service import run_async_server

# Try to import SOAP service, make it optional
try:
    from soap_service import wsgi_soap_app

    SOAP_AVAILABLE = True
    SOAP_TYPE = "spyne"
except ImportError as e:
    print(f"Warning: Spyne SOAP service not available - {e}")
    print("Using simple SOAP service instead...")
    try:
        from simple_soap_service import simple_soap

        SOAP_AVAILABLE = True
        SOAP_TYPE = "simple"
        wsgi_soap_app = None
    except ImportError:
        print("Error: Could not load any SOAP service")
        SOAP_AVAILABLE = False
        SOAP_TYPE = None
        wsgi_soap_app = None

# Try to import Flask-Potion, make it optional
try:
    from potion_api import create_potion_api, add_search_routes

    POTION_AVAILABLE = True
    print("✓ Flask-Potion loaded successfully")
except ImportError as e:
    print(f"Warning: Flask-Potion not available - {e}")
    print("This is due to Werkzeug compatibility. Potion features will be disabled.")
    POTION_AVAILABLE = False
    create_potion_api = None
    add_search_routes = None

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

# Initialize Flask-Potion if available
if POTION_AVAILABLE:
    potion_api = create_potion_api()
    potion_api.init_app(app)
    add_search_routes(potion_api)
    print("✓ Flask-Potion API initialized")
else:
    # Use alternative API when Potion is not available
    from alternative_api import alternative_api

    app.register_blueprint(alternative_api)
    potion_api = None
    print("✓ Alternative API initialized (Flask-Potion replacement)")
    print("⚠️  Flask-Potion API disabled (compatibility issue)")

# Mount SOAP service if available
if SOAP_AVAILABLE:
    if SOAP_TYPE == "spyne" and wsgi_soap_app:
        app.wsgi_app = DispatcherMiddleware(
            app.wsgi_app,
            {'/soap': wsgi_soap_app}
        )
    elif SOAP_TYPE == "simple":
        app.register_blueprint(simple_soap, url_prefix='/simple_soap')


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
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return {'message': 'Username and password required'}, 400

    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return {
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }
    else:
        return {'message': 'Invalid credentials'}, 401


# API endpoint for testing different technologies
@app.route('/api/test/technologies')
def test_technologies():
    """Test endpoint to show all integrated technologies"""
    if SOAP_AVAILABLE:
        if SOAP_TYPE == "spyne":
            soap_status = "✓ (Full spyne implementation)"
            soap_url = "/soap?wsdl"
        else:
            soap_status = "✓ (Simple XML implementation)"
            soap_url = "/simple_soap/soap?wsdl"
    else:
        soap_status = "❌ (Not available)"
        soap_url = "Not available"

    potion_status = "✓" if POTION_AVAILABLE else "✓ (Alternative implementation)"
    potion_endpoints = {
        'Users': '/users',
        'Posts': '/posts',
        'Comments': '/comments',
        'Stats': '/stats',
        'Search Posts': '/search/posts?q=query',
        'Search Users': '/search/users?q=query'
    } if POTION_AVAILABLE else {
        'Users': '/alt/users',
        'Posts': '/alt/posts',
        'Search': '/alt/search?q=query',
        'Stats': '/alt/stats',
        'Health': '/alt/health'
    }

    return {
        'message': 'Technologies integration status',
        'technologies': {
            'Flask': 'Web framework - ✓',
            'MySQL': 'Database - ✓',
            'Flask-SQLAlchemy': 'ORM - ✓',
            'Flask-WTF': 'Forms - ✓',
            'Flask-JWT-Extended': 'Authentication - ✓',
            'Flask-RESTful': 'REST API - ✓ (check /api/posts)',
            'Flask-SOAP': f'SOAP service - {soap_status}',
            'Flask-Potion': f'Advanced REST API - {potion_status}',
            'Flask-Migrate': 'Database migrations - ✓',
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
                'Map': '/map'
            },
            'REST API (Flask-RESTful)': {
                'Users': '/api/users',
                'Posts': '/api/posts',
                'Auth': '/api/auth/login'
            },
            'Potion API': potion_endpoints,
            'SOAP Service': {
                'WSDL': soap_url,
                'Endpoint': soap_url.replace('?wsdl', '') if soap_url != 'Not available' else 'Not available'
            },
            'Async Service (aiohttp)': {
                'Base URL': 'http://localhost:8080',
                'Posts': '/async/posts',
                'External Data': '/async/external',
                'Analytics': '/async/analytics',
                'WebSocket': '/async/ws',
                'Health': '/async/health'
            }
        }
    }


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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_async_server())
        loop.run_forever()

    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()
    print("Async server thread started")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # Start async server
    start_async_server()

    print("\n" + "=" * 60)
    print("FLASK CRUD APP WITH ALL TECHNOLOGIES")
    print("=" * 60)
    print("Main Flask app: http://localhost:5000")
    print("API endpoints: http://localhost:5000/api/test/technologies")
    if SOAP_AVAILABLE:
        if SOAP_TYPE == "spyne":
            print("SOAP service: http://localhost:5000/soap?wsdl")
        else:
            print("SOAP service: http://localhost:5000/simple_soap/soap?wsdl")
    else:
        print("SOAP service: Not available")

    if POTION_AVAILABLE:
        print("Potion API: http://localhost:5000/users (and other endpoints)")
    else:
        print("Alternative API: http://localhost:5000/alt/users (Potion replacement)")
        print("Alternative features: /alt/search, /alt/stats, etc.")

    print("Async service: http://localhost:8080")
    print("=" * 60)

    app.run(debug=True, use_reloader=False)