# Troubleshooting

Solutions to common issues and error messages.

## Installation Issues

### pip install fails

**Symptom:**
```
ERROR: Could not find a version that satisfies the requirement tgdl
```

**Solutions:**

1. **Update pip:**
   ```bash
   # Linux/macOS
   python3 -m pip install --upgrade pip
   
   # Windows
   python -m pip install --upgrade pip
   ```

2. **Check Python version:**
   ```bash
   python --version  # Should be 3.7+
   ```

3. **Try with python3:**
   ```bash
   python3 -m pip install tgdl
   ```

### Import errors on Ubuntu/Debian

**Symptom:**
```
ImportError: cannot import name 'PBKDF2' from 'cryptography.hazmat.primitives.kdf.pbkdf2'
```

**Solution:**

Update cryptography:
```bash
pip install --upgrade cryptography
```

Or reinstall tgdl:
```bash
pip install --force-reinstall tgdl
```

### Permission denied

**Symptom:**
```
PermissionError: [Errno 13] Permission denied
```

**Solution:**

Install in user directory:
```bash
pip install --user tgdl
```

Or use virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install tgdl
```

---

## Authentication Issues

### Invalid phone number

**Symptom:**
```
✗ Error: PHONE_NUMBER_INVALID
```

**Solutions:**

1. **Include country code:**
   ```
   ✗ Wrong: 1234567890
   ✓ Correct: +11234567890
   ```

2. **No spaces or dashes:**
   ```
   ✗ Wrong: +1 123-456-7890
   ✓ Correct: +11234567890
   ```

3. **Verify number is registered:**
   - Check you can login to Telegram app with this number

### Verification code issues

**Symptom:**
```
✗ Error: PHONE_CODE_INVALID
```

**Solutions:**

1. **Check for typos:**
   - Code is usually 5 digits
   - No spaces

2. **Don't wait too long:**
   - Code expires after ~10 minutes
   - Request new code if expired

3. **Check Telegram app:**
   - Code appears in Telegram app (Telegram service message)
   - Not SMS (usually)

4. **Try SMS code:**
   - Wait for SMS if app code doesn't work
   - Check spam folder

### Two-factor authentication error

**Symptom:**
```
SessionPasswordNeededError
```

**Solution:**

1. **tgdl will prompt for 2FA password:**
   ```
   Enter 2FA password:
   ```

2. **If you forgot password:**
   - Reset via Telegram app
   - Settings → Privacy and Security → Two-Step Verification
   - Reset password (requires recovery email)

3. **If you don't have 2FA:**
   - This error shouldn't appear
   - May indicate account security issue

### Session expired

**Symptom:**
```
✗ Error: Session expired or invalid
```

**Solutions:**

1. **Logout and login again:**
   ```bash
   tgdl logout
   tgdl login
   ```

2. **Remove session manually:**
   ```bash
   # Linux/macOS
   rm ~/.tgdl/tgdl.session*
   
   # Windows
   del %USERPROFILE%\.tgdl\tgdl.session*
   ```
   
   Then login again:
   ```bash
   tgdl login
   ```

3. **Check API credentials:**
   ```bash
   tgdl status
   ```
   - Verify API ID and Hash are correct

### Could not find input entity

**Symptom:**
```
✗ Error: Could not find the input entity for PeerUser
```

**Solutions:**

1. **For channels/groups - verify you're a member:**
   ```bash
   # List your channels
   tgdl channels
   
   # Check if channel ID is listed
   ```

2. **Join the channel:**
   - Open Telegram app
   - Join the channel/group
   - Wait a few seconds
   - Try download again

3. **Use correct entity ID:**
   - From `tgdl channels` output
   - Not from web URL (use different format)

4. **For private channels:**
   ```bash
   # Use channel ID from tgdl channels
   tgdl download -c 1234567890
   
   # NOT from web URL
   ```

---

## Download Issues

### No files downloaded

**Symptom:**
```
⚠ No files downloaded.
```

**Possible Causes & Solutions:**

1. **Channel has no media:**
   ```bash
   # Check with limit
   tgdl download -c 1234567890 --limit 5
   ```
   - If still zero, channel may only have text

2. **Filters too restrictive:**
   ```bash
   # Try without filters
   tgdl download -c 1234567890 --limit 5
   
   # If this works, adjust filters
   ```

3. **All files already downloaded:**
   ```bash
   # Check output for:
   Found 50 already downloaded files, will skip...
   Found 0 new media files to download
   ```
   - This is normal (no new content)

4. **Wrong entity type:**
   ```bash
   # If it's a group, use -g not -c
   tgdl download -g 1234567890
   ```

5. **Message ID range issue:**
   ```bash
   # Try without range limits
   tgdl download -c 1234567890 --limit 5
   ```

### Download interrupted

**Symptom:**
```
^C
⚠ Download cancelled by user.
```

**What happens:**

tgdl saves progress automatically. When you run the command again:
- ✅ Skips already downloaded files
- ✅ Resumes partial downloads from where they stopped
- ✅ Only downloads new/missing files
- ✅ No re-downloading necessary

**Example:**

```bash
# Start download
$ tgdl download -c 1234567890
Downloading 100 files...
Downloaded 25 files...
^C
⚠ Download cancelled by user.

