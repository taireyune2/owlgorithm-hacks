from dotenv import load_dotenv
import os
import argparse
import json
import random

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.getenv("CONFIG_DIR", os.path.join(BASE_DIR, "..", "configs", "dev.json"))

with open(CONFIG_PATH, "r") as f:
  file: dict = json.load(f)

if file["logging"]["env"] != "prod":
  random.seed(99)