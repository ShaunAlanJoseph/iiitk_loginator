import re
import bs4
import requests
from requests.exceptions import RequestException
from urllib.parse import urljoin
from logging import error, info
from typing import Tuple, Dict, Optional


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
