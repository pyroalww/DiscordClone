# MADE BY @C4GWN
# WWW.PYROLLC.COM.TR

from flask import Flask, request, jsonify
import json
import os
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
DB_PATH = 'database.json'

##########################
# Yardımcı Fonksiyonlar #
##########################

def load_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({
                "users": [],
                "guilds": [],
                "messages": [],
                "direct_messages": [],
                "friend_requests": []
            }, f, ensure_ascii=False, indent=4)
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(db):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def find_user(db, username):
    for user in db['users']:
        if user['username'] == username:
            return user
    return None

def find_guild(db, guild_id):
    for g in db['guilds']:
        if g['id'] == guild_id:
            return g
    return None

def find_channel_in_guild(guild, channel_id):
    for ch in guild['channels']:
        if ch['id'] == channel_id:
            return ch
    return None

def find_category_in_guild(guild, category_id):
    for cat in guild['categories']:
        if cat['id'] == category_id:
            return cat
    return None

def find_dm(db, dm_id):
    for dm in db['direct_messages']:
        if dm['id'] == dm_id:
            return dm
    return None

def find_user_by_token(db, token):
    # Basit token = username
    return find_user(db, token)

def user_in_guild(guild, username):
    for m in guild['members']:
        if m['username'] == username:
            return m
    return None

def user_has_permission(guild, username, permission):
    """
    Kullanıcının sunucudaki rollerini inceler, 
    eğer rollerden birinde 'permission' True ise yetkili kabul eder.
    """
    member = user_in_guild(guild, username)
    if not member:
        return False
    user_roles = member['roles']
    for r in guild['roles']:
        if r['name'] in user_roles:
            if r['permissions'].get(permission, False):
                return True
    return False

def add_audit_log(guild, action, user, details=""):
    guild['audit_logs'].append({
        "id": str(uuid.uuid4()),
        "action": action,
        "user": user,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details
    })

def create_default_role():
    return {
        "id": str(uuid.uuid4()),
        "name": "member",
        "permissions": {
            "send_messages": True,
            "read_messages": True
        }
    }

def create_admin_role():
    return {
        "id": str(uuid.uuid4()),
        "name": "admin",
        "permissions": {
            "manage_guild": True,
            "manage_roles": True,
            "manage_channels": True,
            "kick_members": True,
            "ban_members": True,
            "send_messages": True,
            "read_messages": True
        }
    }

def message_belongs_to_channel(db, message_id):
    for m in db['messages']:
        if m['id'] == message_id:
            return m
    return None

def is_channel_private(channel):
    return channel.get('is_private', False)

def user_has_access_to_channel(guild, user, channel):
    """
    Kanal private ise allowed_roles listesine bak.
    """
    if not is_channel_private(channel):
        return True
    member = user_in_guild(guild, user['username'])
    if not member:
        return False
    user_roles = member['roles']
    allowed = channel.get('allowed_roles', [])
    return any(r in allowed for r in user_roles)

def find_emoji(guild, emoji_id):
    for e in guild['emojis']:
        if e['id'] == emoji_id:
            return e
    return None

def invite_valid(invite):
    if invite['expires_at']:
        if datetime.fromisoformat(invite['expires_at']) < datetime.utcnow():
            return False
    if invite['max_uses'] is not None and invite['uses'] >= invite['max_uses']:
        return False
    return True

##########################
# Kullanıcı İşlemleri    #
##########################

# /register [POST]
# Body: {"username":"...","password":"...","avatar_url":"optional"}
@app.route('/register', methods=['POST'])
def register():
    db = load_db()
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    avatar_url = data.get('avatar_url', None)

    if find_user(db, username):
        return jsonify({"status": "error", "message": "Username already exists"}), 400

    new_user = {
        "username": username,
        "password": password,
        "online": False,
        "friends": [],
        "guilds": [],
        "dm_channels": [],
        "avatar_url": avatar_url
    }
    db['users'].append(new_user)
    save_db(db)
    return jsonify({"status": "success", "message": "User registered"})


# /login [POST]
# Body: {"username":"...","password":"..."}
@app.route('/login', methods=['POST'])
def login():
    db = load_db()
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = find_user(db, username)
    if not user or user['password'] != password:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    user['online'] = True
    save_db(db)
    return jsonify({"status": "success", "token": username})


# /logout [POST]
@app.route('/logout', methods=['POST'])
def logout():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    token = auth.split(" ")[1]
    user = find_user_by_token(db, token)
    if not user:
        return jsonify({"status": "error", "message": "Invalid token"}), 401
    user['online'] = False
    save_db(db)
    return jsonify({"status": "success", "message": "Logged out"})


# /user/<username> [GET]
@app.route('/user/<username>', methods=['GET'])
def get_user_info(username):
    db = load_db()
    user = find_user(db, username)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({
        "username": user['username'],
        "online": user['online'],
        "friends": user['friends'],
        "guilds": user['guilds'],
        "dm_channels": user['dm_channels'],
        "avatar_url": user['avatar_url']
    })

