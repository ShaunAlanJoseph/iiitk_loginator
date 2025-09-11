#!/usr/bin/env python3

# Modified from Vibhaas' implementation

import re
import subprocess
import requests
from requests.exceptions import RequestException
import bs4
from urllib.parse import urljoin
import secretstorage
import click
import pyperclip
import json
from pathlib import Path
from os import remove, getenv
from textwrap import dedent
from time import sleep
from logging import error, info, debug
import logging
from typing import overload, List, Tuple, Dict, Optional, Union


SECRET_LABEL = "iiitk_portal_login"
TOKEN_FILE = Path.home() / ".iiitk_portal_session"
CHECK_INTERVAL = 60  # seconds

SERVICE_NAME = SECRET_LABEL
SCRIPT_PATH = Path(__file__).resolve()
USER_SYSTEMD_PATH = Path.home() / ".config" / "systemd" / "user"
SERVICE_FILE = USER_SYSTEMD_PATH / f"{SERVICE_NAME}.service"


logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")


@overload
def run_cmd(cmd: List[str]) -> str:
    """
    Run a shell command and return its output.
    Args:
        cmd: The command to run as a string.
    Returns:
        str: The stdout of the command.
    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit status.
    """
    ...


@overload
def run_cmd(cmd: List[str], *, stderr: bool) -> Tuple[str, str]:
    """
    Run a shell command and return its output and error.
    Args:
        cmd: The command to run as a list of strings.
        stderr: If True, capture stderr as well.
    Returns:
        Tuple[str, str]: The stdout and stderr of the command.
    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit status.
    """
    ...


def run_cmd(
    cmd: List[str], *, stderr: Optional[bool] = None
) -> Union[str, Tuple[str, str]]:
    try:
        if stderr is None:
            return subprocess.check_output(cmd, text=True).strip()
        result = subprocess.run(cmd, text=True, capture_output=True, check=True)
        return result.stdout.strip(), (result.stderr.strip() if stderr else "")
    except subprocess.CalledProcessError as e:
        debug(f"Command {' '.join(cmd)} failed: {e}")
        raise e


class Warp:
    WAS_ON: bool = False

    @staticmethod
    def status() -> bool:
        try:
            out = run_cmd(["warp-cli", "status"])
            status = "Connected" in out or "Connecting" in out
            info(f"Warp Connected: {status}")
        except subprocess.CalledProcessError:
            error("Warp CLI is not installed or not available.")
            status = False
        return status

    @staticmethod
    def disconnect() -> None:
        Warp.WAS_ON = Warp.status()
        if Warp.WAS_ON:
            info("Disconnecting Warp...")
            run_cmd(["warp-cli", "disconnect"])

    @staticmethod
    def connect() -> None:
        info("Connecting Warp...")
        run_cmd(["warp-cli", "connect"])

    @staticmethod
    def restore() -> None:
        info(f"Restoring Warp to: Connected: {Warp.WAS_ON}")
        if Warp.WAS_ON:
            Warp.connect()


