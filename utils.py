import subprocess
from logging import error, info, debug
from typing import overload, List, Tuple, Union, Optional


@overload
def run_cmd(cmd: List[str]) -> str:
    """
    Run a shell command and return its output.
    Args:
        cmd: The command to run as a list of strings.
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
        except:
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
