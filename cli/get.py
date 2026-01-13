import click
import pyperclip

from handlers.session_handler import SessionHandler


# Session Details Commands
@click.group()
def get():
    """Get session details."""
    pass


@get.command()
def token():
    """Get the session token."""
    try:
        _, token = SessionHandler.get_session_details()
        click.echo(f"Session Token: {token}")
        pyperclip.copy(token)
        click.echo("Token copied to clipboard.")
    except ValueError:
        pass


@get.command()
def ip():
    """Get the session IP address."""
    try:
        ip, _ = SessionHandler.get_session_details()
        click.echo(f"Session IP: {ip}")
        pyperclip.copy(ip)
        click.echo("IP copied to clipboard.")
    except ValueError:
        pass


@get.command()
def keepalive_url():
    """Get the keepalive URL."""
    try:
        ip, token = SessionHandler.get_session_details()
        url = f"http://{ip}/keepalive?{token}"
        click.echo(f"Keepalive URL: {url}")
        pyperclip.copy(url)
        click.echo("Keepalive URL copied to clipboard.")
    except ValueError:
        pass


@get.command()
def logout_url():
    """Get the logout URL."""
    try:
        ip, token = SessionHandler.get_session_details()
        url = f"http://{ip}/logout?{token}"
        click.echo(f"Logout URL: {url}")
        pyperclip.copy(url)
        click.echo("Logout URL copied to clipboard.")
    except ValueError:
        pass
