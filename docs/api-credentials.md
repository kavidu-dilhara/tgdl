# Getting API Credentials

To use tgdl, you need Telegram API credentials. This guide will walk you through obtaining them.

## Why API Credentials Are Needed

Telegram requires all third-party applications to authenticate using:

- **API ID** - A unique numeric identifier
- **API Hash** - A secret key associated with the API ID

These credentials allow tgdl to connect to Telegram's servers securely on your behalf.

!!! info "Security Note"
    Your API credentials are stored locally in encrypted format and never shared with anyone.

## Step-by-Step Guide

### Step 1: Visit Telegram's API Development Tools

Go to: **[https://my.telegram.org/apps](https://my.telegram.org/apps)**

### Step 2: Log In

1. Enter your phone number (with country code)
2. Click "Next"
3. Enter the verification code sent to your Telegram app
4. If you have two-factor authentication (2FA), enter your password

### Step 3: Create an Application

If this is your first time:

1. Click "Create new application"
2. Fill in the application details:
   
   | Field | What to Enter | Example |
   |-------|---------------|---------|
   | **App title** | Any name for your app | `My Media Downloader` |
   | **Short name** | Short version (5-32 chars) | `downloader` |
   | **Platform** | Select **Desktop** | Desktop |
   | **Description** | Brief description (optional) | `Personal media downloader` |

3. Click "Create application"

!!! tip "Field Requirements"
    - App title: Can be anything descriptive
    - Short name: 5-32 characters, lowercase, no spaces
    - Platform: Always choose "Desktop" for CLI tools

### Step 4: Get Your Credentials

After creating the app, you'll see:

```
App api_id: 12345678
App api_hash: 0123456789abcdef0123456789abcdef
```

!!! warning "Keep These Secret!"
    - **Never share** your API hash publicly
    - **Don't commit** them to public repositories
    - **Don't screenshot** and share online
    
    These credentials give access to your Telegram account!

### Step 5: Save Your Credentials

Copy both values - you'll need them when running `tgdl login`.

## Using Your Credentials

When you run `tgdl login` for the first time, you'll be prompted:

```bash
$ tgdl login

🔐 Telegram Login
Get your API credentials from: https://my.telegram.org/apps

Telegram API ID: 12345678
Telegram API Hash: 0123456789abcdef0123456789abcdef
Phone number (with country code): +1234567890
```

tgdl will:

1. Encrypt your credentials
2. Store them securely in `~/.tgdl/config.json`
3. Use them for all future connections

## Security & Privacy

### How tgdl Protects Your Credentials

1. **Encryption** - API credentials are encrypted using industry-standard Fernet encryption
2. **Local Storage** - Stored only on your computer, never sent anywhere
3. **Permission Protected** - Configuration files have restricted file permissions

### File Locations

Your credentials are stored in:

=== "Linux/macOS"
    ```
    ~/.tgdl/config.json     # Encrypted credentials
    ~/.tgdl/.key            # Encryption key
    ~/.tgdl/tgdl.session    # Telegram session
    ```

=== "Windows"
    ```
    C:\Users\<YourUsername>\.tgdl\config.json     # Encrypted credentials
    C:\Users\<YourUsername>\.tgdl\.key            # Encryption key
    C:\Users\<YourUsername>\.tgdl\tgdl.session    # Telegram session
    ```

### What Telegram Can See

When using API credentials:

- ✅ Telegram knows you're using a third-party application
- ✅ Your account remains secure
- ❌ tgdl developers **cannot** see your credentials
- ❌ tgdl **never** sends your credentials anywhere

## Common Questions

??? question "Can I use the same API credentials on multiple devices?"
    Yes! The same API ID and Hash can be used on multiple devices. However, each device will have its own session.

??? question "Do API credentials expire?"
    No, API credentials don't expire unless you manually delete your application from my.telegram.org/apps.

??? question "Can I change my API credentials later?"
    Yes. Run `tgdl logout` then `tgdl login` with new credentials.

??? question "What if I lose my API credentials?"
    You can retrieve them anytime from [my.telegram.org/apps](https://my.telegram.org/apps) by logging in.

??? question "Will using API credentials ban my account?"
    No. Using official API credentials is completely legitimate and supported by Telegram.

??? question "Can I use someone else's API credentials?"
    While technically possible, it's **not recommended**. Always use your own credentials for security and privacy.

## Troubleshooting

### Error: Invalid API ID or API Hash

**Causes:**
- Typo in API ID or Hash
- Extra spaces in the credentials
- Using wrong credentials

**Solution:**
1. Double-check your credentials at [my.telegram.org/apps](https://my.telegram.org/apps)
2. Copy-paste carefully without extra spaces
3. Make sure API ID is numeric only

### Error: Application not found

**Solution:**
Create a new application at [my.telegram.org/apps](https://my.telegram.org/apps).

### Can't access my.telegram.org

**Possible reasons:**
- Network restrictions
- Regional blocking
- Browser issues

**Solutions:**
1. Try a different browser
2. Clear browser cache
3. Use VPN if regionally blocked
4. Try from Telegram mobile app settings

## Next Steps

Now that you have your API credentials:

1. [Complete the quick start guide](quick-start.md)
2. [Learn about authentication](authentication.md)
3. [Start downloading media](commands.md)

---

!!! success "Ready to Proceed!"
    With your API credentials ready, you can now authenticate tgdl and start downloading!
