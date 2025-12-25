# Command Reference

Complete reference for all tgdl commands.

## Global Options

These options work with all commands:

| Option | Description |
|--------|-------------|
| `--version` | Show version number and exit |
| `--help` | Show help message and exit |

```bash
tgdl --version  # Show version
tgdl --help     # Show all commands
tgdl download --help  # Show help for download command
```

---

## login

Authenticate with Telegram and save session.

### Syntax

```bash
tgdl login
```

### Interactive Prompts

1. **API ID** - Your Telegram API identifier
2. **API Hash** - Your Telegram API hash  
3. **Phone number** - With country code (+1234567890)
4. **Verification code** - 5-digit code from Telegram
5. **2FA password** (if enabled) - Your cloud password

### Example

```bash
$ tgdl login

🔐 Telegram Login
Get your API credentials from: https://my.telegram.org/apps

Telegram API ID: 12345678
Telegram API Hash: 0123456789abcdef0123456789abcdef
Phone number (with country code): +1234567890

Sending verification code to +1234567890...
Enter the verification code you received: 12345

✓ Successfully logged in as John Doe (ID: 123456789)
```

### Notes

- Get API credentials from [my.telegram.org/apps](https://my.telegram.org/apps)
- Session is saved for future use
- You only need to login once
- Credentials are encrypted before storage

---

## logout

Remove session and logout from Telegram.

### Syntax

```bash
tgdl logout
```

### Interactive Prompts

1. Confirmation to logout
2. Option to clear progress tracking

### Example

```bash
$ tgdl logout

🔓 Logout from Telegram

Currently logged in as: John Doe (ID: 123456789)

Are you sure you want to logout? [y/N]: y

⚠️  Note: Downloaded files will NOT be deleted.
Do you want to clear download progress tracking? [y/N]: n

✓ Successfully logged out!
```

### What Gets Deleted

- ✅ Session file
- ✅ Encrypted credentials
- ✅ Progress tracking (optional)
- ❌ Downloaded files (NOT deleted)

---

## channels

List all channels you're a member of.

### Syntax

```bash
tgdl channels
```

### Output

```
📢 Fetching your channels...

📢 Found 3 channels:

ID              Title                                    Username            
===============================================================================
1234567890      Tech News Daily                          @technews           
9876543210      Photography World                        N/A                 
5555555555      Movies & TV                              @moviesandtv        

💡 Tip: Use 'tgdl download -c <ID>' to download from a channel
```

### Output Fields

- **ID** - Channel identifier (use for downloads)
- **Title** - Channel name
- **Username** - Channel username (N/A if private)

---

## groups

List all groups you're a member of.

### Syntax

```bash
tgdl groups
```

### Output

```
👥 Fetching your groups...

👥 Found 2 groups:

ID              Title                                    Username            
===============================================================================
1111111111      Family Chat                              N/A                 
2222222222      Work Team                                @workteam           

💡 Tip: Use 'tgdl download -g <ID>' to download from a group
```

---

## bots

List all bot chats you have.

### Syntax

```bash
tgdl bots
```

### Output

```
🤖 Fetching your bot chats...

🤖 Found 2 bot chats:

ID              Bot Name                                  Username            
===============================================================================
3333333333      File Converter Bot                        @fileconverter      
4444444444      Media Bot                                 @mediabot           

💡 Tip: Use 'tgdl download -b <ID>' to download from a bot chat
```

---

## download

Download media from channels, groups, or bot chats.

### Syntax

```bash
tgdl download [OPTIONS]
```

### Required Options (Choose One)

| Option | Description | Example |
|--------|-------------|---------|
| `-c, --channel ID` | Download from channel | `-c 1234567890` |
| `-g, --group ID` | Download from group | `-g 1234567890` |
| `-b, --bot ID` | Download from bot chat | `-b 1234567890` |

!!! warning "Important"
    You must specify exactly ONE of: `-c`, `-g`, or `-b`

### Media Type Filters

| Option | Description |
|--------|-------------|
| `-p, --photos` | Download only photos |
| `-v, --videos` | Download only videos |
| `-a, --audio` | Download only audio files |
| `-d, --documents` | Download only documents |

**Notes:**
- Can combine multiple types
- If none specified, downloads ALL media types

### Size Filters

| Option | Description | Example |
|--------|-------------|---------|
| `--max-size SIZE` | Maximum file size | `--max-size 100MB` |
| `--min-size SIZE` | Minimum file size | `--min-size 1MB` |

**Supported units:** B, KB, MB, GB, TB

### Message ID Range

| Option | Description | Example |
|--------|-------------|---------|
| `--min-id ID` | Start from message ID (inclusive) | `--min-id 20` |
| `--max-id ID` | Stop at message ID (inclusive) | `--max-id 100` |

### Download Control

| Option | Default | Description |
|--------|---------|-------------|
| `--limit N` | None | Maximum files to download |
| `--concurrent N` | 5 | Parallel download connections (1-50) |
| `-o, --output DIR` | `downloads` | Output directory |

### Examples

#### Basic Downloads

```bash
# Download all media from channel
tgdl download -c 1234567890

# Download from group
tgdl download -g 1234567890

# Download from bot
tgdl download -b 1234567890
```

#### With Media Filters

```bash
# Only videos
tgdl download -c 1234567890 -v

# Photos and videos
tgdl download -c 1234567890 -p -v

# Only documents
tgdl download -c 1234567890 -d

# All except photos
tgdl download -c 1234567890 -v -a -d
```

#### With Size Filters

```bash
# Maximum 100MB
tgdl download -c 1234567890 --max-size 100MB

# Minimum 1MB (skip small files)
tgdl download -c 1234567890 --min-size 1MB

# Between 1MB and 500MB
tgdl download -c 1234567890 --min-size 1MB --max-size 500MB

# Videos under 50MB
tgdl download -c 1234567890 -v --max-size 50MB
```

#### With Message ID Range

```bash
# Messages 20 to 100
tgdl download -c 1234567890 --min-id 20 --max-id 100

# From message 50 onwards
tgdl download -c 1234567890 --min-id 50

# Up to message 200
tgdl download -c 1234567890 --max-id 200

# Specific range with filters
tgdl download -c 1234567890 --min-id 20 --max-id 100 -v
```

#### With Download Control

```bash
# First 50 files only
tgdl download -c 1234567890 --limit 50

# Fast download (10 parallel)
tgdl download -c 1234567890 --concurrent 10

# Super fast (20 parallel)
tgdl download -c 1234567890 --concurrent 20

# Custom output directory
tgdl download -c 1234567890 -o /path/to/folder

# Combined example
tgdl download -c 1234567890 -v --max-size 100MB --limit 10 --concurrent 10
```

### Download Output

```
📥 Download Settings
  Entity: Channel 1234567890
  Media types: videos
  Max size: 100MB (104857600)
  Limit: 50 files
  Parallel downloads: 10
  Output: downloads

💡 Tip: Files already downloaded will be skipped automatically
⚠️  Press Ctrl+C to cancel at any time

Continue with download? [Y/n]: y

Found 25 already downloaded files, will skip...
Fetching messages from entity 1234567890...
Found 45 new media files to download

Downloading: 100%|████████████████████| 45/45 [00:32<00:00,  1.39file/s]

✓ Successfully downloaded 45 files!
Files saved to: /home/user/downloads/entity_1234567890
```

---

## download-link

Download media from a single message link.

### Syntax

```bash
tgdl download-link [OPTIONS] LINK
```

### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `LINK` | Telegram message URL | Yes |

### Supported Link Formats

```
https://t.me/channel_username/123      # Public channel
https://t.me/c/1234567890/123          # Private channel
```

### Options

Same filter options as `download` command:

- `-p, --photos` - Accept only photos
- `-v, --videos` - Accept only videos
- `-a, --audio` - Accept only audio
- `-d, --documents` - Accept only documents
- `--max-size SIZE` - Maximum file size
- `--min-size SIZE` - Minimum file size
- `-o, --output DIR` - Output directory (default: `downloads`)

### Examples

```bash
# Download from public channel message
tgdl download-link https://t.me/channel/123

# Download from private channel message
tgdl download-link https://t.me/c/1234567890/123

# Only if it's a video
tgdl download-link https://t.me/channel/123 -v

# With size limit
tgdl download-link https://t.me/channel/123 --max-size 100MB

# Custom output directory
tgdl download-link https://t.me/channel/123 -o /my/folder
```

### Output

```
📥 Downloading from link
Link: https://t.me/channel/123

File: video.mp4
Size: 45.2 MB

  [██████████████████████████████] 100.0% | 45.2 MB/45.2 MB

✓ Successfully downloaded to: downloads/single_downloads/video.mp4
```

---

## status

Check authentication status and configuration.

### Syntax

```bash
tgdl status
```

### Output (Logged In)

```
📊 tgdl Status

✓ Authenticated
  Name: John Doe
  User ID: 123456789
  Username: @johndoe

Config directory: /home/user/.tgdl
Session file: /home/user/.tgdl/tgdl.session
Progress file: /home/user/.tgdl/progress.json

API ID: 12345678
API Hash: ********abcd
```

### Output (Not Logged In)

```
📊 tgdl Status

✗ Not authenticated
  Run 'tgdl login' to authenticate

Config directory: /home/user/.tgdl
Session file: /home/user/.tgdl/tgdl.session
Progress file: /home/user/.tgdl/progress.json

API credentials: Not configured
```

---

## Command Aliases

Some commands have shorter aliases:

| Full Command | Alias | Notes |
|--------------|-------|-------|
| `tgdl download -c` | N/A | Use full form |
| `tgdl download -g` | N/A | Use full form |
| `tgdl download -b` | N/A | Use full form |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |

---

## Environment Variables

Currently, tgdl does not use environment variables for configuration.

All settings are stored in `~/.tgdl/` directory.

---

## Next Steps

- [Learn about advanced usage](advanced-usage.md)
- [Explore media filters in detail](media-filters.md)
- [Understand message ID ranges](message-ranges.md)
- [Read troubleshooting guide](troubleshooting.md)
