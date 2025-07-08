# bandmantaro/utils.py
import os
import json
from PIL import ImageFont
from flask import current_app # Flaskアプリのコンテキスト内でroot_pathを取得するため

def find_japanese_fonts():
    found_fonts = {}
    try:
        base_fonts_dir = os.path.join(current_app.root_path, 'fonts')
    except RuntimeError:
        # アプリケーションコンテキスト外で呼び出された場合（テストなど）のフォールバック
        # このパスはプロジェクトの構造に合わせて調整してください
        base_fonts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')


    search_paths = [base_fonts_dir]

    font_extensions = ('.ttf', '.otf', '.ttc')

    japanese_font_keywords = [
        "meiryo", "hiragino", "notosanscjk", "yugothic", "msgothic", "ipafont",
        "メイリオ", "ヒラギノ", "游ゴシック", "ＭＳ ゴシック", "源ノ角", "kozgop", "migmix",
        "dela gothic one", "m plus rounded 1c", "noto sans jp", "noto serif jp"
    ]

    for base_path in search_paths:
        if not os.path.exists(base_path):
            continue
        for root, _, files in os.walk(base_path):
            for file_name in files:
                if file_name.lower().endswith(font_extensions):
                    file_path = os.path.join(root, file_name)
                    try:
                        font = ImageFont.truetype(file_path, 30)
                        font_family_name = font.getname()[0]

                        display_name = font_family_name
                        if "noto sans jp" in display_name.lower():
                            display_name = "Noto Sans JP"
                        elif "noto serif jp" in display_name.lower():
                            display_name = "Noto Serif JP"
                        elif "dela gothic one" in display_name.lower():
                            display_name = "Dela Gothic One"
                        elif "m plus rounded 1c" in display_name.lower():
                            display_name = "M PLUS Rounded 1c"
                        else:
                            display_name = display_name.replace("_", " ").replace("  ", " ").strip()

                        if display_name not in found_fonts:
                            found_fonts[display_name] = file_path
                        else:
                            current_path = found_fonts[display_name]
                            if ("regular" in file_name.lower() and "regular" not in os.path.basename(current_path).lower()) or \
                               ("jp-regular" in file_name.lower() and "jp-regular" not in os.path.basename(current_path).lower()):
                                found_fonts[display_name] = file_path

                    except Exception as e:
                        pass

    final_font_list = sorted([(name, path) for name, path in found_fonts.items()], key=lambda x: x[0].lower())

    if not final_font_list:
        final_font_list.append(("（日本語フォントが見つかりません）", None))

    return final_font_list

def load_friends_bands():
    try:
        DATA_DIR = os.path.join(current_app.root_path, 'data')
    except RuntimeError:
        DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

    BANDS_DATA_FILE = os.path.join(DATA_DIR, 'bands.json')

    if not os.path.exists(BANDS_DATA_FILE):
        print(f"Warning: Data file not found at {BANDS_DATA_FILE}. Returning empty list.")
        return []
    try:
        with open(BANDS_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {BANDS_DATA_FILE}: {e}")
        return []
    except Exception as e:
        print(f"Error reading {BANDS_DATA_FILE}: {e}")
        return []