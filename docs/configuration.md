# Configuration Reference

Detailed information about tgdl configuration files and settings.

## Configuration Directory

### Location

**Linux/macOS:**
```
~/.tgdl/
```

**Windows:**
```
%USERPROFILE%\.tgdl\
```

**Example paths:**
- Linux: `/home/username/.tgdl/`
- macOS: `/Users/username/.tgdl/`
- Windows: `C:\Users\username\.tgdl\`

### Directory Structure

```
~/.tgdl/
├── config.json          # Encrypted API credentials
├── .key                 # Encryption key for config
├── tgdl.session         # Telegram session file
├── tgdl.session-journal # Session journal (temporary)
└── progress.json        # Download progress tracking
```

---

## Configuration Files

### config.json

**Purpose:** Stores encrypted API credentials

**Created:** On first `tgdl login`

**Format:** JSON with encrypted values

**Example structure:**
```json
{
  "api_id": "encrypted_value_here",
  "api_hash": "encrypted_value_here"
}
```

!!! warning "Encrypted"
    Values are encrypted using Fernet encryption. Don't try to edit manually.

**To change credentials:**
```bash
tgdl logout
tgdl login
# Enter new credentials
```

**Permissions:**
```bash
# Linux/macOS - should be readable only by you
chmod 600 ~/.tgdl/config.json
```

**Backup:**
```bash
# Backup (won't work without .key file)
cp ~/.tgdl/config.json ~/.tgdl/config.json.backup
```

---

### .key

**Purpose:** Encryption key for config.json

**Created:** Automatically on first `tgdl login`

**Format:** Binary file

**Security:**
- Required to decrypt config.json
- Unique per installation
- Should never be shared

!!! danger "Critical File"
    If you lose `.key`, you'll lose access to your encrypted credentials.
    You'll need to logout and login again.

**Permissions:**
```bash
# Linux/macOS - readable only by you
chmod 600 ~/.tgdl/.key
```

**Do NOT:**
- Share this file
- Commit to version control
- Move without config.json

---

### tgdl.session

**Purpose:** Telegram session data

**Created:** On successful login

**Format:** SQLite database (Telethon format)

**Contains:**
- Authorization key
- Server information
- Entity cache

**Size:** Usually a few KB, grows with cached entities

**Security:**
- Access to this file = access to your Telegram account
- Keep it private
- Don't share or commit to version control

**Permissions:**
```bash
# Linux/macOS - readable only by you
chmod 600 ~/.tgdl/tgdl.session
```

**Session lifespan:**
- Usually persists until explicitly logged out
- Telegram may revoke after long inactivity (rare)
- Can be revoked from Telegram app settings

**Backup:**
```bash
# Backup session
cp ~/.tgdl/tgdl.session ~/.tgdl/tgdl.session.backup

# Restore
cp ~/.tgdl/tgdl.session.backup ~/.tgdl/tgdl.session
```

**Related files:**
- `tgdl.session-journal` - Temporary file, auto-managed by SQLite

---

### progress.json

**Purpose:** Track last downloaded message ID per entity

**Created:** After first successful download

**Format:** JSON

**Example:**
```json
{
  "1234567890": 12345,
  "9876543210": 54321,
  "1122334455": 99999
}
```

**Structure:**
```json
{
  "entity_id": last_message_id
}
```

**How it works:**

1. **First download:**
   ```bash
   tgdl download -c 1234567890
   # Downloads messages 1-1000
   # progress.json: {"1234567890": 1000}
   ```

2. **Second download:**
   ```bash
   tgdl download -c 1234567890
   # Reads progress.json, sees last was 1000
   # Downloads messages 1001+ only
   ```

**Manual editing:**

You can edit this file manually:

```json
{
  "1234567890": 0
}
```

This will restart downloads from the beginning for that entity.

**Reset progress:**
```bash
# Reset all
echo "{}" > ~/.tgdl/progress.json

# Reset specific entity
# Edit progress.json and remove or change the entry
```

**Backup:**
```bash
# Before major operations
cp ~/.tgdl/progress.json ~/.tgdl/progress.json.backup

