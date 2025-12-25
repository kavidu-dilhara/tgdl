# Advanced Usage

Master advanced features and techniques for power users.

## Message ID Ranges

### Overview

Download specific message ID ranges from channels, groups, or bots.

**Use cases:**
- Get specific portion of a channel
- Re-download specific messages
- Skip old content
- Targeted backups

### Basic Range Syntax

```bash
# Messages from ID 20 to 100 (inclusive)
tgdl download -c 1234567890 --min-id 20 --max-id 100
```

### Understanding Message IDs

**Message IDs are sequential:**
```
Message ID 1  - First message in channel
Message ID 2  - Second message
Message ID 3  - Third message
...
Message ID N  - Latest message
```

**Finding message IDs:**

1. **Right-click message in Telegram Desktop:**
   - Select "Copy Message Link"
   - Link contains ID: `https://t.me/channel/12345`
   - Last number (12345) is message ID

2. **From tgdl output:**
   ```
   Downloading: 12345.jpg
   ```
   - Filename starts with message ID (12345)

3. **Try download-link:**
   ```bash
   tgdl download-link https://t.me/channel/12345
   ```
   - Downloads that specific message

### Range Examples

#### Get Recent Messages

```bash
# Last 100 messages (if latest is 1000)
tgdl download -c 1234567890 --min-id 900
```

#### Get Old Messages

```bash
# First 100 messages
tgdl download -c 1234567890 --max-id 100
```

#### Get Middle Section

```bash
# Messages 500-600
tgdl download -c 1234567890 --min-id 500 --max-id 600
```

#### Skip First N Messages

```bash
# Everything after message 1000
tgdl download -c 1234567890 --min-id 1000
```

#### Single Message

```bash
# Just message 12345
tgdl download -c 1234567890 --min-id 12345 --max-id 12345
```

### Combining with Filters

```bash
# Videos in range 100-200
tgdl download -c 1234567890 --min-id 100 --max-id 200 -v

# Photos under 5MB in range 500-1000
tgdl download -c 1234567890 --min-id 500 --max-id 1000 -p --max-size 5MB
```

### Range Limitations

!!! info "Range vs Limit"
    When using both:
    ```bash
    tgdl download -c 1234567890 --min-id 100 --max-id 200 --limit 10
    ```
    
    - Range: Messages 100-200 considered
    - Limit: Only first 10 files downloaded
    - Result: Up to 10 files from range 100-200

!!! warning "Empty Ranges"
    If range has no media:
    ```bash
    tgdl download -c 1234567890 --min-id 100 --max-id 200
    # May download 0 files if no media in that range
    ```

---

## Parallel Downloads

### Concurrent Downloads

**Default:** 5 parallel downloads  
**Range:** 1-50  
**Flag:** `--concurrent N`

#### Performance Tuning

```bash
# Slow/unstable connection (1 at a time)
tgdl download -c 1234567890 --concurrent 1

# Normal connection (default)
tgdl download -c 1234567890

# Fast connection (10 parallel)
tgdl download -c 1234567890 --concurrent 10

# Very fast connection (20 parallel)
tgdl download -c 1234567890 --concurrent 20

# Maximum (50 parallel - use with caution)
tgdl download -c 1234567890 --concurrent 50
```

#### Finding Optimal Value

!!! tip "Test Different Values"
    ```bash
    # Test with small limit
    time tgdl download -c ID --limit 20 --concurrent 5
    time tgdl download -c ID --limit 20 --concurrent 10
    time tgdl download -c ID --limit 20 --concurrent 20
    ```
    
    Choose value with:
    - Fastest speed
    - No errors/timeouts
    - Stable progress bars

#### Factors Affecting Performance

**Internet speed:**
- Slow (< 10 Mbps): 1-3
- Medium (10-50 Mbps): 5-10
- Fast (50-100 Mbps): 10-20
- Very fast (> 100 Mbps): 20-50

**File sizes:**
- Large files (> 100MB): Lower concurrent (5-10)
- Small files (< 10MB): Higher concurrent (10-20)

**System resources:**
- Limited RAM/CPU: Lower concurrent (1-5)
- Powerful system: Higher concurrent (10-20)

