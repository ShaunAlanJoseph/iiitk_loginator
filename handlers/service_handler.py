from pathlib import Path
from os import getenv
from textwrap import dedent
import subprocess
from logging import error, info
from typing import Optional

from config import SERVICE_NAME, SCRIPT_PATH, USER_SYSTEMD_PATH, SERVICE_FILE
from utils import run_cmd


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