# Restore if needed
cp ~/.tgdl/progress.json.backup ~/.tgdl/progress.json
```

---

## Encryption Details

### How Credentials Are Encrypted

tgdl uses **Fernet symmetric encryption** (from Python's cryptography library):

1. **Key generation:**
   - Random 256-bit key generated
   - Stored in `.key` file

2. **Encryption:**
   - API ID and Hash encrypted using key
   - Stored in `config.json`

3. **Decryption:**
   - Key read from `.key`
   - Values decrypted when needed

**Security properties:**
- Strong encryption (AES 128 in CBC mode)
- Authenticated encryption (prevents tampering)
- Timestamp included (prevents replay attacks)

**Limitations:**
- Security depends on `.key` file protection
- If someone has both `.key` and `config.json`, they can decrypt

**Best practices:**
- Set proper file permissions (600)
- Don't share `.key` file
- Regular backups (but keep secure)

---

## Environment Variables

tgdl currently does not support environment variables for configuration.

All configuration must be:
- Provided interactively during `tgdl login`
- Stored in `~/.tgdl/` directory

**Future possibility:**
Could add support for:
```bash
export TGDL_API_ID="12345"
export TGDL_API_HASH="abc123"
export TGDL_SESSION_DIR="/custom/path"
```

This is not currently implemented.

---

## Configuration Management

### Check Current Configuration

```bash
tgdl status
```

**Output shows:**
- Authentication status
- User information
- Configuration file locations
- API credentials (masked)

**Example:**
```
✓ You are logged in!

📋 Configuration Details:
User: John Doe (+11234567890)
API ID: 12345
API Hash: abc***xyz
Session: /home/user/.tgdl/tgdl.session
Config: /home/user/.tgdl/config.json
```

### Backup Configuration

**Full backup:**
```bash
# Create backup directory
mkdir -p ~/tgdl_backup

