## Chat Application Backend Documentation

This document provides comprehensive information about the backend of a chat application built using Flask, SocketIO, and Elasticsearch.

### 1. Overview

This backend serves as the foundation for a feature-rich chat platform, offering real-time communication, file uploads, user and guild management, event planning, notifications, statistics, API integrations, polls, reporting, moderation, achievements, and analytics.

### 2. Technologies

* **Flask:** Python web framework for building the API and handling HTTP requests.
* **SocketIO:** Enables real-time, bidirectional communication between clients and the server for instant messaging and other real-time features.
* **Flask-Babel:**  Provides internationalization and localization support for serving the application in multiple languages.
* **Elasticsearch:**  A powerful search and analytics engine used for indexing and searching through messages, users, and channels.
* **Boto3:**  The AWS SDK for Python, used for interacting with Amazon S3 for storing and retrieving uploaded files.
* **OpenAI:**  Integration with OpenAI's API for potential AI-powered features like chatbots or content generation. (Optional)
* **JWT (JSON Web Token):**  A standard for securely transmitting information between parties, used for authentication and authorization of users.
* **PyDub:**  A Python library for audio manipulation, potentially used for audio message processing. (Optional)
* **Pandas, Matplotlib, Seaborn:**  Data analysis and visualization libraries for generating statistics and analytical reports.

### 3. Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration:**
   * **Create a `config.py` file:**
     ```python
     # config.py
     import os

     BASE_DIR = os.path.abspath(os.path.dirname(__file__))

     # Flask Configuration
     SECRET_KEY = 'your-secret-key'
     UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
     MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
     LANGUAGES = ['en', 'tr', 'es', 'fr', 'de']

     # Elasticsearch Configuration
     ES_HOST = 'localhost'
     ES_PORT = 9200

     # Amazon S3 Configuration
     S3_BUCKET = 'your-s3-bucket-name'
     S3_ACCESS_KEY_ID = 'your-s3-access-key-id'
     S3_SECRET_ACCESS_KEY = 'your-s3-secret-access-key'

     # OpenAI Configuration (Optional)
     OPENAI_API_KEY = 'your-openai-api-key'

     # Database File
     DB_FILE = 'database.json'

     # Allowed File Extensions
     ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav'}
     ```

5. **Run the application:**
   ```bash
   flask run
   ```

### 4. API Documentation

#### 4.1. Authentication

* **POST /register:** Register a new user.
    * **Request Body:**
        ```json
        {
          "username": "username",
          "password": "password",
          "email": "user@example.com"
        }
        ```
    * **Response:** 201 (Created) if successful, returns the new user object.

* **POST /login:** User login.
    * **Request Body:**
        ```json
        {
          "username": "username",
          "password": "password"
        }
        ```
    * **Response:** 200 (OK) if successful, returns an object containing the JWT.

* **POST /logout:** Logs out the user.
    * **Request Header:** `Authorization: Bearer <JWT>`
    * **Response:** 200 (OK) if successful.

#### 4.2. Users

* **GET /users/<user_id>/profile:** Retrieve a user's profile.
* **PUT /users/<user_id>/profile:** Update a user's profile.
* **POST /users/<user_id>/block:** Block a specific user.
* **DELETE /users/<user_id>/block:** Unblock a specific user.

#### 4.3. Guilds (Servers)

* **GET /guilds:** List all guilds.
* **POST /guilds:** Create a new guild.
* **GET /guilds/<guild_id>/settings:** Retrieve guild settings.
* **PUT /guilds/<guild_id>/settings:** Update guild settings.
* **GET /guilds/<guild_id>/channels:** List guild channels.
* **POST /guilds/<guild_id>/channels:** Add a new channel to the guild.
* **GET /guilds/<guild_id>/roles:** List guild roles.
* **POST /guilds/<guild_id>/roles:** Add a new role to the guild.
* **GET /guilds/<guild_id>/bans:** List guild bans.
* **POST /guilds/<guild_id>/bans:** Ban a user from the guild.
* **DELETE /guilds/<guild_id>/bans:** Unban a user from the guild.

#### 4.4. Channels

* **GET /channels/<channel_id>/messages:** Retrieve channel messages.
* **POST /channels/<channel_id>/messages:** Send a new message to the channel.
* **GET /channels/<channel_id>/pins:** Retrieve pinned messages in the channel.
* **POST /channels/<channel_id>/pins:** Pin a message to the channel.
* **DELETE /channels/<channel_id>/pins:** Unpin a message from the channel.

#### 4.5. Messages

* **POST /messages/<message_id>/reactions:** Add a reaction to a message.
* **DELETE /messages/<message_id>/reactions:** Remove a reaction from a message.

#### 4.6. Files

* **POST /upload:** Upload a file.
* **GET /files/<file_id>:** Retrieve file information.
* **GET /files/<file_id>/download:** Download a file.

#### 4.7. Events

* **GET /events:** List all events.
* **POST /events:** Create a new event.
* **POST /events/<event_id>/participate:** Participate in an event.

#### 4.8. Polls

* **GET /polls:** List all polls.
* **POST /polls:** Create a new poll.
* **POST /polls/<poll_id>/vote:** Vote in a poll.

#### 4.9. Reports

* **POST /reports:** Create a new report.
* **GET /reports:** List all reports (authorized users only).
* **PUT /reports/<report_id>:** Update report status (authorized users only).

#### 4.10. Statistics and Analytics

* **GET /statistics/users/<user_id>:** Retrieve user statistics.
* **GET /statistics/guilds/<guild_id>:** Retrieve guild statistics.
* **GET /analytics/users:** Retrieve user analytics (authorized users only).

#### 4.11. Notifications

* **GET /notifications/settings:** Retrieve notification settings.
* **PUT /notifications/settings:** Update notification settings.

#### 4.12. Other

* **GET /search:** Search for messages, users, and channels.
* **GET /roles:** List all roles.
* **POST /roles:** Create a new role.
* **GET /marketplace:** List available API integrations.
* **POST /marketplace/<integration_id>:** Install an API integration.

### 5. SocketIO Events

* **connect:** Triggered when a new client connects.
* **disconnect:** Triggered when a client disconnects.
* **join_room:** Triggered when a client joins a room (channel or guild).
* **leave_room:** Triggered when a client leaves a room.
* **send_message:** Triggered when a client sends a new message.
* **typing:** Triggered when a client starts typing.
* **stop_typing:** Triggered when a client stops typing.
* **join_voice:** Triggered when a client joins a voice channel.
* **leave_voice:** Triggered when a client leaves a voice channel.
* **voice_state:** Triggered when a client's voice state changes (speaking, muted, deafened).

### 6. Code Example (Python Client)

```python
import requests

# Example: Registering a new user
response = requests.post(
    'http://localhost:5000/register',
    json={
        "username": "newuser",
        "password": "password",
        "email": "newuser@example.com"
    }
)

if response.status_code == 201:
    user = response.json()
    print(f"New user created: {user}")
else:
    print(f"Error: {response.text}")
```

### 7. Contact

For any questions, bug reports, or feedback, please contact [root@pyrollc.com.tr].
