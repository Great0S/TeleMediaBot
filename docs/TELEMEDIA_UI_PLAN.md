# TeleMedia UI Implementation Plan

## Overview
Transform TeleMediaBot into a comprehensive multi-page web application that exposes all Telethon capabilities through an intuitive UI.

---

## Architecture

### Tech Stack
- **Backend**: FastAPI (existing) + WebSocket for real-time
- **Frontend**: Enhanced HTML/CSS/JS (progressive enhancement, no framework overhead)
- **State**: Browser-native (localStorage for preferences, EventSource/WebSocket for live data)
- **Auth**: Session-based with role permissions (future: OAuth2)

### Navigation Structure
```
┌─ TeleMedia App ──────────────────────────────────────┐
│ [Logo] TeleMedia                    [User] [Settings]│
├──────────────────────────────────────────────────────┤
│ Sidebar          │ Main Content Area                 │
│ ┌──────────────┐ │                                   │
│ │ 📊 Dashboard │ │  Current: Message list, stats,    │
│ │ 💬 Messages  │ │  filters, media grid, URL scraper │
│ │ 🎬 Media     │ │                                   │
│ │ 👥 Groups    │ │  Future: Context-aware content    │
│ │ 📢 Channels  │ │  based on active sidebar item     │
│ │ 🤖 Bot Tools │ │                                   │
│ │ 🔐 Admin     │ │                                   │
│ │ 📈 Analytics │ │                                   │
│ └──────────────┘ │                                   │
└──────────────────┴───────────────────────────────────┘
```

---

## Phase 1: Foundation (Week 1)

### 1.1 UI Framework
- [ ] Create `telemedia/templates/base.html` – master layout with sidebar + topbar
- [ ] Build `telemedia/static/css/app.css` – unified design system (variables, components)
- [ ] Build `telemedia/static/js/navigation.js` – client-side routing (history API)
- [ ] Add `telemedia/static/js/components.js` – reusable UI elements (modals, toasts, loaders)

### 1.2 Shared Components
**Sidebar Navigation**
```html
<nav class="sidebar">
  <a href="/" class="nav-item active"><icon>📊</icon> Dashboard</a>
  <a href="/messages" class="nav-item"><icon>💬</icon> Messages</a>
  <a href="/media" class="nav-item"><icon>🎬</icon> Media</a>
  <a href="/groups" class="nav-item"><icon>👥</icon> Groups</a>
  <a href="/channels" class="nav-item"><icon>📢</icon> Channels</a>
  <a href="/bot-tools" class="nav-item"><icon>🤖</icon> Bot Tools</a>
  <a href="/admin" class="nav-item"><icon>🔐</icon> Admin</a>
  <a href="/analytics" class="nav-item"><icon>📈</icon> Analytics</a>
</nav>
```

**Topbar**
- Breadcrumbs (Dashboard > Messages > Search Results)
- Quick actions (New Post, Search, Notifications)
- User menu (Profile, Settings, Logout)

**Reusable Components**
- Card wrapper (stats, lists, forms)
- Data table (sortable, filterable, paginated)
- Modal dialog (confirm actions, forms)
- Toast notifications (success, error, info)
- Loading skeletons (already have for messages, extend)
- Empty states (no data placeholders)

### 1.3 Update Existing Dashboard
- [ ] Wrap current dashboard.html in new base.html layout
- [ ] Keep existing features: message list, filters, media grid, URL scraper
- [ ] Add quick stats row: Total Groups, Active Channels, Messages Today, Media Count
- [ ] Add recent activity feed (last 10 actions)

**API Changes**
```python
# telemedia/api.py additions
@app.get("/api/stats/summary")
async def get_dashboard_stats():
    """Quick stats for dashboard cards"""
    return {
        "groups_count": len(await collector.list_joined_groups()),
        "messages_today": await count_messages_today(),
        "media_count": count_cached_media(),
        "last_activity": get_recent_activity()
    }
```

---

## Phase 2: Core Pages (Week 2-3)

### 2.1 Messages Page (`/messages`)
**Features**
- Advanced search (keyword, sender, date range, media type)
- Multi-group search (select which groups to search)
- Bulk actions (export, delete, forward)
- Scheduled posts manager (view/edit/cancel scheduled messages)
- Message thread view (replies/forwards)

