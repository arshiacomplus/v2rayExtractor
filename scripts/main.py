import base64
import json
import logging
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict
import urllib
import pycountry
import requests
from bs4 import BeautifulSoup
import shutil
import telegram_sender

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TELEGRAM_URLS = [
    "https://t.me/s/prrofile_purple", "https://t.me/s/v2line", "https://t.me/s/v2ray1_ng",
    "https://t.me/s/v2ray_swhil", "https://t.me/s/v2rayng_fast", "https://t.me/s/v2rayng_vpnrog",
    "https://t.me/s/v2raytz", "https://t.me/s/vmessorg", "https://t.me/s/ISVvpn",
    "https://t.me/s/forwardv2ray", "https://t.me/s/PrivateVPNs", "https://t.me/s/VlessConfig",
    "https://t.me/s/V2pedia", "https://t.me/s/v2rayNG_Matsuri", "https://t.me/s/proxystore11",
    "https://t.me/s/DirectVPN", "https://t.me/s/OutlineVpnOfficial", "https://t.me/s/networknim",
    "https://t.me/s/beiten", "https://t.me/s/MsV2ray", "https://t.me/s/foxrayiran",
    "https://t.me/s/DailyV2RY", "https://t.me/s/yaney_01", "https://t.me/s/EliV2ray",
    "https://t.me/s/ServerNett", "https://t.me/s/v2rayng_fa2", "https://t.me/s/v2rayng_org",
    "https://t.me/s/V2rayNGvpni", "https://t.me/s/v2rayNG_VPNN", "https://t.me/s/v2_vmess",
    "https://t.me/s/FreeVlessVpn", "https://t.me/s/vmess_vless_v2rayng", "https://t.me/s/freeland8",
    "https://t.me/s/vmessiran", "https://t.me/s/V2rayNG3", "https://t.me/s/ShadowsocksM",
    "https://t.me/s/ShadowSocks_s", "https://t.me/s/VmessProtocol", "https://t.me/s/Easy_Free_VPN",
    "https://t.me/s/V2Ray_FreedomIran", "https://t.me/s/V2RAY_VMESS_free", "https://t.me/s/v2ray_for_free",
    "https://t.me/s/V2rayN_Free", "https://t.me/s/free4allVPN", "https://t.me/s/configV2rayForFree",
    "https://t.me/s/FreeV2rays", "https://t.me/s/DigiV2ray", "https://t.me/s/v2rayNG_VPN",
    "https://t.me/s/freev2rayssr", "https://t.me/s/v2rayn_server", "https://t.me/s/iranvpnet",
    "https://t.me/s/vmess_iran", "https://t.me/s/configV2rayNG", "https://t.me/s/vpn_proxy_custom",
    "https://t.me/s/vpnmasi", "https://t.me/s/ViPVpn_v2ray", "https://t.me/s/vip_vpn_2022",
    "https://t.me/s/FOX_VPN66", "https://t.me/s/YtTe3la", "https://t.me/s/ultrasurf_12",
    "https://t.me/s/frev2rayng", "https://t.me/s/FreakConfig", "https://t.me/s/Awlix_ir",
    "https://t.me/s/arv2ray", "https://t.me/s/flyv2ray", "https://t.me/s/free_v2rayyy",
    "https://t.me/s/ip_cf", "https://t.me/s/lightning6", "https://t.me/s/mehrosaboran",
    "https://t.me/s/oneclickvpnkeys", "https://t.me/s/outline_vpn", "https://t.me/s/outlinev2rayng",
    "https://t.me/s/outlinevpnofficial", "https://t.me/s/v2rayngvpn", "https://t.me/s/V2raNG_DA",
    "https://t.me/s/V2rayNg_madam", "https://t.me/s/v2boxxv2rayng", "https://t.me/s/configshub2",
    "https://t.me/s/v2ray_configs_pool", "https://t.me/s/hope_net", "https://t.me/s/everydayvpn",
    "https://t.me/s/v2nodes", "https://t.me/s/shadowproxy66", "https://t.me/s/free_nettm"
]

SEND_TO_TELEGRAM = os.getenv('SEND_TO_TELEGRAM', 'false').lower() == 'true'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
SUB_CHECKER_DIR = Path("sub-checker")