# Wait 1 hour...

# Run same command - tgdl remembers progress
$ tgdl download -c 1234567890
  Using 25 already downloaded files
  Resuming from file 26...
Downloading from file 26 of 100...
Downloaded 75 more files...
```

**Files saved:**
- `.tgdl_partial` files: Incomplete downloads (auto-detected and resumed)
- Completed files: Marked as complete and skipped

**Just run the same command again** - no need for special flags or recovery procedures!

### Slow download speed

**Possible Causes & Solutions:**

1. **Network speed limitation:**
   - Check internet speed
   - Large files take time

2. **Too many concurrent downloads:**
   ```bash
   # Reduce concurrent count
   tgdl download -c 1234567890 --concurrent 3
   ```

3. **Telegram server limitations:**
   - Normal during peak hours
   - Try different time of day

4. **Large file sizes:**
   ```bash
   # Check file sizes
   ls -lh downloads/entity_1234567890/
   
   # Filter smaller files
   tgdl download -c 1234567890 --max-size 50MB
   ```

### Connection timeout

**Symptom:**
```
TimeoutError: Connection timed out
```

**Automatic handling in v1.2.0+:**

tgdl automatically retries transient network errors! When a timeout occurs:
- Automatically retries up to 3 times
- Uses exponential backoff (2s, 4s, 8s waits)
- Continues to next file if all retries fail
- Downloads continue automatically

**What you'll see:**

```
Downloading file1.jpg...
⚠ Download failed, retrying... (Attempt 1/3)
  Waiting 2 seconds...
✓ Downloaded file1.jpg (succeeded on retry)

Downloading file2.jpg...
⚠ Download failed, retrying... (Attempt 1/3)
⚠ Download failed, retrying... (Attempt 2/3)
  Waiting 4 seconds...
✓ Downloaded file2.jpg (succeeded on 2nd retry)
```

**If all retries fail:**
- File is skipped
- Download continues with next file
- Failed files can be retried later by running command again

**Manual solutions (if auto-retry insufficient):**

1. **Check internet connection:**
   ```bash
   ping telegram.org
   ```

2. **Retry the download:**
   ```bash
   tgdl download -c 1234567890
   ```
   - Auto-retries failed files
   - Already downloaded files skipped

3. **Reduce concurrent downloads:**
   ```bash
   tgdl download -c 1234567890 --concurrent 3
   ```

4. **Check firewall/proxy:**
   - Telegram may be blocked
   - Try VPN if in restricted region

### Rate Limited by Telegram (FloodWaitError)

**What happens:**
tgdl automatically handles rate limiting for you! When Telegram limits requests, tgdl will:
- Detect the rate limit
- Show a countdown timer
- Automatically wait
- Resume downloading

**Example output:**
```
⏳ Rate limited by Telegram. Auto-waiting 45s...
  Resuming in 45s...
  Resuming in 44s...
  Resuming in 43s...
  ...
  Resuming in 1s...
  Resuming now...
