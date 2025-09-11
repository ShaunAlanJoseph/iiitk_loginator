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

## Files
- `loginator.py`: Main script
- `requirements.txt`: Python dependencies

## System Integration
- Uses systemd user services for background tasks
- Stores session tokens in `~/.iiitk_portal_session`

## License
MIT
