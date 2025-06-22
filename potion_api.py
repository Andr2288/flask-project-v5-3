from flask_potion import Api, ModelResource, Route, fields
from flask_potion.contrib.alchemy import SQLAlchemyManager
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, jsonify
from models import db, User, Post, Comment


class UserResource(ModelResource):
    """User resource with Flask-Potion"""

    class Meta:
        model = User
        manager = SQLAlchemyManager(db.session)
        exclude_fields = ['password_hash']  # Don't expose password hash
        include_id = True

    class Schema:
        username = fields.String(required=True, min_length=3, max_length=80)
        email = fields.String(required=True, pattern=r'^[^@]+@[^@]+\.[^@]+$')
        created_at = fields.DateTime(dump_only=True)

    @Route.GET('/stats')
    def get_user_stats(self, user):
        """Get user statistics"""
        return {
            'posts_count': len(user.posts),
            'comments_count': len(user.comments),
            'joined_date': user.created_at.isoformat(),
            'latest_post': user.posts[-1].title if user.posts else None
        }

    @Route.GET('/posts')
    def get_user_posts(self, user):
        """Get all posts by user"""
        posts = [{
            'id': post.id,
            'title': post.title,
            'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
            'created_at': post.created_at.isoformat(),
            'comments_count': len(post.comments)
        } for post in user.posts]

        return {
            'user': user.username,
            'posts': posts,
            'total': len(posts)
        }

    def before_create(self, properties):
        """Hash password before creating user"""
        if 'password' in properties:
            user = User()
            user.set_password(properties['password'])
            properties['password_hash'] = user.password_hash
            del properties['password']
        return properties


class PostResource(ModelResource):
    """Post resource with Flask-Potion"""

    class Meta:
        model = Post
        manager = SQLAlchemyManager(db.session)
        include_id = True

    class Schema:
        title = fields.String(required=True, min_length=5, max_length=100)
        content = fields.String(required=True, min_length=10)
        user_id = fields.Integer(required=True)
        created_at = fields.DateTime(dump_only=True)
        updated_at = fields.DateTime(dump_only=True)

    @Route.GET('/comments')
    def get_post_comments(self, post):
        """Get all comments for post"""
        comments = [{
            'id': comment.id,
            'content': comment.content,
            'author': comment.author.username,
            'created_at': comment.created_at.isoformat()
        } for comment in post.comments]

        return {
            'post_title': post.title,
            'comments': comments,
            'total_comments': len(comments)
        }

    @Route.POST('/comments')
    @jwt_required()
    def add_comment(self, post):
        """Add comment to post"""
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'content' not in data:
            return {'error': 'Content is required'}, 400

        comment = Comment(
            content=data['content'],
            post_id=post.id,
            user_id=current_user_id
        )

        db.session.add(comment)
        db.session.commit()

        return {
            'message': 'Comment added successfully',
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': comment.author.username
            }
        }, 201

    @Route.GET('/analytics')
    def get_post_analytics(self, post):
        """Get post analytics"""
        return {
            'post_id': post.id,
            'title': post.title,
            'author': post.author.username,
            'created_at': post.created_at.isoformat(),
            'word_count': len(post.content.split()),
            'character_count': len(post.content),
            'comments_count': len(post.comments),
            'engagement_score': len(post.comments) * 2 + len(post.content.split()) * 0.1
        }

    @Route.PUT('/publish')
    @jwt_required()
    def publish_post(self, post):
        """Publish or unpublish post"""
        current_user_id = get_jwt_identity()

        if post.user_id != current_user_id:
            return {'error': 'Access denied'}, 403

        # Add a published field to track post status
        # For now, we'll just update the updated_at field
        from datetime import datetime
        post.updated_at = datetime.utcnow()
        db.session.commit()

        return {
            'message': 'Post published successfully',
            'post_id': post.id,
            'published_at': post.updated_at.isoformat()
        }