```

**What you need to do:** Just let it run! No action needed.

**When it occurs:**
- Many concurrent downloads (20+)
- Downloading rapidly from multiple channels
- Downloading many large files
- Normal and expected behavior

**To reduce rate limiting:**

1. **Lower concurrent downloads:**
   ```bash
   # Default is 20, try 5 for slow speed
   tgdl download -c 1234567890 --concurrent 5
   ```

2. **Add delays in scripts:**
   ```bash
   #!/bin/bash
   for channel in 123 456 789; do
     tgdl download -c "$channel"
     sleep 60  # Wait 1 minute between channels
   done
   ```

3. **Download in batches:**
   ```bash
   # First 100
   tgdl download -c 1234567890 --limit 100
   
   # After auto-wait completes, download next 100
   tgdl download -c 1234567890 --limit 100 --min-id 100
   ```

**Note:** The automatic waiting in v1.2.0+ means you rarely need to do anything - just let tgdl handle it!

### Duplicate downloads

**In v1.2.0+:** This is automatically prevented by hash-based deduplication!

**How it works:**
- Each downloaded file gets an MD5 hash
- If the same file appears in multiple messages, tgdl recognizes it
- Duplicate is automatically skipped
- Shows: `⊘ Duplicate of original_name.jpg — removing copy.`

**Example:**

```bash
# Download from channel (gets image: photo123.jpg)
$ tgdl download -c 1234567890 --limit 10
✓ Downloaded photo123.jpg (2.5MB)

# Later, same image appears in different message (as photo456.jpg)
$ tgdl download -c 1234567890 --limit 20
Using 10 already downloaded files
⊘ Duplicate of photo123.jpg — removing copy. (was named photo456.jpg)

# Only 10 NEW files downloaded (not 20)
```

**Benefits:**
- Saves bandwidth
- Saves disk space
- Works across interruptions and resume
- Transparent and automatic

**Verifying deduplication:**
```bash
# Check for duplicate removals in output
$ tgdl download -c 1234567890
...
⊘ Duplicate of file1.jpg — removing copy.
⊘ Duplicate of file2.jpg — removing copy.
...
```

If this was happening in older versions:
1. Update tgdl:
   ```bash
   pip install --upgrade tgdl
   ```

2. Check version is 1.2.0+:
   ```bash
   pip show tgdl | grep Version
   ```

---

## Permission Issues

### Cannot create directory

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/path/to/downloads'
```

**Solutions:**

1. **Use different output directory:**
   ```bash
   # User's home directory
   tgdl download -c 1234567890 -o ~/tgdl_downloads
   ```

2. **Check directory permissions:**
   ```bash
   # Linux/macOS
   ls -ld downloads/
   chmod 755 downloads/
   ```

3. **Run without sudo:**
   - Don't use sudo with tgdl
   - Use user directory instead