class SecretHandler:

    @staticmethod
    def get_secret_collection() -> secretstorage.Collection:
        bus = secretstorage.dbus_init()
        collection = secretstorage.get_default_collection(bus)
        if collection.is_locked():
            collection.unlock()
        return collection

    @staticmethod
    def store_user_credentials(username: str, password: str) -> None:
        collection = SecretHandler.get_secret_collection()
        attrs = {"service": SECRET_LABEL, "username": username}
        collection.create_item(SECRET_LABEL, attrs, password.encode(), replace=True)
        collection.connection.close()
        info(f"Stored credentials for user: {username}")

    @staticmethod
    def delete_user_credentials(username: str) -> None:
        """
        Raises:
            ValueError: If no credentials are found for the given username.
        """
        collection = SecretHandler.get_secret_collection()
        try:
            item = next(
                collection.search_items({"service": SECRET_LABEL, "username": username})
            )
            item.delete()
        except StopIteration:
            error_msg = f"No credentials found for user '{username}'."
            error(error_msg)
            raise ValueError(error_msg)
        finally:
            collection.connection.close()
        info(f"Deleted credentials for user: {username}")

    @staticmethod
    def get_all_users() -> List[str]:
        collection = SecretHandler.get_secret_collection()
        users: List[str] = []
        for item in collection.search_items({"service": SECRET_LABEL}):
            attrs = item.get_attributes()
            if "username" in attrs:
                users.append(attrs["username"])
        return users

    @staticmethod
    def get_user_credentials(username: str) -> Tuple[str, str]:
        """
        Raises:
            ValueError: If no credentials are found for the given username.
        """
        collection = SecretHandler.get_secret_collection()
        try:
            item = next(
                collection.search_items({"service": SECRET_LABEL, "username": username})
            )
            password = item.get_secret()
        except StopIteration:
            error_msg = f"No credentials found for user '{username}'."
            error(error_msg)
            raise ValueError(error_msg)
        finally:
            collection.connection.close()
        info(f"Retrieved credentials for user: {username}")
        return username, password.decode()

    @staticmethod
    def get_first_matching_credentials() -> Tuple[str, str]:
        """
        Raises:
            ValueError: If no credentials are found for the service.
        """
        collection = SecretHandler.get_secret_collection()
        try:
            item = next(collection.search_items({"service": SECRET_LABEL}))
            username = item.get_attributes().get("username", "")
            password = item.get_secret()
        except StopIteration:
            error_msg = f"No credentials found for service '{SECRET_LABEL}'."
            error(error_msg)
            raise ValueError(error_msg)
        finally:
            collection.connection.close()
        info(f"Retrieved credentials for user: {username}")
        return username, password.decode()


class PortalHandler:

    @staticmethod
    def trigger_captive_portal() -> Optional[str]:
        """
        Raises:
            RequestException: If there is an error fetching the captive portal.
        """
        try:
            resp = requests.get("http://clients3.google.com/generate_204", timeout=5)
        except RequestException as e:
            error(f"Error fetching captive portal: {e}")
            raise e

        if resp.status_code == 204:
            info("Connected to the internet, no captive portal.")
            return None

        redirect_url = re.search(r'window\.location="([^"]+)"', resp.text)
        assert redirect_url is not None
        info(f"Redirect URL found: {redirect_url.group(1)}")
        return redirect_url.group(1)

    @staticmethod
    def get_login_form(url: str) -> Tuple[str, str]:
        """
        Raises:
            RequestException: If there is an error fetching the login page.
        """
        try:
            resp = requests.get(url, timeout=5)
        except RequestException as e:
            error(f"Error fetching login page: {e}")
            raise e
        return resp.text, resp.url

    @staticmethod
    def parse_login_form(html: str) -> Tuple[str, Dict[str, str]]:
        """
        Extracts the form action and the hidden input fields from the login page HTML.
        """
        soup = bs4.BeautifulSoup(html, "html.parser")
        form = soup.find("form")
        assert isinstance(form, bs4.Tag)
        action = form.get("action")
        assert isinstance(action, str)
        data: Dict[str, str] = {}
        for input_tag in form.find_all("input"):
            assert isinstance(input_tag, bs4.Tag)
            if input_tag.get("type") == "hidden":
                name = input_tag.get("name")
                value = input_tag.get("value", "")
                if isinstance(name, str) and name and isinstance(value, str):
                    data[name] = value
        info(f"Parsed form action: {action}")
        return action, data

    @staticmethod
    def login(
        login_page_url: str,
        form_action: str,
        form_data: Dict[str, str],
        username: str,
        password: str,
    ) -> str:
        """
        Raises:
            RequestException: If there is an error submitting the login form.
            ValueError: If authentication fails.
        """

        form_data["username"] = username
        form_data["password"] = password

        # Resolve relative action URL
        post_url = (
            form_action
            if form_action.startswith("http")
            else urljoin(login_page_url, form_action)
        )

        try:
            resp = requests.post(post_url, data=form_data, timeout=5)
        except RequestException as e:
            error(f"Error submitting login form: {e}")
            raise e

        if re.search("Authentication Failed", resp.text):
            error(f"Authentication failed for user: {username}.")
            raise ValueError("Authentication failed. Please check your credentials.")

        info(f"Successfully logged in.")
        return resp.text

    @staticmethod
    def login_to_portal(username: str, password: str) -> Optional[str]:
        """
        Raises:
            RequestException: If there is an error with the login requests.
            ValueError: If no credentials are provided and none are found.
        """

        # 1) Trigger captive portal
        url = PortalHandler.trigger_captive_portal()
        if url is None:  # No captive portal detected
            return None

        # 2) Get the login form
        login_html, login_url = PortalHandler.get_login_form(url)
        form_action, form_data = PortalHandler.parse_login_form(login_html)

        # 3) Perform login
        login_response = PortalHandler.login(
            login_url, form_action, form_data, username, password
        )
        return login_response