# /users [GET]
@app.route('/users', methods=['GET'])
def list_users():
    db = load_db()
    users_list = []
    for u in db['users']:
        users_list.append({
            "username": u['username'],
            "online": u['online'],
            "avatar_url": u['avatar_url']
        })
    return jsonify({"users": users_list})

##########################
# Profil Güncelleme (GIF Avatar / Banner)
##########################
@app.route('/update_profile', methods=['POST'])
def update_profile():
    """
    Avatar ve banner güncellemesi (GIF dahil).
    Body: {
      "avatar_url":"(gif veya normal url)",
      "banner_url":"(gif veya normal url)"
    }
    """
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    new_avatar = data.get('avatar_url', None)
    new_banner = data.get('banner_url', None)

    if new_avatar:
        if not (new_avatar.startswith("http://") or new_avatar.startswith("https://")):
            return jsonify({"status":"error","message":"Invalid avatar URL"}),400
        cu['avatar_url'] = new_avatar

    if new_banner:
        if not (new_banner.startswith("http://") or new_banner.startswith("https://")):
            return jsonify({"status":"error","message":"Invalid banner URL"}),400
        # banner_url alanını ekleyelim (yoksa ek oluştur)
        cu['banner_url'] = new_banner

    save_db(db)
    return jsonify({"status":"success","message":"Profile updated"})

##########################
# Arkadaşlık Sistemi     #
##########################

# /send_friend_request [POST]
# Body: {"to_user":"..."}
@app.route('/send_friend_request', methods=['POST'])
def send_friend_request():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    token = auth.split(" ")[1]
    from_user = find_user_by_token(db, token)
    if not from_user:
        return jsonify({"status": "error", "message": "Invalid token"}), 401

    data = request.get_json()
    to_username = data.get('to_user')
    to_user = find_user(db, to_username)
    if not to_user:
        return jsonify({"status":"error","message":"User not found"}),404

    if to_user['username'] in from_user['friends']:
        return jsonify({"status":"error","message":"Already friends"}),400

    for fr in db['friend_requests']:
        if fr['from'] == from_user['username'] and fr['to'] == to_user['username']:
            return jsonify({"status":"error","message":"Request already sent"}),400

    new_req = {
        "id": str(uuid.uuid4()),
        "from": from_user['username'],
        "to": to_user['username']
    }
    db['friend_requests'].append(new_req)
    save_db(db)
    return jsonify({"status":"success","message":"Friend request sent"})


# /friend_requests [GET]
@app.route('/friend_requests', methods=['GET'])
def friend_requests():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    user = find_user_by_token(db, token)
    if not user:
        return jsonify({"status":"error","message":"Invalid token"}),401

    incoming = [fr for fr in db['friend_requests'] if fr['to'] == user['username']]
    return jsonify({"friend_requests": incoming})


# /respond_friend_request [POST]
# Body: {"request_id":"...","action":"accept"|"reject"}
@app.route('/respond_friend_request', methods=['POST'])
def respond_friend_request():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    current_user = find_user_by_token(db, token)
    if not current_user:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    req_id = data.get('request_id')
    action = data.get('action')
    fr_index = None
    fr = None
    for i, r in enumerate(db['friend_requests']):
        if r['id'] == req_id:
            fr = r
            fr_index = i
            break

    if not fr:
        return jsonify({"status":"error","message":"Request not found"}),404

    if fr['to'] != current_user['username']:
        return jsonify({"status":"error","message":"Not your request"}),403

    if action == "accept":
        from_user = find_user(db, fr['from'])
        to_user = current_user
        from_user['friends'].append(to_user['username'])
        to_user['friends'].append(from_user['username'])
        del db['friend_requests'][fr_index]
        save_db(db)
        return jsonify({"status":"success","message":"Friend added"})
    elif action == "reject":
        del db['friend_requests'][fr_index]
        save_db(db)
        return jsonify({"status":"success","message":"Friend request rejected"})
    else:
        return jsonify({"status":"error","message":"Invalid action"}),400

# /friends [GET]
@app.route('/friends', methods=['GET'])
def friends_list():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    user = find_user_by_token(db, token)
    if not user:
        return jsonify({"status":"error","message":"Invalid token"}),401

    friends_data = []
    for f in user['friends']:
        fu = find_user(db, f)
        friends_data.append({
            "username": fu['username'],
            "online": fu['online']
        })
    return jsonify({"friends": friends_data})

##########################
# DM (Özel Mesaj)        #
##########################

# /create_dm [POST]
# Body: {"with_user":"..."}
@app.route('/create_dm', methods=['POST'])
def create_dm():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    current_user = find_user_by_token(db, token)
    if not current_user:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    with_user = data.get('with_user')
    other_user = find_user(db, with_user)
    if not other_user:
        return jsonify({"status":"error","message":"User not found"}),404

    if other_user['username'] not in current_user['friends']:
        return jsonify({"status":"error","message":"You can only DM friends"}),403

    for dm in db['direct_messages']:
        if set(dm['participants']) == set([current_user['username'], other_user['username']]):
            return jsonify({"status":"success","dm_id":dm['id'],"message":"DM already exists"})

    dm_id = str(uuid.uuid4())
    new_dm = {
        "id": dm_id,
        "participants": [current_user['username'], other_user['username']],
        "messages": []
    }
    db['direct_messages'].append(new_dm)
    current_user['dm_channels'].append(dm_id)
    other_user['dm_channels'].append(dm_id)
    save_db(db)
    return jsonify({"status":"success","dm_id":dm_id})

