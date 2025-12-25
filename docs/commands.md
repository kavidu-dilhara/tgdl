# Basic Commands

Learn all the essential commands for using tgdl effectively.

## Command Overview

tgdl has these main commands:

| Command | Purpose |
|---------|---------|
| `login` | Authenticate with Telegram |
| `logout` | Remove session and logout |
| `channels` | List your channels |
| `groups` | List your groups |
| `bots` | List your bot chats |
| `download` | Download media from entities |
| `download-link` | Download from message link |
| `status` | Check authentication status |

---

## Authentication Commands

### login

**Purpose:** Authenticate tgdl with your Telegram account.

```bash
tgdl login
```

**When to use:**
- First time setup
- After logout
- Session expired

**What you need:**
- API ID and Hash from [my.telegram.org/apps](https://my.telegram.org/apps)
- Your phone number
- Access to Telegram app (for verification code)

### logout

**Purpose:** Remove session and credentials.

```bash
tgdl logout
```

**When to use:**
- Switching accounts
- Securing your system
- Troubleshooting authentication issues

!!! warning "Safe Operation"
    Logout does NOT delete your downloaded files!

### status

**Purpose:** Check if you're logged in and see configuration.

```bash
tgdl status
```

**Shows:**
- Authentication status
- User information
- File locations
- API credentials (masked)

---

## Discovery Commands

### channels

**Purpose:** List all channels you're a member of.

```bash
tgdl channels
```

**Output includes:**
- Channel ID (for downloads)
- Channel title
- Username (if public)

**Example output:**
```
📢 Found 5 channels:

ID              Title                          Username            
====================================================================
1234567890      Tech News                      @technews           
9876543210      Daily Photos                   N/A                 
```

**Tips:**
- Copy the ID for use with download command
- N/A means private channel
- Public channels show their @username

### groups

**Purpose:** List all groups you're a member of.

```bash
tgdl groups
```

**Similar to channels command** but shows groups instead.

### bots

**Purpose:** List all bot chats.

```bash
tgdl bots
```

**Shows:**
- Bot ID
- Bot name
- Bot username

---

## Download Commands

### download

**Purpose:** Download media from channels, groups, or bot chats.

#### Basic Usage

```bash
# From channel
tgdl download -c 1234567890

# From group
tgdl download -g 1234567890

# From bot
tgdl download -b 1234567890
```

#### With Media Type Filters

```bash
# Only photos
tgdl download -c 1234567890 -p

# Only videos
tgdl download -c 1234567890 -v

# Photos and videos
tgdl download -c 1234567890 -p -v

# Everything except photos
tgdl download -c 1234567890 -v -a -d
```

**Media type options:**
- `-p` or `--photos` - Photos/images
- `-v` or `--videos` - Video files
- `-a` or `--audio` - Audio files
- `-d` or `--documents` - Documents/files

#### With Size Limits

```bash
# Max 100MB
tgdl download -c 1234567890 --max-size 100MB

# Min 1MB (skip small files)
tgdl download -c 1234567890 --min-size 1MB

# Between 1MB and 100MB
tgdl download -c 1234567890 --min-size 1MB --max-size 100MB
```

**Size units:** B, KB, MB, GB, TB

#### With Download Limits

```bash
# First 50 files only
tgdl download -c 1234567890 --limit 50

# Faster (10 parallel downloads)
tgdl download -c 1234567890 --concurrent 10
```

**Concurrent downloads:**
- Default: 5
- Range: 1-50
- Higher = faster (but more bandwidth)

#### Custom Output Directory

```bash
tgdl download -c 1234567890 -o /path/to/folder
```

#### Combined Example

```bash
# Download videos under 100MB, max 20 files, fast mode
tgdl download -c 1234567890 -v --max-size 100MB --limit 20 --concurrent 10
```

### download-link

**Purpose:** Download media from a single message link.

```bash
tgdl download-link https://t.me/channel/123
```

**Supported links:**
- Public channels: `https://t.me/username/123`
- Private channels: `https://t.me/c/1234567890/123`

**With filters:**
```bash
# Only if it's a video
tgdl download-link https://t.me/channel/123 -v

# With size limit
tgdl download-link https://t.me/channel/123 --max-size 50MB
```

---

## Understanding Download Behavior

### Automatic Skip

**Already downloaded files are automatically skipped:**

```
Found 25 already downloaded files, will skip...
Fetching messages from entity 1234567890...
Found 10 new media files to download
```

How it works:
1. tgdl extracts message IDs from existing filenames
2. Compares with messages to download
3. Skips any that match

### Progress Tracking

**tgdl remembers what it downloaded:**

First run:
```bash
tgdl download -c 1234567890
# Downloads messages 1-100
```

Second run (later):
```bash
tgdl download -c 1234567890
# Only downloads messages 101+ (new content)
```

**Stored in:** `~/.tgdl/progress.json`

### Resume Support

**Interrupted downloads can be resumed:**

1. Download starts
2. Press Ctrl+C or connection lost
3. Run same command again
4. Already downloaded files are skipped
5. Download continues

### File Naming

**Files are named with message ID:**

```
downloads/entity_1234567890/
├── 12345.jpg        # Message ID 12345
├── 12346.mp4        # Message ID 12346
└── 12347.pdf        # Message ID 12347
```

**Benefits:**
- Unique filenames
- Reliable duplicate detection
- Easy to track what's downloaded

---

## Common Use Cases

### Backup a Channel

```bash
# Download everything
tgdl download -c 1234567890
```

### Download Recent Videos

```bash
# Last 50 videos
tgdl download -c 1234567890 -v --limit 50
```

### Download Large Files Only

```bash
# Files over 10MB
tgdl download -c 1234567890 --min-size 10MB
```

### Quick Preview Download

```bash
# First 10 files to see what's there
tgdl download -c 1234567890 --limit 10
```

### Update Collection

```bash
# Run periodically to get new content
tgdl download -c 1234567890
# Only downloads new messages since last run
```

### Download Specific Range

```bash
# Messages 20-100
tgdl download -c 1234567890 --min-id 20 --max-id 100
```

---

## Keyboard Controls

### During Download

- **Ctrl+C** - Cancel download (gracefully)
  - Current file completes
  - Progress is saved
  - Can resume later

- **No other controls** - Download runs automatically

### Cancel vs Error

**Cancelled:**
```
^C
⚠ Download cancelled by user.
💡 You can resume by running the same command again.
```

**Error:**
```
✗ Download failed: Connection timeout

⚠ No files downloaded.
```

---

## Tips & Best Practices

### 1. Start Small

!!! tip "For First Time"
    ```bash
    # Try with limit first
    tgdl download -c 1234567890 --limit 5
    ```
    
    Helps you:
    - See file organization
    - Check download speed
    - Verify filters work

### 2. Use Filters Wisely

!!! tip "Save Storage"
    ```bash
    # Instead of downloading everything
    tgdl download -c 1234567890 --max-size 100MB -v
    ```
    
    Benefits:
    - Saves disk space
    - Faster downloads
    - Only get what you need

### 3. Check Storage First

!!! warning "Disk Space"
    Large channels can have gigabytes of content. Check available space:
    
    ```bash
    # Linux/macOS
    df -h
    
    # Windows
    dir
    ```

### 4. Optimize Speed

!!! tip "Faster Downloads"
    ```bash
    # Default (safe for most connections)
    tgdl download -c 1234567890
    
    # Faster (good connection)
    tgdl download -c 1234567890 --concurrent 10
    
    # Maximum speed (excellent connection)
    tgdl download -c 1234567890 --concurrent 20
    ```

### 5. Regular Updates

!!! tip "Keep Collections Current"
    ```bash
    # Run same command periodically
    tgdl download -c 1234567890
    ```
    
    Only downloads new content each time.

### 6. Use Custom Directories

!!! tip "Organization"
    ```bash
    # Separate by purpose
    tgdl download -c 1234567890 -v -o ~/Videos/TechChannel
    tgdl download -c 9876543210 -p -o ~/Photos/DailyPics
    ```

---

## Common Mistakes

### ❌ Wrong: Forgetting Entity Flag

```bash
tgdl download 1234567890
```

**Error:** Missing -c, -g, or -b

### ✅ Correct

```bash
tgdl download -c 1234567890
```

### ❌ Wrong: Multiple Entity Types

```bash
tgdl download -c 1234567890 -g 9876543210
```

**Error:** Can't download from multiple entities at once

### ✅ Correct

```bash
# Run separately
tgdl download -c 1234567890
tgdl download -g 9876543210
```

### ❌ Wrong: Invalid Size Format

```bash
tgdl download -c 1234567890 --max-size 100M
```

**Error:** Should be 100MB (not 100M)

### ✅ Correct

```bash
tgdl download -c 1234567890 --max-size 100MB
```

---

## Quick Reference

### Most Used Commands

```bash
# Login
tgdl login

# List what's available
tgdl channels

# Download all from channel
tgdl download -c ID

# Download videos only
tgdl download -c ID -v

# Download with size limit
tgdl download -c ID --max-size 100MB

# Fast download
tgdl download -c ID --concurrent 10

# Check status
tgdl status
```

### Command Template

```bash
tgdl download \
  -c|g|b ID \
  [-p] [-v] [-a] [-d] \
  [--max-size SIZE] [--min-size SIZE] \
  [--min-id ID] [--max-id ID] \
  [--limit N] [--concurrent N] \
  [-o DIR]
```

---

## Next Steps

- [Learn advanced usage](advanced-usage.md)
- [Explore media filters](media-filters.md)
- [Use message ID ranges](message-ranges.md)
- [See full command reference](command-reference.md)
