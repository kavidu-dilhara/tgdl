# Message ID Ranges

Complete guide to downloading specific message ranges from Telegram entities.

## Overview

Message ID ranges allow you to download specific portions of a channel, group, or bot chat by specifying start and end message IDs.

**Benefits:**
- Download only what you need
- Re-download specific sections
- Skip old or irrelevant content
- Manage large archives efficiently
- Targeted backup strategies

---

## Understanding Message IDs

### What are Message IDs?

Every message in a Telegram chat has a unique sequential ID number.

```
Message ID 1  ← First message (oldest)
Message ID 2
Message ID 3
...
Message ID N  ← Latest message (newest)
```

**Key points:**
- IDs start at 1
- IDs increment by 1 for each message
- IDs are unique within each entity (channel/group/bot)
- IDs never change
- Deleted messages leave gaps

### Finding Message IDs

#### Method 1: From Telegram Desktop

1. Right-click on a message
2. Select "Copy Message Link"
3. Link format: `https://t.me/channel/12345`
4. The last number (12345) is the message ID

**Public channel example:**
```
https://t.me/technews/12345
                      └─┬──┘
                    message ID
```

**Private channel example:**
```
https://t.me/c/1234567890/54321
                       └───┬──┘
                      message ID
```

#### Method 2: From Downloaded Files

tgdl names files with message ID:

```bash
ls downloads/entity_1234567890/
# Output:
# 12345.jpg    ← Message ID is 12345
# 12346.mp4    ← Message ID is 12346
# 12347.pdf    ← Message ID is 12347
```

#### Method 3: Using download-link

```bash
# Download single message to see its ID
tgdl download-link https://t.me/channel/12345

# Check downloaded file
ls downloads/
# Output: 12345.ext
```

#### Method 4: From Telegram Mobile

1. Long-press message
2. Tap "Forward"
3. Forward to "Saved Messages"
4. In Saved Messages, the forwarded message shows original date
5. Use method 1 (copy link) from there

---

## Basic Range Syntax

### Command Format

```bash
tgdl download -c|g|b ENTITY_ID --min-id MIN --max-id MAX
```

**Parameters:**
- `--min-id` - Start from this message ID (inclusive)
- `--max-id` - Stop at this message ID (inclusive)
- Both are optional
- Can use one or both

### Examples

#### Download Specific Range

```bash
# Messages 100 to 200 (inclusive)
tgdl download -c 1234567890 --min-id 100 --max-id 200
```

This downloads messages: 100, 101, 102, ..., 199, 200

#### From Specific ID Onwards

```bash
# From message 500 to latest
tgdl download -c 1234567890 --min-id 500
```

#### Up to Specific ID

```bash
# From oldest to message 1000
tgdl download -c 1234567890 --max-id 1000
```

#### Single Message

```bash
# Only message 12345
tgdl download -c 1234567890 --min-id 12345 --max-id 12345
```

---

## Use Cases

### 1. Archive Historical Content

**Scenario:** Download old messages from a channel you just joined.

```bash
# First 1000 messages (historical archive)
tgdl download -c 1234567890 --max-id 1000
```

**Benefits:**
- Get old content without downloading everything
- Separate old from new
- Manage archive sizes

### 2. Get Recent Updates

**Scenario:** You've already downloaded messages 1-5000, now want 5000+.

```bash
# Everything after message 5000
tgdl download -c 1234567890 --min-id 5001
```

**Alternative (automatic):**
```bash
# tgdl automatically tracks progress
tgdl download -c 1234567890
# Will download from last saved message ID
```

### 3. Re-download Failed Section

**Scenario:** Downloads failed for messages 2000-2100, want to retry.

```bash
# Re-download specific range
tgdl download -c 1234567890 --min-id 2000 --max-id 2100
```

### 4. Download Specific Event/Period

**Scenario:** Know that interesting content was posted in messages 3000-3500.

