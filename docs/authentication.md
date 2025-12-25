# Authentication

Learn about logging in, managing sessions, and security with tgdl.

## Overview

tgdl uses Telegram's official authentication system to access your account securely. This guide covers everything about authentication.

## Login Process

### First Time Login

```bash
tgdl login
```

You'll go through these steps:

1. **API Credentials** - Enter your API ID and Hash
2. **Phone Number** - Your Telegram phone number
3. **Verification Code** - 5-digit code sent to Telegram app
4. **2FA Password** (if enabled) - Your cloud password

### Example Login Flow

```bash
$ tgdl login

🔐 Telegram Login
Get your API credentials from: https://my.telegram.org/apps

Telegram API ID: 12345678
Telegram API Hash: 0123456789abcdef0123456789abcdef
Phone number (with country code): +1234567890

Sending verification code to +1234567890...

Enter the verification code you received: 12345

Two-factor authentication enabled. Enter your password: ********

✓ Successfully logged in as John Doe (ID: 123456789)

✓ Session saved successfully!
You can now use other tgdl commands.
```

## Already Logged In

If you try to login when already authenticated:

```bash
$ tgdl login

🔐 Telegram Login
Get your API credentials from: https://my.telegram.org/apps

✓ You're already logged in as John Doe (ID: 123456789)

Use 'tgdl logout' to logout and login with a different account.
```

## Session Management

### Understanding Sessions

A **session** is a saved authentication state that allows tgdl to access Telegram without logging in every time.

**Session files:**
```
~/.tgdl/tgdl.session           # Main session file
~/.tgdl/tgdl.session-journal   # Session journal
```

!!! info "Session Security"
    - Sessions are encrypted by Telegram
    - They contain authentication tokens
    - Keep them secure and never share

### Check Authentication Status

```bash
tgdl status
```

**Output when logged in:**
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

**Output when not logged in:**
```
📊 tgdl Status

✗ Not authenticated
  Run 'tgdl login' to authenticate

Config directory: /home/user/.tgdl
Session file: /home/user/.tgdl/tgdl.session
Progress file: /home/user/.tgdl/progress.json

API credentials: Not configured
```

## Logout

### Basic Logout

```bash
tgdl logout
```

**What happens:**

1. Shows current logged-in user
2. Asks for confirmation
3. Deletes session files
4. Removes encrypted credentials
5. Optionally clears progress tracking

### Logout Example

```bash
$ tgdl logout

🔓 Logout from Telegram

Currently logged in as: John Doe (ID: 123456789)

Are you sure you want to logout? [y/N]: y

⚠️  Note: Downloaded files will NOT be deleted.
Do you want to clear download progress tracking? (Your files are safe) [y/N]: n

✓ Successfully logged out!
Run 'tgdl login' to login again.

💡 Your downloaded files in 'downloads/' folder are safe.
```

!!! warning "Downloaded Files Are Safe"
    Logging out does **NOT** delete your downloaded files. They remain in the `downloads/` folder.

### What Gets Deleted

When you logout:

✅ **Deleted:**
- Session file (`.tgdl/tgdl.session`)
- Session journal (`.tgdl/tgdl.session-journal`)
- Encrypted credentials (`.tgdl/config.json`)
- Encryption key (`.tgdl/.key`)
- Progress tracking (`.tgdl/progress.json`) - if you choose to

❌ **NOT Deleted:**
- Downloaded media files
- `downloads/` folder

## Security Best Practices

### 1. Protect Your Session Files

**Do:**
- ✅ Keep session files private
- ✅ Use file permissions (Linux/macOS: `chmod 600`)
- ✅ Back up session to secure location
- ✅ Logout when on shared computers

**Don't:**
- ❌ Share session files with anyone
- ❌ Upload to public repositories
- ❌ Store in cloud storage
- ❌ Leave logged in on public computers

### 2. Two-Factor Authentication (2FA)

**Highly Recommended:**

