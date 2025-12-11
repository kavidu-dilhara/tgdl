"""Authentication module for tgdl."""

import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, ApiIdInvalidError
from tgdl.config import get_config
import click


async def login_user(api_id: int, api_hash: str, phone: str) -> bool:
    """
    Authenticate user with Telegram.
    
    Args:
        api_id: Telegram API ID
        api_hash: Telegram API hash
        phone: Phone number with country code
        
    Returns:
        True if login successful, False otherwise
    """
    config = get_config()
    session_path = config.get_session_path()
    
    try:
        client = TelegramClient(session_path, api_id, api_hash)
        await client.connect()
        
        # Check if already authorized
        if await client.is_user_authorized():
            me = await client.get_me()
            click.echo(click.style(f"\n✓ Already logged in as {me.first_name} (ID: {me.id})", fg='green'))
            await client.disconnect()
            return True
        
        # Send code request
        click.echo(f"\nSending verification code to {phone}...")
        await client.send_code_request(phone)
        
        # Get code from user
        try:
            code = click.prompt("\nEnter the verification code you received", type=str)
        except (click.Abort, KeyboardInterrupt):
            click.echo(click.style("\n\n⚠ Login cancelled.", fg='yellow'))
            await client.disconnect()
            return False
        
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            # Two-factor authentication enabled
            try:
                password = click.prompt("\nTwo-factor authentication enabled. Enter your password", 
                                       type=str, hide_input=True)
            except (click.Abort, KeyboardInterrupt):
                click.echo(click.style("\n\n⚠ Login cancelled.", fg='yellow'))
                await client.disconnect()
                return False
            await client.sign_in(password=password)
        except PhoneCodeInvalidError:
            click.echo(click.style("\n✗ Invalid code. Please try again.", fg='red'))
            await client.disconnect()
            return False
        
        # Confirm successful login
        me = await client.get_me()
        click.echo(click.style(f"\n✓ Successfully logged in as {me.first_name} (ID: {me.id})", fg='green'))
        
        # Save credentials
        config.set_api_credentials(api_id, api_hash)
        
        await client.disconnect()
        return True
        
    except ApiIdInvalidError:
        click.echo(click.style("\n✗ Invalid API ID or API Hash", fg='red'))
        return False
    except (click.Abort, KeyboardInterrupt):
        click.echo(click.style("\n\n⚠ Login cancelled.", fg='yellow'))
        return False
    except Exception as e:
        click.echo(click.style(f"\n✗ Login failed: {e}", fg='red'))
        return False


def get_authenticated_client():
    """
    Get authenticated Telegram client.
    
    Returns:
        TelegramClient instance or None if not authenticated
    """
    config = get_config()
    
    api_id, api_hash = config.get_api_credentials()
    
    if not api_id or not api_hash:
        click.echo(click.style("✗ Not logged in. Run 'tgdl login' first.", fg='red'))
        return None
    
    if not config.is_authenticated():
        click.echo(click.style("✗ Session expired. Run 'tgdl login' again.", fg='red'))
        return None
    
    session_path = config.get_session_path()
    return TelegramClient(session_path, api_id, api_hash)


async def check_auth() -> bool:
    """
    Check if user is authenticated.
    
    Returns:
        True if authenticated, False otherwise
    """
    client = get_authenticated_client()
    if not client:
        return False
    
    try:
        await client.connect()
        is_auth = await client.is_user_authorized()
        await client.disconnect()
        return is_auth
    except Exception:
        try:
            await client.disconnect()
        except Exception:
            pass
        return False
