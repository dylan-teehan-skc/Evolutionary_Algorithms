from pathlib import Path

import yaml

from src.runner import run

if __name__ == "__main__":
    config_path = Path(__file__).with_name("config.yaml")
    run(yaml.safe_load(config_path.read_text()))