def scrape_configs_from_url(url: str) -> List[str]:

    configs = []
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        try:
            channel_name = "@" + url.split("/s/")[1]
        except IndexError:
            channel_name = "@unknown_channel"

        soup = BeautifulSoup(response.content, 'html.parser')
        all_text_content = "\n".join(tag.get_text('\n') for tag in soup.find_all(['div', 'code']))

        pattern = r'((?:vmess|vless|ss|hy2|trojan|hysteria2)://[^\s<>"\'`]+)'
        found_configs = re.findall(pattern, all_text_content)

        for config in found_configs:
            if config.startswith("vmess://"):
                try:
                    parts = config.split('#', 1)
                    base_part = parts[0]

                    encoded_part = base_part.replace("vmess://", "")
                    encoded_part += '=' * (-len(encoded_part) % 4)

                    decoded_json = base64.b64decode(encoded_part).decode("utf-8")
                    vmess_data = json.loads(decoded_json)

                    original_ps = vmess_data.get("ps", "")
                    vmess_data["ps"] = f"{original_ps} >>{channel_name}"

                    updated_json_str = json.dumps(vmess_data, separators=(',', ':'))
                    updated_b64_encoded = base64.b64encode(updated_json_str.encode('utf-8')).decode('utf-8').rstrip('=')

                    configs.append("vmess://" + updated_b64_encoded)

                except Exception as e:
                    logging.warning(f"Failed to process vmess config, adding tag externally: {e}")
                    if '#' in config:
                        configs.append(f"{config} >>{channel_name}")
                    else:
                        configs.append(f"{config}#>>{channel_name}")
            else:
                if '#' in config:
                    base, old_tag = config.split('#', 1)
                    new_tag = f"{old_tag} >>{channel_name}"
                    configs.append(f"{base}#{urllib.parse.quote(new_tag)}")
                else:
                    configs.append(f"{config}#>>{channel_name}")

        logging.info(f"Found and tagged {len(configs)} configs in {url}")
        return configs
    except requests.RequestException as e:
        logging.error(f"Could not fetch or parse {url}: {e}")
        return []

def run_sub_checker(input_configs: List[str]) -> List[str]:

    if not SUB_CHECKER_DIR.is_dir():
        logging.error(f"Sub-checker directory not found at '{SUB_CHECKER_DIR}'")
        return []

    normal_txt_path = SUB_CHECKER_DIR / "normal.txt"
    final_txt_path = SUB_CHECKER_DIR / "final.txt"
    cl_py_path = SUB_CHECKER_DIR / "cl.py"

    logging.info(f"Writing {len(input_configs)} configs to '{normal_txt_path}'")
    normal_txt_path.write_text("\n".join(input_configs), encoding="utf-8")

    logging.info("Running sub-checker script (cl.py)...")
    try:
        process = subprocess.run(
            ["python", cl_py_path.name],
            cwd=SUB_CHECKER_DIR,
            capture_output=True,
            text=True,
            timeout=7200
        )
        logging.info("Sub-checker stdout:\n" + process.stdout)
        if process.stderr:
            logging.error("Sub-checker stderr:\n" + process.stderr)

        if process.returncode != 0:
            logging.error("Sub-checker script failed to execute properly.")
            return []

        if final_txt_path.exists():
            logging.info("Reading checked configs from 'final.txt'")
            checked_configs = final_txt_path.read_text(encoding="utf-8").splitlines()
            return [line for line in checked_configs if line.strip()]
        else:
            logging.error("'final.txt' was not created by the sub-checker.")
            return []

    except subprocess.TimeoutExpired:
        logging.error("Sub-checker script timed out after 30 minutes.")
        return []
    except Exception as e:
        logging.error(f"An error occurred while running sub-checker: {e}")
        return []

