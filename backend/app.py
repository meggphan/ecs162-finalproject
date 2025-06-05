from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://localhost:5173"
])

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# MongoDB connection
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['forum_db']
    posts_collection = db['posts']
    client.admin.command('ping')
    print("MongoDB connected successfully")
    mongodb_connected = True
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    posts_collection = None
    mongodb_connected = False

def serialize_doc(doc):
    """Convert ObjectId to string for JSON serialization"""
    if doc:
        doc['_id'] = str(doc['_id'])
        if 'created_at' in doc:
            doc['created_at'] = doc['created_at'].isoformat()
        if 'updated_at' in doc:
            doc['updated_at'] = doc['updated_at'].isoformat()
    return doc

# SERVE UPLOADED FILES
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# API ROUTES FOR POSTS
@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Get all posts with basic info"""
    try:
        if not mongodb_connected:
            return jsonify({'error': 'Database not available'}), 500
            
        posts = list(posts_collection.find().sort('created_at', -1))
        
        for post in posts:
            post = serialize_doc(post)
        
        return jsonify({'posts': posts}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts', methods=['POST'])
def create_post():
    """Create a new post with optional image"""
    try:
        if not mongodb_connected:
            return jsonify({'error': 'Database not available'}), 500
            
        title = request.form.get('title')
        content = request.form.get('content')
        author = request.form.get('author')
        
        if not title or not content or not author:
            return jsonify({'error': 'Title, content, and author name are required'}), 400
        
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                file.save(filepath)
                image_url = f"/uploads/{unique_filename}"
        
        post = {
            'title': title,
            'content': content,
            'author': author,
            'image_url': image_url,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = posts_collection.insert_one(post)
        post['_id'] = str(result.inserted_id)
        
        return jsonify({
            'message': 'Post created successfully',
            'post': serialize_doc(post)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/<post_id>', methods=['GET'])
def get_post(post_id):
    """Get a specific post"""
    try:
        if not mongodb_connected:
            return jsonify({'error': 'Database not available'}), 500
            
        post = posts_collection.find_one({'_id': ObjectId(post_id)})
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        post = serialize_doc(post)
        
        return jsonify({'post': post}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Delete a specific post and its image"""
    try:
        if not mongodb_connected:
            return jsonify({'error': 'Database not available'}), 500
            
        post = posts_collection.find_one({'_id': ObjectId(post_id)})
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        if post.get('image_url'):
            try:
                filename = post['image_url'].split('/')[-1]
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"Deleted image file: {filename}")
            except Exception as e:
                print(f"Error deleting image file: {e}")
        
        posts_collection.delete_one({'_id': ObjectId(post_id)})
        
        return jsonify({
            'message': 'Post deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ERROR HANDLERS
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'API endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)