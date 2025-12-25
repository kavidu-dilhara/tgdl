# Media Filters

Complete guide to filtering media files during download.

## Overview

tgdl supports filtering by:
- **Media type** (photos, videos, audio, documents)
- **File size** (min/max)
- **Message ID range** (min/max)
- **Download limit** (first N files)

---

## Media Type Filters

### Available Types

| Flag | Type | Includes |
|------|------|----------|
| `-p` or `--photos` | Photos | JPG, PNG, WebP images |
| `-v` or `--videos` | Videos | MP4, MKV, AVI, MOV files |
| `-a` or `--audio` | Audio | MP3, M4A, OGG, FLAC files |
| `-d` or `--documents` | Documents | PDF, ZIP, TXT, any file type |

!!! info "Document Type"
    Documents include ALL file types that aren't photos, videos, or audio. This includes PDFs, ZIPs, APKs, executables, archives, etc.

### Single Type

```bash
# Photos only
tgdl download -c 1234567890 -p

# Videos only
tgdl download -c 1234567890 -v

# Audio only
tgdl download -c 1234567890 -a

# Documents only
tgdl download -c 1234567890 -d
```

### Multiple Types

```bash
# Photos and videos
tgdl download -c 1234567890 -p -v

# Audio and documents
tgdl download -c 1234567890 -a -d

# Everything except videos
tgdl download -c 1234567890 -p -a -d

# Everything (no filter)
tgdl download -c 1234567890
```

### Type Examples

#### Download Profile Pictures
```bash
# Channels often have photos
tgdl download -c 1234567890 -p
```

#### Video Archive
```bash
# Video channels
tgdl download -c 1234567890 -v
```

#### Music Collection
```bash
# Music channels
tgdl download -c 1234567890 -a
```

#### Software/APKs
```bash
# App sharing channels
tgdl download -c 1234567890 -d
```

---

## File Size Filters

### Size Units

Supported units:
- `B` - Bytes
- `KB` - Kilobytes (1024 B)
- `MB` - Megabytes (1024 KB)
- `GB` - Gigabytes (1024 MB)
- `TB` - Terabytes (1024 GB)

!!! warning "Case Sensitive"
    Use uppercase: `MB` not `mb`

### Maximum Size

```bash
# Max 10MB
tgdl download -c 1234567890 --max-size 10MB

# Max 100MB
tgdl download -c 1234567890 --max-size 100MB

# Max 1GB
tgdl download -c 1234567890 --max-size 1GB
```

**Use cases:**
- Limited storage space
- Bandwidth concerns
- Quick downloads only
- Filter out large videos

### Minimum Size

```bash
# Min 1MB (skip small files)
tgdl download -c 1234567890 --min-size 1MB

# Min 10MB (only large files)
tgdl download -c 1234567890 --min-size 10MB

# Min 100MB (very large files only)
tgdl download -c 1234567890 --min-size 100MB
```

**Use cases:**
- Skip thumbnails/previews
- High quality content only
- Avoid compressed versions

### Size Range

```bash
# Between 1MB and 100MB
tgdl download -c 1234567890 --min-size 1MB --max-size 100MB

# Between 10MB and 1GB
tgdl download -c 1234567890 --min-size 10MB --max-size 1GB

# Medium-sized files only (5-50MB)
tgdl download -c 1234567890 --min-size 5MB --max-size 50MB
```

**Use cases:**
- Specific quality range
- Storage budget
- Network limitations

### Size Examples

#### Quick Download (Small Files)
```bash
# Under 5MB (fast)
tgdl download -c 1234567890 --max-size 5MB
```

#### Skip Previews
```bash
# Over 1MB (skip thumbnails)
tgdl download -c 1234567890 --min-size 1MB
```

#### Storage Budget
```bash
# 50 files under 20MB each = ~1GB total
tgdl download -c 1234567890 --max-size 20MB --limit 50
```

#### High Quality Videos
```bash
# Videos over 50MB (likely HD)
tgdl download -c 1234567890 -v --min-size 50MB
```

#### Avoid Huge Files
```bash
# Under 500MB (avoid 4K videos)
tgdl download -c 1234567890 -v --max-size 500MB
```

---

## Message ID Filters

### Basics

Message IDs are sequential numbers assigned by Telegram.

```
Message 1 - Oldest
Message 2
Message 3
...
Message N - Newest
```

### Minimum ID

```bash
# From message 100 onwards
tgdl download -c 1234567890 --min-id 100

# Recent messages only (if latest is 1000)
tgdl download -c 1234567890 --min-id 900
```

**Use cases:**
- Skip old content
- Get recent additions
- Resume from specific point

### Maximum ID

```bash
# Up to message 100
tgdl download -c 1234567890 --max-id 100

# First 50 messages
tgdl download -c 1234567890 --max-id 50
```