# /send_dm [POST]
# Body: {"dm_id":"...","content":"...","file_base64":"optional"}
@app.route('/send_dm', methods=['POST'])
def send_dm():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    dm_id = data.get('dm_id')
    content = data.get('content')
    file_base64 = data.get('file_base64', None)
    dm_obj = find_dm(db, dm_id)
    if not dm_obj:
        return jsonify({"status":"error","message":"DM not found"}),404

    if cu['username'] not in dm_obj['participants']:
        return jsonify({"status":"error","message":"Not a participant"}),403

    msg_id = str(uuid.uuid4())
    dm_msg = {
        "id": msg_id,
        "author": cu['username'],
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
        "file_base64": file_base64
    }
    dm_obj['messages'].append(dm_msg)
    save_db(db)
    return jsonify({"status":"success","message_id":msg_id})

# /dm_messages/<dm_id> [GET]
@app.route('/dm_messages/<dm_id>', methods=['GET'])
def dm_messages(dm_id):
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    dm_obj = find_dm(db, dm_id)
    if not dm_obj:
        return jsonify({"status":"error","message":"DM not found"}),404

    if cu['username'] not in dm_obj['participants']:
        return jsonify({"status":"error","message":"Not participant"}),403

    return jsonify({"messages": dm_obj['messages']})

# /edit_dm_message [POST]
# {"dm_id":"...","message_id":"...","new_content":"..."}
@app.route('/edit_dm_message', methods=['POST'])
def edit_dm_message():
    db = load_db()
    auth = request.headers.get('Authorization')
    token = None
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ")[1]
    if not token:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    dm_id = data.get('dm_id')
    message_id = data.get('message_id')
    new_content = data.get('new_content')
    dm_obj = find_dm(db, dm_id)
    if not dm_obj:
        return jsonify({"status":"error","message":"DM not found"}),404

    if cu['username'] not in dm_obj['participants']:
        return jsonify({"status":"error","message":"Not participant"}),403

    msg = None
    for m in dm_obj['messages']:
        if m['id'] == message_id:
            msg = m
            break
    if not msg:
        return jsonify({"status":"error","message":"Message not found"}),404

    if msg['author'] != cu['username']:
        return jsonify({"status":"error","message":"No permission"}),403

    msg['content'] = new_content
    save_db(db)
    return jsonify({"status":"success","message":"DM message edited"})


# /delete_dm_message [POST]
# {"dm_id":"...","message_id":"..."}
@app.route('/delete_dm_message', methods=['POST'])
def delete_dm_message():
    db = load_db()
    auth = request.headers.get('Authorization')
    token = None
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ")[1]
    if not token:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    dm_id = data.get('dm_id')
    message_id = data.get('message_id')
    dm_obj = find_dm(db, dm_id)
    if not dm_obj:
        return jsonify({"status":"error","message":"DM not found"}),404

    if cu['username'] not in dm_obj['participants']:
        return jsonify({"status":"error","message":"Not participant"}),403

    msg_index = None
    for i,m in enumerate(dm_obj['messages']):
        if m['id'] == message_id:
            msg_index = i
            break
    if msg_index is None:
        return jsonify({"status":"error","message":"Message not found"}),404

    msg = dm_obj['messages'][msg_index]
    if msg['author'] != cu['username']:
        return jsonify({"status":"error","message":"No permission"}),403

    del dm_obj['messages'][msg_index]
    save_db(db)
    return jsonify({"status":"success","message":"DM message deleted"})

##########################
# Sunucu (Guild) İşlemleri
##########################

# /create_guild [POST]
# {"name":"My Server"}
@app.route('/create_guild', methods=['POST'])
def create_guild():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    creator = find_user_by_token(db, token)
    if not creator:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    guild_name = data.get('name')

    guild_id = str(uuid.uuid4())
    admin_role = create_admin_role()
    member_role = create_default_role()

    new_guild = {
        "id": guild_id,
        "name": guild_name,
        "owner": creator['username'],
        "roles": [admin_role, member_role],
        "members": [{
            "username": creator['username'],
            "roles": ["admin"],
            "joined_at": datetime.utcnow().isoformat()
        }],
        "categories": [],
        "channels": [],
        "invites": [],
        "emojis": [],
        "audit_logs": [],
        # Ban listesi gibi ek veriler
        "bans": []
    }

    db['guilds'].append(new_guild)
    if guild_id not in creator['guilds']:
        creator['guilds'].append(guild_id)
    add_audit_log(new_guild, "CREATE_GUILD", creator['username'], f"Guild {guild_name} created")
    save_db(db)
    return jsonify({"status":"success","guild_id":guild_id})

