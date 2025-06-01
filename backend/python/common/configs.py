from dotenv import load_dotenv
import os
import argparse
import json

load_dotenv()

def _get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config-dir", required=True, 
        default="../configs/dev.json",
        help="Path to config file"
    )

    args = parser.parse_args()
    return args

_args = _get_args()

with open(_args.config_dir, "r") as f:
    _configs = json.load(f)

logging = _configs["logging"]
agent = _configs["agent"]

