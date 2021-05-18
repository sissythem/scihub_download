import logging
import re
from datetime import datetime
from os import getcwd, makedirs
from os.path import exists, join
from typing import AnyStr, Dict

import yaml


def preprocess_title(title: AnyStr) -> AnyStr:
    """
    Preprocess of a title in order to match with the retrieved items from Crossref

    Args
        | title (str): the title to be processed

    Returns
        | str: the processed title
    """
    title = title.strip()
    title = title.lower()
    title = re.sub(' +', ' ', title)
    return title


def load_properties() -> Dict:
    current_folder = getcwd()
    folder = join(current_folder, "resources")
    properties_file = join(folder, "properties.yaml")
    examples_properties_file = join(folder, "example_properties.yaml")
    prop_file = properties_file if exists(properties_file) else examples_properties_file
    with open(prop_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f.read())


def get_logger(folder) -> logging.Logger:
    """
    Configures the application logger
    Returns
        logger: the initialized logger
    """
    if not exists(folder):
        makedirs(folder)
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    log_filename = f"logs_{timestamp}.log"
    log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    program_logger = logging.getLogger(__name__)

    program_logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(f"{folder}/{log_filename}", encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    program_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    program_logger.addHandler(console_handler)
    return program_logger