# /guilds [GET]
@app.route('/guilds', methods=['GET'])
def list_guilds():
    db = load_db()
    guild_info = []
    for g in db['guilds']:
        guild_info.append({
            "id": g['id'],
            "name": g['name'],
            "owner": g['owner'],
            "member_count": len(g['members'])
        })
    return jsonify({"guilds": guild_info})

# /guild/<guild_id> [GET]
@app.route('/guild/<guild_id>', methods=['GET'])
def get_guild(guild_id):
    db = load_db()
    guild = find_guild(db, guild_id)
    if not guild:
        return jsonify({"status":"error","message":"Guild not found"}),404
    return jsonify({
        "id": guild['id'],
        "name": guild['name'],
        "owner": guild['owner'],
        "roles": [r['name'] for r in guild['roles']],
        "categories": guild['categories'],
        "channels": guild['channels'],
        "member_count": len(guild['members'])
    })

# /create_category [POST]
# {"guild_id":"...","name":"..."}
@app.route('/create_category', methods=['POST'])
def create_category():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    user = find_user_by_token(db, token)
    if not user:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    guild_id = data.get('guild_id')
    name = data.get('name')

    guild = find_guild(db, guild_id)
    if not guild:
        return jsonify({"status":"error","message":"Guild not found"}),404

    if not user_has_permission(guild, user['username'], "manage_channels"):
        return jsonify({"status":"error","message":"No permission"}),403

    cat_id = str(uuid.uuid4())
    guild['categories'].append({
        "id": cat_id,
        "name": name
    })
    add_audit_log(guild, "CREATE_CATEGORY", user['username'], f"Category {name}")
    save_db(db)
    return jsonify({"status":"success","category_id":cat_id})

# /create_channel [POST]
# {"guild_id":"...", "category_id":"optional","name":"...","description":"...","is_private":bool,"allowed_roles":["..."]}
@app.route('/create_channel', methods=['POST'])
def create_channel():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    user = find_user_by_token(db, token)
    if not user:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    guild_id = data.get('guild_id')
    category_id = data.get('category_id', None)
    name = data.get('name')
    description = data.get('description', "")
    is_private = data.get('is_private', False)
    allowed_roles = data.get('allowed_roles', [])

    guild = find_guild(db, guild_id)
    if not guild:
        return jsonify({"status":"error","message":"Guild not found"}),404

    if not user_has_permission(guild, user['username'], "manage_channels"):
        return jsonify({"status":"error","message":"No permission"}),403

    if category_id and not find_category_in_guild(guild, category_id):
        return jsonify({"status":"error","message":"Category not found"}),404

    ch_id = str(uuid.uuid4())
    new_channel = {
        "id": ch_id,
        "guild_id": guild_id,
        "category_id": category_id,
        "name": name,
        "description": description,
        "is_private": is_private,
        "allowed_roles": allowed_roles,
        "type": "text"  # Default text channel
    }
    guild['channels'].append(new_channel)
    add_audit_log(guild, "CREATE_CHANNEL", user['username'], f"Channel {name}")
    save_db(db)
    return jsonify({"status":"success","channel_id":ch_id})

##########################
# Voice Channel & Screen Share
##########################
@app.route('/create_voice_channel', methods=['POST'])
def create_voice_channel():
    """
    Body: {
      "guild_id": "<guild_id>",
      "name": "My Voice Channel",
      "is_private": false,
      "allowed_roles": ["admin","member"]
    }
    """
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    token = auth.split(" ")[1]
    user = find_user_by_token(db, token)
    if not user:
        return jsonify({"status": "error", "message": "Invalid token"}), 401
    
    data = request.get_json()
    guild_id = data.get('guild_id')
    name = data.get('name')
    is_private = data.get('is_private', False)
    allowed_roles = data.get('allowed_roles', [])
    
    guild = find_guild(db, guild_id)
    if not guild:
        return jsonify({"status":"error","message":"Guild not found"}),404
    
    if not user_has_permission(guild, user['username'], "manage_channels"):
        return jsonify({"status":"error","message":"No permission"}),403

    vc_id = str(uuid.uuid4())
    new_voice_channel = {
        "id": vc_id,
        "guild_id": guild_id,
        "name": name,
        "type": "voice",
        "is_private": is_private,
        "allowed_roles": allowed_roles,
        "connected_users": [],
        "screen_share": {
            "active": False,
            "user": None
        }
    }
    guild['channels'].append(new_voice_channel)
    add_audit_log(guild, "CREATE_VOICE_CHANNEL", user['username'], f"Voice channel {name}")
    save_db(db)
    return jsonify({"status":"success","voice_channel_id":vc_id})

