import click
from logging import error

from handlers.service_handler import ServiceHandler


# Service Management Commands
@click.group(invoke_without_command=True)
@click.pass_context
def service(ctx: click.Context):
    """Manage the IIITK Portal Loginator Service."""

    import config

    if config.ANDROID:
        error("Service management is not supported on Android.")
        return

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


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
