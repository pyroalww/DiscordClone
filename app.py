# LICENSE: APACHE LICENSE
# OWNER: PYROALWW
# WWW.PYROLLC.COM.TR

from flask import Flask, request, jsonify, send_from_directory, g
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_babel import Babel, gettext
from elasticsearch import Elasticsearch
import json
import jwt
from functools import wraps
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import uuid
import re
import requests
from pydub import AudioSegment
import threading
import schedule
import time
import boto3
from botocore.exceptions import ClientError
import openai
from profanity_check import predict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
import string
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cok_gizli_anahtar'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size
app.config['LANGUAGES'] = ['en', 'tr', 'es', 'fr', 'de']
socketio = SocketIO(app, cors_allowed_origins="*")
babel = Babel(app)
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

s3 = boto3.client('s3')
S3_BUCKET = 'your-s3-bucket-name'

openai.api_key = 'your-openai-api-key'

DB_FILE = 'database.json'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
def load_db():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "users": [],
            "channels": [],
            "messages": [],
            "friendships": [],
            "categories": [],
            "guilds": [],
            "roles": [],
            "permissions": [],
            "user_roles": [],
            "blocked_users": [],
            "reactions": [],
            "activity_logs": []
        }

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=2)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = next((u for u in load_db()['users'] if u['username'] == data['username']), None)
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

def translate(text):
    return gettext(text)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def has_permission(user_id, permission_name, guild_id=None, channel_id=None):
    db = load_db()
    user_roles = [ur['role_id'] for ur in db['user_roles'] if ur['user_id'] == user_id]
    permissions = [p for p in db['permissions'] if p['role_id'] in user_roles and p['name'] == permission_name]
    
    if guild_id:
        permissions = [p for p in permissions if p['guild_id'] == guild_id]
    if channel_id:
        permissions = [p for p in permissions if p['channel_id'] == channel_id]
    
    return len(permissions) > 0

def log_activity(user_id, action, details=None):
    db = load_db()
    log = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'action': action,
        'details': details,
        'timestamp': datetime.utcnow().isoformat()
    }
    db['activity_logs'].append(log)
    save_db(db)

@app.route('/register', methods=['POST'])
def register():
    db = load_db()
    user = request.json
    if any(u['username'] == user['username'] for u in db['users']):
        return jsonify({"error": "Username is already taken"}), 400
    user['id'] = str(uuid.uuid4())
    user['role'] = 'user'
    user['online'] = False
    db['users'].append(user)
    save_db(db)
    log_activity(user['id'], 'user_registered')
    return jsonify(user), 201

@app.route('/login', methods=['POST'])
def login():
    db = load_db()
    auth = request.json
    user = next((u for u in db['users'] if u['username'] == auth['username'] and u['password'] == auth['password']), None)
    if user:
        token = jwt.encode({'username': user['username'], 'exp': datetime.utcnow() + timedelta(hours=24)}, app.config['SECRET_KEY'])
        user['online'] = True
        save_db(db)
        socketio.emit('user_online', {'user_id': user['id']}, broadcast=True)
        log_activity(user['id'], 'user_logged_in')
        return jsonify({'token': token, 'user_id': user['id']})
    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    db = load_db()
    user = next(u for u in db['users'] if u['id'] == current_user['id'])
    user['online'] = False
    save_db(db)
    socketio.emit('user_offline', {'user_id': user['id']}, broadcast=True)
    log_activity(user['id'], 'user_logged_out')
    return jsonify({"message": "Logged out successfully"})

@app.route('/guilds', methods=['GET', 'POST'])
@token_required
def guilds(current_user):
    db = load_db()
    if request.method == 'GET':
        return jsonify(db['guilds'])
    elif request.method == 'POST':
        if not has_permission(current_user['id'], 'create_guild'):
            return jsonify({"error": "You don't have permission to create a guild"}), 403
        guild = request.json
        guild['id'] = str(uuid.uuid4())
        guild['owner_id'] = current_user['id']
        db['guilds'].append(guild)
        save_db(db)
        log_activity(current_user['id'], 'guild_created', {'guild_id': guild['id']})
        return jsonify(guild), 201
@app.route('/guilds/<guild_id>/settings', methods=['GET', 'PUT'])
@token_required
def guild_settings(current_user, guild_id):
    db = load_db()
    guild = next((g for g in db['guilds'] if g['id'] == guild_id), None)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    if not has_permission(current_user['id'], 'manage_guild', guild_id=guild_id):
        return jsonify({"error": "You don't have permission to manage this guild"}), 403

    if request.method == 'GET':
        return jsonify({
            'name': guild['name'],
            'icon': guild.get('icon'),
            'owner_id': guild['owner_id'],
            'region': guild.get('region'),
            'verification_level': guild.get('verification_level', 0),
            'default_notifications': guild.get('default_notifications', 'all_messages'),
            'explicit_content_filter': guild.get('explicit_content_filter', 'disabled'),
            'afk_timeout': guild.get('afk_timeout', 300),
            'afk_channel_id': guild.get('afk_channel_id')
        })
    elif request.method == 'PUT':
        guild['name'] = request.json.get('name', guild['name'])
        guild['icon'] = request.json.get('icon', guild.get('icon'))
        guild['region'] = request.json.get('region', guild.get('region'))
        guild['verification_level'] = request.json.get('verification_level', guild.get('verification_level', 0))
        guild['default_notifications'] = request.json.get('default_notifications', guild.get('default_notifications', 'all_messages'))
        guild['explicit_content_filter'] = request.json.get('explicit_content_filter', guild.get('explicit_content_filter', 'disabled'))
        guild['afk_timeout'] = request.json.get('afk_timeout', guild.get('afk_timeout', 300))
        guild['afk_channel_id'] = request.json.get('afk_channel_id', guild.get('afk_channel_id'))
        save_db(db)
        log_activity(current_user['id'], 'guild_settings_updated', {'guild_id': guild_id})
        return jsonify(guild), 200