**UI Layout**
```
┌─ Search Bar ────────────────────────────────────────┐
│ [Keyword] [Groups ▼] [Date Range] [Media ▼] [Search]│
├─────────────────────────────────────────────────────┤
│ Filters: □ Links Only  □ Media  □ Forwarded         │
├─────────────────────────────────────────────────────┤
│ Results (120 messages)              [Export] [Select]│
│ ┌─ Message Card ───────────────────────────────────┐│
│ │ @channel · 2 hours ago                    [⋮]    ││
│ │ Check this sale: https://example.com             ││
│ │ [🖼️ Image preview]                                ││
│ │ 👁️ 1.2K  ↗️ 45  💬 12                             ││
│ └──────────────────────────────────────────────────┘│
│ ...more messages...                                  │
└─────────────────────────────────────────────────────┘
```

**Backend Routes**
```python
@app.get("/api/messages/search")
async def search_messages(
    query: str,
    groups: list[str],
    date_from: datetime | None,
    date_to: datetime | None,
    media_type: str | None,
    limit: int = 100
):
    """Advanced message search across selected groups"""

@app.get("/api/messages/scheduled")
async def list_scheduled_messages(group: str):
    """Get all scheduled posts for a group/channel"""

@app.delete("/api/messages/scheduled/{message_id}")
async def cancel_scheduled_message(group: str, message_id: int):
    """Cancel a scheduled post"""

@app.post("/api/messages/export")
async def export_messages(message_ids: list[int], format: str = "json"):
    """Export messages to JSON/CSV/PDF"""
```

### 2.2 Media Browser (`/media`)
**Features**
- Gallery grid view (thumbnails)
- Filter by type (images, videos, audio, documents)
- Filter by source group/channel
- Date range selector
- Bulk download (zip archive)
- Media details modal (resolution, size, duration, sender)
- Lightbox viewer for images/videos

**UI Layout**
```
┌─ Filters ───────────────────────────────────────────┐
│ [All Types ▼] [All Groups ▼] [Last 7 days ▼]       │
│ Sort: [Newest First ▼]               [Grid] [List]  │
├─────────────────────────────────────────────────────┤
│ 248 media files                   [Download All ⬇️] │
│ ┌────┬────┬────┬────┬────┬────┐                     │
│ │[📷]│[📷]│[🎬]│[📷]│[🎵]│[📷]│  ← Thumbnail grid   │
│ ├────┼────┼────┼────┼────┼────┤                     │
│ │[📷]│[🎬]│[📷]│[📄]│[📷]│[🎬]│                     │
│ └────┴────┴────┴────┴────┴────┘                     │
│ [Load More...]                                       │
└─────────────────────────────────────────────────────┘
```

**Backend Routes**
```python
@app.get("/api/media/list")
async def list_media(
    media_type: str | None,
    groups: list[str] | None,
    date_from: datetime | None,
    date_to: datetime | None,
    limit: int = 100,
    offset: int = 0
):
    """Paginated media listing with filters"""

@app.get("/api/media/{media_id}/info")
async def get_media_info(media_id: str):
    """Detailed media metadata"""

@app.post("/api/media/download-batch")
async def download_media_batch(media_ids: list[str]):
    """Create zip archive of selected media"""
```

### 2.3 Group Manager (`/groups`)
**Features**
- List all joined groups with stats (members, admins, unread)
- Member directory (search, filter by role)
- Permission editor (visual checkboxes for each permission)
- Bulk moderation (ban multiple users, assign roles)
- Group settings (title, description, photo, slow mode)
- Invite link generator with expiry/limit settings

**UI Layout**
```
┌─ My Groups (24) ────────────────────────────────────┐
│ [Search groups...] [+ Join Group]                   │
│ ┌─ Group Card ────────────────────────────────────┐ │
│ │ [Photo] CryptoTraders                           │ │
│ │         1,245 members · 8 admins                │ │
│ │         Last active: 5 min ago                  │ │
│ │         [View] [Settings] [Leave]               │ │
│ └─────────────────────────────────────────────────┘ │
│ ...more groups...                                    │
└─────────────────────────────────────────────────────┘

Click "Settings" →
┌─ Group Settings: CryptoTraders ─────────────────────┐
│ Tabs: [Info] [Members] [Permissions] [Moderation]   │
│                                                      │
│ [Members Tab Selected]                               │
│ ┌─ Members (1,245) ──────────────────────────────┐ │
│ │ [Search members...] [Filter: All ▼] [+ Invite] │ │
│ │ ┌────────────────────────────────────────────┐ │ │
│ │ │ @user123      Admin      [Edit] [Remove]   │ │ │
│ │ │ @user456      Member     [Promote] [Ban]   │ │ │
│ │ │ @user789      Restricted [Unban]           │ │ │
│ │ └────────────────────────────────────────────┘ │ │
│ └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Backend Routes**
```python
@app.get("/api/groups/list")
async def list_groups():
    """Enhanced group list with stats"""