```bash
# Download specific event range
tgdl download -c 1234567890 --min-id 3000 --max-id 3500 -o ~/Events/Conference2024
```

### 5. Incremental Backups

**Scenario:** Create monthly backups with specific ranges.

```bash
# January (messages 1-1000)
tgdl download -c 1234567890 --min-id 1 --max-id 1000 -o ~/Backups/2024-01

# February (messages 1001-2000)
tgdl download -c 1234567890 --min-id 1001 --max-id 2000 -o ~/Backups/2024-02

# March (messages 2001-3000)
tgdl download -c 1234567890 --min-id 2001 --max-id 3000 -o ~/Backups/2024-03
```

### 6. Sample Downloads

**Scenario:** Want to see what's in different parts of a large channel.

```bash
# Sample early messages
tgdl download -c 1234567890 --min-id 1 --max-id 50

# Sample middle
tgdl download -c 1234567890 --min-id 5000 --max-id 5050

# Sample recent
tgdl download -c 1234567890 --min-id 9900 --max-id 10000
```

### 7. Skip Unwanted Content

**Scenario:** Channel has spam/ads in messages 1000-2000, want to skip.

```bash
# Get messages before spam
tgdl download -c 1234567890 --max-id 999

# Get messages after spam
tgdl download -c 1234567890 --min-id 2001
```

---

## Combining with Other Filters

### With Media Type Filters

```bash
# Videos in specific range
tgdl download -c 1234567890 --min-id 100 --max-id 200 -v

# Photos from recent messages
tgdl download -c 1234567890 --min-id 9000 -p
```

### With Size Filters

```bash
# Large files in specific range
tgdl download -c 1234567890 --min-id 500 --max-id 1000 --min-size 100MB

# Small photos from old messages
tgdl download -c 1234567890 --max-id 500 -p --max-size 5MB
```

### With Download Limit

```bash
# First 10 files from range
tgdl download -c 1234567890 --min-id 1000 --max-id 2000 --limit 10
```

**Important:** Limit applies AFTER range filter.

**Example:**
- Range: 1000-2000 (1000 messages)
- Has: 500 media files in range
- Limit: 10
- Result: First 10 of those 500 media files

### Combined Example

```bash
# Recent videos, 50-100MB, max 20 files
tgdl download -c 1234567890 \
  --min-id 9000 \
  -v \
  --min-size 50MB \
  --max-size 100MB \
  --limit 20 \
  --concurrent 10
```

---

## Advanced Techniques

### Automatic Progress Tracking

tgdl automatically tracks the last downloaded message ID:

```bash
# First run
tgdl download -c 1234567890
# Downloads messages 1-1000
# Saves: {"1234567890": 1000} in progress.json

# Second run (later)
tgdl download -c 1234567890
# Reads progress.json
# Downloads messages 1001+ (new content only)
```

**Manual override:**
```bash
# Force specific range (ignores progress)
tgdl download -c 1234567890 --min-id 1
```

### Finding Latest Message ID

**Method 1: Download one message**
```bash
# Get latest message
tgdl download -c 1234567890 --limit 1

# Check filename
ls downloads/entity_1234567890/
# Latest file shows latest message ID
```

**Method 2: From Telegram app**
- Scroll to bottom of channel
- Copy message link
- Extract ID from link

### Batch Downloads by Range

**Script example (Linux/macOS):**
```bash
#!/bin/bash

CHANNEL=1234567890
BATCH_SIZE=1000

for start in {1..10000..1000}; do
    end=$((start + BATCH_SIZE - 1))
    echo "Downloading messages $start to $end..."
    tgdl download -c $CHANNEL --min-id $start --max-id $end
    sleep 60  # Wait between batches
done
```