**Use cases:**
- Get old content only
- Archive historical messages
- Stop at specific point

### ID Range

```bash
# Messages 100-200
tgdl download -c 1234567890 --min-id 100 --max-id 200

# Specific section (500-600)
tgdl download -c 1234567890 --min-id 500 --max-id 600

# Single message
tgdl download -c 1234567890 --min-id 12345 --max-id 12345
```

**Use cases:**
- Download specific period
- Re-download failed range
- Targeted backup

### Finding Message IDs

**Method 1: Telegram Desktop**
1. Right-click message
2. "Copy Message Link"
3. Link format: `https://t.me/channel/12345`
4. Last number is message ID

**Method 2: From Downloads**
```bash
# Filename is message_id.extension
ls downloads/entity_1234567890/
# Output: 12345.jpg, 12346.mp4, etc.
```

**Method 3: Use download-link**
```bash
# Download single message to see its ID
tgdl download-link https://t.me/channel/12345
# Downloads 12345.ext
```

### ID Filter Examples

#### Archive Old Content
```bash
# First 1000 messages
tgdl download -c 1234567890 --max-id 1000
```

#### Get Recent Updates
```bash
# Last 100 messages (if latest is 5000)
tgdl download -c 1234567890 --min-id 4900
```

#### Re-download Failed Range
```bash
# Had errors in messages 2000-2100
tgdl download -c 1234567890 --min-id 2000 --max-id 2100
```

#### Monthly Archives
```bash
# January messages (1-1000)
tgdl download -c 1234567890 --min-id 1 --max-id 1000 -o ~/Archives/Jan

# February messages (1001-2000)
tgdl download -c 1234567890 --min-id 1001 --max-id 2000 -o ~/Archives/Feb
```

---

## Download Limit

### Limit Count

```bash
# First 10 files
tgdl download -c 1234567890 --limit 10

# First 50 files
tgdl download -c 1234567890 --limit 50

# First 100 files
tgdl download -c 1234567890 --limit 100
```

!!! info "How Limit Works"
    Limit applies AFTER all other filters:
    
    1. Filter by message ID range
    2. Filter by media type
    3. Filter by file size
    4. Apply limit to remaining files

### Limit Examples

#### Quick Preview
```bash
# See first 5 files
tgdl download -c 1234567890 --limit 5
```

#### Test Filters
```bash
# Test if filter works
tgdl download -c 1234567890 -v --max-size 10MB --limit 3
```

#### Storage Budget
```bash
# Get 20 videos under 50MB
tgdl download -c 1234567890 -v --max-size 50MB --limit 20
```

#### Sample Collection
```bash
# 10 random photos
tgdl download -c 1234567890 -p --limit 10
```

---

## Combining Filters

### Filter Execution Order

1. **Message ID range** - Which messages to consider
2. **Media type** - Filter by photo/video/audio/document
3. **File size** - Filter by size constraints
4. **Limit** - Take first N after all filters

### Common Combinations

#### Small Photos Only
```bash
tgdl download -c 1234567890 -p --max-size 5MB
```

#### Recent Large Videos
```bash
# Last 50 messages, videos over 100MB
tgdl download -c 1234567890 --min-id 1950 -v --min-size 100MB
```

#### Limited Music Collection
```bash
# First 50 audio files under 10MB
tgdl download -c 1234567890 -a --max-size 10MB --limit 50
```

#### Specific Range, Specific Type
```bash
# Messages 100-200, videos only, under 50MB
tgdl download -c 1234567890 --min-id 100 --max-id 200 -v --max-size 50MB
```

#### Everything Except Large Videos
```bash
# Photos, audio, documents, and small videos
tgdl download -c 1234567890 -p -a -d
tgdl download -c 1234567890 -v --max-size 10MB
```

### Complex Filter Examples

#### High-Quality Recent Videos
```bash
# Last 100 messages, videos, 50-500MB (HD quality)
tgdl download -c 1234567890 \
  --min-id 1900 \
  -v \
  --min-size 50MB \
  --max-size 500MB \
  --limit 20
```

#### Quick Photo Gallery
```bash
# First 50 photos under 2MB
tgdl download -c 1234567890 \
  -p \
  --max-size 2MB \
  --limit 50 \
  -o ~/Pictures/Gallery
```

#### Document Archive (No Large Files)
```bash
# All documents under 100MB
tgdl download -c 1234567890 \
  -d \
  --max-size 100MB \
  -o ~/Documents/Archive
```

#### Music Playlist
```bash
# 100 audio files, 2-10MB each
tgdl download -c 1234567890 \
  -a \
  --min-size 2MB \
  --max-size 10MB \
  --limit 100 \
  -o ~/Music/Telegram
```

---

## Filter Performance

### Fast Filters

**These are checked before download:**
- Message ID range
- Media type
- File size

**Result:** Very fast, no bandwidth wasted

