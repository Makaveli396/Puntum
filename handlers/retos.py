import os
import json
from datetime import datetime

RETO_SEMANAL = {
    "hashtag": "#crítica",
    "min_words": 100,
    "bonus_points": 15
}

def get_current_challenge():
    if os.path.exists("custom_challenge.txt"):
        with open("custom_challenge.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def get_weekly_challenge():
    return RETO_SEMANAL

def validate_challenge_submission(challenge, text):
    hashtag_ok = challenge["hashtag"] in text.lower()
    word_count = len(text.split())
    if hashtag_ok and word_count >= challenge.get("min_words", 0):
        return True
    return False