### Cannot write file

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: 'downloads/12345.jpg'
```

**Solutions:**

1. **Check available disk space:**
   ```bash
   # Linux/macOS
   df -h
   
   # Windows
   dir
   ```

2. **Check file already exists:**
   ```bash
   ls -l downloads/entity_1234567890/12345.jpg
   ```
   - Delete if corrupted

3. **Change output directory:**
   ```bash
   tgdl download -c 1234567890 -o ~/Downloads
   ```

---

## API Credential Issues

### Invalid API credentials

**Symptom:**
```
✗ Error: API_ID_INVALID
```

**Solutions:**

1. **Verify credentials:**
   - Go to https://my.telegram.org/apps
   - Check API ID and Hash

2. **Re-enter credentials:**
   ```bash
   tgdl logout
   tgdl login
   ```
   - Enter correct API ID and Hash

3. **Check for typos:**
   - API ID: numbers only
   - API Hash: 32 character alphanumeric string

### API credentials not found

**Symptom:**
```
✗ Error: API credentials not found
```

**Solution:**

Login first:
```bash
tgdl login
```

This will prompt for API credentials.

---

## File Issues

### Files not named correctly

**Symptom:**
Files named generically (photo.jpg) instead of with message ID

**This is expected for:**
- Old versions (pre-1.1.0)
- Single file downloads via download-link

**For regular downloads:**
- Should be named: `{message_id}.{extension}`
- Example: `12345.jpg`

**If incorrect:**
1. **Update tgdl:**
   ```bash
   pip install --upgrade tgdl
   ```

2. **Re-download:**
   ```bash
   tgdl download -c 1234567890
   ```

### Corrupted files

**Symptom:**
Files won't open or are incomplete

**Solutions:**

1. **Check file size:**
   ```bash
   ls -lh downloads/entity_1234567890/
   ```
   - Very small files (< 1KB) may be corrupted

2. **Delete and re-download:**
   ```bash
   # Delete corrupted file
   rm downloads/entity_1234567890/12345.jpg
   
   # Re-download (tgdl will get missing files)
   tgdl download -c 1234567890
   ```

3. **Check disk space:**
   - Insufficient space can cause corruption

4. **Download interrupted:**
   - Run download again to resume

---

## Configuration Issues

### Config file not found

**Symptom:**
```
✗ Error: Configuration file not found
```

**Solution:**

Login to create config:
```bash
tgdl login
```

### Cannot read config file

**Symptom:**
```
✗ Error: Cannot read configuration file
```

**Solutions:**

1. **Check file permissions:**
   ```bash
   # Linux/macOS
   ls -l ~/.tgdl/config.json
   chmod 600 ~/.tgdl/config.json
   ```

2. **Reset configuration:**
   ```bash
   # Backup first
   cp ~/.tgdl/config.json ~/.tgdl/config.json.backup
   
   # Logout and login again
   tgdl logout
   tgdl login
   ```

3. **Manually remove config:**
   ```bash
   # Linux/macOS
   rm ~/.tgdl/config.json
   rm ~/.tgdl/.key
   
   # Windows
   del %USERPROFILE%\.tgdl\config.json
   del %USERPROFILE%\.tgdl\.key
   
   # Login again
   tgdl login
   ```

---

## Progress Tracking Issues

### Progress not saved

**Symptom:**
Downloads start from beginning each time

**Solutions:**

1. **Check progress file:**
   ```bash
   # Linux/macOS
   cat ~/.tgdl/progress.json
   
   # Windows
   type %USERPROFILE%\.tgdl\progress.json
   ```

2. **Verify file permissions:**
   ```bash
   # Linux/macOS
   ls -l ~/.tgdl/progress.json
   chmod 644 ~/.tgdl/progress.json
   ```

3. **Reset progress:**
   ```bash
   # Backup first
   cp ~/.tgdl/progress.json ~/.tgdl/progress.json.backup
   
   # Reset
   echo "{}" > ~/.tgdl/progress.json
   ```

### Wrong progress tracking

**Symptom:**
Downloads skip files that weren't downloaded

**Solutions:**

1. **Check progress file:**
   ```bash
   cat ~/.tgdl/progress.json
   ```
   - Shows last downloaded message ID per entity

2. **Reset progress for entity:**
   ```bash
   # Edit progress.json
   # Remove entry for entity ID
   ```

3. **Or reset all progress:**
   ```bash
   echo "{}" > ~/.tgdl/progress.json
   tgdl download -c 1234567890
   ```

---

## Command Issues

### Command not found

**Symptom:**
```
tgdl: command not found
```

**Solutions:**

1. **Check installation:**
   ```bash
   pip show tgdl
   ```

2. **Add to PATH:**
   ```bash
   # Linux/macOS - add to ~/.bashrc or ~/.zshrc
   export PATH="$HOME/.local/bin:$PATH"
   source ~/.bashrc
   
   # Windows - pip should handle this automatically
   ```

3. **Use python -m:**
   ```bash
   python -m tgdl login
   ```

4. **Reinstall:**
   ```bash
   pip uninstall tgdl
   pip install tgdl
   ```

### Invalid command/option

**Symptom:**
```
Error: No such option: --xyz
```

**Solutions:**

1. **Check help:**
   ```bash
   tgdl --help
   tgdl download --help
   ```

2. **Verify spelling:**
   ```
   ✗ Wrong: --max_size
   ✓ Correct: --max-size
   ```

3. **Check command structure:**
   ```bash
   # Correct order
   tgdl download -c 1234567890 --max-size 100MB
   
   # Wrong order
   tgdl --max-size 100MB download -c 1234567890
   ```

---

## Platform-Specific Issues

### Windows: PowerShell encoding issues

**Symptom:**
Unicode characters display incorrectly

**Solution:**

Set UTF-8 encoding:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

Add to PowerShell profile to make permanent:
```powershell
notepad $PROFILE
```

### Linux: SSL certificate errors

**Symptom:**
```
SSLError: certificate verify failed
```

**Solutions:**

1. **Update certificates:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install ca-certificates
   
   # Fedora
   sudo dnf update ca-certificates
   ```

