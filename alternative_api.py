"""
Alternative API routes when Flask-Potion is not available
Provides similar functionality using standard Flask routes
"""

from flask import Blueprint, request, jsonify
from models import db, User, Post, Comment
from flask_jwt_extended import jwt_required, get_jwt_identity
import math

alternative_api = Blueprint('alternative_api', __name__)


@alternative_api.route('/alt/users', methods=['GET'])
def get_users():
    """Get all users with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)  # Limit to 100 per page
    
    users_query = User.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    users = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat(),
        'posts_count': len(user.posts),
        'comments_count': len(user.comments)
    } for user in users_query.items]
    
    return jsonify({
        'users': users,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': users_query.total,
            'pages': users_query.pages,
            'has_next': users_query.has_next,
            'has_prev': users_query.has_prev
        }
    })


@alternative_api.route('/alt/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID with statistics"""
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat(),
        'stats': {
            'posts_count': len(user.posts),
            'comments_count': len(user.comments),
            'latest_post': user.posts[-1].title if user.posts else None,
            'latest_post_date': user.posts[-1].created_at.isoformat() if user.posts else None
        },
        'recent_posts': [{
            'id': post.id,
            'title': post.title,
            'created_at': post.created_at.isoformat(),
            'comments_count': len(post.comments)
        } for post in user.posts[-5:]]  # Last 5 posts
    })


@alternative_api.route('/alt/posts', methods=['GET'])
def get_posts():
    """Get all posts with filtering and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    author = request.args.get('author')
    search = request.args.get('search')
    sort_by = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    
    per_page = min(per_page, 100)
    
    # Build query
    query = Post.query
    
    # Filter by author
    if author:
        query = query.join(User).filter(User.username.contains(author))
    
    # Search in title and content
    if search:
        query = query.filter(
            db.or_(
                Post.title.contains(search),
                Post.content.contains(search)
            )
        )
    
    # Sort
    if sort_by == 'title':
        sort_column = Post.title
    elif sort_by == 'updated_at':
        sort_column = Post.updated_at
    else:
        sort_column = Post.created_at
    
    if order.lower() == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # Paginate
    posts_query = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    posts = [{
        'id': post.id,
        'title': post.title,
        'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
        'author': post.author.username,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat() if post.updated_at else None,
        'comments_count': len(post.comments)
    } for post in posts_query.items]
    
    return jsonify({
        'posts': posts,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': posts_query.total,
            'pages': posts_query.pages,
            'has_next': posts_query.has_next,
            'has_prev': posts_query.has_prev
        },
        'filters': {
            'author': author,
            'search': search,
            'sort_by': sort_by,
            'order': order
        }
    })


@alternative_api.route('/alt/posts/<int:post_id>/analytics', methods=['GET'])
def get_post_analytics(post_id):
    """Get detailed post analytics"""
    post = Post.query.get_or_404(post_id)
    
    return jsonify({
        'post_id': post.id,
        'title': post.title,
        'author': post.author.username,
        'created_at': post.created_at.isoformat(),
        'analytics': {
            'word_count': len(post.content.split()),
            'character_count': len(post.content),
            'paragraph_count': len(post.content.split('\n\n')),
            'comments_count': len(post.comments),
            'engagement_score': len(post.comments) * 2 + len(post.content.split()) * 0.1,
            'readability_score': min(100, max(0, 100 - len(post.content.split()) * 0.1))
        },
        'comments_stats': {
            'total_comments': len(post.comments),
            'unique_commenters': len(set(comment.user_id for comment in post.comments)),
            'average_comment_length': sum(len(comment.content) for comment in post.comments) / len(post.comments) if post.comments else 0
        }
    })


@alternative_api.route('/alt/search', methods=['GET'])
def search_content():
    """Universal search endpoint"""
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')  # all, posts, users, comments
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    results = {}
    
    if search_type in ['all', 'posts']:
        posts = Post.query.filter(
            db.or_(
                Post.title.contains(query),
                Post.content.contains(query)
            )
        ).limit(limit).all()
        
        results['posts'] = [{
            'id': post.id,
            'title': post.title,
            'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
            'author': post.author.username,
            'created_at': post.created_at.isoformat(),
            'relevance_score': post.title.lower().count(query.lower()) * 2 + post.content.lower().count(query.lower())
        } for post in posts]
        
        # Sort by relevance
        results['posts'].sort(key=lambda x: x['relevance_score'], reverse=True)
    
    if search_type in ['all', 'users']:
        users = User.query.filter(
            db.or_(
                User.username.contains(query),
                User.email.contains(query)
            )
        ).limit(limit).all()
        
        results['users'] = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'posts_count': len(user.posts),
            'comments_count': len(user.comments)
        } for user in users]
    
    if search_type in ['all', 'comments']:
        comments = Comment.query.filter(
            Comment.content.contains(query)
        ).limit(limit).all()
        
        results['comments'] = [{
            'id': comment.id,
            'content': comment.content[:100] + '...' if len(comment.content) > 100 else comment.content,
            'author': comment.author.username,
            'post_title': comment.post.title,
            'created_at': comment.created_at.isoformat()
        } for comment in comments]
    
    return jsonify({
        'query': query,
        'search_type': search_type,
        'results': results,
        'total_found': sum(len(result_list) for result_list in results.values())
    })


@alternative_api.route('/alt/stats', methods=['GET'])
def get_statistics():
    """Get comprehensive blog statistics"""
    users_count = User.query.count()
    posts_count = Post.query.count()
    comments_count = Comment.query.count()
    
    # Most active user
    most_active_user = db.session.query(User).join(Post).group_by(User.id).order_by(
        db.func.count(Post.id).desc()
    ).first()
    
    # Most commented post
    most_commented_post = db.session.query(Post).join(Comment).group_by(Post.id).order_by(
        db.func.count(Comment.id).desc()
    ).first()
    
    # Recent activity
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
    
    return jsonify({
        'overview': {
            'total_users': users_count,
            'total_posts': posts_count,
            'total_comments': comments_count,
            'most_active_user': most_active_user.username if most_active_user else None,
            'most_commented_post': most_commented_post.title if most_commented_post else None,
            'average_posts_per_user': round(posts_count / users_count, 2) if users_count > 0 else 0,
            'average_comments_per_post': round(comments_count / posts_count, 2) if posts_count > 0 else 0
        },
        'recent_activity': {
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
    })


@alternative_api.route('/alt/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment_alt(post_id):
    """Add comment to post (alternative endpoint)"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({'error': 'Content is required'}), 400
    
    # Check if post exists
    post = Post.query.get_or_404(post_id)
    
    comment = Comment(
        content=data['content'],
        post_id=post_id,
        user_id=current_user_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'message': 'Comment added successfully',
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'author': comment.author.username,
            'created_at': comment.created_at.isoformat()
        }
    }), 201


@alternative_api.route('/alt/health', methods=['GET'])
def health_check():
    """Health check for alternative API"""
    return jsonify({
        'status': 'healthy',
        'service': 'alternative_api',
        'message': 'Alternative API is running (Flask-Potion replacement)',
        'endpoints_available': [
            '/alt/users',
            '/alt/posts', 
            '/alt/search',
            '/alt/stats'
        ]
    })