class CommentResource(ModelResource):
    """Comment resource with Flask-Potion"""

    class Meta:
        model = Comment
        manager = SQLAlchemyManager(db.session)
        include_id = True

    class Schema:
        content = fields.String(required=True, min_length=5)
        post_id = fields.Integer(required=True)
        user_id = fields.Integer(required=True)
        created_at = fields.DateTime(dump_only=True)

    @Route.GET('/details')
    def get_comment_details(self, comment):
        """Get detailed comment information"""
        return {
            'comment_id': comment.id,
            'content': comment.content,
            'author': {
                'id': comment.author.id,
                'username': comment.author.username,
                'email': comment.author.email
            },
            'post': {
                'id': comment.post.id,
                'title': comment.post.title,
                'author': comment.post.author.username
            },
            'created_at': comment.created_at.isoformat(),
            'word_count': len(comment.content.split()),
            'character_count': len(comment.content)
        }

    @Route.PUT('/approve')
    @jwt_required()
    def approve_comment(self, comment):
        """Approve comment (for moderation)"""
        # In a real app, you'd have approval logic here
        return {
            'message': 'Comment approved',
            'comment_id': comment.id,
            'status': 'approved'
        }


class BlogStatsResource(ModelResource):
    """Special resource for blog statistics"""

    class Meta:
        model = User  # We use User as base model but override routes
        manager = SQLAlchemyManager(db.session)

    @Route.GET('/overview', rel="self")
    def get_blog_overview(self):
        """Get overall blog statistics"""
        users_count = User.query.count()
        posts_count = Post.query.count()
        comments_count = Comment.query.count()

        # Get most active user
        most_active_user = db.session.query(User).join(Post).group_by(User.id).order_by(
            db.func.count(Post.id).desc()
        ).first()

        # Get most commented post
        most_commented_post = db.session.query(Post).join(Comment).group_by(Post.id).order_by(
            db.func.count(Comment.id).desc()
        ).first()

        return {
            'total_users': users_count,
            'total_posts': posts_count,
            'total_comments': comments_count,
            'most_active_user': most_active_user.username if most_active_user else None,
            'most_commented_post': most_commented_post.title if most_commented_post else None,
            'average_posts_per_user': round(posts_count / users_count, 2) if users_count > 0 else 0,
            'average_comments_per_post': round(comments_count / posts_count, 2) if posts_count > 0 else 0
        }

    @Route.GET('/activity')
    def get_recent_activity(self):
        """Get recent activity"""
        recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
        recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()

        return {
            'recent_posts': [{
                'id': post.id,
                'title': post.title,
                'author': post.author.username,
                'created_at': post.created_at.isoformat()
            } for post in recent_posts],
            'recent_comments': [{
                'id': comment.id,
                'content': comment.content[:50] + '...' if len(comment.content) > 50 else comment.content,
                'author': comment.author.username,
                'post_title': comment.post.title,
                'created_at': comment.created_at.isoformat()
            } for comment in recent_comments]
        }


def create_potion_api():
    """Create and configure Flask-Potion API"""
    api = Api()

    # Register resources
    api.add_resource(UserResource)
    api.add_resource(PostResource)
    api.add_resource(CommentResource)
    api.add_resource(BlogStatsResource, '/stats', id_field_class=fields.Integer)

    return api


# Custom route for search functionality
def add_search_routes(api):
    """Add search functionality to API"""

    @api.route('/search/posts')
    def search_posts():
        """Search posts by title or content"""
        query = request.args.get('q', '')
        if not query:
            return {'error': 'Query parameter q is required'}, 400

        posts = Post.query.filter(
            db.or_(
                Post.title.contains(query),
                Post.content.contains(query)
            )
        ).all()

        results = [{
            'id': post.id,
            'title': post.title,
            'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
            'author': post.author.username,
            'created_at': post.created_at.isoformat(),
            'relevance_score': post.title.lower().count(query.lower()) * 2 + post.content.lower().count(query.lower())
        } for post in posts]

        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)

        return {
            'query': query,
            'results': results,
            'total_found': len(results)
        }

    @api.route('/search/users')
    def search_users():
        """Search users by username"""
        query = request.args.get('q', '')
        if not query:
            return {'error': 'Query parameter q is required'}, 400

        users = User.query.filter(User.username.contains(query)).all()

        results = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'posts_count': len(user.posts),
            'comments_count': len(user.comments)
        } for user in users]

        return {
            'query': query,
            'results': results,
            'total_found': len(results)
        }