Enable 2FA in Telegram for extra security:

1. Open Telegram app
2. Go to Settings → Privacy and Security
3. Enable Two-Step Verification
4. Set a strong password

Benefits:
- 🔒 Extra protection for your account
- 🔒 Required every time you login with tgdl
- 🔒 Prevents unauthorized access even if someone has your phone

### 3. API Credentials Security

**Remember:**
- Never share your API Hash
- Don't commit to public repos
- Treat them like passwords
- Regenerate if compromised

### 4. Regular Security Checkups

```bash
# Check who's logged in
tgdl status

# Review active sessions in Telegram app
# Settings → Privacy → Active Sessions
```

## Multiple Accounts

### Using Different Accounts

To switch accounts:

1. Logout from current account:
   ```bash
   tgdl logout
   ```

2. Login with different account:
   ```bash
   tgdl login
   ```

!!! note "One Account at a Time"
    tgdl supports one logged-in account at a time. To use multiple accounts, logout and login with different credentials.

### Multiple Installations

For simultaneous use of multiple accounts:

1. Create separate virtual environments
2. Install tgdl in each
3. Each will have separate session files

## Troubleshooting Authentication

### Error: Session Expired

**Symptoms:**
```
✗ Session expired. Run 'tgdl login' again.
```

**Solution:**
```bash
tgdl login
```

**Why it happens:**
- Logged out from other devices
- Changed password
- Session invalidated by Telegram
- Security settings changed

### Error: Invalid Phone Number

**Common issues:**
- Missing country code
- Wrong format
- Extra spaces

**Correct format:**
```
+1234567890  ✅ Correct
1234567890   ❌ Missing +
+1 234 567   ❌ Spaces (may work)
```

### Error: Invalid Verification Code

**Solutions:**
1. Wait for code to arrive (can take 30 seconds)
2. Try "Call me" option in Telegram
3. Check if code expired (60 seconds)
4. Request new code

### Error: Invalid 2FA Password

**Solutions:**
1. Double-check password (case-sensitive)
2. Reset password if forgotten (Telegram app)
3. Disable 2FA temporarily (not recommended)

### Error: Flood Wait

```
✗ Too many login attempts. Try again in X seconds.
```

**Solution:**
Wait for the specified time. Telegram has rate limits to prevent abuse.

## Advanced Topics

### Session Location

Custom session location (for advanced users):

Session files are always stored in:
```
~/.tgdl/  # Linux/macOS
C:\Users\<Username>\.tgdl\  # Windows
```

Cannot be changed (by design for security).

### Credentials Encryption

How tgdl protects your API credentials:

1. **Fernet encryption** - Industry-standard symmetric encryption
2. **Unique key** - Generated per installation
3. **Local storage** - Never transmitted
4. **Secure deletion** - Proper cleanup on logout

### Session Persistence

Sessions typically last:
- **Indefinitely** - Until you logout or invalidate
- **Can expire** - If changed password or logged out elsewhere
- **Revokable** - From Telegram app (Active Sessions)

## FAQ

??? question "Do I need to login every time?"
    No. Once logged in, your session persists until you logout or it expires.

??? question "Can I use tgdl without logging in?"
    No. Authentication is required to access Telegram's API.

??? question "Is my password stored?"
    No. Only your API credentials (encrypted) and session are stored. Your Telegram password is never saved.

??? question "What if I forget my 2FA password?"
    You'll need to reset it through Telegram's account recovery process.

??? question "Can someone access my account with my session file?"
    Yes, if they have your session file, they can access your account. Keep it secure!

??? question "How do I revoke tgdl's access?"
    Go to Telegram app → Settings → Privacy → Active Sessions, and terminate the tgdl session.

## Next Steps

- [Learn basic commands](commands.md)
- [Explore advanced features](advanced-usage.md)
- [Understand configuration](configuration.md)

---

!!! info "Stay Secure"
    Always protect your session files and API credentials. Enable 2FA for maximum security.
