# Frequently Asked Questions

Common questions and answers about tgdl.

## General Questions

### What is tgdl?

tgdl is a command-line tool for downloading media files (photos, videos, audio, documents) from Telegram channels, groups, and bot chats.

### Is tgdl free?

Yes, tgdl is completely free and open-source under the MIT license.

### Is it safe to use?

Yes. tgdl:
- Uses official Telegram API
- Stores credentials encrypted locally
- Never sends your data anywhere except Telegram
- Open source (you can audit the code)

### Do I need Telegram Premium?

No. tgdl works with free Telegram accounts.

---

## Installation Questions

### Which Python version do I need?

Python 3.7 or higher.

Check your version:
```bash
python --version
```

### Can I use tgdl on Windows?

Yes! tgdl works on:
- Windows 10/11
- Linux (all distributions)
- macOS

### Do I need to install Telegram Desktop?

No. tgdl is independent of Telegram Desktop. However, you need:
- A Telegram account (with phone number)
- Access to Telegram (app or web) to receive verification codes

### How do I update tgdl?

```bash
pip install --upgrade tgdl
```

---

## API Credentials Questions

### Why do I need API credentials?

Telegram requires all API applications to have unique API ID and Hash. This identifies your application to Telegram's servers.

### Where do I get API credentials?