class SessionHandler:

    @staticmethod
    def parse_session_details(html: str) -> Tuple[str, str]:
        # Response html contains a url with a keepalive token
        match = re.search(r'http://([^/]+)/keepalive\?([^"]+)', html)
        assert match is not None
        ip = match.group(1)
        token = match.group(2)
        info(f"Session - ip: {ip} token: {token}")

        with open(TOKEN_FILE, "w") as f:
            f.write("// This file is auto-generated by IIITK Portal Loginator\n")
            json.dump({"ip": ip, "token": token}, f)
        info("Session details saved.")

        return ip, token

    @staticmethod
    def get_session_details() -> Tuple[str, str]:
        """
        Raises:
            ValueError: If no session token is found.
        """
        try:
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
                return data["ip"], data["token"]
        except (ValueError, KeyError):
            error("No session token found. Please login first.")
            raise ValueError("No session token found. Please login first.")

    @staticmethod
    def login(
        *, username: Optional[str] = None, password: Optional[str] = None
    ) -> None:
        try:
            if username is None:
                username, password = SecretHandler.get_first_matching_credentials()
            elif password is None:
                username, password = SecretHandler.get_user_credentials(username)
        except ValueError:
            return
        
        try:
            Warp.disconnect()
            login_response = PortalHandler.login_to_portal(username, password)
            if login_response is None:
                return None

            SessionHandler.parse_session_details(login_response)
        except (RequestException, ValueError):
            pass
        finally:
            Warp.restore()


class ServiceHandler:

    @staticmethod
    def create() -> None:
        """Creates a systemd service file for the IIITK Portal Loginator service."""
        USER_SYSTEMD_PATH.mkdir(parents=True, exist_ok=True)

        service_content = dedent(
            f"""\
            [Unit]
            Description=IIITK Portal Loginator
            After=default.target

            [Service]
            Type=simple
            ExecStart={SCRIPT_PATH} run
            Restart=on-failure
            RestartSec=5
            WorkingDirectory={Path.home()}

            [Install]
            WantedBy=default.target
            """
        )

        SERVICE_FILE.write_text(service_content)
        info(f"Service file created at {SERVICE_FILE}")

    @staticmethod
    def enable() -> None:
        """Enables the IIITK Portal Loginator service."""
        try:
            run_cmd(["systemctl", "--user", "daemon-reload"])
            _, result = run_cmd(
                ["systemctl", "--user", "enable", SERVICE_NAME], stderr=True
            )
            if result:
                info("Service enabled successfully.")
            else:
                info("Service already enabled.")
        except subprocess.CalledProcessError:
            error(f"Failed to enable service {SERVICE_NAME}. It may not be created.")

    @staticmethod
    def disable() -> None:
        """Disables the IIITK Portal Loginator service."""
        try:
            _, result = run_cmd(
                ["systemctl", "--user", "disable", SERVICE_NAME], stderr=True
            )
            if result:
                info("Service disabled successfully.")
            else:
                info("Service already disabled.")
        except subprocess.CalledProcessError:
            error(
                f"Failed to disable service {SERVICE_NAME}. It may not be enabled or created."
            )

    @staticmethod
    def start() -> None:
        """Starts the IIITK Portal Loginator service."""
        try:
            run_cmd(["systemctl", "--user", "start", SERVICE_NAME])
            info(f"Service {SERVICE_NAME} started.")
        except subprocess.CalledProcessError:
            error(
                f"Failed to start service {SERVICE_NAME}. It may not be enabled or created."
            )

    @staticmethod
    def stop() -> None:
        """Stops the IIITK Portal Loginator service."""
        try:
            run_cmd(["systemctl", "--user", "stop", SERVICE_NAME])
            info(f"Service {SERVICE_NAME} stopped.")
        except subprocess.CalledProcessError:
            error(f"Failed to stop service {SERVICE_NAME}. It may not be running.")

    @staticmethod
    def restart() -> None:
        """Restarts the IIITK Portal Loginator service."""
        try:
            run_cmd(["systemctl", "--user", "restart", SERVICE_NAME])
            info(f"Service {SERVICE_NAME} restarted.")
        except subprocess.CalledProcessError:
            error(
                f"Failed to restart service {SERVICE_NAME}. It may not be running or created."
            )

    @staticmethod
    def status() -> bool:
        """Checks the status of the IIITK Portal Loginator service."""
        try:
            run_cmd(["systemctl", "--user", "is-active", "--quiet", SERVICE_NAME])
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def invocation_id() -> Optional[str]:
        return getenv("INVOCATION_ID")


