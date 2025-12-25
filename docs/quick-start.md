# Quick Start Guide

Get up and running with tgdl in just 5 minutes!

## Prerequisites

Before you begin, ensure you have:

- ✅ [Installed tgdl](installation.md)
- ✅ [Obtained API credentials](api-credentials.md)
- ✅ Your Telegram phone number

## Step 1: Login to Telegram

Run the login command:

```bash
tgdl login
```

You'll be prompted for:

1. **API ID** - Your numeric API identifier
2. **API Hash** - Your secret API hash
3. **Phone number** - With country code (e.g., +1234567890)
4. **Verification code** - Sent to your Telegram app
5. **2FA password** - If you have two-factor authentication enabled

### Example Login Session

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

✓ Session saved successfully!
You can now use other tgdl commands.
```

!!! tip "Two-Factor Authentication"
    If you have 2FA enabled, you'll be prompted for your password after entering the verification code.

## Step 2: List Your Channels/Groups

Check what's available to download:

### List Channels

```bash
tgdl channels
```

**Output:**
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

### List Groups

```bash
tgdl groups
```

### List Bot Chats

```bash
tgdl bots
```

## Step 3: Download Media

Now you're ready to download!

### Basic Download (All Media)

Download everything from a channel:

```bash
tgdl download -c 1234567890
```

### Download with Confirmation

```
📥 Download Settings
  Entity: Channel 1234567890
  Media types: all
  Parallel downloads: 5
  Output: downloads

💡 Tip: Files already downloaded will be skipped automatically
⚠️  Press Ctrl+C to cancel at any time

Continue with download? [Y/n]: y
Fetching messages from entity 1234567890...
Found 125 media files to download

Downloading: 100%|████████████████████| 125/125 [02:15<00:00,  1.08s/file]

✓ Successfully downloaded 125 files!
Files saved to: F:\Downloads\entity_1234567890
```

## Common Use Cases

### Download Only Videos

```bash
tgdl download -c 1234567890 -v
```

### Download Photos and Videos

```bash
tgdl download -c 1234567890 -p -v
```

### Download with Size Limit

```bash
tgdl download -c 1234567890 --max-size 100MB
```

### Download First 50 Files

```bash
tgdl download -c 1234567890 --limit 50
```

### Fast Download (10 parallel)

```bash
tgdl download -c 1234567890 --concurrent 10
```

## Understanding the Output

### Download Progress

```
Fetching messages from entity 1234567890...
Found 125 media files to download

Downloading: 45%|█████████░░░░░░░░░░░| 56/125 [01:02<01:13,  1.11s/file]
```

- **Progress bar** - Visual download progress
- **Current/Total** - Files downloaded so far
- **Time elapsed** - How long it's been running
- **Time remaining** - Estimated time to completion
- **Speed** - Files per second

### Success Message

```
✓ Successfully downloaded 125 files!
Files saved to: F:\Downloads\entity_1234567890
```

Your files are saved in the `downloads/entity_<ID>` folder.

## File Organization

Downloaded files are organized like this:

```
downloads/
├── entity_1234567890/          # Channel 1
│   ├── 12345.jpg
│   ├── 12346.mp4
│   └── 12347.pdf
├── entity_9876543210/          # Channel 2
│   ├── 98765.jpg
│   └── 98766.png
└── single_downloads/           # Individual link downloads
    └── file_123.mp4
```

!!! info "File Naming"
    Files are named with their message ID for reliable tracking and duplicate prevention.

## Smart Features

### Automatic Skip

Already downloaded files are automatically skipped:

```
Found 25 already downloaded files, will skip...
Fetching messages from entity 1234567890...
Found 10 new media files to download
```

### Resume Support

If interrupted, just run the command again:

```bash
# Download starts again
tgdl download -c 1234567890
```

tgdl will:
- ✅ Skip already downloaded files
- ✅ Continue from where it stopped
- ✅ Only download new media

### Progress Tracking

tgdl remembers what it downloaded:

- Each entity's progress is tracked separately
- Next time you run download, only NEW messages are fetched
- Efficient for keeping media collections up-to-date

## Quick Reference Card

| Task | Command |
|------|---------|
| Login | `tgdl login` |
| Logout | `tgdl logout` |
| List channels | `tgdl channels` |
| List groups | `tgdl groups` |
| List bots | `tgdl bots` |
| Download all | `tgdl download -c ID` |
| Download videos | `tgdl download -c ID -v` |
| Download photos | `tgdl download -c ID -p` |
| With size limit | `tgdl download -c ID --max-size 100MB` |
| Fast download | `tgdl download -c ID --concurrent 10` |
| Check status | `tgdl status` |

## Keyboard Shortcuts

While downloading:

- **Ctrl+C** - Cancel download (can resume later)
- Progress is automatically saved

## Tips for Beginners

!!! tip "Start Small"
    For your first download, use `--limit 10` to download just 10 files and see how it works.

!!! tip "Check Storage"
    Large channels can have gigabytes of media. Check available disk space first.

!!! tip "Use Filters"
    Instead of downloading everything, use filters like `-v` (videos only) or `--max-size` to save space.

!!! tip "Increase Speed"
    Default is 5 parallel downloads. For faster downloads, try `--concurrent 10` or even `--concurrent 20`.

## Next Steps

Now that you know the basics:

1. [Learn all commands](commands.md)
2. [Explore advanced usage](advanced-usage.md)
3. [Use media filters](media-filters.md)
4. [Download message ranges](message-ranges.md)

---

!!! success "You're All Set!"
    You now know enough to start downloading media from Telegram. Explore the advanced features when you're ready!
