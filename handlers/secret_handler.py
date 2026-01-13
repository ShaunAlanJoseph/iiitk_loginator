import json
from logging import error, info
from typing import List, Tuple, TYPE_CHECKING

from config import SECRET_LABEL, SECRET_FILE

if TYPE_CHECKING:
    import secretstorage


class SecretHandlerSecretStorage:

    @staticmethod
    def get_secret_collection() -> "secretstorage.Collection":
        import secretstorage

        bus = secretstorage.dbus_init()
        collection = secretstorage.get_default_collection(bus)
        if collection.is_locked():
            collection.unlock()
        return collection

    @staticmethod
    def store_user_credentials(username: str, password: str) -> None:
        collection = SecretHandlerSecretStorage.get_secret_collection()
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
        collection = SecretHandlerSecretStorage.get_secret_collection()
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
        collection = SecretHandlerSecretStorage.get_secret_collection()
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
        collection = SecretHandlerSecretStorage.get_secret_collection()
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
        collection = SecretHandlerSecretStorage.get_secret_collection()
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


class SecretHandlerPlainText:
    @staticmethod
    def store_user_credentials(username: str, password: str) -> None:
        credentials = {}
        try:
            with open(SECRET_FILE, "r") as f:
                credentials = json.load(f)
        except:
            pass

        credentials[username] = password
        with open(SECRET_FILE, "w") as f:
            json.dump(credentials, f)
        info(f"Stored credentials for user: {username}")

    @staticmethod
    def delete_user_credentials(username: str) -> None:
        """
        Raises:
            ValueError: If no credentials are found for the given username.
        """
        try:
            with open(SECRET_FILE, "r") as f:
                credentials = json.load(f)
            if username not in credentials:
                raise ValueError(f"No credentials found for user '{username}'.")
            del credentials[username]
            with open(SECRET_FILE, "w") as f:
                json.dump(credentials, f)
            info(f"Deleted credentials for user: {username}")
        except:
            raise ValueError(f"No credentials found for user '{username}'.")

    @staticmethod
    def get_all_users() -> List[str]:
        try:
            with open(SECRET_FILE, "r") as f:
                credentials = json.load(f)
            return list(credentials.keys())
        except:
            return []

    @staticmethod
    def get_user_credentials(username: str) -> Tuple[str, str]:
        """
        Raises:
            ValueError: If no credentials are found for the given username.
        """
        try:
            with open(SECRET_FILE, "r") as f:
                credentials = json.load(f)
            if username not in credentials:
                raise ValueError(f"No credentials found for user '{username}'.")
            return username, credentials[username]
        except:
            raise ValueError(f"No credentials found for user '{username}'.")

    @staticmethod
    def get_first_matching_credentials() -> Tuple[str, str]:
        """
        Raises:
            ValueError: If no credentials are found.
        """
        try:
            with open(SECRET_FILE, "r") as f:
                credentials = json.load(f)
            if not credentials:
                raise ValueError(f"No credentials found.")
            username, password = next(iter(credentials.items()))
            return username, password
        except:
            raise ValueError(f"No credentials found.")


def get_secret_handler():
    import config

    return SecretHandlerPlainText if config.ANDROID else SecretHandlerSecretStorage