@app.route('/join_voice_channel', methods=['POST'])
def join_voice_channel():
    """
    Body: {"channel_id":"..."}
    """
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status": "error", "message": "Invalid token"}), 401

    data = request.get_json()
    channel_id = data.get('channel_id')
    
    ch_guild = None
    ch_obj = None
    for g in db['guilds']:
        for c in g['channels']:
            if c['id'] == channel_id and c.get('type') == 'voice':
                ch_guild = g
                ch_obj = c
                break
        if ch_obj:
            break
    
    if not ch_obj:
        return jsonify({"status":"error","message":"Voice channel not found"}),404
    
    if not user_in_guild(ch_guild, cu['username']):
        return jsonify({"status":"error","message":"Not in guild"}),403

    if ch_obj.get('is_private'):
        member = user_in_guild(ch_guild, cu['username'])
        if not any(r in ch_obj.get('allowed_roles', []) for r in member['roles']):
            return jsonify({"status":"error","message":"No access to this voice channel"}),403
    
    if cu['username'] not in ch_obj['connected_users']:
        ch_obj['connected_users'].append(cu['username'])
    save_db(db)
    return jsonify({"status":"success","message":"Joined voice channel"})

@app.route('/leave_voice_channel', methods=['POST'])
def leave_voice_channel():
    """
    Body: {"channel_id":"..."}
    """
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status": "error", "message": "Invalid token"}), 401

    data = request.get_json()
    channel_id = data.get('channel_id')

    ch_guild = None
    ch_obj = None
    for g in db['guilds']:
        for c in g['channels']:
            if c['id'] == channel_id and c.get('type') == 'voice':
                ch_guild = g
                ch_obj = c
                break
        if ch_obj:
            break
    
    if not ch_obj:
        return jsonify({"status":"error","message":"Voice channel not found"}),404

    if cu['username'] in ch_obj['connected_users']:
        ch_obj['connected_users'].remove(cu['username'])
    save_db(db)
    return jsonify({"status":"success","message":"Left voice channel"})

@app.route('/start_screen_share', methods=['POST'])
def start_screen_share():
    """
    Body: {"channel_id":"..."}
    """
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    channel_id = data.get('channel_id')

    ch_guild = None
    ch_obj = None
    for g in db['guilds']:
        for c in g['channels']:
            if c['id'] == channel_id and c.get('type') == 'voice':
                ch_guild = g
                ch_obj = c
                break
        if ch_obj:
            break
    if not ch_obj:
        return jsonify({"status":"error","message":"Voice channel not found"}),404

    if cu['username'] not in ch_obj['connected_users']:
        return jsonify({"status":"error","message":"You are not in this voice channel"}),403

    ch_obj['screen_share'] = {
        "active": True,
        "user": cu['username'],
        "started_at": datetime.utcnow().isoformat()
    }
    save_db(db)
    return jsonify({"status":"success","message":"Screen share started"})

@app.route('/stop_screen_share', methods=['POST'])
def stop_screen_share():
    """
    Body: {"channel_id":"..."}
    """
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    channel_id = data.get('channel_id')
    
    ch_guild = None
    ch_obj = None
    for g in db['guilds']:
        for c in g['channels']:
            if c['id'] == channel_id and c.get('type') == 'voice':
                ch_guild = g
                ch_obj = c
                break
        if ch_obj:
            break
    if not ch_obj:
        return jsonify({"status":"error","message":"Voice channel not found"}),404
    
    scr_share = ch_obj.get('screen_share')
    if not scr_share or not scr_share.get('active'):
        return jsonify({"status":"error","message":"No active screen share"}),400

    if scr_share['user'] != cu['username']:
        return jsonify({"status":"error","message":"You are not the one sharing"}),403

    ch_obj['screen_share'] = {"active": False, "user": None}
    save_db(db)
    return jsonify({"status":"success","message":"Screen share stopped"})

##########################
# Davetiye (Invite)
##########################

# /invite_create [POST]
# {"guild_id":"...","channel_id":"...","expires_in_seconds":3600,"max_uses":10}
@app.route('/invite_create', methods=['POST'])
def invite_create():
    db = load_db()
    auth = request.headers.get('Authorization')
    token = None
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ")[1]
    if not token:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    user = find_user_by_token(db, token)
    if not user:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    guild_id = data.get('guild_id')
    channel_id = data.get('channel_id')
    expires_in = data.get('expires_in_seconds', 3600)
    max_uses = data.get('max_uses', None)

    guild = find_guild(db, guild_id)
    if not guild:
        return jsonify({"status":"error","message":"Guild not found"}),404

    if not user_has_permission(guild, user['username'], "manage_channels"):
        return jsonify({"status":"error","message":"No permission"}),403

    ch = find_channel_in_guild(guild, channel_id)
    if not ch:
        return jsonify({"status":"error","message":"Channel not found"}),404

    inv_id = str(uuid.uuid4())
    expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat() if expires_in else None
    new_invite = {
        "id": inv_id,
        "channel_id": channel_id,
        "created_by": user['username'],
        "expires_at": expires_at,
        "uses": 0,
        "max_uses": max_uses
    }
    guild['invites'].append(new_invite)
    add_audit_log(guild, "CREATE_INVITE", user['username'], f"Invite {inv_id}")
    save_db(db)
    return jsonify({"status":"success","invite_id":inv_id})