@app.get("/api/groups/{group_id}/members")
async def list_group_members(group_id: str, role: str | None):
    """Get group members with optional role filter"""

@app.post("/api/groups/{group_id}/members/{user_id}/promote")
async def promote_member(group_id: str, user_id: int, permissions: dict):
    """Promote user with specific permissions"""

@app.post("/api/groups/{group_id}/members/{user_id}/ban")
async def ban_member(group_id: str, user_id: int, reason: str | None):
    """Ban a member from the group"""

@app.put("/api/groups/{group_id}/settings")
async def update_group_settings(group_id: str, settings: GroupSettings):
    """Update group info, photo, slow mode, etc."""

@app.post("/api/groups/{group_id}/invite-link")
async def create_invite_link(
    group_id: str,
    expire_days: int | None,
    usage_limit: int | None
):
    """Generate invite link with optional limits"""
```

### 2.4 Channel Manager (`/channels`)
**Features**
- List subscribed channels with stats (subscribers, views)
- Post composer (rich text, media upload, link preview)
- Schedule post (date/time picker)
- View statistics (views, forwards, reactions per post)
- Subscriber growth chart
- Generate invite links

**UI Layout**
```
┌─ My Channels (5) ───────────────────────────────────┐
│ [Search...] [+ Create Channel]                      │
│ ┌─ Channel Card ──────────────────────────────────┐ │
│ │ [Photo] Tech News Daily                         │ │
│ │         12.4K subscribers                       │ │
│ │         Last post: 1 hour ago (1.2K views)      │ │
│ │         [View Posts] [New Post] [Analytics]     │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘

Click "New Post" →
┌─ Create Post ───────────────────────────────────────┐
│ Channel: [Tech News Daily ▼]                        │
│ ┌────────────────────────────────────────────────┐ │
│ │ [Compose your message...]                      │ │
│ │                                                │ │
│ │                                                │ │
│ └────────────────────────────────────────────────┘ │
│ [📷 Photo] [🎬 Video] [📎 File] [🔗 Link Preview] │
│ □ Disable notification                              │
│ Schedule: [Now ▼] or [Pick date/time...]           │
│                                 [Cancel] [Post ✓]   │
└─────────────────────────────────────────────────────┘
```

**Backend Routes**
```python
@app.get("/api/channels/list")
async def list_channels():
    """List channels with subscriber counts"""

@app.post("/api/channels/{channel_id}/post")
async def create_channel_post(
    channel_id: str,
    text: str,
    media: UploadFile | None,
    schedule: datetime | None,
    silent: bool = False
):
    """Post to channel (immediate or scheduled)"""

@app.get("/api/channels/{channel_id}/posts")
async def get_channel_posts(channel_id: str, limit: int = 50):
    """Get recent posts with view counts"""

@app.get("/api/channels/{channel_id}/stats")
async def get_channel_stats(channel_id: str, days: int = 30):
    """Subscriber growth, engagement metrics"""
```

---

## Phase 3: Advanced Features (Week 4-5)

### 3.1 Bot Tools (`/bot-tools`)
**Features**
- Command manager (list, add, edit bot commands)
- Auto-reply rules (trigger keyword → response template)
- Inline query tester (test inline bot responses)
- Button builder (visual interface to create inline keyboards)
- Webhook config (set/view webhook URL and logs)

**UI Layout**
```
┌─ Bot Tools ─────────────────────────────────────────┐
│ Tabs: [Commands] [Auto-Reply] [Buttons] [Webhooks]  │
│                                                      │
│ [Commands Tab]                                       │
│ ┌─ Registered Commands ───────────────────────────┐ │
│ │ /start       Welcome new users          [Edit] │ │
│ │ /help        Show help menu             [Edit] │ │
│ │ /stats       Show bot statistics        [Edit] │ │
│ │                                      [+ Add New] │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│ [Auto-Reply Tab]                                     │
│ ┌─ Rules (3) ─────────────────────────────────────┐ │
│ │ Keyword: "price"                                │ │
│ │ Reply: "Check our pricing at..."       [Edit]  │ │
│ │ Active: ☑️                             [Delete] │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Backend Routes**
```python
@app.get("/api/bot/commands")
async def list_bot_commands():
    """Get current bot command list"""

@app.post("/api/bot/commands")
async def add_bot_command(command: str, description: str, handler: str):
    """Register a new bot command"""

@app.post("/api/bot/auto-reply")
async def add_auto_reply_rule(trigger: str, response: str, active: bool = True):
    """Create auto-reply rule"""

@app.post("/api/bot/test-inline")
async def test_inline_query(query: str):
    """Test inline query results"""
```

