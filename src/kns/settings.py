"""Project settings. There is no need to edit this file unless you want to change values
from the Kedro defaults. For further information, including these default values, see
https://docs.kedro.org/en/stable/kedro_project_setup/settings.html.
"""

from pathlib import Path
from kedro.config import OmegaConfigLoader
from kns import pipeline_registry  # ✅ Manually registered pipelines

# Class that manages how configuration is loaded.
CONFIG_LOADER_CLASS = OmegaConfigLoader
CONFIG_LOADER_ARGS = {
    "base_env": "base",
    "default_run_env": "local",
    # Optional: Uncomment to support additional config patterns
    # "config_patterns": {
    #     "spark": ["spark*/"],
    #     "parameters": ["parameters*", "parameters*/**", "**/parameters*"],
    # }
}

# ✅ Register manually written pipelines
PIPELINE_REGISTRY = pipeline_registry
