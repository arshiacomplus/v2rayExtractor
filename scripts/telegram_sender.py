import base64
import json
import logging
import re
import time
from datetime import datetime
from typing import List, Dict
import pytz
import telebot
from telebot import types
import os
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY', 'arshiacomplus/V2rayExtractor')
GITHUB_REPO_URL = f"https://github.com/{GITHUB_REPOSITORY}"

MAIN_CHANNEL_ID = os.getenv('TELEGRAM_CHAT_ID', '@arshia_mod_fun')
MAIN_CHANNEL_URL = f"https://t.me/{MAIN_CHANNEL_ID.lstrip('@')}"

CONFIG_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '@v2ray_Extractor')
CONFIG_CHANNEL_URL = f"https://t.me/{CONFIG_CHANNEL_ID.lstrip('@')}"
MARKUP = types.InlineKeyboardMarkup(row_width=2)
btn1 = types.InlineKeyboardButton("Github", url="https://github.com/arshiacomplus")
btn2 = types.InlineKeyboardButton("Author", url="https://t.me/arshiacomplus")
MARKUP.add(btn1, btn2)
def init_bot(token: str) -> telebot.TeleBot | None:
    try:
        return telebot.TeleBot(token)
    except Exception as e:
        logging.error(f"Failed to initialize Telegram bot: {e}")
        return None
def send_summary_message(bot: telebot.TeleBot, chat_id: str, counts: Dict[str, int]):
    base_raw_url = f"https://raw.githubusercontent.com/{os.getenv('GITHUB_REPOSITORY', 'arshiacomplus/V2rayExtractor')}/main"
    message = "📊 **خلاصه کانفیگ‌های جدید** 📊\n\n"
    total_configs = sum(counts.values())
    message += f"تعداد کل کانفیگ‌های سالم: **{total_configs}**\n\n"
    links = {
        "mix": f"{base_raw_url}/mix/sub.html",
        "vless": f"{base_raw_url}/vless.html",
        "vmess": f"{base_raw_url}/vmess.html",
        "ss": f"{base_raw_url}/ss.html",
        "trojan": f"{base_raw_url}/trojan.html",
        "hy2": f"{base_raw_url}/hy2.html",
    }
    for protocol, count in counts.items():
        if count > 0:
            message += f"▫️ **{protocol.upper()}**: {count} کانفیگ `[لینک]`({links.get(protocol, '')})\n"
    iran_tz = pytz.timezone("Asia/Tehran")
    time_ir = datetime.now(iran_tz).strftime("%Y-%m-%d %H:%M")
    message += f"\n\n*آخرین بروزرسانی (به وقت ایران): {time_ir}*"
    try:
        bot.send_message(chat_id, message, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        logging.error(f"Failed to send summary message to {chat_id}: {e}")
def regroup_configs_by_source(checked_configs: List[str]) -> Dict[str, List[str]]:
    regrouped = {}
    for config in checked_configs:
        source_channel = "unknown_source"
        match = re.search(r'#>>@([\w\d_]+)', config)
        if match:
            source_channel = f"@{match.group(1)}"
        if source_channel not in regrouped:
            regrouped[source_channel] = []
        regrouped[source_channel].append(config)
    return regrouped
def send_all_grouped_configs(bot: telebot.TeleBot, channel_id: str, grouped_configs: Dict[str, List[str]]):
    for source, configs in grouped_configs.items():
        if not configs:
            continue
        logging.info(f"Sending {len(configs)} configs from source '{source}' to {channel_id}")
        for i in range(0, len(configs), 10):
            batch = configs[i:i + 10]
            message_text = "```\n" + "\n\n".join(batch) + "\n```"
            iran_tz = pytz.timezone("Asia/Tehran")
            time_ir = datetime.now(iran_tz).strftime("%Y-%m-%d %H:%M:%S")
            from_link = f"https://t.me/{source[1:]}" if source.startswith('@') else "منبع نامشخص"
            caption = (
                f"{message_text}\n\n"
                f"⏰ **Time**: {time_ir}\n"
                f"🔍 **From**: [{source}]({from_link})\n\n"
                f"🆔 Main Channel: [arshia_mod_fun]({MAIN_CHANNEL_URL})\n"
                f"V2ray_Extractor]({CONFIG_CHANNEL_URL}) 🚀"
            )
            try:
                bot.send_message(channel_id, caption, reply_markup=MARKUP, parse_mode='Markdown', disable_web_page_preview=True)
                time.sleep(2)
            except Exception as e:
                logging.error(f"Failed to send a batch from {source} to {channel_id}: {e}")
                if "message is too long" in str(e):
                    for single_config in batch:
                        single_caption = f"```\n{single_config}\n```\n\n(بقیه اطلاعات)"
                        bot.send_message(channel_id, single_caption, parse_mode='Markdown')
                        time.sleep(1)