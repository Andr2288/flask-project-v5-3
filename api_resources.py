from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import jsonify
from models import db, User, Post, Comment
from datetime import datetime

api = Api()

# Parser for user registration/login
user_parser = reqparse.RequestParser()
user_parser.add_argument('username', type=str, required=True, help='Username is required')
user_parser.add_argument('email', type=str, required=True, help='Email is required')
user_parser.add_argument('password', type=str, required=True, help='Password is required')

# Parser for posts
post_parser = reqparse.RequestParser()
post_parser.add_argument('title', type=str, required=True, help='Title is required')
post_parser.add_argument('content', type=str, required=True, help='Content is required')

# Parser for comments
comment_parser = reqparse.RequestParser()
comment_parser.add_argument('content', type=str, required=True, help='Content is required')


class UsersAPI(Resource):
    def get(self):
        """Get all users"""
        users = User.query.all()
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat()
        } for user in users])

    def post(self):
        """Create new user"""
        args = user_parser.parse_args()

        # Check if user exists
        if User.query.filter_by(username=args['username']).first():
            return {'message': 'Username already exists'}, 400
        if User.query.filter_by(email=args['email']).first():
            return {'message': 'Email already exists'}, 400

        user = User(username=args['username'], email=args['email'])
        user.set_password(args['password'])
        db.session.add(user)
        db.session.commit()

        return {
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, 201


class UserAPI(Resource):
    def get(self, user_id):
        """Get user by ID"""
        user = User.query.get_or_404(user_id)
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'posts_count': len(user.posts),
            'comments_count': len(user.comments)
        }

    @jwt_required()
    def delete(self, user_id):
        """Delete user"""
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            return {'message': 'Access denied'}, 403

        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {'message': 'User deleted successfully'}


class PostsAPI(Resource):
    def get(self):
        """Get all posts"""
        posts = Post.query.order_by(Post.created_at.desc()).all()
        return jsonify([{
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author': post.author.username,
            'created_at': post.created_at.isoformat(),
            'comments_count': len(post.comments)
        } for post in posts])

    @jwt_required()
    def post(self):
        """Create new post"""
        args = post_parser.parse_args()
        current_user_id = get_jwt_identity()

        post = Post(
            title=args['title'],
            content=args['content'],
            user_id=current_user_id
        )
        db.session.add(post)
        db.session.commit()

        return {
            'message': 'Post created successfully',
            'post': {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'author': post.author.username
            }
        }, 201


class PostAPI(Resource):
    def get(self, post_id):
        """Get post by ID"""
        post = Post.query.get_or_404(post_id)
        return {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author': post.author.username,
            'created_at': post.created_at.isoformat(),
            'updated_at': post.updated_at.isoformat() if post.updated_at else None,
            'comments': [{
                'id': comment.id,
                'content': comment.content,
                'author': comment.author.username,
                'created_at': comment.created_at.isoformat()
            } for comment in post.comments]
        }

    @jwt_required()
    def put(self, post_id):
        """Update post"""
        args = post_parser.parse_args()
        current_user_id = get_jwt_identity()

        post = Post.query.get_or_404(post_id)
        if post.user_id != current_user_id:
            return {'message': 'Access denied'}, 403

        post.title = args['title']
        post.content = args['content']
        post.updated_at = datetime.utcnow()
        db.session.commit()

        return {
            'message': 'Post updated successfully',
            'post': {
                'id': post.id,
                'title': post.title,
                'content': post.content
            }
        }

    @jwt_required()
    def delete(self, post_id):
        """Delete post"""
        current_user_id = get_jwt_identity()

        post = Post.query.get_or_404(post_id)
        if post.user_id != current_user_id:
            return {'message': 'Access denied'}, 403

        db.session.delete(post)
        db.session.commit()
        return {'message': 'Post deleted successfully'}


class CommentsAPI(Resource):
    @jwt_required()
    def post(self, post_id):
        """Add comment to post"""
        args = comment_parser.parse_args()
        current_user_id = get_jwt_identity()

        # Check if post exists
        post = Post.query.get_or_404(post_id)

        comment = Comment(
            content=args['content'],
            post_id=post_id,
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


class CommentAPI(Resource):
    @jwt_required()
    def delete(self, comment_id):
        """Delete comment"""
        current_user_id = get_jwt_identity()

        comment = Comment.query.get_or_404(comment_id)
        if comment.user_id != current_user_id:
            return {'message': 'Access denied'}, 403

        db.session.delete(comment)
        db.session.commit()
        return {'message': 'Comment deleted successfully'}


# Register API routes
api.add_resource(UsersAPI, '/api/users')
api.add_resource(UserAPI, '/api/users/<int:user_id>')
api.add_resource(PostsAPI, '/api/posts')
api.add_resource(PostAPI, '/api/posts/<int:post_id>')
api.add_resource(CommentsAPI, '/api/posts/<int:post_id>/comments')
api.add_resource(CommentAPI, '/api/comments/<int:comment_id>')