@app.route('/search', methods=['GET'])
@token_required
def search(current_user):
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    
    if search_type == 'messages':
        result = es.search(index="messages", body={"query": {"match": {"content": query}}})
    elif search_type == 'users':
        result = es.search(index="users", body={"query": {"match": {"username": query}}})
    elif search_type == 'channels':
        result = es.search(index="channels", body={"query": {"match": {"name": query}}})
    else:
        result = es.multi_search(
            index=["messages", "users", "channels"],
            body=[
                {},
                {"query": {"match": {"content": query}}},
                {},
                {"query": {"match": {"username": query}}},
                {},
                {"query": {"match": {"name": query}}}
            ]
        )
    
    return jsonify(result['hits']['hits'])

@app.route('/roles', methods=['GET', 'POST'])
@token_required
def roles(current_user):
    db = load_db()
    if request.method == 'GET':
        return jsonify(db.get('roles', []))
    elif request.method == 'POST':
        if not has_permission(current_user['id'], 'manage_roles'):
            return jsonify({"error": translate("You don't have permission to manage roles")}), 403
        new_role = {
            'id': str(uuid.uuid4()),
            'name': request.json['name'],
            'color': request.json.get('color'),
            'permissions': request.json['permissions'],
            'position': request.json['position'],
            'created_by': current_user['id'],
            'created_at': datetime.utcnow().isoformat()
        }
        if 'roles' not in db:
            db['roles'] = []
        db['roles'].append(new_role)
        save_db(db)
        log_activity(current_user['id'], 'role_created', {'role_id': new_role['id']})
        return jsonify(new_role), 201
@app.route('/events', methods=['GET', 'POST'])
@token_required
def events(current_user):
    db = load_db()
    if request.method == 'GET':
        return jsonify(db.get('events', []))
    elif request.method == 'POST':
        new_event = {
            'id': str(uuid.uuid4()),
            'title': request.json['title'],
            'description': request.json['description'],
            'start_time': request.json['start_time'],
            'end_time': request.json['end_time'],
            'created_by': current_user['id'],
            'created_at': datetime.utcnow().isoformat(),
            'participants': [current_user['id']]
        }
        if 'events' not in db:
            db['events'] = []
        db['events'].append(new_event)
        save_db(db)
        log_activity(current_user['id'], 'event_created', {'event_id': new_event['id']})
        return jsonify(new_event), 201

@app.route('/events/<event_id>/participate', methods=['POST'])
@token_required
def participate_event(current_user, event_id):
    db = load_db()
    event = next((e for e in db.get('events', []) if e['id'] == event_id), None)
    if not event:
        return jsonify({"error": translate("Event not found")}), 404

    if current_user['id'] not in event['participants']:
        event['participants'].append(current_user['id'])
        save_db(db)
        log_activity(current_user['id'], 'event_joined', {'event_id': event_id})
    return jsonify(event), 200

@app.route('/emojis', methods=['GET', 'POST'])
@token_required
def emojis(current_user):
    db = load_db()
    if request.method == 'GET':
        return jsonify(db.get('emojis', []))
    elif request.method == 'POST':
        if not has_permission(current_user['id'], 'manage_emojis'):
            return jsonify({"error": translate("You don't have permission to manage emojis")}), 403
        new_emoji = {
            'id': str(uuid.uuid4()),
            'name': request.json['name'],
            'image_url': request.json['image_url'],
            'created_by': current_user['id'],
            'created_at': datetime.utcnow().isoformat()
        }
        if 'emojis' not in db:
            db['emojis'] = []
        db['emojis'].append(new_emoji)
        save_db(db)
        log_activity(current_user['id'], 'emoji_created', {'emoji_id': new_emoji['id']})
        return jsonify(new_emoji), 201

@app.route('/stickers', methods=['GET', 'POST'])
@token_required
def stickers(current_user):
    db = load_db()
    if request.method == 'GET':
        return jsonify(db.get('stickers', []))
    elif request.method == 'POST':
        if not has_permission(current_user['id'], 'manage_stickers'):
            return jsonify({"error": translate("You don't have permission to manage stickers")}), 403
        new_sticker = {
            'id': str(uuid.uuid4()),
            'name': request.json['name'],
            'image_url': request.json['image_url'],
            'created_by': current_user['id'],
            'created_at': datetime.utcnow().isoformat()
        }
        if 'stickers' not in db:
            db['stickers'] = []
        db['stickers'].append(new_sticker)
        save_db(db)
        log_activity(current_user['id'], 'sticker_created', {'sticker_id': new_sticker['id']})
        return jsonify(new_sticker), 201

