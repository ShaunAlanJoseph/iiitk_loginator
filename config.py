from pathlib import Path


SECRET_LABEL = "iiitk_portal_login"
TOKEN_FILE = Path.home() / ".iiitk_portal_session"
SECRET_FILE = Path.home() / ".iiitk_portal_credentials"
CHECK_INTERVAL = 60  # seconds

SERVICE_NAME = SECRET_LABEL
SCRIPT_PATH = Path(__file__).resolve()
USER_SYSTEMD_PATH = Path.home() / ".config" / "systemd" / "user"
SERVICE_FILE = USER_SYSTEMD_PATH / f"{SERVICE_NAME}.service"

ANDROID = False