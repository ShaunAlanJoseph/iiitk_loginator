import requests
import click
from os import remove
from time import sleep
from logging import error, info
from typing import Optional

from config import CHECK_INTERVAL, TOKEN_FILE
from handlers.portal_handler import PortalHandler
from handlers.session_handler import SessionHandler
from handlers.service_handler import ServiceHandler
from cli.credentials import credentials
from cli.get import get
from cli.service import service


@click.group()
@click.option("--android", is_flag=True, help="Run in an Android environment.")
def cli(android: bool):
    import config

    config.ANDROID = android


@cli.command()
def run():
    """Run the IIITK Portal Loginator service in the foreground."""

    import config

    if (
        not config.ANDROID
        and ServiceHandler.status()
        and ServiceHandler.invocation_id() is None
    ):
        error("Service is already running.")
        return
    while True:
        try:
            result = PortalHandler.trigger_captive_portal()
            if result is not None:
                info(f"Run: Captive portal detected.")
                SessionHandler.login(username=None, password=None)
        except Exception as e:
            error(f"Run: {e}")
        sleep(CHECK_INTERVAL)


@cli.command()
@click.option(
    "--username",
    "-u",
    type=str,
    help="If not provided, will use stored credentials.",
)
@click.option(
    "--password",
    "-p",
    type=str,
    help="If not provided, will use stored credentials.",
)
def login(username: Optional[str] = None, password: Optional[str] = None):
    """Login to the IIITK Portal."""
    if username is None and password is not None:
        raise click.UsageError("Username must be provided if password is given.")
    SessionHandler.login(username=username, password=password)


@cli.command()
def logout():
    """Logout from the IIITK Portal."""
    try:
        ip, token = SessionHandler.get_session_details()
        url = f"http://{ip}/logout?{token}"
        info(f"Logout url: {url}")
        requests.get(url, timeout=5)
        click.echo("Logged out successfully.")
        remove(TOKEN_FILE)
    except ValueError:
        pass


cli.add_command(credentials)
cli.add_command(get)
cli.add_command(service)