@app.route('/bots', methods=['GET', 'POST'])
@token_required
def bots(current_user):
    db = load_db()
    if request.method == 'GET':
        return jsonify(db.get('bots', []))
    elif request.method == 'POST':
        if not has_permission(current_user['id'], 'manage_bots'):
            return jsonify({"error": translate("You don't have permission to manage bots")}), 403
        new_bot = {
            'id': str(uuid.uuid4()),
            'name': request.json['name'],
            'avatar': request.json.get('avatar'),
            'token': str(uuid.uuid4()),
            'created_by': current_user['id'],
            'created_at': datetime.utcnow().isoformat()
        }
        if 'bots' not in db:
            db['bots'] = []
        db['bots'].append(new_bot)
        save_db(db)
        log_activity(current_user['id'], 'bot_created', {'bot_id': new_bot['id']})
        return jsonify(new_bot), 201

@app.route('/bots/<bot_id>/commands', methods=['GET', 'POST'])
@token_required
def bot_commands(current_user, bot_id):
    db = load_db()
    bot = next((b for b in db.get('bots', []) if b['id'] == bot_id), None)
    if not bot:
        return jsonify({"error": translate("Bot not found")}), 404

    if request.method == 'GET':
        return jsonify(bot.get('commands', []))
    elif request.method == 'POST':
        if not has_permission(current_user['id'], 'manage_bots') and current_user['id'] != bot['created_by']:
            return jsonify({"error": translate("You don't have permission to manage this bot")}), 403
        new_command = {
            'id': str(uuid.uuid4()),
            'name': request.json['name'],
            'description': request.json['description'],
            'usage': request.json['usage']
        }
        if 'commands' not in bot:
            bot['commands'] = []
        bot['commands'].append(new_command)
        save_db(db)
        log_activity(current_user['id'], 'bot_command_created', {'bot_id': bot_id, 'command_id': new_command['id']})
        return jsonify(new_command), 201

@app.route('/statistics/users/<user_id>', methods=['GET'])
@token_required
def user_statistics(current_user, user_id):
    db = load_db()
    user = next((u for u in db['users'] if u['id'] == user_id), None)
    if not user:
        return jsonify({"error": translate("User not found")}), 404

    messages = [m for m in db['messages'] if m['author_id'] == user_id]
    return jsonify({
        'total_messages': len(messages),
        'guilds_joined': len(set(m['guild_id'] for m in messages)),
        'first_message_date': min(m['timestamp'] for m in messages) if messages else None,
        'last_message_date': max(m['timestamp'] for m in messages) if messages else None
    })
def send_notification(user_id, message):
    # In a real application, this would send a push notification or email
    print(f"Sending notification to user {user_id}: {message}")

@app.route('/notifications/settings', methods=['GET', 'PUT'])
@token_required
def notification_settings(current_user):
    db = load_db()
    if request.method == 'GET':
        return jsonify(current_user.get('notification_settings', {}))
    elif request.method == 'PUT':
        current_user['notification_settings'] = request.json
        save_db(db)
        return jsonify(current_user['notification_settings']), 200

@socketio.on('update_status')
def update_status(data):
    db = load_db()
    user = next((u for u in db['users'] if u['id'] == request.sid), None)
    if user:
        user['status'] = data['status']
        user['game_activity'] = data.get('game_activity')
        save_db(db)
        emit('user_status_updated', {
            'user_id': user['id'],
            'status': user['status'],
            'game_activity': user['game_activity']
        }, broadcast=True)

def check_scheduled_events():
    db = load_db()
    now = datetime.utcnow()
    for event in db.get('scheduled_events', []):
        if datetime.fromisoformat(event['scheduled_time']) <= now and not event.get('notified'):
            for user_id in event['participants']:
                send_notification(user_id, f"Event '{event['name']}' is starting now!")
            event['notified'] = True
    save_db(db)
@app.route('/statistics/guilds/<guild_id>', methods=['GET'])
@token_required
def guild_statistics(current_user, guild_id):
    db = load_db()
    guild = next((g for g in db['guilds'] if g['id'] == guild_id), None)
    if not guild:
        return jsonify({"error": translate("Guild not found")}), 404

    if not has_permission(current_user['id'], 'view_guild_stats', guild_id=guild_id):
        return jsonify({"error": translate("You don't have permission to view guild statistics")}), 403

    messages = [m for m in db['messages'] if m['guild_id'] == guild_id]
    return jsonify({
        'total_messages': len(messages),
        'active_users': len(set(m['author_id'] for m in messages)),
        'most_active_channel': max(set(m['channel_id'] for m in messages), key=lambda c: len([m for m in messages if m['channel_id'] == c])),
        'messages_per_day': len(messages) / ((datetime.utcnow() - datetime.fromisoformat(guild['created_at'])).days or 1)
    })