@click.group()
def cli():
    pass


@cli.command()
def run():
    """Run the IIITK Portal Loginator service in the foreground."""
    if ServiceHandler.status() and ServiceHandler.invocation_id() is None:
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


# Credential Management Commands
@cli.group()
def credentials():
    """Manage user credentials."""
    pass


@credentials.command()
def add():
    """Add or update user credentials."""
    username = click.prompt("Enter your username", type=str)
    while True:
        password = click.prompt("Enter your password", type=str, hide_input=True)
        cnf_password = click.prompt("Confirm your password", type=str, hide_input=True)
        if password == cnf_password:
            break
        click.echo("Passwords do not match. Please try again.")

    SecretHandler.store_user_credentials(username, password)
    click.echo("Credentials stored successfully.")


@credentials.command()
@click.argument("username", type=str)
def delete(username: str):
    """Delete user credentials."""
    try:
        _ = SecretHandler.get_user_credentials(username)
        click.confirm(
            f"Are you sure you want to delete credentials for {username}?",
            default=False,
            abort=True,
        )
        SecretHandler.delete_user_credentials(username)
        click.echo(f"Credentials for {username} deleted successfully.")
    except ValueError:
        click.echo(f"No credentials found for user: {username}")


@credentials.command()
def list():
    """List all stored user credentials."""
    users = SecretHandler.get_all_users()
    if not users:
        click.echo("No users found.")
    else:
        click.echo("Stored users:")
        for user in users:
            click.echo(f"- {user}")


@credentials.command()
def copy():
    """Copy user credentials to clipboard."""
    username = click.prompt("Enter the username to retrieve credentials", type=str)
    try:
        _, password = SecretHandler.get_user_credentials(username)
        click.confirm(
            "Are you sure you want to copy the password to clipboard?",
            default=False,
            abort=True,
        )
        pyperclip.copy(password)
        click.echo("Password copied to clipboard.")
    except ValueError:
        click.echo(f"No credentials found for user: {username}")


# Session Details Commands
@cli.group()
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


# Service Management Commands
@cli.group()
def service():
    """Manage the IIITK Portal Loginator Service."""
    pass


@service.command()
def enable():
    """Enable the IIITK Portal Loginator service."""
    ServiceHandler.enable()


@service.command()
def disable():
    """Disable the IIITK Portal Loginator service."""
    ServiceHandler.disable()


@service.command()
def start():
    """Start the IIITK Portal Loginator service."""
    ServiceHandler.start()


@service.command()
def stop():
    """Stop the IIITK Portal Loginator service."""
    ServiceHandler.stop()


@service.command()
def restart():
    """Restart the IIITK Portal Loginator service."""
    ServiceHandler.restart()


@service.command()
def status():
    """Check the status of the IIITK Portal Loginator service."""
    if ServiceHandler.status():
        click.echo("Service is running.")
    else:
        click.echo("Service is not running or does not exist.")


@service.command()
def setup():
    """Setup the IIITK Portal Loginator service."""
    ServiceHandler.stop()
    ServiceHandler.disable()
    ServiceHandler.create()
    ServiceHandler.enable()
    ServiceHandler.start()


if __name__ == "__main__":
    cli()