# /join_by_invite [POST]
# {"invite_id":"..."}
@app.route('/join_by_invite', methods=['POST'])
def join_by_invite():
    db = load_db()
    auth = request.headers.get('Authorization')
    token = None
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ")[1]
    if not token:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    user = find_user_by_token(db, token)
    if not user:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    inv_id = data.get('invite_id')

    found_inv = None
    found_guild = None
    for g in db['guilds']:
        for inv in g['invites']:
            if inv['id'] == inv_id:
                found_inv = inv
                found_guild = g
                break
        if found_inv:
            break

    if not found_inv:
        return jsonify({"status":"error","message":"Invite not found"}),404

    if not invite_valid(found_inv):
        return jsonify({"status":"error","message":"Invite invalid or expired"}),400

    if user_in_guild(found_guild, user['username']):
        return jsonify({"status":"error","message":"Already in guild"}),400

    found_guild['members'].append({
        "username": user['username'],
        "roles": ["member"],
        "joined_at": datetime.utcnow().isoformat()
    })
    if found_guild['id'] not in user['guilds']:
        user['guilds'].append(found_guild['id'])

    found_inv['uses'] += 1
    add_audit_log(found_guild, "GUILD_JOIN", user['username'], f"Joined via invite {inv_id}")
    save_db(db)
    return jsonify({"status":"success","message":"Joined guild"})

##########################
# Mesaj İşlemleri (Guild)
##########################

# /send_message [POST]
# {"channel_id":"...","content":"...","file_base64":"optional"}
@app.route('/send_message', methods=['POST'])
def send_message():
    db = load_db()
    auth = request.headers.get('Authorization')
    token = None
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ")[1]
    if not token:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    channel_id = data.get('channel_id')
    content = data.get('content')
    file_base64 = data.get('file_base64', None)

    ch_guild = None
    ch_obj = None
    for g in db['guilds']:
        for c in g['channels']:
            if c['id'] == channel_id:
                ch_guild = g
                ch_obj = c
                break
        if ch_obj:
            break

    if not ch_obj:
        return jsonify({"status":"error","message":"Channel not found"}),404

    if not user_in_guild(ch_guild, cu['username']):
        return jsonify({"status":"error","message":"Not in guild"}),403

    if not user_has_access_to_channel(ch_guild, cu, ch_obj):
        return jsonify({"status":"error","message":"No access to this channel"}),403

    msg_id = str(uuid.uuid4())
    new_msg = {
        "id": msg_id,
        "channel_id": channel_id,
        "author": cu['username'],
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
        "file_base64": file_base64,
        "pinned": False,
        "reactions": []
    }
    db['messages'].append(new_msg)
    save_db(db)
    return jsonify({"status":"success","message_id":msg_id})

# /messages/<channel_id> [GET]
@app.route('/messages/<channel_id>', methods=['GET'])
def get_messages(channel_id):
    db = load_db()
    ch_guild = None
    ch_obj = None
    for g in db['guilds']:
        for c in g['channels']:
            if c['id'] == channel_id:
                ch_guild = g
                ch_obj = c
                break
        if ch_obj:
            break

    if not ch_obj:
        return jsonify({"status":"error","message":"Channel not found"}),404

    auth = request.headers.get('Authorization')
    token = None
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ")[1]

    if is_channel_private(ch_obj):
        if not token:
            return jsonify({"status":"error","message":"Unauthorized"}),401
        cu = find_user_by_token(db, token)
        if not cu:
            return jsonify({"status":"error","message":"Invalid token"}),401
        if not user_in_guild(ch_guild, cu['username']):
            return jsonify({"status":"error","message":"Not in guild"}),403
        if not user_has_access_to_channel(ch_guild, cu, ch_obj):
            return jsonify({"status":"error","message":"No access"}),403

    msgs = [m for m in db['messages'] if m['channel_id'] == channel_id]
    return jsonify({"messages": msgs})

# /edit_message [POST]
# {"message_id":"...","new_content":"..."}
@app.route('/edit_message', methods=['POST'])
def edit_message():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    message_id = data.get('message_id')
    new_content = data.get('new_content')

    msg = message_belongs_to_channel(db, message_id)
    if not msg:
        return jsonify({"status":"error","message":"Message not found"}),404

    ch_guild = None
    ch_obj = None
    for g in db['guilds']:
        for c in g['channels']:
            if c['id'] == msg['channel_id']:
                ch_guild = g
                ch_obj = c
                break
        if ch_obj:
            break

    if not user_in_guild(ch_guild, cu['username']):
        return jsonify({"status":"error","message":"Not in guild"}),403

    if not user_has_access_to_channel(ch_guild, cu, ch_obj):
        return jsonify({"status":"error","message":"No access"}),403

    # Yazar veya manage_channels izni olan düzenleyebilir
    if msg['author'] != cu['username'] and not user_has_permission(ch_guild, cu['username'], "manage_channels"):
        return jsonify({"status":"error","message":"No permission"}),403

    msg['content'] = new_content
    save_db(db)
    return jsonify({"status":"success","message":"Message edited"})