@app.route('/guilds/<guild_id>/webhooks', methods=['GET', 'POST'])
@token_required
def guild_webhooks(current_user, guild_id):
    db = load_db()
    guild = next((g for g in db['guilds'] if g['id'] == guild_id), None)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    if not has_permission(current_user['id'], 'manage_webhooks', guild_id=guild_id):
        return jsonify({"error": "You don't have permission to manage webhooks in this guild"}), 403

    if request.method == 'GET':
        webhooks = [w for w in db.get('webhooks', []) if w['guild_id'] == guild_id]
        return jsonify(webhooks)
    elif request.method == 'POST':
        new_webhook = {
            'id': str(uuid.uuid4()),
            'guild_id': guild_id,
            'channel_id': request.json['channel_id'],
            'name': request.json['name'],
            'avatar': request.json.get('avatar'),
            'token': str(uuid.uuid4()),
            'created_by': current_user['id'],
            'created_at': datetime.utcnow().isoformat()
        }
        if 'webhooks' not in db:
            db['webhooks'] = []
        db['webhooks'].append(new_webhook)
        save_db(db)
        log_activity(current_user['id'], 'webhook_created', {'guild_id': guild_id, 'webhook_id': new_webhook['id']})
        return jsonify(new_webhook), 201

@app.route('/webhooks/<webhook_id>', methods=['POST'])
def execute_webhook(webhook_id):
    db = load_db()
    webhook = next((w for w in db.get('webhooks', []) if w['id'] == webhook_id), None)
    if not webhook:
        return jsonify({"error": "Webhook not found"}), 404

    message = {
        'id': str(uuid.uuid4()),
        'channel_id': webhook['channel_id'],
        'content': request.json['content'],
        'author': {
            'username': request.json.get('username', webhook['name']),
            'avatar_url': request.json.get('avatar_url', webhook['avatar'])
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    db['messages'].append(message)
    save_db(db)
    socketio.emit('new_message', message, room=webhook['channel_id'])
    return '', 204

def auto_moderate_message(message):
    # Simple word filter
    forbidden_words = ['badword1', 'badword2', 'badword3']
    for word in forbidden_words:
        if word in message['content'].lower():
            return False
    
    # URL filter
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message['content'])
    for url in urls:
        response = requests.get(url)
        if response.status_code != 200:
            return False
    
    return True

@app.route('/guilds/<guild_id>/channels', methods=['GET', 'POST'])
@token_required
def guild_channels(current_user, guild_id):
    db = load_db()
    if request.method == 'GET':
        channels = [c for c in db['channels'] if c['guild_id'] == guild_id]
        return jsonify(channels)
    elif request.method == 'POST':
        if not has_permission(current_user['id'], 'create_channel', guild_id=guild_id):
            return jsonify({"error": "You don't have permission to create a channel in this guild"}), 403
        channel = request.json
        channel['id'] = str(uuid.uuid4())
        channel['guild_id'] = guild_id
        db['channels'].append(channel)
        save_db(db)
        log_activity(current_user['id'], 'channel_created', {'guild_id': guild_id, 'channel_id': channel['id']})
        return jsonify(channel), 201

@app.route('/channels/<channel_id>/messages', methods=['GET', 'POST'])
@token_required
def messages(current_user, channel_id):
    db = load_db()
    channel = next((c for c in db['channels'] if c['id'] == channel_id), None)
    if not channel:
        return jsonify({"error": "Channel not found"}), 404
    
    if request.method == 'GET':
        if not has_permission(current_user['id'], 'read_messages', guild_id=channel['guild_id'], channel_id=channel_id):
            return jsonify({"error": "You don't have permission to read messages in this channel"}), 403
        channel_messages = [m for m in db['messages'] if m['channel_id'] == channel_id]
        return jsonify(channel_messages)
    elif request.method == 'POST':
        if not has_permission(current_user['id'], 'send_messages', guild_id=channel['guild_id'], channel_id=channel_id):
            return jsonify({"error": "You don't have permission to send messages in this channel"}), 403
        message = request.json
        message['id'] = str(uuid.uuid4())
        message['user_id'] = current_user['id']
        message['channel_id'] = channel_id
        message['timestamp'] = datetime.utcnow().isoformat()
        db['messages'].append(message)
        save_db(db)
        socketio.emit('new_message', message, room=channel_id)
        log_activity(current_user['id'], 'message_sent', {'channel_id': channel_id, 'message_id': message['id']})
        return jsonify(message), 201
@app.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    if 'file' not in request.files:
        return jsonify({"error": translate("No file part")}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": translate("No selected file")}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Upload to S3
        try:
            s3.upload_file(file_path, S3_BUCKET, unique_filename)
            os.remove(file_path)  # Remove local file after successful S3 upload
        except ClientError as e:
            return jsonify({"error": str(e)}), 500

        db = load_db()
        new_file = {
            'id': str(uuid.uuid4()),
            'filename': unique_filename,
            'original_filename': file.filename,
            'uploader_id': current_user['id'],
            'upload_date': datetime.utcnow().isoformat(),
            'file_type': file.filename.rsplit('.', 1)[1].lower(),
            's3_url': f"https://{S3_BUCKET}.s3.amazonaws.com/{unique_filename}"
        }
        if 'files' not in db:
            db['files'] = []
        db['files'].append(new_file)
        save_db(db)
        log_activity(current_user['id'], 'file_uploaded', {'file_id': new_file['id']})
        return jsonify(new_file), 201
    return jsonify({"error": translate("File type not allowed")}), 400

@app.route('/files/<file_id>', methods=['GET'])
@token_required
def get_file(current_user, file_id):
    db = load_db()
    file = next((f for f in db.get('files', []) if f['id'] == file_id), None)
    if not file:
        return jsonify({"error": translate("File not found")}), 404
    return jsonify(file), 200

@app.route('/files/<file_id>/download', methods=['GET'])
@token_required
def download_file(current_user, file_id):
    db = load_db()
    file = next((f for f in db.get('files', []) if f['id'] == file_id), None)
    if not file:
        return jsonify({"error": translate("File not found")}), 404
    
    try:
        response = s3.generate_presigned_url('get_object',
                                             Params={'Bucket': S3_BUCKET,
                                                     'Key': file['filename']},
                                             ExpiresIn=3600)
    except ClientError as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"download_url": response}), 200
