import click
import pyperclip

from handlers.secret_handler import get_secret_handler


# Credential Management Commands
@click.group()
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

    get_secret_handler().store_user_credentials(username, password)
    click.echo("Credentials stored successfully.")


@credentials.command()
@click.argument("username", type=str)
def delete(username: str):
    """Delete user credentials."""

    try:
        _ = get_secret_handler().get_user_credentials(username)
        click.confirm(
            f"Are you sure you want to delete credentials for {username}?",
            default=False,
            abort=True,
        )
        get_secret_handler().delete_user_credentials(username)
        click.echo(f"Credentials for {username} deleted successfully.")
    except ValueError:
        click.echo(f"No credentials found for user: {username}")


@credentials.command()
def list():
    """List all stored user credentials."""
    users = get_secret_handler().get_all_users()
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
        _, password = get_secret_handler().get_user_credentials(username)
        click.confirm(
            "Are you sure you want to copy the password to clipboard?",
            default=False,
            abort=True,
        )
        pyperclip.copy(password)
        click.echo("Password copied to clipboard.")
    except ValueError:
        click.echo(f"No credentials found for user: {username}")
