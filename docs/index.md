# tgdl - Telegram Media Downloader

<div align="center">

**High-performance CLI tool for downloading media from Telegram**

[![PyPI version](https://badge.fury.io/py/tgdl.svg)](https://pypi.org/project/tgdl/)
[![Python versions](https://img.shields.io/pypi/pyversions/tgdl.svg)](https://pypi.org/project/tgdl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## Overview

**tgdl** is a powerful command-line tool designed to download media files from Telegram channels, groups, and bot chats with advanced filtering and parallel download capabilities.

## ✨ Key Features

- 🚀 **Fast Parallel Downloads** - Download multiple files simultaneously (configurable concurrency)
- 🎯 **Advanced Filtering** - Filter by media type, file size, and message ID ranges
- 📊 **Smart Resume** - Automatically skip already downloaded files
- 🔒 **Secure** - Encrypted credential storage with industry-standard encryption
- 📝 **Progress Tracking** - Visual progress bars and download statistics
- 🎨 **User-Friendly** - Intuitive CLI with helpful tips and error messages
- 💾 **Efficient** - Track downloads by message ID to prevent duplicates

## 🎯 Use Cases

- **Backup Telegram channels** - Archive important media from channels
- **Media collection** - Download photos, videos, documents from groups
- **Bot downloads** - Retrieve files shared by bots
- **Selective downloading** - Download specific file types or size ranges
- **Range downloads** - Download media from specific message ID ranges

## 🚦 Quick Example

```bash
# Install
pip install tgdl

# Login
tgdl login

# List your channels
tgdl channels

# Download all media from a channel
tgdl download -c 1234567890

# Download only videos with size limit
tgdl download -c 1234567890 -v --max-size 100MB

# Download messages from ID 20 to 100
tgdl download -c 1234567890 --min-id 20 --max-id 100
```

## 📖 Documentation Structure

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } __Installation__

    ---

    Get tgdl installed on your system

    [:octicons-arrow-right-24: Install now](installation.md)

-   :material-rocket-launch:{ .lg .middle } __Quick Start__

    ---

    Start downloading in 5 minutes

    [:octicons-arrow-right-24: Get started](quick-start.md)

-   :material-book-open-variant:{ .lg .middle } __User Guide__

    ---

    Learn all features and options

    [:octicons-arrow-right-24: Read guide](commands.md)

-   :material-help-circle:{ .lg .middle } __Troubleshooting__

    ---

    Common issues and solutions

    [:octicons-arrow-right-24: Get help](troubleshooting.md)

</div>

## ⚡ Why tgdl?

| Feature | tgdl | Manual Download |
|---------|------|----------------|
| Parallel Downloads | ✅ Up to 20+ concurrent | ❌ One at a time |
| Resume Support | ✅ Automatic | ❌ Manual |
| Media Filtering | ✅ Type, size, range | ❌ None |
| Progress Tracking | ✅ Real-time | ❌ None |
| Duplicate Prevention | ✅ Message ID tracking | ❌ Manual checking |
| Automation | ✅ CLI scriptable | ❌ Manual |

## 📋 Requirements

- Python 3.7 or higher
- Telegram account
- API credentials from [my.telegram.org](https://my.telegram.org/apps)

## 🎬 Next Steps

Ready to get started? Follow these steps:

1. [Install tgdl](installation.md)
2. [Get API credentials](api-credentials.md)
3. [Follow the quick start guide](quick-start.md)
4. [Explore advanced features](advanced-usage.md)

## 💡 Support

- 📚 [Documentation](https://kavidu-dilhara.github.io/tgdl/)
- 🐛 [Issue Tracker](https://github.com/kavidu-dilhara/tgdl/issues)
- 💬 [Discussions](https://github.com/kavidu-dilhara/tgdl/discussions)

## 📄 License

tgdl is released under the [MIT License](https://github.com/kavidu-dilhara/tgdl/blob/main/LICENSE).

---

<div align="center">
Made with ❤️ by <a href="https://github.com/kavidu-dilhara">kavidu-dilhara</a>
</div>
