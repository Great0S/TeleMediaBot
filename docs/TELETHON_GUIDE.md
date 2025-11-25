# Telethon Capabilities Guide

A practical reference showing what Telethon can do with real code examples.

## Table of Contents
- [Authentication & Session Management](#authentication--session-management)
- [Dialog & Group Discovery](#dialog--group-discovery)
- [Message Operations](#message-operations)
- [Media Handling](#media-handling)
- [Real-time Updates & Events](#real-time-updates--events)
- [Group Administration](#group-administration)
- [Channel Management](#channel-management)
- [Bot Features](#bot-features)
- [Advanced Queries](#advanced-queries)
- [File Operations](#file-operations)

---

## Authentication & Session Management

**What it does**: Authenticate as a user or bot, manage persistent sessions, handle 2FA.

```python
from telethon import TelegramClient

# Connect as a user (requires phone + verification code)
client = TelegramClient('session_name', api_id, api_hash)
await client.start(phone='+1234567890')

# Connect as a bot (token from @BotFather)
bot_client = TelegramClient('bot_session', api_id, api_hash)
await bot_client.start(bot_token='YOUR_BOT_TOKEN')

# Check authorization status
is_authorized = await client.is_user_authorized()

# Get current logged-in user info
me = await client.get_me()
print(f"Logged in as: {me.username} (ID: {me.id})")
```

---

## Dialog & Group Discovery

**What it does**: List all chats, groups, channels the account has joined; fetch names, IDs, participant counts.

```python
# Get all dialogs (chats, groups, channels)
async for dialog in client.iter_dialogs():
    print(f"{dialog.name} | Type: {'Group' if dialog.is_group else 'Channel' if dialog.is_channel else 'User'}")
    print(f"  ID: {dialog.id}, Unread: {dialog.unread_count}")

# Filter only groups
groups = [d async for d in client.iter_dialogs() if d.is_group]

# Get specific chat by username or ID
chat = await client.get_entity('@channelname')  # or numeric ID
print(f"Chat: {chat.title}, Members: {chat.participants_count}")

# Search for dialogs by name
matching = [d async for d in client.iter_dialogs() if 'crypto' in d.name.lower()]
```

---

## Message Operations

**What it does**: Send, edit, delete, forward, reply to messages; read history; search messages.

```python
# Send a simple message
await client.send_message('@username', 'Hello from Telethon!')

# Send with formatting
from telethon.tl.types import MessageEntityBold, MessageEntityItalic
await client.send_message('chat_id', 'Bold text', 
                          parse_mode='markdown')  # or 'html'

# Reply to a specific message
message = await client.get_messages('@chat', ids=123)
await message.reply('This is a reply')

# Edit an existing message
await client.edit_message('@chat', message_id, 'Updated text')

# Forward messages
await client.forward_messages('destination_chat', [msg_id1, msg_id2], 'source_chat')

# Delete messages
await client.delete_messages('@chat', [message_id])

# Fetch message history
messages = await client.get_messages('@chat', limit=100)
for msg in messages:
    print(f"[{msg.date}] {msg.sender.username}: {msg.text}")

# Search messages by keyword
results = await client.get_messages('@chat', search='discount', limit=50)

# Mark messages as read
await client.send_read_acknowledge('@chat', max_id=message_id)

# Pin a message
await client.pin_message('@chat', message_id)

# Schedule a message
from datetime import datetime, timedelta
scheduled_time = datetime.now() + timedelta(hours=2)
await client.send_message('@chat', 'Scheduled message', schedule=scheduled_time)
```

---

## Media Handling

**What it does**: Upload/download photos, videos, files, audio, stickers; generate thumbnails; stream large files.

```python
# Send a photo
await client.send_file('@chat', '/path/to/photo.jpg', caption='Check this out!')

# Send multiple files as album
await client.send_file('@chat', ['/path/img1.jpg', '/path/img2.jpg'])

# Send video with thumbnail
await client.send_file('@chat', 'video.mp4', 
                       thumb='thumbnail.jpg',
                       supports_streaming=True,
                       attributes=[DocumentAttributeVideo(
                           duration=120,
                           w=1920,
                           h=1080
                       )])

# Download media from a message
message = await client.get_messages('@chat', ids=123)
if message.media:
    path = await message.download_media(file='downloads/')
    print(f"Downloaded to: {path}")

# Download only thumbnail (faster)
thumb_path = await message.download_media(file='thumbs/', thumb=-1)

# Stream large files with progress callback
async def progress(current, total):
    print(f"Downloaded {current}/{total} bytes ({100*current/total:.1f}%)")

await client.download_media(message, file='video.mp4', progress_callback=progress)

# Upload file with progress
await client.upload_file('/path/large_file.zip', progress_callback=progress)

# Get file info without downloading
if message.document:
    print(f"File: {message.file.name}, Size: {message.file.size} bytes")
    print(f"MIME: {message.file.mime_type}")

# Send voice message
await client.send_file('@chat', 'audio.ogg', 
                       voice_note=True,
                       attributes=[DocumentAttributeAudio(
                           duration=30,
                           voice=True
                       )])
```

---

## Real-time Updates & Events

**What it does**: Listen for new messages, edits, user typing, status changes; build bots and automation.

```python
from telethon import events

# Handle new messages
@client.on(events.NewMessage(pattern='/start'))
async def handler(event):
    await event.respond('Hello! I received your message.')

# Listen in specific chats
@client.on(events.NewMessage(chats=['@channel1', '@group2']))
async def channel_handler(event):
    print(f"New message in {event.chat.title}: {event.text}")

# Handle message edits
@client.on(events.MessageEdited)
async def edit_handler(event):
    print(f"Message {event.id} was edited to: {event.text}")

# Detect typing
@client.on(events.UserUpdate)
async def user_update(event):
    if event.typing:
        print(f"{event.user.username} is typing...")

# Handle button clicks (for bots)
@client.on(events.CallbackQuery)
async def callback_handler(event):
    if event.data == b'button1':
        await event.answer('You clicked button 1!')

# Album/media group handler
@client.on(events.Album)
async def album_handler(event):
    print(f"Received album with {len(event.messages)} photos/videos")

# Run the event loop
await client.run_until_disconnected()
```

---

## Group Administration

**What it does**: Manage permissions, ban/kick users, promote admins, control group settings.

```python
from telethon.tl.types import ChatBannedRights, ChatAdminRights

# Kick a user
await client.kick_participant('@group', 'user_id')

# Ban a user
await client.edit_permissions('@group', 'user_id', view_messages=False)

# Restrict user (mute, limit media, etc.)
restricted_rights = ChatBannedRights(
    until_date=None,  # Permanent
    send_messages=True,
    send_media=True,
)
await client.edit_permissions('@group', 'user_id', restricted_rights)

# Promote to admin
admin_rights = ChatAdminRights(
    change_info=True,
    delete_messages=True,
    ban_users=True,
    invite_users=True,
    pin_messages=True,
)
await client.edit_admin('@group', 'user_id', admin_rights, rank='Moderator')

# Demote admin
await client.edit_admin('@group', 'user_id', is_admin=False)

# Get participant list
participants = await client.get_participants('@group', limit=100)
for user in participants:
    print(f"{user.username} - Admin: {user.participant.admin_rights is not None}")

# Get admins only
admins = await client.get_participants('@group', filter=ChannelParticipantsAdmins)

# Change group title/description
await client.edit_title('@group', 'New Group Title')
await client.edit_about('@group', 'New group description')

# Update group photo
await client.edit_photo('@group', '/path/to/photo.jpg')

# Enable slow mode
await client(EditChatDefaultBannedRightsRequest(
    peer='@group',
    banned_rights=ChatBannedRights(
        until_date=None,
        send_messages=False
    )
))
```

---

## Channel Management

**What it does**: Post to channels, manage subscribers, get view statistics, handle comments.

```python
# Post to channel
await client.send_message('@channel', 'Breaking news!')

# Post with link preview disabled
await client.send_message('@channel', 'https://example.com', link_preview=False)

# Schedule channel post
from datetime import datetime, timedelta
await client.send_message('@channel', 'Scheduled post',
                          schedule=datetime.now() + timedelta(hours=1))

# Get channel subscribers
subs = await client.get_participants('@channel')
print(f"Total subscribers: {len(subs)}")

# Get message view statistics
message = await client.get_messages('@channel', ids=123)
print(f"Views: {message.views}, Forwards: {message.forwards}")

# Create invite link
from telethon.tl.functions.messages import ExportChatInviteRequest
invite = await client(ExportChatInviteRequest('@channel'))
print(f"Invite link: {invite.link}")

# Create invite link with limits
from telethon.tl.functions.messages import ExportChatInviteLinkRequest
invite = await client(ExportChatInviteLinkRequest(
    peer='@channel',
    expire_date=datetime.now() + timedelta(days=7),
    usage_limit=100
))

# Get channel info and stats
full_channel = await client.get_entity('@channel')
print(f"Subscribers: {full_channel.participants_count}")
```

---

## Bot Features

**What it does**: Inline queries, custom keyboards, callback buttons, bot commands, polls.

```python
from telethon.tl.custom import Button

# Send message with inline buttons
await client.send_message('@user', 
    'Choose an option:',
    buttons=[
        [Button.inline('Option 1', b'opt1'), Button.inline('Option 2', b'opt2')],
        [Button.url('Visit website', 'https://example.com')]
    ]
)

# Send with keyboard (forces user reply)
await client.send_message('@user',
    'Select:',
    buttons=[
        [Button.text('Button 1'), Button.text('Button 2')],
        [Button.request_phone('Share phone')]
    ]
)

# Answer inline query
@client.on(events.InlineQuery)
async def inline_handler(event):
    builder = event.builder
    results = [
        builder.article('Result 1', text='Content 1'),
        builder.article('Result 2', text='Content 2')
    ]
    await event.answer(results)

# Send a poll
from telethon.tl.types import Poll, PollAnswer
poll = Poll(
    id=0,
    question='Favorite color?',
    answers=[
        PollAnswer('Red', b'red'),
        PollAnswer('Blue', b'blue'),
        PollAnswer('Green', b'green')
    ]
)
await client.send_message('@chat', file=InputMediaPoll(poll))

# Get bot commands list
from telethon.tl.functions.bots import GetBotCommandsRequest
commands = await client(GetBotCommandsRequest())
```

---

## Advanced Queries

**What it does**: Call any Telegram MTProto method directly; access features not wrapped by helpers.

```python
from telethon.tl.functions.messages import GetHistoryRequest, SearchRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import InputMessagesFilterPhotos

# Raw API call to get history
history = await client(GetHistoryRequest(
    peer='@chat',
    offset_id=0,
    offset_date=None,
    add_offset=0,
    limit=50,
    max_id=0,
    min_id=0,
    hash=0
))

# Search with specific filter (e.g., photos only)
photos = await client(SearchRequest(
    peer='@chat',
    q='',
    filter=InputMessagesFilterPhotos(),
    min_date=None,
    max_date=None,
    offset_id=0,
    add_offset=0,
    limit=100,
    max_id=0,
    min_id=0,
    hash=0
))

# Get full channel details (not available via get_entity)
full = await client(GetFullChannelRequest(channel='@channel'))
print(f"About: {full.full_chat.about}")
print(f"Participants: {full.full_chat.participants_count}")
print(f"Admins: {full.full_chat.admins_count}")

# Access flood wait info
from telethon.errors import FloodWaitError
try:
    await client.send_message('@chat', 'test')
except FloodWaitError as e:
    print(f"Need to wait {e.seconds} seconds")
```

---

## File Operations

**What it does**: Batch uploads/downloads, chunk handling, resumable transfers, custom attributes.

```python
# Upload file with custom attributes
from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeVideo

attributes = [
    DocumentAttributeFilename('custom_name.mp4'),
    DocumentAttributeVideo(
        duration=120,
        w=1920,
        h=1080,
        supports_streaming=True
    )
]
await client.send_file('@chat', '/path/video.mp4', attributes=attributes)

# Batch download from channel
messages = await client.get_messages('@channel', limit=100)
for msg in messages:
    if msg.media:
        await msg.download_media(file=f'downloads/{msg.id}')

# Get download URL (for web access)
# Note: Telethon doesn't generate public URLs; you need to serve downloaded files yourself
# or use Telegram's web interface

# Upload large file with resume support
from telethon import utils
file_id = await client.upload_file(
    '/path/large.zip',
    part_size_kb=512,  # Upload in 512KB chunks
    progress_callback=progress
)

# Check file size before download
message = await client.get_messages('@chat', ids=123)
if message.file and message.file.size < 50_000_000:  # 50MB
    await message.download_media()
else:
    print("File too large, skipping")

# Download to BytesIO (in-memory)
from io import BytesIO
buffer = BytesIO()
await client.download_media(message, file=buffer)
buffer.seek(0)
# Now process buffer.read()
```

---

## Practical Examples from TeleMediaBot

### Example 1: Fetch Group Messages with Attachments
```python
async def fetch_messages_with_media(client, group, limit=50):
    messages = []
    async for message in client.iter_messages(group, limit=limit):
        if not message.text:
            continue
        
        attachments = []
        if message.media:
            file = getattr(message, 'file', None)
            if file:
                attachments.append({
                    'type': message.media.__class__.__name__,
                    'name': file.name,
                    'size': file.size,
                    'mime': file.mime_type
                })
        
        messages.append({
            'id': message.id,
            'date': message.date,
            'text': message.text,
            'attachments': attachments
        })
    
    return messages
```

### Example 2: Auto-reply Bot
```python
@client.on(events.NewMessage(pattern=r'/help'))
async def help_command(event):
    help_text = """
    Available commands:
    /start - Start the bot
    /help - Show this message
    /info - Get chat info
    """
    await event.respond(help_text)

@client.on(events.NewMessage(pattern=r'/info'))
async def info_command(event):
    chat = await event.get_chat()
    info = f"Chat: {chat.title}\nID: {chat.id}\nType: {'Group' if chat.megagroup else 'Channel'}"
    await event.respond(info)
```

### Example 3: Channel Content Aggregator
```python
async def aggregate_channel_links(client, channels, keyword, days=7):
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=days)
    
    results = []
    for channel in channels:
        async for message in client.iter_messages(channel, offset_date=cutoff):
            if keyword.lower() in (message.text or '').lower():
                results.append({
                    'channel': channel,
                    'text': message.text,
                    'date': message.date,
                    'link': f"https://t.me/{channel.lstrip('@')}/{message.id}"
                })
    
    return results
```

---

## Additional Resources

- **Official Docs**: https://docs.telethon.dev/
- **API Reference**: https://tl.telethon.dev/
- **Examples**: https://github.com/LonamiWebs/Telethon/tree/master/telethon_examples

## Tips

1. **Rate Limits**: Telegram enforces flood limits. Use `await asyncio.sleep()` between bulk operations.
2. **Sessions**: Session files store auth state. Keep them secure; they grant full account access.
3. **Entity Cache**: Telethon caches entities. Use `client.get_entity()` to refresh if data seems stale.
4. **Error Handling**: Wrap API calls in try/except for `RPCError`, `FloodWaitError`, `ChatWriteForbiddenError`, etc.
5. **Privacy**: User clients can do more than bots, but respect privacy and Telegram's ToS.
