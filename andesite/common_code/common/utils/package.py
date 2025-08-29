import sys
from pathlib import Path

from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)


def get_process_root() -> Path:
    """
    Get the root directory of the current process.

    This function returns the directory of the main script that initiated the process.
    It can be used to determine the base directory for configurations, resources, or other
    assets needed by the application.

    Returns:
        Path: The root directory of the current process.
    """
    main_module = sys.modules.get("__main__", None) or sys.modules.get("main", None) or sys.argv[0]
    if main_module is not None and hasattr(main_module, "__file__") and main_module.__file__:
        return Path(main_module.__file__).parent
    else:
        # If main_module is not a file, look in all subdirectories to find the main file
        for path in Path.cwd().rglob("*.py"):
            if path.stem == "main":
                return path.parent

    return Path.cwd()


def get_package_root() -> Path:
    """
    Get the root directory of the current package.

    This function returns the directory that contains the current module and is recognized
    as the root of the package. It looks for a file named "py.typed" to identify the package root.

    Returns:
        Path: The root directory of the current package.
    """
    current_path = Path(__file__).resolve()
    package_path = current_path.parent
    while package_path != package_path.parent:
        if (package_path / "py.typed").exists():
            break

        package_path = package_path.parent

    return package_path