@app.route('/messages/<message_id>/reactions', methods=['POST', 'DELETE'])
@token_required
def message_reactions(current_user, message_id):
    db = load_db()
    message = next((m for m in db['messages'] if m['id'] == message_id), None)
    if not message:
        return jsonify({"error": "Message not found"}), 404
    
    channel = next((c for c in db['channels'] if c['id'] == message['channel_id']), None)
    if not has_permission(current_user['id'], 'react_to_messages', guild_id=channel['guild_id'], channel_id=message['channel_id']):
        return jsonify({"error": "You don't have permission to react to messages in this channel"}), 403
    
    if request.method == 'POST':
        reaction = request.json['reaction']
        new_reaction = {
            'id': str(uuid.uuid4()),
            'user_id': current_user['id'],
            'message_id': message_id,
            'reaction': reaction
        }
        db['reactions'].append(new_reaction)
        save_db(db)
        socketio.emit('new_reaction', new_reaction, room=message['channel_id'])
        log_activity(current_user['id'], 'reaction_added', {'message_id': message_id, 'reaction': reaction})
        return jsonify(new_reaction), 201
    elif request.method == 'DELETE':
        reaction = request.json['reaction']
        db['reactions'] = [r for r in db['reactions'] if not (r['user_id'] == current_user['id'] and r['message_id'] == message_id and r['reaction'] == reaction)]
        save_db(db)
        socketio.emit('reaction_removed', {'user_id': current_user['id'], 'message_id': message_id, 'reaction': reaction}, room=message['channel_id'])
        log_activity(current_user['id'], 'reaction_removed', {'message_id': message_id, 'reaction': reaction})
        return '', 204
@app.route('/users/<user_id>/profile', methods=['GET', 'PUT'])
@token_required
def user_profile(current_user, user_id):
    db = load_db()
    user = next((u for u in db['users'] if u['id'] == user_id), None)
    if not user:
        return jsonify({"error": translate("User not found")}), 404

    if request.method == 'GET':
        return jsonify({
            'username': user['username'],
            'avatar': user.get('avatar'),
            'bio': user.get('bio'),
            'created_at': user.get('created_at'),
            'custom_status': user.get('custom_status'),
            'badges': user.get('badges', []),
            'theme': user.get('theme', 'light')
        })
    elif request.method == 'PUT':
        if current_user['id'] != user_id:
            return jsonify({"error": translate("You can only edit your own profile")}), 403
        user['bio'] = request.json.get('bio', user.get('bio'))
        user['avatar'] = request.json.get('avatar', user.get('avatar'))
        user['custom_status'] = request.json.get('custom_status', user.get('custom_status'))
        user['theme'] = request.json.get('theme', user.get('theme'))
        save_db(db)
        log_activity(current_user['id'], 'profile_updated')
        return jsonify(user), 200
@app.route('/users/<user_id>/block', methods=['POST', 'DELETE'])
@token_required
def block_user(current_user, user_id):
    db = load_db()
    if request.method == 'POST':
        new_block = {
            'id': str(uuid.uuid4()),
            'blocker_id': current_user['id'],
            'blocked_id': user_id
        }
        db['blocked_users'].append(new_block)
        save_db(db)
        log_activity(current_user['id'], 'user_blocked', {'blocked_user_id': user_id})
        return jsonify(new_block), 201
    elif request.method == 'DELETE':
        db['blocked_users'] = [b for b in db['blocked_users'] if not (b['blocker_id'] == current_user['id'] and b['blocked_id'] == user_id)]
        save_db(db)
        log_activity(current_user['id'], 'user_unblocked', {'unblocked_user_id': user_id})
        return '', 204

@app.route('/guilds/<guild_id>/roles', methods=['GET', 'POST'])
@token_required
def guild_roles(current_user, guild_id):
    db = load_db()
    guild = next((g for g in db['guilds'] if g['id'] == guild_id), None)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404
    
    if request.method == 'GET':
        roles = [r for r in db['roles'] if r['guild_id'] == guild_id]
        return jsonify(roles)
    elif request.method == 'POST':
        if not has_permission(current_user['id'], 'manage_roles', guild_id=guild_id):
            return jsonify({"error": "You don't have permission to manage roles in this guild"}), 403
        role = request.json
        role['id'] = str(uuid.uuid4())
        role['guild_id'] = guild_id
        db['roles'].append(role)
        save_db(db)
        log_activity(current_user['id'], 'role_created', {'guild_id': guild_id, 'role_id': role['id']})
        return jsonify(role), 201


