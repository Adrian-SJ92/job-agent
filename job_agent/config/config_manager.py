import json
from pathlib import Path
from dotenv import dotenv_values

CONFIG_DIR = Path("config")
USERS_JSON = CONFIG_DIR / "users.json"


def load_users_index():
    if not USERS_JSON.exists():
        return {"users": []}
    with open(USERS_JSON) as f:
        return json.load(f)


def get_user_entry(username):
    data = load_users_index()
    for user in data.get("users", []):
        if user["username"] == username:
            return user
    return None


def load_user_config(username):
    """Load environment variables for a specific user from config/[username].env."""
    user_entry = get_user_entry(username)
    if not user_entry:
        raise ValueError(f"User '{username}' not found in config/users.json")

    config_file = CONFIG_DIR / user_entry.get("config_file", f"{username}.env")
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    config = dict(dotenv_values(config_file))
    config["username"] = username
    config["chat_id"] = user_entry.get("chat_id")
    # telegram_token can live in users.json or in the .env
    config["TELEGRAM_BOT_TOKEN"] = (
        user_entry.get("telegram_token") or config.get("TELEGRAM_BOT_TOKEN")
    )
    return config


def get_all_usernames():
    data = load_users_index()
    return [u["username"] for u in data.get("users", [])]