2. **Update Python certifi:**
   ```bash
   pip install --upgrade certifi
   ```

### macOS: notarization warnings

**Symptom:**
Security warnings when running tgdl

**Solution:**

This shouldn't happen with pip installations. If it does:

```bash
# Reinstall
pip uninstall tgdl
pip install tgdl
```

---

## Performance Issues

### High memory usage

**Symptom:**
System slows down during download

**Solutions:**

1. **Reduce concurrent downloads:**
   ```bash
   tgdl download -c 1234567890 --concurrent 2
   ```

2. **Download in smaller batches:**
   ```bash
   tgdl download -c 1234567890 --limit 50
   ```

3. **Close other applications:**
   - Free up RAM
   - Close browser tabs

4. **Check system resources:**
   ```bash
   # Linux
   top
   
   # macOS
   top
   
   # Windows
   Task Manager
   ```

### High disk usage

**Symptom:**
Disk space fills up quickly

**Solutions:**

1. **Use size limits:**
   ```bash
   tgdl download -c 1234567890 --max-size 50MB
   ```

2. **Use download limits:**
   ```bash
   tgdl download -c 1234567890 --limit 100
   ```

3. **Check available space first:**
   ```bash
   df -h  # Linux/macOS
   ```

4. **Clean old downloads:**
   ```bash
   # Remove files older than 30 days
   find downloads -type f -mtime +30 -delete
   ```

---

## Getting Help

### Check logs

**Download logs:**
```bash
tgdl download -c 1234567890 > download.log 2>&1
cat download.log
```

**System info:**
```bash
# Python version
python --version

# tgdl version
pip show tgdl

# OS info
uname -a  # Linux/macOS
systeminfo  # Windows
```

### Report bugs

**On GitHub:**
https://github.com/kavidu-dilhara/tgdl/issues

**Include:**
1. tgdl version (`pip show tgdl`)
2. Python version (`python --version`)
3. Operating system
4. Full error message
5. Command you ran
6. Expected vs actual behavior

### Ask for help

**Provide:**
- What you're trying to do
- What command you ran
- Full error message (if any)
- What you've tried so far

**Example:**
```
I'm trying to download videos from a channel but getting zero files.

Command: tgdl download -c 1234567890 -v
Output: ⚠ No files downloaded.

I can see the channel has videos in Telegram app.
I've tried without filters and still get zero files.

tgdl version: 1.1.4
Python version: 3.9.7
OS: Ubuntu 22.04
```

---

## Quick Diagnosis

### Checklist for issues:

- [ ] Latest tgdl version? (`pip install --upgrade tgdl`)
- [ ] Python 3.7+? (`python --version`)
- [ ] Logged in? (`tgdl status`)
- [ ] Member of channel/group?
- [ ] Correct entity flag (-c/-g/-b)?
- [ ] Internet connection working?
- [ ] Enough disk space?
- [ ] Correct API credentials?

### Common fixes:

```bash
# Update tgdl
pip install --upgrade tgdl

# Reset session
tgdl logout
tgdl login

# Test with minimal command
tgdl download -c 1234567890 --limit 3

# Check status
tgdl status
```

---

## Next Steps

- [View FAQ](faq.md)
- [Command reference](command-reference.md)
- [Advanced usage](advanced-usage.md)
- [Report issue on GitHub](https://github.com/kavidu-dilhara/tgdl/issues)
