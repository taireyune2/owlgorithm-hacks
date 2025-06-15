from dotenv import load_dotenv
import os
import argparse
import json
import random

load_dotenv()
random.seed(99)

# def _get_args():
#   parser = argparse.ArgumentParser()

#   parser.add_argument(
#     "--config-dir",
#     default=os.getenv("CONFIG_DIR", "../configs/dev.json"),
#     type=str,
#     help="Path to config file"
#   )

#   args = parser.parse_args()
#   return args

# _args = _get_args()

with open(os.getenv("CONFIG_DIR", "../configs/dev.json"), "r") as f:
  file: dict = json.load(f)
