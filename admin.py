from flask import session, redirect, url_for, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import BaseForm
from models import db, User, Post, Comment


class NoCSRFForm(BaseForm):
    """Form without CSRF protection"""

    class Meta:
        csrf = False


class AdminAuthMixin:
    """Mixin to require admin authentication"""

    def is_accessible(self):
        if 'user_id' not in session:
            return False
        user = User.query.get(session['user_id'])
        if not user:
            return False
        return user.username in ['admin', 'admin2']

    def inaccessible_callback(self, name, **kwargs):
        flash('You need admin rights to access this page.', 'error')
        return redirect(url_for('login'))


class BasicAdminIndexView(AdminAuthMixin, AdminIndexView):
    @expose('/')
    def index(self):
        users_count = User.query.count()
        posts_count = Post.query.count()
        comments_count = Comment.query.count()

        return self.render('admin/index.html',
                           users_count=users_count,
                           posts_count=posts_count,
                           comments_count=comments_count)


class BasicUserAdmin(AdminAuthMixin, ModelView):
    form_base_class = NoCSRFForm
    column_exclude_list = ['password_hash']
    form_excluded_columns = ['password_hash']
    column_searchable_list = ['username', 'email']
    column_filters = ['username', 'email', 'created_at']

    def on_model_change(self, form, model, is_created):
        if is_created and not hasattr(model, 'password_hash'):
            model.set_password('123456')


class BasicPostAdmin(AdminAuthMixin, ModelView):
    form_base_class = NoCSRFForm
    column_searchable_list = ['title', 'content']
    column_filters = ['title', 'created_at', 'user_id']
    column_list = ['id', 'title', 'author', 'created_at']


class BasicCommentAdmin(AdminAuthMixin, ModelView):
    form_base_class = NoCSRFForm
    column_searchable_list = ['content']
    column_filters = ['created_at', 'user_id', 'post_id']
    column_list = ['id', 'content', 'author', 'post', 'created_at']


def init_basic_admin(app):
    """Initialize Flask-Admin"""
    admin = Admin(
        app,
        name='Flask CRUD Admin',
        template_mode='bootstrap4',
        index_view=BasicAdminIndexView()
    )

    admin.add_view(BasicUserAdmin(User, db.session, name='Users'))
    admin.add_view(BasicPostAdmin(Post, db.session, name='Posts'))
    admin.add_view(BasicCommentAdmin(Comment, db.session, name='Comments'))

    return admin