**Telegram limits:**
- Too high may trigger rate limits
- May see temporary flood waits
- If errors occur, reduce value

---

## Automation & Scripting

### Scheduled Downloads

#### Windows Task Scheduler

**Create batch file `update_channel.bat`:**
```batch
@echo off
cd /d "C:\path\to\downloads"
tgdl download -c 1234567890 -v --max-size 100MB
```

**Schedule in Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 2 AM
4. Action: Start program `update_channel.bat`

#### Linux/macOS Cron

**Edit crontab:**
```bash
crontab -e
```

**Add job:**
```bash
# Update channel daily at 2 AM
0 2 * * * cd /path/to/downloads && tgdl download -c 1234567890
```

**With logging:**
```bash
0 2 * * * cd /path/to/downloads && tgdl download -c 1234567890 >> /var/log/tgdl.log 2>&1
```

### Backup Script

**backup_all.sh (Linux/macOS):**
```bash
#!/bin/bash

# Configuration
CHANNELS=(1234567890 9876543210)
OUTPUT_BASE="/backups/telegram"
LOG_FILE="/var/log/tgdl_backup.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "Starting Telegram backup..."

# Loop through channels
for channel in "${CHANNELS[@]}"; do
    log "Backing up channel $channel..."
    
    if tgdl download -c "$channel" -o "$OUTPUT_BASE/$channel" >> "$LOG_FILE" 2>&1; then
        log "✓ Successfully backed up channel $channel"
    else
        log "✗ Failed to backup channel $channel"
    fi
done

log "Backup complete!"
```

**Make executable:**
```bash
chmod +x backup_all.sh
```

**Run:**
```bash
./backup_all.sh
```

**backup_all.bat (Windows):**
```batch
@echo off
setlocal enabledelayedexpansion

set CHANNELS=1234567890 9876543210
set OUTPUT_BASE=C:\backups\telegram
set LOG_FILE=C:\logs\tgdl_backup.log

echo [%date% %time%] Starting Telegram backup... >> %LOG_FILE%

for %%c in (%CHANNELS%) do (
    echo [%date% %time%] Backing up channel %%c... >> %LOG_FILE%
    tgdl download -c %%c -o %OUTPUT_BASE%\%%c >> %LOG_FILE% 2>&1
    
    if !errorlevel! equ 0 (
        echo [%date% %time%] Successfully backed up channel %%c >> %LOG_FILE%
    ) else (
        echo [%date% %time%] Failed to backup channel %%c >> %LOG_FILE%
    )
)

echo [%date% %time%] Backup complete! >> %LOG_FILE%
```

### Multi-Channel Download

**Download from multiple channels:**

```bash
#!/bin/bash

# Channel IDs
TECH_NEWS=1234567890
DAILY_PICS=9876543210
VIDEO_ARCHIVE=1122334455

# Download videos from tech channel
tgdl download -c $TECH_NEWS -v --max-size 100MB -o ~/Videos/Tech

# Download photos from pictures channel
tgdl download -c $DAILY_PICS -p -o ~/Pictures/Daily

# Download everything from archive
tgdl download -c $VIDEO_ARCHIVE -o ~/Archive/Videos
```

### Error Handling

**Robust script with error handling:**

```bash
#!/bin/bash

CHANNEL_ID=1234567890
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if tgdl download -c $CHANNEL_ID; then
        echo "Download successful!"
        exit 0
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "Download failed. Retry $RETRY_COUNT of $MAX_RETRIES..."
        sleep 60  # Wait 1 minute before retry
    fi
done

echo "Download failed after $MAX_RETRIES attempts."
exit 1
```

---

## Output Organization

### Custom Directory Structure

**By entity type:**
```bash
tgdl download -c 1234567890 -o ~/Telegram/Channels/TechNews
tgdl download -g 9876543210 -o ~/Telegram/Groups/MyGroup
tgdl download -b 1122334455 -o ~/Telegram/Bots/FileBot
```

**By media type:**
```bash
tgdl download -c 1234567890 -v -o ~/Videos/Telegram
tgdl download -c 1234567890 -p -o ~/Pictures/Telegram
tgdl download -c 1234567890 -a -o ~/Music/Telegram
```