# Backup all config files
cp ~/.tgdl/config.json ~/tgdl_backup/
cp ~/.tgdl/.key ~/tgdl_backup/
cp ~/.tgdl/tgdl.session* ~/tgdl_backup/
cp ~/.tgdl/progress.json ~/tgdl_backup/
```

**Restore:**
```bash
# Restore from backup
cp ~/tgdl_backup/* ~/.tgdl/
```

!!! warning "Backup Security"
    Keep backups secure! They contain:
    - Encrypted credentials (but with encryption key)
    - Active session (full account access)
    - Download history

### Reset Configuration

**Complete reset:**
```bash
# Remove all config (downloads stay safe)
rm -rf ~/.tgdl/

# Login again
tgdl login
```

**Partial reset:**
```bash
# Reset only session (keep progress)
rm ~/.tgdl/tgdl.session*
tgdl login

# Reset only progress (keep session)
echo "{}" > ~/.tgdl/progress.json
```

### Migrate Configuration

**To new machine:**

1. **On old machine:**
   ```bash
   # Backup config
   tar czf tgdl_config.tar.gz ~/.tgdl/
   ```

2. **Transfer `tgdl_config.tar.gz` to new machine**

3. **On new machine:**
   ```bash
   # Install tgdl
   pip install tgdl
   
   # Extract config
   tar xzf tgdl_config.tar.gz -C ~/
   
   # Test
   tgdl status
   ```

**Between different OSes:**

Session files are portable between Linux/macOS/Windows, but paths differ:
- Linux/macOS: `~/.tgdl/`
- Windows: `%USERPROFILE%\.tgdl\`

Copy files to appropriate location on target OS.

---

## File Permissions

### Recommended Permissions

**Linux/macOS:**
```bash
# Configuration directory
chmod 700 ~/.tgdl/

# Sensitive files
chmod 600 ~/.tgdl/config.json
chmod 600 ~/.tgdl/.key
chmod 600 ~/.tgdl/tgdl.session*

# Progress file (less sensitive)
chmod 644 ~/.tgdl/progress.json
```

**Windows:**
- Use NTFS permissions
- Restrict to your user account only
- Remove inheritance from parent folders

**Check permissions:**
```bash
# Linux/macOS
ls -la ~/.tgdl/

# Expected output:
# drwx------  .tgdl/
# -rw-------  config.json
# -rw-------  .key
# -rw-------  tgdl.session
# -rw-r--r--  progress.json
```

---

## Security Best Practices

### 1. Protect Configuration Files

!!! danger "Critical"
    - Never share `config.json` + `.key` together
    - Never share `tgdl.session` files
    - Never commit to version control

**Add to `.gitignore`:**
```gitignore
.tgdl/
*.session
*.session-journal
config.json
.key
```

### 2. Use Proper Permissions

```bash
# Lock down config directory
chmod 700 ~/.tgdl/
chmod 600 ~/.tgdl/*
```

### 3. Regular Backups

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR=~/tgdl_backups/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR
cp -r ~/.tgdl/ $BACKUP_DIR/
# Encrypt backup
tar czf - $BACKUP_DIR | gpg -c > $BACKUP_DIR.tar.gz.gpg
rm -rf $BACKUP_DIR
```

### 4. Logout on Shared Computers

```bash
# Before leaving shared computer
tgdl logout
```

### 5. Monitor Active Sessions

In Telegram app:
1. Settings → Privacy and Security
2. Active Sessions
3. Review and revoke unknown sessions

### 6. Use Two-Factor Authentication

Enable 2FA in Telegram:
1. Settings → Privacy and Security
2. Two-Step Verification
3. Set password

This adds extra protection even if session is compromised.

---

## Troubleshooting Configuration

### Cannot read config file

**Check permissions:**
```bash
ls -l ~/.tgdl/config.json
```

**Fix:**
```bash
chmod 600 ~/.tgdl/config.json
```

### Config file corrupted

**Symptoms:**
- JSON decode errors
- Decryption errors

**Solution:**
```bash
# Remove corrupted config
rm ~/.tgdl/config.json
rm ~/.tgdl/.key

# Login again
tgdl login
```

### Key file missing

**Symptom:**
```
Error: Encryption key not found
```

**Solution:**
```bash
# Must login again (old config is unrecoverable)
tgdl logout
tgdl login
```

### Session file corrupted

**Symptoms:**
- Session errors
- Authorization errors

**Solution:**
```bash
# Remove session
rm ~/.tgdl/tgdl.session*

# Login again
tgdl login
```

### Progress file corrupted

**Symptoms:**
- JSON decode errors
- Downloads restart from beginning

**Solution:**
```bash
# Reset progress
echo "{}" > ~/.tgdl/progress.json

# Or delete
rm ~/.tgdl/progress.json
```

---

## Advanced Configuration

### Custom Session Location

Not currently supported. Session must be in `~/.tgdl/`.

**Workaround using symlinks:**
```bash
# Create custom directory
mkdir -p /custom/path/tgdl_config

# Remove default location
rm -rf ~/.tgdl

# Create symlink
ln -s /custom/path/tgdl_config ~/.tgdl

# Now tgdl uses custom location
tgdl login
```

### Multiple Configurations

For multiple accounts:

```bash
# Account 1
tgdl login
cp -r ~/.tgdl ~/.tgdl_account1

# Account 2
tgdl logout
tgdl login
cp -r ~/.tgdl ~/.tgdl_account2

# Switch to account 1
rm -rf ~/.tgdl
cp -r ~/.tgdl_account1 ~/.tgdl

# Switch to account 2
rm -rf ~/.tgdl
cp -r ~/.tgdl_account2 ~/.tgdl
```

**Or use shell aliases:**
```bash
# .bashrc or .zshrc
alias tgdl1="cp -r ~/.tgdl_account1 ~/.tgdl && tgdl"
alias tgdl2="cp -r ~/.tgdl_account2 ~/.tgdl && tgdl"
```

---

## Configuration File Examples

### config.json (encrypted)

```json
{
  "api_id": "gAAAAABhxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "api_hash": "gAAAAABhxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

!!! info "Encrypted Values"
    The `gAAAAA...` strings are Fernet-encrypted values. Cannot be decrypted without `.key` file.

### progress.json

```json
{
  "1234567890": 15432,
  "9876543210": 8765,
  "1122334455": 45678
}
```

**Explanation:**
- Channel 1234567890: Last downloaded message ID 15432
- Channel 9876543210: Last downloaded message ID 8765
- Group 1122334455: Last downloaded message ID 45678

**Manual reset example:**
```json
{
  "1234567890": 0,
  "9876543210": 8765,
  "1122334455": 45678
}
```

This will re-download channel 1234567890 from the beginning, while others continue from last position.

---

## Next Steps

- [Learn about authentication](authentication.md)
- [Security best practices](authentication.md#security-best-practices)
- [Troubleshooting guide](troubleshooting.md)
- [FAQ](faq.md)