@app.route('/users/<user_id>/roles', methods=['POST', 'DELETE'])
@token_required
def user_roles(current_user, user_id):
    db = load_db()
    user = next((u for u in db['users'] if u['id'] == user_id), None)
    if not user:
        return jsonify({"error": translate("User not found")}), 404

    if not has_permission(current_user['id'], 'manage_roles'):
        return jsonify({"error": translate("You don't have permission to manage roles")}), 403

    if request.method == 'POST':
        role_id = request.json['role_id']
        if 'roles' not in user:
            user['roles'] = []
        if role_id not in user['roles']:
            user['roles'].append(role_id)
            save_db(db)
            log_activity(current_user['id'], 'role_assigned', {'user_id': user_id, 'role_id': role_id})
        return jsonify(user['roles']), 200
    elif request.method == 'DELETE':
        role_id = request.json['role_id']
        if 'roles' in user and role_id in user['roles']:
            user['roles'].remove(role_id)
            save_db(db)
            log_activity(current_user['id'], 'role_removed', {'user_id': user_id, 'role_id': role_id})
        return jsonify(user['roles']), 200
@app.route('/marketplace', methods=['GET'])
@token_required
def marketplace(current_user):
    db = load_db()
    return jsonify(db.get('integrations', []))

@app.route('/marketplace/<integration_id>', methods=['POST'])
@token_required
def install_integration(current_user, integration_id):
    db = load_db()
    integration = next((i for i in db.get('integrations', []) if i['id'] == integration_id), None)
    if not integration:
        return jsonify({"error": translate("Integration not found")}), 404

    if 'installed_integrations' not in current_user:
        current_user['installed_integrations'] = []
    current_user['installed_integrations'].append(integration_id)
    save_db(db)
    log_activity(current_user['id'], 'integration_installed', {'integration_id': integration_id})
    return jsonify({"message": translate("Integration installed successfully")}), 200

@app.route('/polls', methods=['GET', 'POST'])
@token_required
def polls(current_user):
    db = load_db()
    if request.method == 'GET':
        return jsonify(db.get('polls', []))
    elif request.method == 'POST':
        new_poll = {
            'id': str(uuid.uuid4()),
            'question': request.json['question'],
            'options': request.json['options'],
            'created_by': current_user['id'],
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=request.json.get('duration_days', 1))).isoformat(),
            'votes': {}
        }
        if 'polls' not in db:
            db['polls'] = []
        db['polls'].append(new_poll)
        save_db(db)
        log_activity(current_user['id'], 'poll_created', {'poll_id': new_poll['id']})
        return jsonify(new_poll), 201

@app.route('/polls/<poll_id>/vote', methods=['POST'])
@token_required
def vote_poll(current_user, poll_id):
    db = load_db()
    poll = next((p for p in db.get('polls', []) if p['id'] == poll_id), None)
    if not poll:
        return jsonify({"error": translate("Poll not found")}), 404

    if datetime.fromisoformat(poll['expires_at']) < datetime.utcnow():
        return jsonify({"error": translate("This poll has expired")}), 400

    option = request.json['option']
    if option not in poll['options']:
        return jsonify({"error": translate("Invalid option")}), 400

    poll['votes'][current_user['id']] = option
    save_db(db)
    log_activity(current_user['id'], 'poll_voted', {'poll_id': poll_id, 'option': option})
    return jsonify({"message": translate("Vote recorded successfully")}), 200

@app.route('/reports', methods=['POST'])
@token_required
def create_report(current_user):
    db = load_db()
    new_report = {
        'id': str(uuid.uuid4()),
        'reporter_id': current_user['id'],
        'reported_id': request.json['reported_id'],
        'reason': request.json['reason'],
        'details': request.json.get('details'),
        'status': 'open',
        'created_at': datetime.utcnow().isoformat()
    }
    if 'reports' not in db:
        db['reports'] = []
    db['reports'].append(new_report)
    save_db(db)
    log_activity(current_user['id'], 'report_created', {'report_id': new_report['id']})
    return jsonify(new_report), 201

@app.route('/reports', methods=['GET'])
@token_required
def get_reports(current_user):
    if not has_permission(current_user['id'], 'view_reports'):
        return jsonify({"error": translate("You don't have permission to view reports")}), 403
    db = load_db()
    return jsonify(db.get('reports', []))

@app.route('/reports/<report_id>', methods=['PUT'])
@token_required
def update_report(current_user, report_id):
    if not has_permission(current_user['id'], 'manage_reports'):
        return jsonify({"error": translate("You don't have permission to manage reports")}), 403
    db = load_db()
    report = next((r for r in db.get('reports', []) if r['id'] == report_id), None)
    if not report:
        return jsonify({"error": translate("Report not found")}), 404

    report['status'] = request.json['status']
    report['resolved_by'] = current_user['id']
    report['resolved_at'] = datetime.utcnow().isoformat()
    save_db(db)
    log_activity(current_user['id'], 'report_updated', {'report_id': report_id})
    return jsonify(report), 200

