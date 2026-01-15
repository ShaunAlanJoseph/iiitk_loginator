# Loginator
Loginator is a Python utility for Linux to securely automate the login process for the IIITK captive portal
It leverages system secret storage, session management and command-line tools for a seamless experience.

## Features
- Securely store, retrieve and delete user credentials using system secret storage
- Manage session tokens and automate login flows
- Integrates with systemd for background service management
- Clipboard support for quick credential access
- Command-line interface via `click`
- Optional integration with Cloudflare Warp
- Can be run on android using Termux

### Notes for Android
- Secret storage is not supported so credentials are stored in plain text in `~/.iiitk_portal_credentials`
- If Cloudflare Warp is used, set Termux as an excluded app in the Warp settings to avoid connectivity issues.
- If mobile data is on, disable it before running the script to ensure proper captive portal detection.

## Requirements
See `requirements.txt` for Python dependencies.

## Usage
1. Install dependencies listed in `requirements.txt`.
2. Make the script executable:
   ```bash
   chmod +x loginator.py
   ```
3. Run the script directly:
   ```bash
   ./loginator.py [OPTIONS]
   ```
4. Use the CLI to store, retrieve or delete credentials, manage sessions and more.

## Usage (Android/Termux)
1. Install Termux from F-Droid.
2. Install Python and Git on Termux.
   ```bash
   pkg install python git
   ```
3. Clone the repo.
4. Install all dependencies except `secretstorage`.
5. Run the script using Python:
   ```bash
   python loginator.py --android [OPTIONS]
   ```
6. Use the CLI as usual.
7. Can be paired with Automate and Termux plugins for automation.

### Termux:Boot Setup
1. Install Termux:Boot from F-Droid.
2. Create a script in `~/.termux/boot/iiitk_loginator.sh` with the following content:
   ```bash
   #!/data/data/com.termux/files/usr/bin/sh

   pkill -f iiitk_loginator.py

   termux-wake-lock
   exec python /path/to/loginator.py --android run
   ```
3. Make the script executable:
   ```bash
   chmod +x ~/.termux/boot/iiitk_loginator.sh
   ```
4. The script will run automatically on device boot.

## Files
- `loginator.py`: Main script
- `requirements.txt`: Python dependencies

## System Integration
- Uses systemd user services for background tasks
- Stores session tokens in `~/.iiitk_portal_session`

## License
MIT
