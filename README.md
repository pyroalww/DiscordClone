# Frontend Integration Guide for Discord Clone Backend

Welcome to the **Discord Clone Frontend Integration Guide**! This guide will help you understand how to interact with the provided backend API to build a fully functional frontend application. Whether you're using React, Vue, Angular, or any other frontend framework, this guide will provide the necessary information to connect seamlessly with the backend.

## Table of Contents

1. [Authentication](#authentication)
   - [Register](#register)
   - [Login](#login)
   - [Logout](#logout)
2. [User Management](#user-management)
   - [Get User Information](#get-user-information)
   - [Update Profile](#update-profile)
3. [Friend System](#friend-system)
   - [Send Friend Request](#send-friend-request)
   - [Respond to Friend Request](#respond-to-friend-request)
   - [List Friend Requests](#list-friend-requests)
   - [List Friends](#list-friends)
4. [Direct Messages (DM)](#direct-messages-dm)
   - [Create DM Channel](#create-dm-channel)
   - [Send DM Message](#send-dm-message)
   - [Retrieve DM Messages](#retrieve-dm-messages)
   - [Edit DM Message](#edit-dm-message)
   - [Delete DM Message](#delete-dm-message)
5. [Guild (Server) Management](#guild-server-management)
   - [Create Guild](#create-guild)
   - [List Guilds](#list-guilds)
   - [Get Guild Information](#get-guild-information)
   - [Create Category](#create-category)
   - [Create Channel](#create-channel)
   - [Create Voice Channel](#create-voice-channel)
6. [Invite Management](#invite-management)
   - [Create Invite](#create-invite)
   - [Join Guild via Invite](#join-guild-via-invite)
7. [Message Management](#message-management)
   - [Send Message](#send-message)
   - [Retrieve Messages](#retrieve-messages)
   - [Edit Message](#edit-message)
   - [Delete Message](#delete-message)
   - [Pin Message](#pin-message)
   - [Add Reaction](#add-reaction)
   - [Remove Reaction](#remove-reaction)
   - [Search Messages](#search-messages)
8. [Voice Channel Management](#voice-channel-management)
   - [Join Voice Channel](#join-voice-channel)
   - [Leave Voice Channel](#leave-voice-channel)
   - [Start Screen Share](#start-screen-share)
   - [Stop Screen Share](#stop-screen-share)
9. [Emoji Management](#emoji-management)
   - [Add Emoji](#add-emoji)
   - [Remove Emoji](#remove-emoji)
10. [Additional Features](#additional-features)
    - [Update Profile with GIFs and Banners](#update-profile-with-gifs-and-banners)
11. [Error Handling](#error-handling)
12. [Example API Calls](#example-api-calls)
13. [Best Practices](#best-practices)

---

## Authentication

Authentication is crucial for securing your application. The backend uses a simple token-based system where the token is the username. **Note:** For production environments, it's highly recommended to implement a more secure authentication mechanism like JWT (JSON Web Tokens) and hash passwords using algorithms like bcrypt or Argon2.

### Register

**Endpoint:** `/register`  
**Method:** `POST`  
**Description:** Register a new user.

**Headers:**  
- `Content-Type: application/json`

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "securepassword123",
  "avatar_url": "https://example.com/avatar.gif" // Optional
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "User registered"
  }
  ```
- **Error (400):**
  ```json
  {
    "status": "error",
    "message": "Username already exists"
  }
  ```

### Login

**Endpoint:** `/login`  
**Method:** `POST`  
**Description:** Authenticate a user and retrieve a token.

**Headers:**  
- `Content-Type: application/json`

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "securepassword123"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "token": "john_doe"
  }
  ```
- **Error (401):**
  ```json
  {
    "status": "error",
    "message": "Invalid credentials"
  }
  ```

### Logout

**Endpoint:** `/logout`  
**Method:** `POST`  
**Description:** Logout the authenticated user.

**Headers:**  
- `Authorization: Bearer john_doe`

**Request Body:**  
_None_

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Logged out"
  }
  ```
- **Error (401):**
  ```json
  {
    "status": "error",
    "message": "Unauthorized"
  }
  ```

---

## User Management

### Get User Information

**Endpoint:** `/user/<username>`  
**Method:** `GET`  
**Description:** Retrieve information about a specific user.

**Headers:**  
_None_

**URL Parameters:**
- `<username>`: The username of the user to retrieve.

**Response:**
- **Success (200):**
  ```json
  {
    "username": "john_doe",
    "online": true,
    "friends": ["jane_smith"],
    "guilds": ["guild_id_1"],
    "dm_channels": ["dm_id_1"],
    "avatar_url": "https://example.com/avatar.gif"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "User not found"
  }
  ```

### Update Profile

**Endpoint:** `/update_profile`  
**Method:** `POST`  
**Description:** Update the authenticated user's profile, including avatar and banner.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "avatar_url": "https://example.com/new_avatar.gif", // Optional
  "banner_url": "https://example.com/banner.gif"    // Optional
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Profile updated"
  }
  ```
- **Error (400):**
  ```json
  {
    "status": "error",
    "message": "Invalid avatar URL"
  }
  ```

---

## Friend System

### Send Friend Request

**Endpoint:** `/send_friend_request`  
**Method:** `POST`  
**Description:** Send a friend request to another user.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "to_user": "jane_smith"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Friend request sent"
  }
  ```
- **Error (400):**
  ```json
  {
    "status": "error",
    "message": "Already friends"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "User not found"
  }
  ```

### Respond to Friend Request

**Endpoint:** `/respond_friend_request`  
**Method:** `POST`  
**Description:** Accept or reject a received friend request.

**Headers:**  
- `Authorization: Bearer jane_smith`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "request_id": "request_uuid",
  "action": "accept" // or "reject"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Friend added"
  }
  ```
- **Error (400):**
  ```json
  {
    "status": "error",
    "message": "Invalid action"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "Not your request"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Request not found"
  }
  ```

### List Friend Requests

**Endpoint:** `/friend_requests`  
**Method:** `GET`  
**Description:** Retrieve incoming friend requests for the authenticated user.

**Headers:**  
- `Authorization: Bearer jane_smith`

**Request Body:**  
_None_

**Response:**
- **Success (200):**
  ```json
  {
    "friend_requests": [
      {
        "id": "request_uuid",
        "from": "john_doe",
        "to": "jane_smith"
      }
    ]
  }
  ```
- **Error (401):**
  ```json
  {
    "status": "error",
    "message": "Unauthorized"
  }
  ```

### List Friends

**Endpoint:** `/friends`  
**Method:** `GET`  
**Description:** Retrieve the list of friends for the authenticated user.

**Headers:**  
- `Authorization: Bearer john_doe`

**Request Body:**  
_None_

**Response:**
- **Success (200):**
  ```json
  {
    "friends": [
      {
        "username": "jane_smith",
        "online": true
      }
    ]
  }
  ```
- **Error (401):**
  ```json
  {
    "status": "error",
    "message": "Unauthorized"
  }
  ```

---

## Direct Messages (DM)

### Create DM Channel

**Endpoint:** `/create_dm`  
**Method:** `POST`  
**Description:** Create a direct message channel with a friend.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "with_user": "jane_smith"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "dm_id": "dm_uuid",
    "message": "DM already exists"
  }
  ```
  *or*
  ```json
  {
    "status": "success",
    "dm_id": "dm_uuid"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "You can only DM friends"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "User not found"
  }
  ```

### Send DM Message

**Endpoint:** `/send_dm`  
**Method:** `POST`  
**Description:** Send a message in a DM channel.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "dm_id": "dm_uuid",
  "content": "Hello Jane!",
  "file_base64": "base64_encoded_file" // Optional
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message_id": "message_uuid"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "Not a participant"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "DM not found"
  }
  ```

### Retrieve DM Messages

**Endpoint:** `/dm_messages/<dm_id>`  
**Method:** `GET`  
**Description:** Retrieve all messages from a DM channel.

**Headers:**  
- `Authorization: Bearer john_doe`

**URL Parameters:**
- `<dm_id>`: The ID of the DM channel.

**Response:**
- **Success (200):**
  ```json
  {
    "messages": [
      {
        "id": "message_uuid",
        "author": "john_doe",
        "content": "Hello Jane!",
        "timestamp": "2024-04-27T12:34:56.789Z",
        "file_base64": "base64_encoded_file"
      }
    ]
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "Not participant"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "DM not found"
  }
  ```

### Edit DM Message

**Endpoint:** `/edit_dm_message`  
**Method:** `POST`  
**Description:** Edit a message in a DM channel.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "dm_id": "dm_uuid",
  "message_id": "message_uuid",
  "new_content": "Hello Jane! (edited)"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "DM message edited"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No permission"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "DM not found"
  }
  ```

### Delete DM Message

**Endpoint:** `/delete_dm_message`  
**Method:** `POST`  
**Description:** Delete a message in a DM channel.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "dm_id": "dm_uuid",
  "message_id": "message_uuid"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "DM message deleted"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No permission"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Message not found"
  }
  ```

---

## Guild (Server) Management

### Create Guild

**Endpoint:** `/create_guild`  
**Method:** `POST`  
**Description:** Create a new guild (server).

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "name": "My Awesome Server"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "guild_id": "guild_uuid"
  }
  ```
- **Error (401):**
  ```json
  {
    "status": "error",
    "message": "Unauthorized"
  }
  ```

### List Guilds

**Endpoint:** `/guilds`  
**Method:** `GET`  
**Description:** Retrieve a list of all guilds.

**Headers:**  
_None_

**Request Body:**  
_None_

**Response:**
- **Success (200):**
  ```json
  {
    "guilds": [
      {
        "id": "guild_uuid",
        "name": "My Awesome Server",
        "owner": "john_doe",
        "member_count": 5
      }
    ]
  }
  ```

### Get Guild Information

**Endpoint:** `/guild/<guild_id>`  
**Method:** `GET`  
**Description:** Retrieve detailed information about a specific guild.

**Headers:**  
_None_

**URL Parameters:**
- `<guild_id>`: The ID of the guild to retrieve.

**Response:**
- **Success (200):**
  ```json
  {
    "id": "guild_uuid",
    "name": "My Awesome Server",
    "owner": "john_doe",
    "roles": ["admin", "member"],
    "categories": [],
    "channels": [
      {
        "id": "channel_uuid",
        "guild_id": "guild_uuid",
        "name": "general",
        "description": "General discussion",
        "is_private": false,
        "allowed_roles": [],
        "type": "text"
      }
    ],
    "member_count": 5
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Guild not found"
  }
  ```

### Create Category

**Endpoint:** `/create_category`  
**Method:** `POST`  
**Description:** Create a new category within a guild.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "guild_id": "guild_uuid",
  "name": "Announcements"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "category_id": "category_uuid"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No permission"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Guild not found"
  }
  ```

### Create Channel

**Endpoint:** `/create_channel`  
**Method:** `POST`  
**Description:** Create a new text or voice channel within a guild.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "guild_id": "guild_uuid",
  "category_id": "category_uuid", // Optional
  "name": "general",
  "description": "General discussion",
  "is_private": false,
  "allowed_roles": ["admin", "member"]
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "channel_id": "channel_uuid"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No permission"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Guild not found"
  }
  ```

### Create Voice Channel

**Endpoint:** `/create_voice_channel`  
**Method:** `POST`  
**Description:** Create a new voice channel within a guild.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "guild_id": "guild_uuid",
  "name": "Voice Channel",
  "is_private": false,
  "allowed_roles": ["admin", "member"]
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "voice_channel_id": "voice_channel_uuid"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No permission"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Guild not found"
  }
  ```

---

## Invite Management

### Create Invite

**Endpoint:** `/invite_create`  
**Method:** `POST`  
**Description:** Create an invite link for a specific channel within a guild.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "guild_id": "guild_uuid",
  "channel_id": "channel_uuid",
  "expires_in_seconds": 3600, // Optional, default is 3600 seconds
  "max_uses": 10               // Optional, default is unlimited
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "invite_id": "invite_uuid"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No permission"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Guild not found"
  }
  ```

### Join Guild via Invite

**Endpoint:** `/join_by_invite`  
**Method:** `POST`  
**Description:** Join a guild using an invite link.

**Headers:**  
- `Authorization: Bearer jane_smith`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "invite_id": "invite_uuid"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Joined guild"
  }
  ```
- **Error (400):**
  ```json
  {
    "status": "error",
    "message": "Already in guild"
  }
  ```
- **Error (400):**
  ```json
  {
    "status": "error",
    "message": "Invite invalid or expired"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Invite not found"
  }
  ```
- **Error (401):**
  ```json
  {
    "status": "error",
    "message": "Unauthorized"
  }
  ```

---

## Message Management

### Send Message

**Endpoint:** `/send_message`  
**Method:** `POST`  
**Description:** Send a message in a text channel.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "channel_id": "channel_uuid",
  "content": "Hello everyone!",
  "file_base64": "base64_encoded_file" // Optional
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message_id": "message_uuid"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No access to this channel"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Channel not found"
  }
  ```

### Retrieve Messages

**Endpoint:** `/messages/<channel_id>`  
**Method:** `GET`  
**Description:** Retrieve all messages from a specific channel.

**Headers:**  
- `Authorization: Bearer john_doe` // Required if channel is private

**URL Parameters:**
- `<channel_id>`: The ID of the channel to retrieve messages from.

**Response:**
- **Success (200):**
  ```json
  {
    "messages": [
      {
        "id": "message_uuid",
        "channel_id": "channel_uuid",
        "author": "john_doe",
        "content": "Hello everyone!",
        "timestamp": "2024-04-27T12:34:56.789Z",
        "file_base64": "base64_encoded_file",
        "pinned": false,
        "reactions": []
      }
    ]
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No access"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Channel not found"
  }
  ```

### Edit Message

**Endpoint:** `/edit_message`  
**Method:** `POST`  
**Description:** Edit a message in a channel.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "message_id": "message_uuid",
  "new_content": "Hello everyone! (edited)"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Message edited"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No permission"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Message not found"
  }
  ```

### Delete Message

**Endpoint:** `/delete_message`  
**Method:** `POST`  
**Description:** Delete a message from a channel.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "message_id": "message_uuid"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Message deleted"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No permission"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Message not found"
  }
  ```

### Pin Message

**Endpoint:** `/pin_message`  
**Method:** `POST`  
**Description:** Pin a message in a channel.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "message_id": "message_uuid"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Message pinned"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No permission"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Message not found"
  }
  ```

### Add Reaction

**Endpoint:** `/add_reaction`  
**Method:** `POST`  
**Description:** Add an emoji reaction to a message.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "message_id": "message_uuid",
  "emoji_id": "emoji_uuid"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Reaction added"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No access"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Message not found"
  }
  ```

### Remove Reaction

**Endpoint:** `/remove_reaction`  
**Method:** `POST`  
**Description:** Remove an emoji reaction from a message.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "message_id": "message_uuid",
  "emoji_id": "emoji_uuid"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Reaction removed"
  }
  ```
- **Error (400):**
  ```json
  {
    "status": "error",
    "message": "You did not react"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Reaction not found"
  }
  ```

### Search Messages

**Endpoint:** `/search_messages`  
**Method:** `GET`  
**Description:** Search for messages containing a specific query string.

**Headers:**  
- `Content-Type: application/json`

**Query Parameters:**
- `q`: The search query string.

**Example URL:**
```
/search_messages?q=hello
```

**Response:**
- **Success (200):**
  ```json
  {
    "results": [
      {
        "id": "message_uuid",
        "channel_id": "channel_uuid",
        "author": "john_doe",
        "content": "Hello everyone!",
        "timestamp": "2024-04-27T12:34:56.789Z",
        "file_base64": "base64_encoded_file",
        "pinned": false,
        "reactions": []
      }
    ]
  }
  ```
- **Error (400):**
  ```json
  {
    "status": "error",
    "message": "Invalid query"
  }
  ```

---

## Voice Channel Management

### Join Voice Channel

**Endpoint:** `/join_voice_channel`  
**Method:** `POST`  
**Description:** Join a voice channel.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "channel_id": "voice_channel_uuid"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Joined voice channel"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No access to this voice channel"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Voice channel not found"
  }
  ```

### Leave Voice Channel

**Endpoint:** `/leave_voice_channel`  
**Method:** `POST`  
**Description:** Leave a voice channel.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "channel_id": "voice_channel_uuid"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Left voice channel"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Voice channel not found"
  }
  ```

### Start Screen Share

**Endpoint:** `/start_screen_share`  
**Method:** `POST`  
**Description:** Start screen sharing in a voice channel.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "channel_id": "voice_channel_uuid"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Screen share started"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "You are not in this voice channel"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Voice channel not found"
  }
  ```

### Stop Screen Share

**Endpoint:** `/stop_screen_share`  
**Method:** `POST`  
**Description:** Stop screen sharing in a voice channel.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "channel_id": "voice_channel_uuid"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Screen share stopped"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "You are not the one sharing"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Voice channel not found"
  }
  ```
- **Error (400):**
  ```json
  {
    "status": "error",
    "message": "No active screen share"
  }
  ```

---

## Emoji Management

### Add Emoji

**Endpoint:** `/add_emoji`  
**Method:** `POST`  
**Description:** Add a custom emoji to a guild.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "guild_id": "guild_uuid",
  "name": "cool_emoji",
  "image_base64": "base64_encoded_image"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "emoji_id": "emoji_uuid"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No permission"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Guild not found"
  }
  ```

### Remove Emoji

**Endpoint:** `/remove_emoji`  
**Method:** `POST`  
**Description:** Remove a custom emoji from a guild.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "guild_id": "guild_uuid",
  "emoji_id": "emoji_uuid"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Emoji removed"
  }
  ```
- **Error (403):**
  ```json
  {
    "status": "error",
    "message": "No permission"
  }
  ```
- **Error (404):**
  ```json
  {
    "status": "error",
    "message": "Emoji not found"
  }
  ```

---

## Additional Features

### Update Profile with GIFs and Banners

**Endpoint:** `/update_profile`  
**Method:** `POST`  
**Description:** Update the authenticated user's profile with GIF avatars and banners.

**Headers:**  
- `Authorization: Bearer john_doe`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "avatar_url": "https://example.com/avatar.gif",
  "banner_url": "https://example.com/banner.gif"
}
```

**Response:**
- **Success (200):**
  ```json
  {
    "status": "success",
    "message": "Profile updated"
  }
  ```
- **Error (400):**
  ```json
  {
    "status": "error",
    "message": "Invalid avatar URL"
  }
  ```

---

## Error Handling

The backend uses standard HTTP status codes to indicate the success or failure of an API request. Here's a summary of common status codes and their meanings:

- **200 OK:** The request was successful.
- **400 Bad Request:** The server could not understand the request due to invalid syntax.
- **401 Unauthorized:** Authentication is required and has failed or has not been provided.
- **403 Forbidden:** The client does not have access rights to the content.
- **404 Not Found:** The server can not find the requested resource.

Each error response includes a JSON object with a `status` and a `message` to provide more context about the error.

---

## Example API Calls

Below are some example API calls using `fetch` in JavaScript. Replace placeholders like `BASE_URL`, `token`, and IDs with actual values.

### Register a New User

```javascript
fetch('https://your-api.com/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'john_doe',
    password: 'securepassword123',
    avatar_url: 'https://example.com/avatar.gif'
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

### Login

```javascript
fetch('https://your-api.com/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'john_doe',
    password: 'securepassword123'
  })
})
.then(response => response.json())
.then(data => {
  if (data.status === 'success') {
    localStorage.setItem('token', data.token);
  }
  console.log(data);
})
.catch(error => console.error('Error:', error));
```

### Send a Message in a Channel

```javascript
const token = localStorage.getItem('token');

fetch('https://your-api.com/send_message', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    channel_id: 'channel_uuid',
    content: 'Hello everyone!',
    file_base64: 'base64_encoded_file' // Optional
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

### Create a Guild

```javascript
const token = localStorage.getItem('token');

fetch('https://your-api.com/create_guild', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'My Awesome Server'
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

### Add an Emoji to a Guild

```javascript
const token = localStorage.getItem('token');

fetch('https://your-api.com/add_emoji', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    guild_id: 'guild_uuid',
    name: 'cool_emoji',
    image_base64: 'base64_encoded_image'
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

---

## Best Practices

1. **Secure Authentication:**
   - Implement JWT for secure token-based authentication.
   - Always hash and salt passwords using strong algorithms like bcrypt or Argon2.

2. **Use a Robust Database:**
   - Transition from using a JSON file to a scalable database like PostgreSQL or MongoDB.
   - Ensure proper indexing for faster query performance.

3. **Implement Real-Time Features:**
   - Use WebSockets or Socket.IO for real-time communication (e.g., live chat updates, voice/video calls).
   - Integrate WebRTC for peer-to-peer media streaming.

4. **Handle File Uploads Properly:**
   - Instead of storing files as base64 in JSON, use cloud storage services like AWS S3.
   - Implement file size and type validations on both frontend and backend.

5. **Enhance Security:**
   - Protect against common web vulnerabilities (CSRF, XSS, SQL Injection).
   - Implement rate limiting to prevent abuse.
   - Use HTTPS to encrypt data in transit.

6. **Optimize Performance:**
   - Implement caching strategies using tools like Redis.
   - Use pagination or infinite scrolling for message retrieval to reduce load times.

7. **Improve Error Handling:**
   - Provide meaningful error messages to the frontend.
   - Log errors on the server for monitoring and debugging purposes.

8. **Scalability:**
   - Design the application architecture to handle increased load.
   - Consider using microservices for different functionalities.

9. **User Experience:**
   - Ensure the frontend provides responsive and intuitive interfaces.
   - Implement loading states and feedback for asynchronous operations.

10. **Documentation:**
    - Maintain up-to-date API documentation using tools like Swagger or Postman.
    - Clearly document all endpoints, request parameters, and response formats.

---

## Conclusion

This guide provides a comprehensive overview of how to integrate your frontend application with the provided Discord Clone backend. By following the outlined steps and best practices, you can build a robust and feature-rich application. Remember to continuously test and iterate on both frontend and backend to ensure a seamless user experience.

Happy coding!