### 3.2 Admin Panel (`/admin`)
**Features**
- User lookup (search by username/ID, view profile)
- Bulk moderation queue (pending join requests, reported messages)
- Audit log (who did what, when)
- Permission templates (save common permission sets)
- System health (Telethon connection status, API rate limits)

**UI Layout**
```
┌─ Admin Panel ───────────────────────────────────────┐
│ Tabs: [Users] [Moderation] [Audit Log] [System]     │
│                                                      │
│ [Users Tab]                                          │
│ ┌─ User Lookup ────────────────────────────────────┐│
│ │ [Search by username or ID...]          [Search] ││
│ └──────────────────────────────────────────────────┘│
│ Results: @john_doe (ID: 123456789)                  │
│ ┌─ Profile ────────────────────────────────────────┐│
│ │ Name: John Doe                                   ││
│ │ Username: @john_doe                              ││
│ │ Status: Active                                   ││
│ │ Groups: CryptoTraders, Tech News (2 total)       ││
│ │ [View Activity] [Send Message] [Ban User]        ││
│ └──────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

**Backend Routes**
```python
@app.get("/api/admin/users/{user_id}")
async def get_user_profile(user_id: int):
    """Fetch user details"""

@app.get("/api/admin/moderation-queue")
async def get_moderation_queue():
    """Pending join requests, reports"""

@app.get("/api/admin/audit-log")
async def get_audit_log(date_from: datetime, date_to: datetime):
    """Action history"""

@app.get("/api/admin/system-health")
async def get_system_health():
    """Connection status, rate limits, cache stats"""
```

### 3.3 Analytics (`/analytics`)
**Features**
- Message volume chart (messages per day/hour)
- Top keywords trending (word cloud + table)
- Engagement metrics (most viewed posts, forwarded content)
- Group activity comparison (which groups are most active)
- Export reports (PDF/CSV)

**UI Layout**
```
┌─ Analytics ─────────────────────────────────────────┐
│ Date Range: [Last 30 Days ▼]              [Export] │
│ ┌─ Message Volume ─────────────────────────────────┐│
│ │      📊 Chart: Messages per Day                  ││
│ │     ┌────────────────────────────────────────┐   ││
│ │ 500 │         ╱╲                             │   ││
│ │ 400 │        ╱  ╲     ╱╲                     │   ││
│ │ 300 │       ╱    ╲   ╱  ╲    ╱╲              │   ││
│ │ 200 │      ╱      ╲ ╱    ╲  ╱  ╲             │   ││
│ │ 100 │─────╱────────╲──────╲╱────╲────────────│   ││
│ │     └────────────────────────────────────────┘   ││
│ │         1   5   10  15  20  25  30 (Days)        ││
│ └──────────────────────────────────────────────────┘│
│ ┌─ Top Keywords ───────────────────────────────────┐│
│ │ 1. bitcoin     1,245 mentions                    ││
│ │ 2. sale          892 mentions                    ││
│ │ 3. discount      654 mentions                    ││
│ └──────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

**Backend Routes**
```python
@app.get("/api/analytics/message-volume")
async def get_message_volume(date_from: datetime, date_to: datetime, group_by: str = "day"):
    """Time-series message counts"""

@app.get("/api/analytics/keywords")
async def get_top_keywords(date_from: datetime, date_to: datetime, limit: int = 50):
    """Trending keywords"""

@app.get("/api/analytics/engagement")
async def get_engagement_metrics(date_from: datetime, date_to: datetime):
    """Top posts, forwards, reactions"""

@app.post("/api/analytics/export")
async def export_analytics_report(format: str, date_from: datetime, date_to: datetime):
    """Generate PDF/CSV report"""
```

---

## Phase 4: Real-time & Polish (Week 6)