@app.route('/guilds/<guild_id>/bans', methods=['GET', 'POST', 'DELETE'])
@token_required
def guild_bans(current_user, guild_id):
    db = load_db()
    guild = next((g for g in db['guilds'] if g['id'] == guild_id), None)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    if request.method == 'GET':
        if not has_permission(current_user['id'], 'view_bans', guild_id=guild_id):
            return jsonify({"error": "You don't have permission to view bans in this guild"}), 403
        bans = [b for b in db.get('bans', []) if b['guild_id'] == guild_id]
        return jsonify(bans)
    elif request.method == 'POST':
        if not has_permission(current_user['id'], 'ban_members', guild_id=guild_id):
            return jsonify({"error": "You don't have permission to ban members in this guild"}), 403
        user_id = request.json['user_id']
        reason = request.json.get('reason', '')
        new_ban = {
            'id': str(uuid.uuid4()),
            'guild_id': guild_id,
            'user_id': user_id,
            'banned_by': current_user['id'],
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }
        if 'bans' not in db:
            db['bans'] = []
        db['bans'].append(new_ban)
        save_db(db)
        log_activity(current_user['id'], 'user_banned', {'guild_id': guild_id, 'banned_user_id': user_id})
        return jsonify(new_ban), 201
    elif request.method == 'DELETE':
        if not has_permission(current_user['id'], 'unban_members', guild_id=guild_id):
            return jsonify({"error": "You don't have permission to unban members in this guild"}), 403
        user_id = request.json['user_id']
        db['bans'] = [b for b in db.get('bans', []) if not (b['guild_id'] == guild_id and b['user_id'] == user_id)]
        save_db(db)
        log_activity(current_user['id'], 'user_unbanned', {'guild_id': guild_id, 'unbanned_user_id': user_id})
        return '', 204

@app.route('/channels/<channel_id>/pins', methods=['GET', 'POST', 'DELETE'])
@token_required
def channel_pins(current_user, channel_id):
    db = load_db()
    channel = next((c for c in db['channels'] if c['id'] == channel_id), None)
    if not channel:
        return jsonify({"error": "Channel not found"}), 404

    if request.method == 'GET':
        if not has_permission(current_user['id'], 'read_messages', guild_id=channel['guild_id'], channel_id=channel_id):
            return jsonify({"error": "You don't have permission to view pins in this channel"}), 403
        pins = [m for m in db['messages'] if m['channel_id'] == channel_id and m.get('pinned', False)]
        return jsonify(pins)
    elif request.method == 'POST':
        if not has_permission(current_user['id'], 'manage_messages', guild_id=channel['guild_id'], channel_id=channel_id):
            return jsonify({"error": "You don't have permission to pin messages in this channel"}), 403
        message_id = request.json['message_id']
        message = next((m for m in db['messages'] if m['id'] == message_id and m['channel_id'] == channel_id), None)
        if not message:
            return jsonify({"error": "Message not found"}), 404
        message['pinned'] = True
        save_db(db)
        log_activity(current_user['id'], 'message_pinned', {'channel_id': channel_id, 'message_id': message_id})
        return jsonify(message), 200
    elif request.method == 'DELETE':
        if not has_permission(current_user['id'], 'manage_messages', guild_id=channel['guild_id'], channel_id=channel_id):
            return jsonify({"error": "You don't have permission to unpin messages in this channel"}), 403
        message_id = request.json['message_id']
        message = next((m for m in db['messages'] if m['id'] == message_id and m['channel_id'] == channel_id), None)
        if not message:
            return jsonify({"error": "Message not found"}), 404
        message['pinned'] = False
        save_db(db)
        log_activity(current_user['id'], 'message_unpinned', {'channel_id': channel_id, 'message_id': message_id})
        return '', 204
@app.route('/achievements', methods=['GET'])
@token_required
def get_achievements(current_user):
    db = load_db()
    return jsonify(db.get('achievements', []))

@app.route('/users/<user_id>/badges', methods=['GET'])
@token_required
def get_user_badges(current_user, user_id):
    db = load_db()
    user = next((u for u in db['users'] if u['id'] == user_id), None)
    if not user:
        return jsonify({"error": translate("User not found")}), 404
    return jsonify(user.get('badges', []))

def check_achievements(user_id):
    db = load_db()
    user = next((u for u in db['users'] if u['id'] == user_id), None)
    if not user:
        return

    user_messages = [m for m in db['messages'] if m['author_id'] == user_id]
    
    # Example achievement: Sent 100 messages
    if len(user_messages) >= 100 and 'centurion' not in user.get('badges', []):
        user.setdefault('badges', []).append('centurion')
        save_db(db)
        socketio.emit('achievement_unlocked', {'user_id': user_id, 'badge': 'centurion'}, room=user_id)