**By date:**
```bash
TODAY=$(date +%Y-%m-%d)
tgdl download -c 1234567890 -o ~/Backups/$TODAY
```

**Hierarchical:**
```bash
BASE=~/Telegram
CHANNEL=TechNews
DATE=$(date +%Y-%m-%d)

tgdl download -c 1234567890 -o $BASE/$CHANNEL/$DATE
# Result: ~/Telegram/TechNews/2025-12-25/
```

### Filename Understanding

**Format:** `{message_id}.{extension}`

**Examples:**
```
12345.jpg    - Photo from message 12345
12346.mp4    - Video from message 12346
12347.pdf    - Document from message 12347
12348_2.jpg  - Second file from message 12348
```

**Post-processing script:**
```bash
#!/bin/bash

# Rename files with timestamp
for file in *.jpg; do
    # Get message ID
    id=$(echo $file | cut -d'.' -f1)
    
    # Get file modification time
    timestamp=$(stat -f %Sm -t "%Y%m%d_%H%M%S" "$file")
    
    # Rename
    mv "$file" "${timestamp}_${id}.jpg"
done
```

---

## Advanced Filtering

### Complex Filter Combinations

```bash
# Only large videos
tgdl download -c 1234567890 -v --min-size 100MB --max-size 1GB

# Small photos and documents
tgdl download -c 1234567890 -p -d --max-size 10MB

# Audio files in specific range
tgdl download -c 1234567890 -a --min-id 1000 --max-id 2000
```

### Selective Downloads by Type

**Photos only:**
```bash
tgdl download -c 1234567890 -p -o ~/Pictures
```

**Videos only:**
```bash
tgdl download -c 1234567890 -v -o ~/Videos
```

**Documents only:**
```bash
tgdl download -c 1234567890 -d -o ~/Documents
```

**Everything except videos:**
```bash
tgdl download -c 1234567890 -p -a -d
```

### Size-Based Strategies

**Quick preview (small files only):**
```bash
tgdl download -c 1234567890 --max-size 1MB --limit 20
```

**High quality only (large files):**
```bash
tgdl download -c 1234567890 --min-size 10MB
```

**Storage-conscious:**
```bash
# Max 50MB per file, limit 100 files
tgdl download -c 1234567890 --max-size 50MB --limit 100
```

---

## Performance Optimization

### Network Optimization

**Bandwidth limit simulation:**
```bash
# Use lower concurrent for limited bandwidth
tgdl download -c 1234567890 --concurrent 3
```

**Avoid peak hours:**
```bash
# Schedule for off-peak times (cron example)
0 2 * * * tgdl download -c 1234567890  # 2 AM daily
```

### Storage Optimization

**Free up space before download:**
```bash
# Check available space
df -h

# Clean old files
find ~/downloads -type f -mtime +30 -delete  # Remove files older than 30 days

# Then download
tgdl download -c 1234567890
```

**Download to external drive:**
```bash
# Linux/macOS
tgdl download -c 1234567890 -o /mnt/external/telegram

# Windows
tgdl download -c 1234567890 -o E:\Telegram
```

### Resume Strategy

**For large channels:**
```bash
# Download in batches
tgdl download -c 1234567890 --max-id 1000
tgdl download -c 1234567890 --min-id 1001 --max-id 2000
tgdl download -c 1234567890 --min-id 2001 --max-id 3000
# etc...
```

**With automatic retry:**
```bash
#!/bin/bash
until tgdl download -c 1234567890; do
    echo "Download interrupted, retrying in 60s..."
    sleep 60
done
```

---

## Working with Private Channels

### Private Channel Links

**Format:**
```
https://t.me/c/1234567890/123
           └─┬─┘└────┬────┘└┬┘
           scheme channel  msg
```

**Extract channel ID:**
- From link: `https://t.me/c/1234567890/123`
- Channel ID: `1234567890`

**Download:**
```bash
tgdl download -c 1234567890
```

### Access Requirements

!!! warning "Private Channel Access"
    You must be a member of the private channel!
    
    **Symptoms of no access:**
    ```
    ✗ Error: Could not find the input entity
    ```
    
    **Solution:**
    1. Join channel in Telegram app
    2. Run `tgdl channels` to verify it's listed
    3. Try download again

