"""kns __main__.py to run the project with `python -m kns` or `python src/kns/__main__.py run`"""

import sys
from pathlib import Path

from kedro.framework.cli.utils import find_run_command
from kedro.framework.project import configure_project


def main(*args, **kwargs):
    package_name = Path(__file__).parent.name  # should be 'kns'
    configure_project(package_name)

    interactive = hasattr(sys, 'ps1')
    kwargs["standalone_mode"] = not interactive

    run = find_run_command(package_name)  # This now works since no broken cli.py
    run(*args, **kwargs)


if __name__ == "__main__":
    main()
