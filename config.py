import os, sys, configparser
import streamlit as st
import configparser
from logging.handlers import RotatingFileHandler
import logging


os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("autoschedulerstemlit")
logger.setLevel(logging.INFO)
file_handler = RotatingFileHandler(
    "logs/error.log", maxBytes=5 * 1024 * 1024, backupCount=3
)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class SchApp:
    __conf = None
    __cache = None

    @staticmethod
    def config():
        if SchApp.__conf is None:
            env = None
            conf_file = None

            if len(sys.argv) > 1:
                env = sys.argv[1]
                conf_file = f"setup/{env}_conf.ini"
            if env is None and "app_env" in os.environ.keys():
                env = os.environ["app_env"]
                conf_file = f"setup/{env}_conf.ini"
            if env is None:
                conf_file = "setup/conf.ini"
                env = "default"

            if not os.path.exists(conf_file):
                st.error(f"⚠️ Config file `{conf_file}` not found. Please check your environment setup.")
                st.stop()
            SchApp.__conf = configparser.ConfigParser()
            SchApp.__conf.read(conf_file)

        return SchApp.__conf
    @staticmethod
    def cache():
        if SchApp.__cache is None:
            SchApp.__cache = {}
        return SchApp.__cache