---

## Monitoring & Logging

### Save Download Logs

```bash
# Redirect output to file
tgdl download -c 1234567890 > download.log 2>&1

# Append to existing log
tgdl download -c 1234567890 >> download.log 2>&1

# View log in real-time
tail -f download.log
```

### Extract Statistics

```bash
# Count downloaded files
grep "✓ Downloaded:" download.log | wc -l

# Total size downloaded
grep "✓ Downloaded:" download.log | grep -o "[0-9.]*[KMGT]B" | paste -sd+ | bc

# Failed downloads
grep "✗" download.log
```

### Progress Tracking File

**Location:** `~/.tgdl/progress.json`

**Format:**
```json
{
  "1234567890": 12345
}
```

**Usage:**
```bash
# View last downloaded message ID
cat ~/.tgdl/progress.json | jq

# Reset progress (start over)
echo "{}" > ~/.tgdl/progress.json

# Backup progress
cp ~/.tgdl/progress.json ~/.tgdl/progress.json.backup
```

---

## Best Practices

### 1. Test Before Bulk Download

!!! tip "Always Test First"
    ```bash
    # Test with small limit
    tgdl download -c 1234567890 --limit 5
    
    # Check results
    ls downloads/entity_1234567890/
    
    # If OK, run full download
    tgdl download -c 1234567890
    ```

### 2. Use Appropriate Filters

!!! tip "Save Time & Space"
    ```bash
    # Instead of downloading everything then deleting
    tgdl download -c 1234567890 -v --max-size 100MB
    
    # Much better than:
    # tgdl download -c 1234567890
    # rm downloads/*.jpg  # Delete unwanted files
    ```

### 3. Regular Backups

!!! tip "Automate Updates"
    ```bash
    # Cron job for daily updates
    0 3 * * * tgdl download -c 1234567890 >> /var/log/tgdl.log 2>&1
    ```

### 4. Monitor Progress Files

!!! tip "Track State"
    ```bash
    # Backup progress before major operations
    cp ~/.tgdl/progress.json ~/.tgdl/progress.backup
    
    # If something goes wrong, restore
    cp ~/.tgdl/progress.backup ~/.tgdl/progress.json
    ```

### 5. Handle Errors Gracefully

!!! tip "Robust Scripts"
    ```bash
    #!/bin/bash
    if ! tgdl download -c 1234567890; then
        # Send notification
        echo "tgdl failed!" | mail -s "Alert" user@example.com
        
        # Log error
        echo "$(date): Download failed" >> /var/log/tgdl_errors.log
        
        # Exit with error code
        exit 1
    fi
    ```

---

## Troubleshooting Advanced Issues

### FloodWaitError

**Symptom:**
```
FloodWaitError: A wait of X seconds is required
```

**Cause:** Too many requests to Telegram

**Solutions:**
```bash
# Reduce concurrent downloads
tgdl download -c 1234567890 --concurrent 3

# Add delay between batches (script)
tgdl download -c 1234567890 --max-id 1000
sleep 300  # Wait 5 minutes
tgdl download -c 1234567890 --min-id 1001
```

### Memory Issues

**Symptom:** System slows down or crashes

**Solutions:**
```bash
# Reduce concurrent downloads
tgdl download -c 1234567890 --concurrent 2

# Download in smaller batches
tgdl download -c 1234567890 --limit 50

# Use smaller files
tgdl download -c 1234567890 --max-size 50MB
```

### Incomplete Downloads

**Symptom:** Files partially downloaded

**Check:**
```bash
# Find files with unusual sizes
find downloads -type f -size 0  # Empty files
find downloads -type f -size -1k  # Very small files
```

**Solution:**
```bash
# Delete incomplete files
find downloads -type f -size -1k -delete

# Re-download
tgdl download -c 1234567890
```

---

## Next Steps

- [Explore media filters in detail](media-filters.md)
- [Learn about message ID ranges](message-ranges.md)
- [Configure tgdl](configuration.md)
- [Get help with common issues](troubleshooting.md)