**Script example (Windows PowerShell):**
```powershell
$channel = 1234567890
$batchSize = 1000

for ($start = 1; $start -le 10000; $start += $batchSize) {
    $end = $start + $batchSize - 1
    Write-Host "Downloading messages $start to $end..."
    tgdl download -c $channel --min-id $start --max-id $end
    Start-Sleep -Seconds 60
}
```

### Gap Detection

**Find missing downloads:**
```bash
#!/bin/bash

# List downloaded message IDs
ls downloads/entity_1234567890/ | sed 's/\..*//' | sort -n > downloaded.txt

# Check for gaps
prev=0
while read id; do
    if [ $((id - prev)) -gt 1 ]; then
        echo "Gap: $prev to $id"
    fi
    prev=$id
done < downloaded.txt
```

---

## How It Works Internally

### Telethon's iter_messages()

tgdl uses Telethon's `iter_messages()` method:

```python
async for message in client.iter_messages(
    entity,
    min_id=min_msg_id - 1,  # Subtract 1 for inclusive
    max_id=max_msg_id,
    reverse=False  # Newest first
):
    # Process message
```

**Important details:**
- `min_id` is **exclusive** in Telethon
- tgdl subtracts 1 to make it **inclusive**
- `max_id` is already **inclusive**
- Messages fetched newest to oldest (unless `reverse=True`)

**Example:**
```bash
# User command
tgdl download -c ID --min-id 100 --max-id 200

# Internal Telethon call
iter_messages(entity, min_id=99, max_id=200)
# Returns messages 100, 101, ..., 199, 200
```

### Progress Tracking Logic

```python
# 1. Read progress
last_id = progress.get(entity_id, 0)

# 2. Use as min_id if no explicit range
if not min_msg_id:
    min_msg_id = last_id + 1

# 3. Download messages
# ... download logic ...

# 4. Update progress with highest downloaded ID
progress[entity_id] = highest_downloaded_id
save_progress(progress)
```

---

## Limitations and Considerations

### Empty Ranges

If range contains no media files:

```bash
tgdl download -c 1234567890 --min-id 100 --max-id 200
# May download 0 files if range only has text messages
```

**Check first:**
```bash
# Try with limit
tgdl download -c 1234567890 --min-id 100 --max-id 200 --limit 1
```

### Deleted Messages

Deleted messages leave gaps in IDs:

```
Message 10 ← Exists
Message 11 ← Deleted (gap)
Message 12 ← Exists
```

**Impact:**
- No errors
- Simply skipped (not counted)
- Range 10-12 downloads messages 10 and 12 only

### Large Ranges

Very large ranges may take long:

```bash
# Inefficient: Checking 100,000 messages
tgdl download -c 1234567890 --min-id 1 --max-id 100000 -v
```

**Better approach:**
```bash
# Use limit if you don't need all
tgdl download -c 1234567890 --min-id 1 --max-id 100000 -v --limit 100
```

### Range vs Limit Interaction

**Important:**

```bash
# This does NOT mean "download 10 messages in range"
# It means "from messages in range, download first 10 media files"
tgdl download -c 1234567890 --min-id 100 --max-id 200 --limit 10
```

**Execution:**
1. Filter messages: 100-200
2. Filter media: Only messages with media
3. Apply limit: First 10

---

## Troubleshooting

### No files downloaded from range

**Possible causes:**

1. **No media in range:**
   ```bash
   # Check without media filters
   tgdl download -c ID --min-id 100 --max-id 200 --limit 1
   ```

2. **All files already downloaded:**
   - Normal behavior
   - tgdl skips existing files

3. **Range beyond channel size:**
   ```bash
   # If channel only has 1000 messages
   tgdl download -c ID --min-id 2000 --max-id 3000
   # Downloads 0 files
   ```

### Wrong range downloaded

**Check command:**
```bash
# Make sure IDs are correct
tgdl download -c 1234567890 --min-id 100 --max-id 200
```

**Verify:**
```bash
# Check downloaded filenames
ls downloads/entity_1234567890/
# Should see 100.ext, 101.ext, etc.
```