def process_and_save_results(checked_configs: List[str]) -> Dict[str, int]:
    if not checked_configs:
        logging.warning("No checked configs to process.")
        return {}

    loc_dir = Path("loc")
    mix_dir = Path("mix")


    logging.info(f"Cleaning up old files in '{loc_dir}' directory...")
    if loc_dir.is_dir():
        try:
            shutil.rmtree(loc_dir)
            logging.info(f"Directory '{loc_dir}' and its contents have been removed successfully.")
        except OSError as e:
            logging.error(f"Error removing directory {loc_dir}: {e}")

    loc_dir.mkdir(exist_ok=True)
    mix_dir.mkdir(exist_ok=True)



    configs_by_protocol = {
        "vless": [], "vmess": [], "ss": [], "trojan": [], "hy2": []
    }
    configs_by_location = {}

    for config in checked_configs:

        if config.startswith(("hysteria://", "hysteria2://", "hy2://")):
            configs_by_protocol["hy2"].append(config)
        elif config.startswith("vless://"):
            configs_by_protocol["vless"].append(config)
        elif config.startswith("vmess://"):
            configs_by_protocol["vmess"].append(config)
        elif config.startswith("ss://"):
            configs_by_protocol["ss"].append(config)
        elif config.startswith("trojan://"):
            configs_by_protocol["trojan"].append(config)

        location_code = "XX"
        try:
            decoded_config = urllib.parse.unquote(config)
            match = re.search(r'::([A-Za-z]{2})$', decoded_config)
            if match:
                location_code = match.group(1).upper()
        except Exception:
            pass

        if location_code not in configs_by_location:
            configs_by_location[location_code] = []
        configs_by_location[location_code].append(config)

    for proto, configs in configs_by_protocol.items():
        if configs:

            file_path = Path(f"{proto}.html")
            file_path.write_text("\n".join(configs), encoding="utf-8")
            logging.info(f"Saved {len(configs)} configs to '{file_path}'")

    Path("mix/sub.html").write_text("\n".join(checked_configs), encoding="utf-8")
    logging.info(f"Saved {len(checked_configs)} configs to 'mix/sub.html'")

    for loc_code, configs in configs_by_location.items():
        country_flag = "❓"
        try:
            country = pycountry.countries.get(alpha_2=loc_code)
            if country and hasattr(country, 'flag'):
                country_flag = country.flag
        except Exception:
            pass

        file_path = Path("loc") / f"{loc_code} {country_flag}.txt"
        file_path.write_text("\n".join(configs), encoding="utf-8")
        logging.info(f"Saved {len(configs)} configs for location {loc_code} to '{file_path}'")
    protocol_counts = {proto: len(configs) for proto, configs in configs_by_protocol.items()}
    logging.info(f"Final protocol counts: {protocol_counts}")
    return protocol_counts


def main():
    logging.info("--- Starting V2Ray Extractor ---")

    logging.info("Step 1: Scraping new configs from Telegram channels...")
    all_raw_configs = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_url = {executor.submit(scrape_configs_from_url, url): url for url in TELEGRAM_URLS}
        for future in future_to_url:
            all_raw_configs.extend(future.result())

    unique_new_configs = sorted(list(set(all_raw_configs)))
    logging.info(f"Collected {len(unique_new_configs)} unique new configs from Telegram.")

    logging.info("Step 2: Reading previously checked configs from 'mix/sub.html'...")
    previous_configs = []
    previous_mix_file = Path("mix/sub.html")
    if previous_mix_file.is_file():
        try:
            previous_configs = previous_mix_file.read_text(encoding="utf-8").splitlines()
            previous_configs = [line.strip() for line in previous_configs if '://' in line]
            logging.info(f"Successfully read {len(previous_configs)} previously checked configs.")
        except Exception as e:
            logging.error(f"Could not read or process '{previous_mix_file}': {e}")
    else:
        logging.info("No previous 'mix/sub.html' file found. Proceeding with new configs only.")


    logging.info("Step 3: Merging new and previous configs...")
    combined_configs = unique_new_configs + previous_configs

    unique_combined_configs = sorted(list(set(combined_configs)))
    logging.info(f"Total unique configs to be tested: {len(unique_combined_configs)}")

    if not unique_combined_configs:
        logging.warning("No configs to check after merging. Exiting.")
        return

    logging.info("Step 4: Running the sub-checker...")
    checked_configs = run_sub_checker(unique_combined_configs)

    logging.info(f"Sub-checker returned {len(checked_configs)} valid configs.")

    logging.info("Step 5: Processing, saving results, and getting counts...")
    protocol_counts = process_and_save_results(checked_configs)
    if SEND_TO_TELEGRAM:
        logging.info("Flag 'sendToTelegram' is true. Proceeding with Telegram notifications.")

        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or not TELEGRAM_CHANNEL_ID:
            logging.warning("Telegram notifications are enabled, but bot token or chat/channel ID is missing in secrets. Skipping.")
        else:
            if not protocol_counts:
                logging.warning("Protocol counts are empty, skipping summary message.")
            else:
                try:
                    bot = telegram_sender.init_bot(TELEGRAM_BOT_TOKEN)
                    if bot:
                        logging.info(f"Sending summary to main channel: {TELEGRAM_CHANNEL_ID}")
                        telegram_sender.send_summary_message(bot, TELEGRAM_CHANNEL_ID, protocol_counts)

                        logging.info(f"Sending grouped configs to channel: {TELEGRAM_CHANNEL_ID}")
                        grouped_configs = telegram_sender.regroup_configs_by_source(checked_configs)
                        telegram_sender.send_all_grouped_configs(bot, TELEGRAM_CHANNEL_ID, grouped_configs)

                        logging.info("Successfully sent all Telegram notifications.")
                except Exception as e:
                    logging.error(f"An error occurred during Telegram operations: {e}")
    else:
        logging.info("Flag 'sendToTelegram' is false. Skipping Telegram notifications.")

    logging.info("--- V2Ray Extractor finished successfully! ---")
if __name__ == "__main__":
    main()