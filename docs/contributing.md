# Contributing to tgdl

Thank you for your interest in contributing to tgdl! This guide will help you get started.

## Ways to Contribute

### 1. Report Bugs

Found a bug? Please report it!

**Before reporting:**
- Check [existing issues](https://github.com/kavidu-dilhara/tgdl/issues)
- Update to latest version: `pip install --upgrade tgdl`
- Read [troubleshooting guide](troubleshooting.md)

**When reporting:**
1. Go to [GitHub Issues](https://github.com/kavidu-dilhara/tgdl/issues/new)
2. Use clear, descriptive title
3. Include:
   - tgdl version (`pip show tgdl`)
   - Python version (`python --version`)
   - Operating system
   - Complete error message
   - Steps to reproduce
   - Expected vs actual behavior

**Example:**
```markdown
## Bug: Download fails with FloodWaitError

**Environment:**
- tgdl version: 1.1.4
- Python version: 3.9.7
- OS: Ubuntu 22.04

**Steps to reproduce:**
1. Run `tgdl download -c 1234567890 --concurrent 20`
2. After ~100 files, error occurs

**Error message:**
```
FloodWaitError: A wait of 300 seconds is required
```

**Expected:** Download should handle rate limits gracefully
**Actual:** Download stops with error

**Additional context:**
This happens consistently with --concurrent values above 15.
```

### 2. Suggest Features

Have an idea for improvement?

**Before suggesting:**
- Check [existing issues](https://github.com/kavidu-dilhara/tgdl/issues)
- Consider if it fits tgdl's scope (CLI tool for media downloads)

**When suggesting:**
1. Open a [feature request](https://github.com/kavidu-dilhara/tgdl/issues/new)
2. Describe the feature clearly
3. Explain the use case
4. Provide examples

**Example:**
```markdown
## Feature Request: Schedule downloads with built-in scheduler

**Use case:**
Currently users must set up cron/Task Scheduler manually. Built-in scheduling would be more user-friendly.

**Proposed solution:**
```bash
tgdl schedule add --cron "0 2 * * *" --channel 1234567890
tgdl schedule list
tgdl schedule remove <id>
```

**Alternatives considered:**
- External cron (current solution - less user-friendly)
- Config file with schedules

**Additional context:**
This would be especially helpful for Windows users who may not be familiar with Task Scheduler.
```

### 3. Improve Documentation

Documentation improvements are always welcome!

**What needs docs:**
- Clarification of existing features
- Common use cases and examples
- Platform-specific instructions
- Screenshots/GIFs
- Translation to other languages

**How to contribute docs:**
1. Fork repository
2. Edit files in `docs/` directory
3. Preview locally: `mkdocs serve`
4. Submit pull request

### 4. Write Code

Ready to code? Great!

**Types of contributions welcome:**
- Bug fixes
- New features (discuss in issue first)
- Performance improvements
- Code refactoring
- Test coverage
- Type hints

---

## Development Setup

### Prerequisites

- Python 3.7 or higher
- pip
- git
- (Optional) virtualenv or venv

### Fork and Clone

1. **Fork the repository** on GitHub

2. **Clone your fork:**
   ```bash
   git clone https://github.com/kavidu-dilhara/tgdl.git
   cd tgdl
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/kavidu-dilhara/tgdl.git
   ```

### Setup Virtual Environment

**Create virtual environment:**
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

**Install in development mode:**
```bash
# Install package in editable mode with dev dependencies
pip install -e .

# Or install from requirements
pip install -r requirements.txt
```

### Install Development Tools

```bash
# Code formatting
pip install black

# Linting
pip install flake8 pylint

# Type checking
pip install mypy

# Testing
pip install pytest pytest-asyncio pytest-cov
```

---

## Code Guidelines

### Style Guide

**Follow PEP 8:**
- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black default)
- Use meaningful variable names
- Add docstrings to functions/classes

**Format code with Black:**
```bash
black tgdl/
```

**Check with flake8:**
```bash
flake8 tgdl/ --max-line-length=88 --extend-ignore=E203
```

### Code Structure

```
tgdl/
├── __init__.py       # Package initialization, version
├── __main__.py       # Entry point
├── cli.py            # Click CLI commands
├── auth.py           # Authentication logic
├── downloader.py     # Download logic
├── list.py           # List entities logic
├── config.py         # Configuration management
├── crypto.py         # Encryption utilities (if exists)
└── utils.py          # Utility functions (if exists)
```

**Module responsibilities:**
- `cli.py` - User-facing commands, CLI interface
- `auth.py` - Login, logout, session management
- `downloader.py` - Core download logic, file operations
- `list.py` - Fetching and displaying entities
- `config.py` - Reading/writing config files
- `crypto.py` - Encryption/decryption utilities
- `utils.py` - Shared helper functions

### Code Patterns

**Async functions:**
```python
async def download_file(client, message):
    """Download a single file from message."""
    try:
        path = await client.download_media(message)
        return path
    except Exception as e:
        click.echo(f"✗ Error: {e}")
        return None
```

**Error handling:**
```python
# Use specific exceptions
try:
    config = load_config()
except FileNotFoundError:
    click.echo("✗ Config file not found")
    return
except json.JSONDecodeError:
    click.echo("✗ Invalid config file")
    return
except Exception as e:
    click.echo(f"✗ Unexpected error: {e}")
    return
```

**Click commands:**
```python
@click.command()
@click.option('-c', '--channel', type=int, help='Channel ID')
@click.option('-v', '--videos', is_flag=True, help='Download videos only')
def download(channel, videos):
    """Download media from channel."""
    # Implementation
```

### Documentation

**Docstrings for functions:**
```python
def download_from_entity(client, entity_id, limit=None):
    """
    Download media files from a Telegram entity.
    
    Args:
        client: Telethon TelegramClient instance
        entity_id: ID of channel, group, or bot
        limit: Maximum number of files to download (None = all)
        
    Returns:
        Number of files successfully downloaded
        
    Raises:
        ValueError: If entity_id is invalid
        ConnectionError: If connection to Telegram fails
    """
    pass
```

**Comments for complex logic:**
```python
# Calculate start_id for inclusive min_msg_id
# Telethon's min_id is exclusive, so we subtract 1
# to include the min_msg_id message itself
start_id = min_msg_id - 1 if min_msg_id else 0
```

### Type Hints

**Use type hints where helpful:**
```python
from typing import Optional, List, Set
from telethon import TelegramClient

async def get_downloaded_ids(directory: str) -> Set[int]:
    """Get set of already downloaded message IDs."""
    ids: Set[int] = set()
    # Implementation
    return ids

def format_size(size: int) -> str:
    """Format bytes to human-readable size."""
    units: List[str] = ['B', 'KB', 'MB', 'GB', 'TB']
    # Implementation
    return f"{size:.2f} {unit}"
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tgdl

# Run specific test file
pytest tests/test_downloader.py

# Run specific test
pytest tests/test_downloader.py::test_file_naming
```

### Writing Tests

**Test file structure:**
```
tests/
├── __init__.py
├── test_auth.py
├── test_cli.py
├── test_config.py
├── test_downloader.py
└── test_list.py
```

**Example test:**
```python
import pytest
from tgdl.downloader import extract_message_id_from_filename

def test_extract_message_id():
    """Test message ID extraction from filenames."""
    assert extract_message_id_from_filename("12345.jpg") == 12345
    assert extract_message_id_from_filename("67890.mp4") == 67890
    assert extract_message_id_from_filename("invalid.jpg") is None

@pytest.mark.asyncio
async def test_download_single_file():
    """Test single file download."""
    # Mock Telethon client
    # Test download logic
    pass
```

### Test Guidelines

- Write tests for new features
- Update tests for bug fixes
- Aim for high coverage (>80%)
- Use mocks for Telegram API calls
- Test both success and failure cases

---

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code follows style guide
- [ ] Formatted with Black
- [ ] Passes flake8 checks
- [ ] Includes docstrings
- [ ] Tests added/updated
- [ ] Tests pass locally
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated
- [ ] Commit messages are clear

### Commit Messages

**Format:**
```
<type>: <short summary>

<detailed description>

<issue reference>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process, dependencies

**Examples:**
```
feat: Add support for message ID range filtering

Implement --min-id and --max-id options to allow downloading
specific message ranges from channels and groups.

Fixes #42
```

```
fix: Prevent duplicate downloads with message ID tracking

Changed from filename-based to message ID-based duplicate detection
to handle Telethon's filename variations.

Fixes #38
```

### Creating Pull Request

1. **Create feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "feat: Add new feature"
   ```

3. **Update from upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

4. **Push to your fork:**
   ```bash
   git push origin feature/my-feature
   ```

5. **Open pull request on GitHub**

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added (if applicable)
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] CHANGELOG.md updated

## Related Issues
Fixes #(issue number)
```

---

## Release Process

(For maintainers)

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

**Examples:**
- `1.0.0` → `1.0.1`: Bug fix
- `1.0.1` → `1.1.0`: New feature
- `1.1.0` → `2.0.0`: Breaking change

### Release Steps

1. **Update version:**
   ```python
   # tgdl/__init__.py
   __version__ = "1.2.0"
   ```
   
   ```toml
   # pyproject.toml
   version = "1.2.0"
   ```
   
   ```python
   # setup.py
   version="1.2.0"
   ```

2. **Update CHANGELOG.md:**
   ```markdown
   ## [1.2.0] - 2025-12-25
   
   ### Added
   - New feature X
   - New feature Y
   
   ### Fixed
   - Bug fix A
   - Bug fix B
   
   ### Changed
   - Improvement C
   ```

3. **Commit changes:**
   ```bash
   git add .
   git commit -m "chore: Bump version to 1.2.0"
   ```

4. **Create tag:**
   ```bash
   git tag -a v1.2.0 -m "Release version 1.2.0"
   ```

5. **Push to GitHub:**
   ```bash
   git push origin main
   git push origin v1.2.0
   ```

6. **Build and upload to PyPI:**
   ```bash
   # Build
   python -m build
   
   # Upload to PyPI
   python -m twine upload dist/*
   ```

7. **Create GitHub Release:**
   - Go to GitHub Releases
   - Create release from tag
   - Add release notes from CHANGELOG

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project harassment-free for everyone.

### Our Standards

**Positive behavior:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Accepting constructive criticism gracefully
- Focusing on what's best for the community
- Showing empathy towards others

**Unacceptable behavior:**
- Harassment or discriminatory language
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information
- Other unprofessional conduct

### Enforcement

Report unacceptable behavior to project maintainers.
All complaints will be reviewed and investigated.

---

## Getting Help

### Questions?

- Check [FAQ](faq.md)
- Read [Documentation](index.md)
- Search [GitHub Issues](https://github.com/kavidu-dilhara/tgdl/issues)
- Ask in [Discussions](https://github.com/kavidu-dilhara/tgdl/discussions)

### Stuck on Development?

- Comment on the relevant issue
- Ask in pull request
- Reach out to maintainers

---

## Recognition

Contributors are recognized:
- In CHANGELOG.md
- In GitHub contributors page
- In project README.md

Thank you for contributing to tgdl! 🎉

---

## Quick Start for Contributors

```bash
# 1. Fork and clone
git clone https://github.com/kavidu-dilhara/tgdl.git
cd tgdl

# 2. Setup environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .
pip install black flake8 pytest

# 3. Create branch
git checkout -b feature/my-feature

# 4. Make changes
# ... edit code ...

# 5. Format and test
black tgdl/
flake8 tgdl/
pytest

# 6. Commit and push
git add .
git commit -m "feat: Add my feature"
git push origin feature/my-feature

# 7. Open pull request on GitHub
```

---

## Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Telethon Documentation](https://docs.telethon.dev/)
- [Click Documentation](https://click.palletsprojects.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Semantic Versioning](https://semver.org/)

---

## Thank You!

Your contributions make tgdl better for everyone. We appreciate your time and effort! 💙