### Progress tracking interferes

**Progress takes precedence:**
```bash
# progress.json has: {"1234567890": 5000}

# This command
tgdl download -c 1234567890 --min-id 100 --max-id 200

# Actually downloads from 5001 (progress overrides)
```

**Solution - reset progress for that entity:**
```bash
# Edit progress.json, remove entity or set to 0
# OR force specific range by ensuring max-id > progress
```

---

## Examples Gallery

### Beginner Examples

```bash
# Download first 100 messages
tgdl download -c 1234567890 --max-id 100

# Download last 100 messages (if latest is 10000)
tgdl download -c 1234567890 --min-id 9900

# Download single message
tgdl download -c 1234567890 --min-id 12345 --max-id 12345
```

### Intermediate Examples

```bash
# Videos from specific range
tgdl download -c 1234567890 --min-id 1000 --max-id 2000 -v

# Photos under 5MB from old messages
tgdl download -c 1234567890 --max-id 500 -p --max-size 5MB

# Recent large files
tgdl download -c 1234567890 --min-id 9000 --min-size 50MB
```

### Advanced Examples

```bash
# HD videos from conference messages
tgdl download -c 1234567890 \
  --min-id 3000 \
  --max-id 3500 \
  -v \
  --min-size 100MB \
  --max-size 500MB \
  -o ~/Conferences/2024/Videos

# Sample every 1000 messages
for i in {0..10000..1000}; do
  tgdl download -c 1234567890 --min-id $i --max-id $((i+10))
done

# Batch download with error handling
#!/bin/bash
for start in {1..10000..500}; do
    end=$((start + 499))
    if ! tgdl download -c 1234567890 --min-id $start --max-id $end; then
        echo "Failed: $start-$end" >> failed_ranges.txt
    fi
    sleep 60
done
```

---

## Best Practices

### 1. Test with Small Range

!!! tip "Test First"
    ```bash
    # Test with 10-message range
    tgdl download -c 1234567890 --min-id 100 --max-id 110
    
    # If successful, expand range
    tgdl download -c 1234567890 --min-id 100 --max-id 1000
    ```

### 2. Use Appropriate Batch Sizes

!!! tip "Batch Strategy"
    - Small files: 1000-5000 messages per batch
    - Large files: 100-500 messages per batch
    - Very large files: 50-100 messages per batch

### 3. Combine with Filters

!!! tip "Efficient Filtering"
    ```bash
    # Instead of downloading everything then filtering
    tgdl download -c 1234567890 --min-id 1000 --max-id 2000 -v --max-size 100MB
    ```

### 4. Monitor Progress

!!! tip "Track Progress"
    ```bash
    # Check progress file
    cat ~/.tgdl/progress.json
    
    # Backup before major operations
    cp ~/.tgdl/progress.json ~/.tgdl/progress.backup
    ```

### 5. Handle Errors Gracefully

!!! tip "Error Handling"
    ```bash
    # Script with retry logic
    #!/bin/bash
    for attempt in {1..3}; do
        if tgdl download -c ID --min-id 1000 --max-id 2000; then
            break
        fi
        echo "Attempt $attempt failed, retrying..."
        sleep 60
    done
    ```

---

## Quick Reference

### Command Template

```bash
tgdl download -c|g|b ID [--min-id MIN] [--max-id MAX] [OPTIONS]
```

### Common Patterns

```bash
# From ID onwards
--min-id ID

# Up to ID
--max-id ID

# Specific range
--min-id START --max-id END

# Single message
--min-id ID --max-id ID

# With filters
--min-id ID --max-id ID -v --max-size 100MB --limit 50
```

---

## Next Steps

- [Learn about media filters](media-filters.md)
- [Explore advanced usage](advanced-usage.md)
- [See full command reference](command-reference.md)
- [Troubleshooting](troubleshooting.md)