### Example

```bash
tgdl download -c 1234567890 -v --max-size 10MB
```

**Process:**
1. Fetch message list (fast)
2. Filter: Keep only video messages
3. Filter: Check size (from message metadata)
4. Download only matching files

**Advantage:** Doesn't download files to check size!

---

## Filter Tips

### 1. Start Broad, Then Narrow

!!! tip "Iterative Filtering"
    ```bash
    # Step 1: See what's there
    tgdl channels
    
    # Step 2: Small test
    tgdl download -c 1234567890 --limit 5
    
    # Step 3: Check file types
    ls downloads/entity_1234567890/
    
    # Step 4: Apply appropriate filter
    tgdl download -c 1234567890 -v --max-size 100MB
    ```

### 2. Use Limit for Testing

!!! tip "Test First"
    ```bash
    # Test filter with limit
    tgdl download -c 1234567890 -v --max-size 50MB --limit 3
    
    # If results look good, run full download
    tgdl download -c 1234567890 -v --max-size 50MB
    ```

### 3. Combine Size and Type

!!! tip "Precision Filtering"
    ```bash
    # Instead of downloading all then deleting
    tgdl download -c 1234567890 -v --max-size 100MB
    
    # Better than:
    # tgdl download -c 1234567890
    # (then manually delete non-videos and large files)
    ```

### 4. Use Range for Updates

!!! tip "Incremental Downloads"
    ```bash
    # First run: Get everything
    tgdl download -c 1234567890
    # Downloads messages 1-1000, progress saved
    
    # Later: Get new content only
    tgdl download -c 1234567890
    # Automatically gets messages 1001+
    ```

### 5. Budget Your Storage

!!! tip "Calculate Before Downloading"
    ```bash
    # Want ~1GB of content
    # Max 20MB per file
    # = ~50 files
    
    tgdl download -c 1234567890 --max-size 20MB --limit 50
    ```

---

## Filter Troubleshooting

### No Files Downloaded

**Symptom:**
```
⚠ No files downloaded.
```

**Possible causes:**

1. **Filters too restrictive**
   ```bash
   # Try without filters
   tgdl download -c 1234567890 --limit 5
   ```

2. **No media in range**
   ```bash
   # Try broader range
   tgdl download -c 1234567890 --min-id 1
   ```

3. **Wrong media type**
   ```bash
   # Try all types
   tgdl download -c 1234567890
   ```

4. **Size constraint too strict**
   ```bash
   # Try without size limits
   tgdl download -c 1234567890 --limit 5
   ```

### Unexpected File Types

**Symptom:** Got documents instead of videos

**Cause:** Telegram categorization

**Solution:**
```bash
# Be explicit with type
tgdl download -c 1234567890 -v  # Videos only

# Or check media info
tgdl download -c 1234567890 --limit 1
ls -lh downloads/entity_1234567890/
```

### Size Limit Not Working

**Symptom:** Downloaded files larger than max-size

**Cause:** Size in message metadata may differ slightly

**Note:** tgdl uses size from Telegram's metadata, which is usually accurate but may have small variations.

---

## Filter Reference

### Quick Reference Table

| Filter | Flag | Example | Effect |
|--------|------|---------|--------|
| Photos | `-p` | `tgdl download -c ID -p` | Only photos |
| Videos | `-v` | `tgdl download -c ID -v` | Only videos |
| Audio | `-a` | `tgdl download -c ID -a` | Only audio |
| Documents | `-d` | `tgdl download -c ID -d` | Only documents |
| Max Size | `--max-size` | `--max-size 100MB` | Files ≤ 100MB |
| Min Size | `--min-size` | `--min-size 10MB` | Files ≥ 10MB |
| Min ID | `--min-id` | `--min-id 100` | Messages ≥ 100 |
| Max ID | `--max-id` | `--max-id 200` | Messages ≤ 200 |
| Limit | `--limit` | `--limit 50` | First 50 files |

### Filter Combinations

```bash
# Template
tgdl download \
  -c|g|b ID \
  [-p] [-v] [-a] [-d] \
  [--min-size SIZE] [--max-size SIZE] \
  [--min-id ID] [--max-id ID] \
  [--limit N]
```

**Examples:**
```bash
# Photos under 5MB, first 20
tgdl download -c 1234567890 -p --max-size 5MB --limit 20

# Videos in range, 10-100MB
tgdl download -c 1234567890 -v --min-id 100 --max-id 200 --min-size 10MB --max-size 100MB

# Everything except videos, under 50MB
tgdl download -c 1234567890 -p -a -d --max-size 50MB
```

---

## Next Steps

- [Learn about message ID ranges](message-ranges.md)
- [See advanced usage examples](advanced-usage.md)
- [Full command reference](command-reference.md)
- [Troubleshooting common issues](troubleshooting.md)