1. Go to https://my.telegram.org/apps
2. Login with your phone number
3. Create an app (if you haven't)
4. Copy API ID and Hash

[Detailed guide](api-credentials.md)

### Can I share my API credentials?

**No!** Your API credentials are:
- Personal to you
- Should never be shared
- Used to identify your API usage

Sharing them could:
- Allow others to make API calls as you
- Risk account suspension if misused

### What if I lose my API credentials?

You can always retrieve them:
1. Go to https://my.telegram.org/apps
2. Login
3. View your existing app
4. Copy credentials again

### Can I use someone else's API credentials?

**No.** This violates Telegram's Terms of Service and could result in:
- Account suspension
- API ban
- Security risks

Always use your own credentials.

---

## Authentication Questions

### How does authentication work?

1. **First time:**
   - Enter API credentials
   - Enter phone number
   - Receive verification code in Telegram
   - Enter code
   - Session created

2. **After first time:**
   - Session file is saved (`~/.tgdl/tgdl.session`)
   - No login needed until session expires

### How long does a session last?

Telegram sessions typically last indefinitely unless:
- You explicitly logout
- Telegram revokes session (rare)
- You remove session files

### Can I use multiple accounts?

Not directly with current version. Workaround:

```bash
# Save session for account 1
cp ~/.tgdl/tgdl.session ~/.tgdl/account1.session

# Login to account 2
tgdl logout
tgdl login

# Switch back to account 1
cp ~/.tgdl/account1.session ~/.tgdl/tgdl.session
```

### Is my session secure?

Yes:
- Telegram uses encryption
- Session file is stored locally
- Only you can access it (file permissions)
- Encrypted credentials storage

**Security tips:**
- Don't share session files
- Keep `~/.tgdl/` directory private
- Use `tgdl logout` on shared computers

### What happens if I logout?

When you run `tgdl logout`:
- Session file is deleted
- API credentials are removed
- Progress tracking is kept
- Downloaded files are NOT deleted

---

## Download Questions

### Where are files downloaded?

**Default location:**
```
downloads/entity_{ID}/
```

**Example:**
```
downloads/entity_1234567890/
├── 12345.jpg
├── 12346.mp4
└── 12347.pdf
```

**Custom location:**
```bash
tgdl download -c 1234567890 -o /path/to/folder
```

### How are files named?

Files are named: `{message_id}.{extension}`

**Examples:**
- `12345.jpg` - Photo from message 12345
- `12346.mp4` - Video from message 12346
- `12347.pdf` - Document from message 12347

**Why message ID?**
- Unique identifier
- Prevents duplicates
- Easy to track

### Can I download from private channels?

**Yes**, but you must be a member of the private channel.

**Steps:**
1. Join channel in Telegram app
2. Run `tgdl channels` to verify it's listed
3. Download: `tgdl download -c {ID}`

### Can I download from public channels I'm not a member of?

**No.** You must join the channel first, even if it's public.

### How do I download from a group?

```bash
# List groups
tgdl groups

# Download from group
tgdl download -g {GROUP_ID}
```

Use `-g` flag (not `-c`) for groups.

### Can I download specific messages?

**Yes**, using message ID ranges:

```bash
# Messages 20-100
tgdl download -c 1234567890 --min-id 20 --max-id 100

# Single message
tgdl download -c 1234567890 --min-id 50 --max-id 50

# Or use direct link
tgdl download-link https://t.me/channel/50
```

### Does tgdl skip already downloaded files?

**Yes!** tgdl automatically:
1. Checks existing files in download directory
2. Extracts message IDs from filenames
3. Skips messages that are already downloaded
4. Only downloads new files

### Can I resume interrupted downloads?

**Yes.** Just run the same command again:
```bash
tgdl download -c 1234567890
```

tgdl will:
- Skip files completely downloaded
- Continue from where it stopped

### How does progress tracking work?

tgdl remembers the last downloaded message ID for each entity in:
```
~/.tgdl/progress.json
```

**Example:**
```json
{
  "1234567890": 12345
}
```

This means: "For channel 1234567890, we've downloaded up to message 12345."

Next download will start from message 12346.

### Can I reset progress?

**Yes:**

```bash
# Reset all progress
echo "{}" > ~/.tgdl/progress.json

# Or delete the file
rm ~/.tgdl/progress.json
```

Next download will start from the beginning.

### Why are some files not downloading?

Possible reasons:

1. **Not media files:**
   - Text-only messages don't download

2. **Filters:**
   - Check your size/type filters
   - Try without filters: `tgdl download -c ID --limit 5`

3. **Already downloaded:**
   - Check for "skipping" message in output

4. **Private channel:**
   - You must be a member

5. **File was deleted:**
   - Original message may have been deleted

### Can I download all messages at once?

tgdl downloads in batches for efficiency:

```bash
# Default: Downloads all available
tgdl download -c 1234567890

# With limit
tgdl download -c 1234567890 --limit 1000
```

### How fast is download speed?

Speed depends on:
- Your internet connection
- Telegram server load
- File sizes
- Concurrent downloads setting

**Optimize speed:**
```bash
# Faster (more parallel downloads)
tgdl download -c 1234567890 --concurrent 10
```

---

## Filtering Questions

### What media types can I filter?

- `-p` or `--photos` - Photos/images
- `-v` or `--videos` - Video files
- `-a` or `--audio` - Audio/music
- `-d` or `--documents` - Documents/files

### Can I download only photos?

```bash
tgdl download -c 1234567890 -p
```

### Can I download multiple types?

**Yes:**
```bash
# Photos and videos
tgdl download -c 1234567890 -p -v

# Everything except videos
tgdl download -c 1234567890 -p -a -d
```

### Can I filter by file size?

**Yes:**
```bash
# Maximum size
tgdl download -c 1234567890 --max-size 100MB

# Minimum size
tgdl download -c 1234567890 --min-size 10MB

# Range
tgdl download -c 1234567890 --min-size 10MB --max-size 100MB
```

### What size units are supported?

- `B` - Bytes
- `KB` - Kilobytes
- `MB` - Megabytes
- `GB` - Gigabytes
- `TB` - Terabytes

**Case sensitive:** Use `MB` not `mb`

### Can I limit the number of downloads?

**Yes:**
```bash
# Download only first 50 files
tgdl download -c 1234567890 --limit 50
```

---

## Performance Questions

### How many files can tgdl download at once?

**Default:** 5 concurrent downloads  
**Maximum:** 50 concurrent downloads

```bash
# Adjust with --concurrent flag
tgdl download -c 1234567890 --concurrent 10
```

### Should I increase concurrent downloads?

Depends on your connection:
- Slow (< 10 Mbps): Use 1-3
- Medium (10-50 Mbps): Use 5-10
- Fast (> 50 Mbps): Use 10-20

**Higher isn't always better:**
- Can trigger rate limits
- May overwhelm connection
- Can cause timeouts

### Why am I getting FloodWaitError?

**Cause:** Too many requests to Telegram servers

**Solutions:**
- Reduce `--concurrent` value
- Add delays between downloads
- Wait the specified time before retrying

### Can I run multiple tgdl instances?

**Not recommended.** This can:
- Trigger rate limits
- Cause FloodWaitError
- Download duplicates

Run one instance at a time.

---

## Storage Questions

### How much storage do I need?

Depends on:
- Number of messages in channel
- File sizes
- Media types

**Check channel size:**
```bash
# Test with limit
tgdl download -c 1234567890 --limit 10

# Check downloaded size
du -sh downloads/entity_1234567890/
```

**Use filters to control:**
```bash
# Limit size
tgdl download -c 1234567890 --max-size 50MB --limit 100
```

### Where does tgdl store config files?

**Linux/macOS:** `~/.tgdl/`
**Windows:** `%USERPROFILE%\.tgdl\`

**Files:**
- `config.json` - Encrypted API credentials
- `.key` - Encryption key
- `tgdl.session` - Telegram session
- `progress.json` - Download progress

### Can I change the download location?

**Yes:**
```bash
tgdl download -c 1234567890 -o /custom/path
```

**Default:** `downloads/entity_{ID}/` in current directory

### Can I delete config files safely?

**Delete these ONLY if you know what you're doing:**

**Safe to delete (will need to login again):**
- `config.json`
- `.key`
- `tgdl.session*`

**Safe to delete (will re-download from beginning):**
- `progress.json`

**DO NOT delete if you want to keep:**
- Downloaded files (in `downloads/`)

---

## Error Questions

### What does "Could not find the input entity" mean?

**Cause:** You're not a member of the channel/group

**Solution:**
1. Join channel in Telegram app
2. Verify: `tgdl channels`
3. Try download again

### What does "Session expired" mean?

**Cause:** Your session is no longer valid

**Solution:**
```bash
tgdl logout
tgdl login
```

### What does "API_ID_INVALID" mean?

**Cause:** Wrong API credentials

**Solution:**
1. Verify credentials at https://my.telegram.org/apps
2. Logout and login with correct credentials

### Why do I get "No files downloaded"?

Common reasons:

1. **No media in channel:**
   - Channel only has text messages

2. **Filters too restrictive:**
   - Try: `tgdl download -c ID --limit 5`

3. **All files already downloaded:**
   - Normal behavior if nothing new

4. **Wrong entity type:**
   - Use `-g` for groups, `-c` for channels

5. **Not a member:**
   - Join channel first

---

## Automation Questions

### Can I schedule automatic downloads?

**Yes!**

**Linux/macOS (cron):**
```bash
# Edit crontab
crontab -e

# Add daily download at 2 AM
0 2 * * * cd /path/to/dir && tgdl download -c 1234567890
```

**Windows (Task Scheduler):**
1. Create batch file with tgdl command
2. Schedule in Task Scheduler

[Learn more](advanced-usage.md#automation--scripting)

### Can I download from multiple channels automatically?

**Yes:**

Create script:
```bash
#!/bin/bash
tgdl download -c 1234567890
tgdl download -c 9876543210
tgdl download -g 1122334455
```

Schedule with cron or Task Scheduler.

---

## Comparison Questions

### tgdl vs Telegram Desktop export?

| Feature | tgdl | Telegram Desktop |
|---------|------|------------------|
| Command-line | ✅ | ❌ |
| Automation | ✅ | ❌ |
| Filtering | ✅ | Limited |
| Resume support | ✅ | ✅ |
| Progress tracking | ✅ | ❌ |
| Cross-platform | ✅ | ✅ |
| GUI | ❌ | ✅ |

### tgdl vs other downloaders?

**Advantages of tgdl:**
- Official Telegram API (safe)
- Automatic duplicate skip
- Progress tracking
- Flexible filtering
- Open source
- Cross-platform
- Resume support
- Message ID-based downloads

---

## Privacy & Security Questions

### Is tgdl tracking me?

**No.** tgdl:
- Does not collect any analytics
- Does not send data anywhere (except Telegram API)
- Does not phone home
- Is completely open source

### Can others see I'm using tgdl?

**No.** To Telegram, tgdl appears as a regular client. Others cannot tell you're using tgdl specifically.

### Does tgdl share my data?

**No.** All data stays local:
- API credentials (encrypted locally)
- Session file (local only)
- Downloaded files (local only)

### Should I use VPN with tgdl?

Optional, but consider if:
- Telegram is blocked in your region
- You want extra privacy
- You're downloading sensitive content

tgdl works fine without VPN in most regions.

---

## Troubleshooting Quick Answers

### tgdl command not found?

```bash
pip install --user tgdl
# Or
python -m tgdl
```

### Permission denied error?

```bash
# Install in user directory
pip install --user tgdl

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install tgdl
```

### Download is slow?

```bash
# Try adjusting concurrent downloads
tgdl download -c 1234567890 --concurrent 10
```

### Getting timeouts?

```bash
# Reduce concurrent downloads
tgdl download -c 1234567890 --concurrent 3
```

---

## Still Have Questions?

- [Check Troubleshooting Guide](troubleshooting.md)
- [Read Command Reference](command-reference.md)
- [View Advanced Usage](advanced-usage.md)
- [Report Issue on GitHub](https://github.com/kavidu-dilhara/tgdl/issues)

---

## Quick Tips

!!! tip "Getting Started"
    ```bash
    # 1. Login
    tgdl login
    
    # 2. List channels
    tgdl channels
    
    # 3. Download
    tgdl download -c ID
    ```

!!! tip "Test Before Bulk Download"
    ```bash
    # Try with small limit first
    tgdl download -c ID --limit 5
    ```

!!! tip "Optimize Speed"
    ```bash
    # Faster downloads on good connection
    tgdl download -c ID --concurrent 10
    ```

!!! tip "Save Storage"
    ```bash
    # Use size limits
    tgdl download -c ID --max-size 100MB
    ```

!!! tip "Automate"
    ```bash
    # Add to cron for daily updates
    0 2 * * * tgdl download -c ID
    ```