# /delete_message [POST]
# {"message_id":"..."}
@app.route('/delete_message', methods=['POST'])
def delete_message():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    message_id = data.get('message_id')
    msg_index = None
    msg_obj = None
    for i,m in enumerate(db['messages']):
        if m['id'] == message_id:
            msg_index = i
            msg_obj = m
            break
    if msg_index is None:
        return jsonify({"status":"error","message":"Message not found"}),404

    ch_guild = None
    ch_obj = None
    for g in db['guilds']:
        for c in g['channels']:
            if c['id'] == msg_obj['channel_id']:
                ch_guild = g
                ch_obj = c
                break
        if ch_obj:
            break

    if not user_in_guild(ch_guild, cu['username']):
        return jsonify({"status":"error","message":"Not in guild"}),403

    if not user_has_access_to_channel(ch_guild, cu, ch_obj):
        return jsonify({"status":"error","message":"No access"}),403

    if msg_obj['author'] != cu['username'] and not user_has_permission(ch_guild, cu['username'], "manage_channels"):
        return jsonify({"status":"error","message":"No permission"}),403

    del db['messages'][msg_index]
    save_db(db)
    return jsonify({"status":"success","message":"Message deleted"})

# /pin_message [POST]
# {"message_id":"..."}
@app.route('/pin_message', methods=['POST'])
def pin_message():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    message_id = data.get('message_id')
    msg = message_belongs_to_channel(db, message_id)
    if not msg:
        return jsonify({"status":"error","message":"Message not found"}),404

    ch_guild = None
    ch_obj = None
    for g in db['guilds']:
        for c in g['channels']:
            if c['id'] == msg['channel_id']:
                ch_guild = g
                ch_obj = c
                break
        if ch_obj:
            break

    if not user_in_guild(ch_guild, cu['username']):
        return jsonify({"status":"error","message":"Not in guild"}),403

    if not user_has_permission(ch_guild, cu['username'], "manage_channels"):
        return jsonify({"status":"error","message":"No permission"}),403

    msg['pinned'] = True
    save_db(db)
    return jsonify({"status":"success","message":"Message pinned"})

# /search_messages [GET]
# query params: q=...
@app.route('/search_messages', methods=['GET'])
def search_messages():
    db = load_db()
    q = request.args.get('q', "")
    results = []
    for m in db['messages']:
        if q.lower() in m['content'].lower():
            results.append(m)
    return jsonify({"results": results})

# /add_reaction [POST]
# {"message_id":"...","emoji_id":"..."}
@app.route('/add_reaction', methods=['POST'])
def add_reaction():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    message_id = data.get('message_id')
    emoji_id = data.get('emoji_id')

    msg = message_belongs_to_channel(db, message_id)
    if not msg:
        return jsonify({"status":"error","message":"Message not found"}),404

    ch_guild = None
    ch_obj = None
    for g in db['guilds']:
        for c in g['channels']:
            if c['id'] == msg['channel_id']:
                ch_guild = g
                ch_obj = c
                break
        if ch_obj:
            break

    if not user_in_guild(ch_guild, cu['username']):
        return jsonify({"status":"error","message":"Not in guild"}),403

    emoji = find_emoji(ch_guild, emoji_id)
    if not emoji:
        return jsonify({"status":"error","message":"Emoji not found"}),404

    found_reaction = None
    for r in msg['reactions']:
        if r['emoji_id'] == emoji_id:
            found_reaction = r
            break
    if found_reaction:
        if cu['username'] not in found_reaction['users']:
            found_reaction['users'].append(cu['username'])
    else:
        msg['reactions'].append({
            "emoji_id": emoji_id,
            "users": [cu['username']]
        })
    save_db(db)
    return jsonify({"status":"success","message":"Reaction added"})

# /remove_reaction [POST]
# {"message_id":"...","emoji_id":"..."}
@app.route('/remove_reaction', methods=['POST'])
def remove_reaction():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    message_id = data.get('message_id')
    emoji_id = data.get('emoji_id')

    msg = message_belongs_to_channel(db, message_id)
    if not msg:
        return jsonify({"status":"error","message":"Message not found"}),404

    ch_guild = None
    for g in db['guilds']:
        for c in g['channels']:
            if c['id'] == msg['channel_id']:
                ch_guild = g
                break
        if ch_guild:
            break

    found_reaction = None
    for r in msg['reactions']:
        if r['emoji_id'] == emoji_id:
            found_reaction = r
            break
    if not found_reaction:
        return jsonify({"status":"error","message":"Reaction not found"}),404

    if cu['username'] in found_reaction['users']:
        found_reaction['users'].remove(cu['username'])
        if len(found_reaction['users']) == 0:
            msg['reactions'].remove(found_reaction)
        save_db(db)
        return jsonify({"status":"success","message":"Reaction removed"})
    else:
        return jsonify({"status":"error","message":"You did not react"}),400

##########################
# Emoji Yönetimi (Guild)
##########################

# /add_emoji [POST]
# {"guild_id":"...","name":"...","image_base64":"..."}
@app.route('/add_emoji', methods=['POST'])
def add_emoji():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    guild_id = data.get('guild_id')
    name = data.get('name')
    image_base64 = data.get('image_base64')

    guild = find_guild(db, guild_id)
    if not guild:
        return jsonify({"status":"error","message":"Guild not found"}),404

    if not user_has_permission(guild, cu['username'], "manage_guild"):
        return jsonify({"status":"error","message":"No permission"}),403

    emoji_id = str(uuid.uuid4())
    guild['emojis'].append({
        "id": emoji_id,
        "name": name,
        "image_base64": image_base64
    })
    add_audit_log(guild, "ADD_EMOJI", cu['username'], f"Emoji {name}")
    save_db(db)
    return jsonify({"status":"success","emoji_id":emoji_id})