### 4.1 WebSocket Integration
**Features**
- Live message notifications (toast when new message arrives)
- Typing indicators (show when someone is typing)
- Online status updates (who's online in groups)
- Activity feed (live log of actions)

**Implementation**
```python
# telemedia/api.py
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Register client for push notifications
    # Send updates when new messages arrive
```

```javascript
// telemedia/static/js/websocket.js
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'new_message') {
        showToast(`New message in ${data.group}`);
        updateMessageList(data.message);
    }
};
```

### 4.2 Authentication & Multi-User
**Features**
- Login page (phone + verification code)
- Session management (multiple Telegram accounts)
- Role-based access (admin, moderator, viewer)
- User preferences (theme, notifications, default group)

**Backend Routes**
```python
@app.post("/api/auth/login")
async def login(phone: str):
    """Initiate Telegram login flow"""

@app.post("/api/auth/verify")
async def verify_code(phone: str, code: str):
    """Complete login with verification code"""

@app.get("/api/auth/sessions")
async def list_sessions():
    """List active Telegram sessions"""

@app.delete("/api/auth/sessions/{session_id}")
async def logout_session(session_id: str):
    """Remove a session"""
```

### 4.3 UI Polish
- [ ] Dark mode toggle
- [ ] Keyboard shortcuts (Ctrl+K for search, etc.)
- [ ] Responsive design (mobile-friendly)
- [ ] Accessibility (ARIA labels, keyboard navigation)
- [ ] Error boundaries (graceful error handling)
- [ ] Loading states for all async operations
- [ ] Confirmation dialogs for destructive actions
- [ ] Tooltips and inline help

---

## File Structure

```
TeleMediaBot/
├─ telemedia/
│  ├─ api.py                    # Main FastAPI app with all routes
│  ├─ telegram_collector.py     # Telethon wrapper (existing + new methods)
│  ├─ web_scraper.py            # Existing scraper
│  ├─ analysis.py               # Existing analytics
│  ├─ auth.py                   # NEW: Authentication logic
│  ├─ websocket.py              # NEW: WebSocket handlers
│  ├─ static/
│  │  ├─ css/
│  │  │  ├─ app.css             # Main stylesheet
│  │  │  ├─ components.css      # Reusable components
│  │  │  └─ themes.css          # Light/dark themes
│  │  ├─ js/
│  │  │  ├─ navigation.js       # Client-side routing
│  │  │  ├─ components.js       # UI components
│  │  │  ├─ websocket.js        # Real-time updates
│  │  │  └─ utils.js            # Helper functions
│  │  └─ icons/                 # SVG icons
│  └─ templates/
│     ├─ base.html              # Master layout
│     ├─ dashboard.html         # Existing dashboard (wrapped in base)
│     ├─ messages.html          # Message search page
│     ├─ media.html             # Media browser
│     ├─ groups.html            # Group manager
│     ├─ channels.html          # Channel manager
│     ├─ bot_tools.html         # Bot features
│     ├─ admin.html             # Admin panel
│     ├─ analytics.html         # Analytics dashboard
│     └─ login.html             # Login page
├─ docs/
│  ├─ TELETHON_GUIDE.md         # Existing guide
│  ├─ TELEMEDIA_UI_PLAN.md      # This file
│  └─ USER_MANUAL.md            # NEW: User guide
├─ tests/
│  ├─ test_api.py               # Existing tests
│  ├─ test_groups.py            # NEW: Group management tests
│  ├─ test_channels.py          # NEW: Channel tests
│  └─ test_websocket.py         # NEW: Real-time tests
└─ README.md                    # Updated with new features
```

---

## Development Priorities

### Week 1: Foundation
1. Create base layout and navigation
2. Wrap existing dashboard in new layout
3. Build reusable components library
4. Update existing routes to use new layout

### Week 2: Core Pages
1. Messages page (most requested)
2. Media browser (high value)
3. Group manager (essential admin feature)

### Week 3: Publishing Features
1. Channel manager (content creation)
2. Bot tools (automation)

### Week 4: Advanced
1. Admin panel (moderation)
2. Analytics (insights)

### Week 5: Polish
1. Real-time features (WebSocket)
2. Authentication (multi-user)
3. UI refinements (dark mode, mobile)

### Week 6: Launch
1. Testing & bug fixes
2. Documentation
3. Deployment guide

---

## Success Metrics

- **Usability**: All Telethon features accessible via UI (no code required)
- **Performance**: Pages load <1s, real-time updates <100ms latency
- **Reliability**: Graceful error handling, offline mode support
- **Accessibility**: WCAG 2.1 AA compliance
- **Documentation**: Complete user manual + inline help

---

## Next Steps

1. Review and approve this plan
2. Start with Phase 1.1 (base layout)
3. Iterate on each page (build → test → refine)
4. Get user feedback at end of each phase
5. Adjust priorities based on feedback

Ready to start building?