@app.route('/analytics/users', methods=['GET'])
@token_required
def user_analytics(current_user):
    if not has_permission(current_user['id'], 'view_analytics'):
        return jsonify({"error": translate("You don't have permission to view analytics")}), 403

    db = load_db()
    users = db['users']
    
    # User growth over time
    user_growth = pd.DataFrame(users)
    user_growth['created_at'] = pd.to_datetime(user_growth['created_at'])
    user_growth = user_growth.resample('D', on='created_at').size().cumsum()
    
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=user_growth)
    plt.title('User Growth Over Time')
    plt.xlabel('Date')
    plt.ylabel('Total Users')
    plt.savefig('user_growth.png')
    plt.close()

    # Active users per day
    messages = db['messages']
    active_users = pd.DataFrame(messages)
    active_users['timestamp'] = pd.to_datetime(active_users['timestamp'])
    active_users = active_users.groupby(active_users['timestamp'].dt.date)['author_id'].nunique()

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=active_users)
    plt.title('Active Users per Day')
    plt.xlabel('Date')
    plt.ylabel('Active Users')
    plt.savefig('active_users.png')
    plt.close()

    return jsonify({
        "user_growth_chart": "user_growth.png",
        "active_users_chart": "active_users.png",
        "total_users": len(users),
        "average_daily_active_users": active_users.mean()
    }), 200
@app.route('/guilds/<guild_id>/invites', methods=['GET', 'POST'])
@token_required
def guild_invites(current_user, guild_id):
    db = load_db()
    guild = next((g for g in db['guilds'] if g['id'] == guild_id), None)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404

    if request.method == 'GET':
        if not has_permission(current_user['id'], 'manage_guild', guild_id=guild_id):
            return jsonify({"error": "You don't have permission to view invites in this guild"}), 403
        invites = [i for i in db.get('invites', []) if i['guild_id'] == guild_id]
        return jsonify(invites)
    elif request.method == 'POST':
        if not has_permission(current_user['id'], 'create_invite', guild_id=guild_id):
            return jsonify({"error": "You don't have permission to create invites in this guild"}), 403
        new_invite = {
            'id': str(uuid.uuid4()),
            'guild_id': guild_id,
            'created_by': current_user['id'],
            'code': ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat()  # Default expiry of 7 days
        }
        if 'invites' not in db:
            db['invites'] = []
        db['invites'].append(new_invite)
        save_db(db)
        log_activity(current_user['id'], 'invite_created', {'guild_id': guild_id, 'invite_code': new_invite['code']})
        return jsonify(new_invite), 201

@app.route('/invites/<invite_code>', methods=['GET'])
def join_guild(invite_code):
    db = load_db()
    invite = next((i for i in db.get('invites', []) if i['code'] == invite_code), None)
    if not invite:
        return jsonify({"error": "Invalid invite code"}), 404
    if datetime.fromisoformat(invite['expires_at']) < datetime.utcnow():
        return jsonify({"error": "Invite has expired"}), 400
    # Here you would typically add the user to the guild
    # For simplicity, we'll just return the guild information
    guild = next((g for g in db['guilds'] if g['id'] == invite['guild_id']), None)
    return jsonify(guild), 200

@socketio.on('typing')
def on_typing(data):
    channel_id = data['channel_id']
    emit('user_typing', {'user_id': request.sid}, room=channel_id)

@socketio.on('stop_typing')
def on_stop_typing(data):
    channel_id = data['channel_id']
    emit('user_stop_typing', {'user_id': request.sid}, room=channel_id)

@socketio.on('send_message')
def handle_message(data):
    db = load_db()
    message = {
        'id': str(uuid.uuid4()),
        'channel_id': data['channel_id'],
        'author_id': request.sid,
        'content': data['content'],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if auto_moderate_message(message):
        db['messages'].append(message)
        save_db(db)
        emit('new_message', message, room=data['channel_id'])
    else:
        emit('message_blocked', {'error': 'Your message was blocked by auto-moderation'}, room=request.sid)

@socketio.on('join_voice')
def on_join_voice(data):
    room = f"voice_{data['channel_id']}"
    join_room(room)
    emit('user_joined_voice', {'user_id': request.sid}, room=room)

@socketio.on('leave_voice')
def on_leave_voice(data):
    room = f"voice_{data['channel_id']}"
    leave_room(room)
    emit('user_left_voice', {'user_id': request.sid}, room=room)

@socketio.on('start_video')
def on_start_video(data):
    room = f"video_{data['channel_id']}"
    join_room(room)
    emit('user_started_video', {'user_id': request.sid}, room=room)

@socketio.on('stop_video')
def on_stop_video(data):
    room = f"video_{data['channel_id']}"
    leave_room(room)
    emit('user_stopped_video', {'user_id': request.sid}, room=room)
@socketio.on('voice_state')
def handle_voice_state(data):
    room = f"voice_{data['channel_id']}"
    emit('voice_state_update', {
        'user_id': request.sid,
        'speaking': data['speaking'],
        'muted': data['muted'],
        'deafened': data['deafened']
    }, room=room)
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)

schedule.every(1).minutes.do(check_scheduled_events)
threading.Thread(target=run_schedule, daemon=True).start()
if __name__ == '__main__':
    socketio.run(app, debug=True)