# /remove_emoji [POST]
# {"guild_id":"...","emoji_id":"..."}
@app.route('/remove_emoji', methods=['POST'])
def remove_emoji():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    guild_id = data.get('guild_id')
    emoji_id = data.get('emoji_id')

    guild = find_guild(db, guild_id)
    if not guild:
        return jsonify({"status":"error","message":"Guild not found"}),404

    if not user_has_permission(guild, cu['username'], "manage_guild"):
        return jsonify({"status":"error","message":"No permission"}),403

    e_index = None
    for i,e in enumerate(guild['emojis']):
        if e['id'] == emoji_id:
            e_index = i
            break
    if e_index is None:
        return jsonify({"status":"error","message":"Emoji not found"}),404

    del guild['emojis'][e_index]
    add_audit_log(guild, "REMOVE_EMOJI", cu['username'], f"Removed emoji {emoji_id}")
    save_db(db)
    return jsonify({"status":"success","message":"Emoji removed"})

##########################
# Üye Yönetimi (Kick / Ban)
##########################

# /kick_member [POST]
# {"guild_id":"...","username":"..."}
@app.route('/kick_member', methods=['POST'])
def kick_member():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    guild_id = data.get('guild_id')
    target_user = data.get('username')

    guild = find_guild(db, guild_id)
    if not guild:
        return jsonify({"status":"error","message":"Guild not found"}),404

    if not user_has_permission(guild, cu['username'], "kick_members"):
        return jsonify({"status":"error","message":"No permission"}),403

    mem = user_in_guild(guild, target_user)
    if not mem:
        return jsonify({"status":"error","message":"User not in guild"}),404

    # Remove user from guild
    guild['members'] = [m for m in guild['members'] if m['username'] != target_user]
    t_user = find_user(db, target_user)
    if guild_id in t_user['guilds']:
        t_user['guilds'].remove(guild_id)
    add_audit_log(guild, "KICK_MEMBER", cu['username'], f"Kicked {target_user}")
    save_db(db)
    return jsonify({"status":"success","message":"User kicked"})

# /ban_member [POST]
# {"guild_id":"...","username":"..."}
@app.route('/ban_member', methods=['POST'])
def ban_member():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    guild_id = data.get('guild_id')
    target_user = data.get('username')

    guild = find_guild(db, guild_id)
    if not guild:
        return jsonify({"status":"error","message":"Guild not found"}),404

    if not user_has_permission(guild, cu['username'], "ban_members"):
        return jsonify({"status":"error","message":"No permission"}),403

    mem = user_in_guild(guild, target_user)
    if mem:
        guild['members'] = [m for m in guild['members'] if m['username'] != target_user]
        t_user = find_user(db, target_user)
        if t_user and guild_id in t_user['guilds']:
            t_user['guilds'].remove(guild_id)

    if 'bans' not in guild:
        guild['bans'] = []
    if target_user not in guild['bans']:
        guild['bans'].append(target_user)

    add_audit_log(guild, "BAN_MEMBER", cu['username'], f"Banned {target_user}")
    save_db(db)
    return jsonify({"status":"success","message":"User banned"})

# /unban_member [POST]
# {"guild_id":"...","username":"..."}
@app.route('/unban_member', methods=['POST'])
def unban_member():
    db = load_db()
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({"status":"error","message":"Unauthorized"}),401
    token = auth.split(" ")[1]
    cu = find_user_by_token(db, token)
    if not cu:
        return jsonify({"status":"error","message":"Invalid token"}),401

    data = request.get_json()
    guild_id = data.get('guild_id')
    target_user = data.get('username')

    guild = find_guild(db, guild_id)
    if not guild:
        return jsonify({"status":"error","message":"Guild not found"}),404

    if not user_has_permission(guild, cu['username'], "ban_members"):
        return jsonify({"status":"error","message":"No permission"}),403

    if 'bans' not in guild or target_user not in guild['bans']:
        return jsonify({"status":"error","message":"User not banned"}),400

    guild['bans'].remove(target_user)
    add_audit_log(guild, "UNBAN_MEMBER", cu['username'], f"Unbanned {target_user}")
    save_db(db)
    return jsonify({"status":"success","message":"User unbanned"})

##########################
# Audit Logs
##########################
# /audit_logs/<guild_id> [GET]
@app.route('/audit_logs/<guild_id>', methods=['GET'])
def audit_logs(guild_id):
    db = load_db()
    guild = find_guild(db, guild_id)
    if not guild:
        return jsonify({"status":"error","message":"Guild not found"}),404

    return jsonify({"audit_logs": guild['audit_logs']})

##########################
# Uygulama Başlatma
##########################
if __name__ == '__main__':
    app.run(debug=True)
