# Installation

This guide will help you install tgdl on your system.

## Requirements

Before installing tgdl, ensure you have:

- **Python 3.7 or higher** installed
- **pip** package manager
- Internet connection

## Installation Methods

### Method 1: Install from PyPI (Recommended)

The easiest way to install tgdl is using pip:

```bash
pip install tgdl
```

### Method 2: Install with pipx (Isolated)

For a cleaner installation that doesn't interfere with system packages:

```bash
# Install pipx first (if not already installed)
pip install pipx
pipx ensurepath

# Install tgdl
pipx install tgdl
```

### Method 3: Install from Source

For the latest development version:

```bash
# Clone the repository
git clone https://github.com/kavidu-dilhara/tgdl.git
cd tgdl

# Install in development mode
pip install -e .
```

## Verify Installation

After installation, verify that tgdl is installed correctly:

```bash
tgdl --version
```

You should see the version number:

```
tgdl, version 1.1.4
```

## Platform-Specific Instructions

=== "Windows"

    **Using Command Prompt or PowerShell:**

    ```powershell
    # Install
    pip install tgdl

    # Verify
    tgdl --version
    ```

    !!! warning "Windows PATH"
        If `tgdl` command is not found, add Python Scripts directory to PATH:
        ```
        C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python3x\Scripts\
        ```

=== "Linux"

    **Using terminal:**

    ```bash
    # Install for current user
    pip install --user tgdl

    # Or system-wide (requires sudo)
    sudo pip install tgdl

    # Verify
    tgdl --version
    ```

    !!! tip "Add to PATH"
        If command not found, add to your `~/.bashrc` or `~/.zshrc`:
        ```bash
        export PATH="$HOME/.local/bin:$PATH"
        ```

=== "macOS"

    **Using terminal:**

    ```bash
    # Install
    pip3 install tgdl

    # Verify
    tgdl --version
    ```

    !!! info "Homebrew Python"
        If using Homebrew Python, pip3 is recommended over pip.

## Virtual Environment (Optional)

For isolated installation:

```bash
# Create virtual environment
python -m venv telegram-downloader
source telegram-downloader/bin/activate  # Linux/macOS
# or
telegram-downloader\Scripts\activate  # Windows

# Install tgdl
pip install tgdl
```

## Updating tgdl

To update to the latest version:

```bash
pip install --upgrade tgdl
```

To update to a specific version:

```bash
pip install tgdl==1.1.4
```

## Uninstallation

To remove tgdl:

```bash
pip uninstall tgdl
```

!!! note "Data Preservation"
    Uninstalling tgdl does NOT delete:
    
    - Your configuration files (`~/.tgdl/`)
    - Your downloaded files (`downloads/`)
    - Your session data
    
    To remove these manually, delete the `.tgdl` folder in your home directory.

## Dependencies

tgdl automatically installs these dependencies:

- **telethon** (>=1.42.0) - Telegram client library
- **click** (>=8.3.0) - CLI framework
- **tqdm** (>=4.67.1) - Progress bars
- **aiofiles** (>=25.1.0) - Async file operations
- **cryptography** (>=43.0.0) - Credential encryption

## Troubleshooting Installation

### Issue: `pip` command not found

**Solution:** Install pip first:

```bash
# Linux/macOS
python -m ensurepip --upgrade

# Windows
py -m ensurepip --upgrade
```

### Issue: Permission denied

**Solution:** Install for user only:

```bash
pip install --user tgdl
```

### Issue: Command not found after installation

**Solution:** Add Python scripts directory to PATH (see platform-specific instructions above).

### Issue: SSL Certificate Error

**Solution:** Update pip and certificates:

```bash
pip install --upgrade pip certifi
```

## Next Steps

Now that tgdl is installed, you need to:

1. [Get Telegram API credentials](api-credentials.md)
2. [Complete the quick start guide](quick-start.md)
3. [Learn about authentication](authentication.md)

---

!!! success "Installation Complete!"
    You're ready to start using tgdl! Continue to the [Quick Start](quick-start.md) guide.
