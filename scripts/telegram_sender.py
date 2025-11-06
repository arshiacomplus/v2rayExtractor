import base64
import json
import logging
import re
import time
from datetime import datetime
from typing import List, Dict
import os
import urllib.parse

import pytz
import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY', 'arshiacomplus/V2rayExtractor')
GITHUB_REPO_URL = f"https://github.com/{GITHUB_REPOSITORY}"

MAIN_CHANNEL_ID_RAW = os.getenv('TELEGRAM_CHAT_ID', 'arshia_mod_fun').lstrip('@')
MAIN_CHANNEL_URL = f"https://t.me/{MAIN_CHANNEL_ID_RAW}"

CONFIG_CHANNEL_ID_RAW = os.getenv('TELEGRAM_CHANNEL_ID', 'v2ray_Extractor').lstrip('@')
CONFIG_CHANNEL_URL = f"https://t.me/{CONFIG_CHANNEL_ID_RAW}"

MARKUP = types.InlineKeyboardMarkup(row_width=2)
btn1 = types.InlineKeyboardButton("Github", url="https://github.com/Ali-Anv1")
btn2 = types.InlineKeyboardButton("Author", url="https://t.me/Ali1994tm")
MARKUP.add(btn1, btn2)


def init_bot(token: str) -> telebot.TeleBot | None:
    try:
        return telebot.TeleBot(token)
    except Exception as e:
        logging.error(f"Failed to initialize Telegram bot: {e}")
        return None

def send_summary_message(bot: telebot.TeleBot, chat_id: str, counts: Dict[str, int]):

    base_raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/main"

    message = "📊 خلاصه ساب‌لینک‌های V2rayExtractor 📊\n\n"
    total_configs = sum(counts.values())
    message += f"تعداد کل کانفیگ‌های سالم: {total_configs}\n\n"

    links_map = {
        "mix": f"{base_raw_url}/mix/sub.html", "vless": f"{base_raw_url}/vless.html",
        "vmess": f"{base_raw_url}/vmess.html", "ss": f"{base_raw_url}/ss.html",
        "trojan": f"{base_raw_url}/trojan.html", "hy2": f"{base_raw_url}/hy2.html",
    }

    if total_configs > 0:
        message += f"MIX (ALL):\n"
        message += f"
\n{links_map['mix']}\n
\n"

    for protocol, count in counts.items():
        if count > 0:
            message += f"{protocol.upper()}:\n"
            message += f"
\n{links_map.get(protocol, '')}\n
\n"

    iran_tz = pytz.timezone("Asia/Tehran")
    time_ir = datetime.now(iran_tz).strftime("%Y-%m-%d %H:%M")
    message += f"\n*آخرین بروزرسانی: {time_ir}*"

    try:
        bot.send_message(chat_id, message, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        logging.error(f"Failed to send summary message to {chat_id}: {e}")

    for protocol, count in counts.items():
        message += f"**{protocol.upper()}:**\n"
        message += f"```\n{links_map.get(protocol, '')}\n```\n"

    iran_tz = pytz.timezone("Asia/Tehran")
    time_ir = datetime.now(iran_tz).strftime("%Y-%m-%d %H:%M")
    message += f"\n*آخرین بروزرسانی: {time_ir}*"

    try:
        bot.send_message(chat_id, message, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        logging.error(f"Failed to send summary message to {chat_id}: {e}")

def clean_config_for_telegram(config: str) -> str:

    return re.sub(r'(#.*?)::[A-Z]{2}$', r'\1', config)

def regroup_configs_by_source(checked_configs: List[str]) -> Dict[str, List[str]]:

    regrouped = {}
    for config in checked_configs:
        source_channel = "unknown_source"

        try:
            full_tag = ""
            if config.startswith("vmess://"):
                encoded_part = config.split("://")[1]
                encoded_part += '=' * (-len(encoded_part) % 4)
                decoded_json = base64.b64decode(encoded_part).decode("utf-8")
                vmess_data = json.loads(decoded_json)
                full_tag = vmess_data.get("ps", "")
            elif '#' in config:
                full_tag = urllib.parse.unquote(config.split('#', 1)[1])

            match = re.search(r'>>\s*@([\w\d_]+)', full_tag)
            if match:
                source_channel = f"@{match.group(1)}"
        except Exception as e:
            logging.warning(f"Could not parse tag for source detection in '{config[:50]}...': {e}")

        if source_channel not in regrouped:
            regrouped[source_channel] = []

        cleaned_config = clean_config_for_telegram(config)
        regrouped[source_channel].append(cleaned_config)
    return regrouped

def send_with_rate_limit_handling(bot_instance, *args, **kwargs):
    while True:
        try:
            bot_instance.send_message(*args, **kwargs)
            time.sleep(1)
            break
        except ApiTelegramException as e:
            if e.error_code == 429:
                retry_after = int(e.result_json.get('parameters', {}).get('retry_after', 20))
                logging.warning(f"Rate limited by Telegram. Retrying after {retry_after + 1} seconds...")
                time.sleep(retry_after + 1)
            else:
                logging.error(f"An unhandled Telegram API error occurred: {e}")
                break

def send_all_grouped_configs(bot: telebot.TeleBot, channel_id: str, grouped_configs: Dict[str, List[str]]):

    for source in sorted(grouped_configs.keys()):
        configs = grouped_configs[source]
        if not configs:
            continue

        logging.info(f"Sending {len(configs)} configs from source '{source}' to {channel_id}")

        for i in range(0, len(configs), 15):
            batch = configs[i:i + 15]
            message_text = "```\n" + "\n\n".join(batch) + "\n```"

            iran_tz = pytz.timezone("Asia/Tehran")
            time_ir = datetime.now(iran_tz).strftime("%Y-%m-%d %H:%M:%S")
            from_link = f"https://t.me/{source[1:]}" if source.startswith('@') else "منبع نامشخص"


            safe_source = source.replace('__', '\\_\\_')
            safe_main_channel_id = ("@" + MAIN_CHANNEL_ID_RAW).replace('__', '\\_\\_')
            safe_config_channel_id = ("@" + CONFIG_CHANNEL_ID_RAW).replace('__', '\\_\\_')

            caption = (
                f"{message_text}\n\n"
                f"⏰ Time: {time_ir}\n"
                f"🆔 Main Channel: [{safe_main_channel_id}]({MAIN_CHANNEL_URL})\n"
                f"🚀 Config Channel: [{safe_config_channel_id}]({CONFIG_CHANNEL_URL})"
            )

            send_with_rate_limit_handling(
                bot,
                chat_id=channel_id,
                text=caption,
                reply_markup=MARKUP,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )



