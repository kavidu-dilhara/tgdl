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
    client = TelegramClient(session_path, api_id, api_hash)

    try:
        await client.connect()

        if await client.is_user_authorized():
            me = await client.get_me()
            click.echo(click.style(f"\n✓ Already logged in as {me.first_name} (ID: {me.id})", fg='green'))
            return True

        click.echo(f"\nSending verification code to {phone}...")
        await client.send_code_request(phone)

        try:
            code = click.prompt("\nEnter the verification code you received", type=str)
        except (click.Abort, KeyboardInterrupt):
            click.echo(click.style("\n\n⚠ Login cancelled.", fg='yellow'))
            return False

        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            try:
                password = click.prompt(
                    "\nTwo-factor authentication enabled. Enter your password",
                    type=str, hide_input=True
                )
            except (click.Abort, KeyboardInterrupt):
                click.echo(click.style("\n\n⚠ Login cancelled.", fg='yellow'))
                return False
            await client.sign_in(password=password)
        except PhoneCodeInvalidError:
            click.echo(click.style("\n✗ Invalid code. Please try again.", fg='red'))
            return False

        me = await client.get_me()
        click.echo(click.style(f"\n✓ Successfully logged in as {me.first_name} (ID: {me.id})", fg='green'))
        config.set_api_credentials(api_id, api_hash)
        return True

    except ApiIdInvalidError:
        # Fix #10: disconnect before returning so the client doesn't leak
        click.echo(click.style("\n✗ Invalid API ID or API Hash", fg='red'))
        return False
    except (click.Abort, KeyboardInterrupt):
        click.echo(click.style("\n\n⚠ Login cancelled.", fg='yellow'))
        return False
    except Exception as e:
        click.echo(click.style(f"\n✗ Login failed: {e}", fg='red'))
        return False
    finally:
        # Fix #10: always disconnect, regardless of which code path exits
        try:
            await client.disconnect()
        except Exception as disc_err:
            import logging
            logging.getLogger(__name__).debug(f"Error disconnecting after login: {disc_err}")


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
        return is_auth
    except Exception:
        return False
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
