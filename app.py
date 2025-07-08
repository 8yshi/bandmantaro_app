import io
import os
import re 
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import calendar # calendarモジュールをインポート
import math
import platform
import json # jsonモジュールをインポート

# ★追加: Blueprintをインポート
from blueprints.set_diagram import set_diagram_bp

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# データファイルのパスを定義
DATA_DIR = os.path.join(app.root_path, 'data')
BANDS_DATA_FILE = os.path.join(DATA_DIR, 'bands.json')

# バンド情報をJSONファイルから読み込む関数
def load_friends_bands():
    if not os.path.exists(BANDS_DATA_FILE):
        print(f"Warning: Data file not found at {BANDS_DATA_FILE}. Returning empty list.")
        return [] # ファイルがない場合は空のリストを返す
    try:
        with open(BANDS_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {BANDS_DATA_FILE}: {e}")
        return [] # JSON形式が不正な場合も空のリストを返す
    except Exception as e:
        print(f"Error reading {BANDS_DATA_FILE}: {e}")
        return []

# --- 日本語フォントをサーバー上で見つけるための関数 ---
def find_japanese_fonts():
    found_fonts = {}
    
    #  プロジェクトのルートにある 'fonts' フォルダを指すように変更
    base_fonts_dir = os.path.join(app.root_path, 'fonts') 
    
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
                        # 軽くフォントをロードして名前を取得
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
                        # print(f"Error loading font {file_path}: {e}") # デバッグ用
                        pass
    
    final_font_list = sorted([(name, path) for name, path in found_fonts.items()], key=lambda x: x[0].lower())

    if not final_font_list:
        final_font_list.append(("（日本語フォントが見つかりません）", None))

    return final_font_list

# ★追加: Blueprintを登録
app.register_blueprint(set_diagram_bp)


@app.route('/')
def home():
    """
    トップメニューページを表示します。
    """
    return render_template('index.html')

@app.route('/about')
def about_page():
    """
    「バンドマン太郎とは？」の説明ページを表示します。
    """
    return render_template('about.html')

@app.route('/flyer_maker')
def flyer_maker_form():
    """
    フライヤー作成フォームページを表示します。
    """
    month_options = [str(i) for i in range(1, 13)]
    current_month_num = datetime.now().month # ★変更: 現在の月の数値を取得

    today = datetime.now()
    current_year = today.year
    
    # 選択式の日付リストを生成
    # 指定された月の最終日を取得
    num_days = calendar.monthrange(current_year, current_month_num)[1]
    date_options = [str(i) for i in range(1, num_days + 1)]

    day_of_week_options = ["(月)", "(火)", "(水)", "(木)", "(金)", "(土)", "(日)"]
    
    japanese_fonts = find_japanese_fonts()
    default_selected_font_name = "Noto Sans JP" 
    default_selected_font_path = None
    for name, path in japanese_fonts:
        if name == "Noto Sans JP":
            default_selected_font_path = path
            break
    if not default_selected_font_path and japanese_fonts: 
        default_selected_font_name = japanese_fonts[0][0]
        default_selected_font_path = japanese_fonts[0][1]


    return render_template('flyer_form.html',
                           band_name="", 
                           month="", 
                           schedules=[], 
                           other_info="",
                           photo_scale=0.7, 
                           font_selection=default_selected_font_name, 
                           japanese_font_options=[{'name': name, 'path': path} for name, path in japanese_fonts],
                           default_selected_font_path=default_selected_font_path,
                           date_options=date_options, # ★追加
                           day_of_week_options=day_of_week_options # ★追加
                           )

@app.route('/sns_announcement')
def sns_announcement_form():
    """
    SNS告知文作成ツールのフォームページを表示します。
    """
    return render_template('sns_announcement_form.html')


@app.route('/generate_sns_announcement', methods=['POST'])
def generate_sns_announcement():
    """
    フォームからデータを受け取り、SNS告知文を生成して返します。
    """
    live_name = request.form.get('live_name', '').strip()
    live_date = request.form.get('live_date', '').strip()
    live_day_of_week = request.form.get('live_day_of_week', '').strip()
    venue = request.form.get('venue', '').strip()
    open_time = request.form.get('open_time', '').strip()
    start_time = request.form.get('start_time', '').strip()
    ticket_info = request.form.get('ticket_info', '').strip()
    ticket_link = request.form.get('ticket_link', '').strip()
    streaming_link = request.form.get('streaming_link', '').strip()
    performers = request.form.get('performers', '').strip() 

    selected_hashtags = request.form.getlist('hashtags') 

    announcement_parts = []

    # 【Live Info】
    # 日付 (曜日) 会場
    if live_date or live_day_of_week or venue:
        announcement_parts.append("【Live Info】")
        date_venue_line = []
        if live_date:
            date_venue_line.append(live_date)
        if live_day_of_week:
            # 曜日が入力されていれば、(月)のように括弧付きで追加
            date_venue_line.append(f"({live_day_of_week})")
        if venue:
            date_venue_line.append(venue)
        
        # すべて空でなければ行を追加
        if date_venue_line:
            announcement_parts.append(" ".join(date_venue_line))

    # ライブ名
    if live_name:
        # 直前の要素がLive Infoの行なら、間に空行を入れない
        # それ以外の場合は、前に空行を入れる
        if announcement_parts and announcement_parts[-1] not in ["【Live Info】"]:
            announcement_parts.append("") # 空行
        announcement_parts.append(f"『{live_name}』")

    # OPEN / START
    if open_time or start_time:
        announcement_parts.append("") # 空行
        if open_time and start_time:
            announcement_parts.append(f"OPEN / START {open_time} / {start_time}")
        elif open_time:
            announcement_parts.append(f"OPEN {open_time}")
        elif start_time:
            announcement_parts.append(f"START {start_time}")

    # チケット情報
    if ticket_info:
        announcement_parts.append("") # 空行
        announcement_parts.append(ticket_info)
    
    # URL (チケットリンクと配信リンク)
    url_added = False
    if ticket_link:
        if not url_added: announcement_parts.append("") # 空行
        announcement_parts.append(ticket_link)
        url_added = True
    if streaming_link:
        if not url_added: announcement_parts.append("") # 空行
        announcement_parts.append(f"配信 {streaming_link}")
        url_added = True

    # 共演者
    if performers:
        announcement_parts.append("") # 空行
        announcement_parts.append("w/")
        # 共演者を改行区切りで追加
        for performer_line in performers.split('\n'):
            if performer_line.strip(): # 空行でなければ追加
                announcement_parts.append(performer_line.strip())

    # ハッシュタグ
    if selected_hashtags:
        # 直前の要素が空行でなければ空行を追加
        if announcement_parts and announcement_parts[-1] != "":
            announcement_parts.append("") # 空行
        announcement_parts.append(" ".join(selected_hashtags)) 

    generated_text = "\n".join(announcement_parts)

    return render_template('sns_announcement_form.html', generated_text=generated_text)


@app.route('/generate_flyer', methods=['POST']) 
def generate_flyer():
    """
    フォームからデータを受け取り、フライヤー画像を生成して返します。
    """
    band_name = request.form['band_name']
    month_str = request.form['month']
    free_text = request.form.get('other_info', '').strip() 
    artist_photo = request.files.get('artist_photo')
    artist_photo_scale_factor = float(request.form.get('photo_scale', 0.7))
    
    background_color_hex = request.form.get('background_color', '#000000') 
    text_color_hex = request.form.get('text_color', '#FFFFFF') 

    selected_font_name = request.form.get('font_selection')
    selected_font_path = None
    all_japanese_fonts = find_japanese_fonts()
    for name, path in all_japanese_fonts:
        if name == selected_font_name:
            selected_font_path = path
            break
    
    if selected_font_path == "None" or not selected_font_path:
        selected_font_path = None

    schedules = []
    # ★変更: selectから値を受け取る
    schedule_date_nums = request.form.getlist('schedule_date_num[]')
    schedule_day_of_weeks = request.form.getlist('schedule_day_of_week[]')
    schedule_venues = request.form.getlist('schedule_venue[]')

    for i in range(len(schedule_date_nums)):
        date_num = schedule_date_nums[i].strip()
        day_of_week = schedule_day_of_weeks[i].strip()
        venue = schedule_venues[i].strip()
        
        # 少なくとも日付、曜日、会場のいずれかがあれば有効なスケジュールとみなす
        if date_num or day_of_week or venue:
            schedule_line_parts = []
            if date_num:
                schedule_line_parts.append(date_num)
            if day_of_week: 
                schedule_line_parts.append(day_of_week)
            
            if (date_num or day_of_week) and venue: 
                schedule_line_parts.append(" ") 

            if venue:
                schedule_line_parts.append(venue)
            
            filtered_parts = [p for p in schedule_line_parts if p.strip() != ""]
            schedule_line = "".join(filtered_parts) 
            
            if schedule_line: 
                schedules.append(schedule_line)

    if not schedules:
        print("Warning: No live schedules entered.")

    width = 2480
    height = 3508

    title_text = "Live Schedule"
    month_display_text = f"{month_str}"

    selected_font_path_for_pil = None
    if selected_font_path and os.path.exists(selected_font_path):
        selected_font_path_for_pil = selected_font_path
    else:
        print(f"Warning: Selected font file not found at {selected_font_path}. Attempting fallback.")
        if all_japanese_fonts and all_japanese_fonts[0][1]:
            selected_font_path_for_pil = all_japanese_fonts[0][1]
            print(f"Fallback to: {selected_font_path_for_pil}")
        else:
            print("No Japanese fonts found. Using Pillow's default font.")


    initial_font_size_title_month = 210
    initial_font_size_band_name = 180
    initial_font_size_free_text = 72
    initial_font_size_schedule = 120

    min_font_size_title_month = 120
    min_font_size_band_name = 100
    min_font_size_free_text = 40
    min_font_size_schedule = 45

    current_font_size_title_month = initial_font_size_title_month
    current_font_size_band_name = initial_font_size_band_name
    current_font_size_schedule = initial_font_size_schedule
    current_font_size_free_text = initial_font_size_free_text

    horizontal_padding = 120
    fallback_vertical_padding = 30
    gap_title_band = 100
    gap_band_photo = 120
    gap_photo_schedule = 120
    schedule_line_gap = 40 
    gap_schedule_free = 80
    free_text_line_gap = 20 
    schedule_part_gap = 60 

    SCHEDULE_TWO_COLUMN_THRESHOLD = 4

    max_adjustment_iterations = 150

    total_content_height_needed = 0

    for iteration in range(max_adjustment_iterations):
        try:
            font_title_month = ImageFont.truetype(selected_font_path_for_pil, current_font_size_title_month) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_title_month)
            font_band_name = ImageFont.truetype(selected_font_path_for_pil, current_font_size_band_name) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_band_name)
            font_schedule_for_check = ImageFont.truetype(selected_font_path_for_pil, current_font_size_schedule) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_schedule)
            font_free_text = ImageFont.truetype(selected_font_path_for_pil, current_font_size_free_text) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_free_text)

        except Exception as e:
            print(f"Font loading error during adjustment: {e}. Attempting fallback.")
            if selected_font_path_for_pil: 
                selected_font_path_for_pil = None 
                print("Switched to Pillow's default font for calculation.")
                continue 
            else: 
                print("Could not load any font. Exiting font adjustment loop.")
                break

        temp_draw_for_height_calc = ImageDraw.Draw(Image.new('RGB', (1, 1)))

        combined_title_text = f"{title_text} {month_display_text}"
        title_bbox = temp_draw_for_height_calc.textbbox((0,0), combined_title_text, font=font_title_month)
        title_height = title_bbox[3] - title_bbox[1]

        band_name_bbox = temp_draw_for_height_calc.textbbox((0,0), band_name, font=font_band_name)
        band_name_height = band_name_bbox[3] - band_name_bbox[1]

        artist_photo_height = 0
        artist_photo_max_width = width - (horizontal_padding * 2)
        if artist_photo and artist_photo.filename:
            artist_photo.stream.seek(0) 
            try:
                artist_photo_img_temp = Image.open(artist_photo.stream).convert("RGBA")
                target_width = artist_photo_max_width * artist_photo_scale_factor
                if artist_photo_img_temp.width > target_width:
                    aspect_ratio = target_width / artist_photo_img_temp.width
                    resized_height = int(artist_photo_img_temp.height * aspect_ratio)
                    artist_photo_height = resized_height
                else:
                    artist_photo_height = artist_photo_img_temp.height
            except Exception as e:
                print(f"Error processing uploaded image for height calculation: {e}")
                artist_photo_height = 0 
        photo_area_height = artist_photo_height 

        total_schedule_height_calc = 0
        min_schedule_font_size_for_width = current_font_size_schedule 

        schedule_items_parsed = []
        for s_line in schedules:
            # 日付(曜日)とそれ以降（会場）を分ける
            match = re.match(r'(\d+ ?\(.\))?\s*(.*)', s_line) 
            if match:
                date_day_part = match.group(1) if match.group(1) else ""
                venue_part = match.group(2) if match.group(2) else s_line 
                schedule_items_parsed.append({'date_day': date_day_part.strip(), 'venue_text': venue_part.strip()})
            else: 
                schedule_items_parsed.append({'date_day': '', 'venue_text': s_line.strip()})
        
        for s_item in schedule_items_parsed:
            date_day_text = s_item['date_day']
            venue_text = s_item['venue_text'] 

            temp_check_font_size = min_schedule_font_size_for_width

            while temp_check_font_size >= min_font_size_schedule:
                temp_check_font = ImageFont.truetype(selected_font_path_for_pil, temp_check_font_size) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=temp_check_font_size)
                
                date_width = temp_draw_for_height_calc.textlength(date_day_text, font=temp_check_font)
                venue_width = temp_draw_for_height_calc.textlength(venue_text, font=temp_check_font)

                current_item_total_width = date_width + schedule_part_gap + venue_width

                if len(schedules) > SCHEDULE_TWO_COLUMN_THRESHOLD:
                    col_total_width = width - (horizontal_padding * 2)
                    col_gap_actual = 80 
                    col_width_per_item = (col_total_width - col_gap_actual) / 2 
                    if current_item_total_width <= col_width_per_item:
                        break 
                else:
                    if current_item_total_width <= (width - (horizontal_padding * 2)):
                        break 

                temp_check_font_size -= 1 

            min_schedule_font_size_for_width = min(min_schedule_font_size_for_width, temp_check_font_size)

        current_font_size_schedule = min(current_font_size_schedule, min_schedule_font_size_for_width)
        current_font_size_schedule = max(min_font_size_schedule, current_font_size_schedule)

        font_schedule_for_calc_height = ImageFont.truetype(selected_font_path_for_pil, current_font_size_schedule) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_schedule)
        schedule_bbox = temp_draw_for_height_calc.textbbox((0,0), "A", font=font_schedule_for_calc_height)
        schedule_line_base_height = schedule_bbox[3] - schedule_bbox[1]

        current_schedule_item_height_calc = schedule_line_base_height + schedule_line_gap

        if len(schedules) > SCHEDULE_TWO_COLUMN_THRESHOLD:
            num_rows = math.ceil(len(schedules) / 2)
            total_schedule_height_calc = num_rows * current_schedule_item_height_calc
        else:
            total_schedule_height_calc = len(schedules) * current_schedule_item_height_calc

        free_text_display_lines = []
        free_text_area_height_calc = 0
        if free_text:
            free_text_max_width = width - (horizontal_padding * 2)
            
            temp_wrapped_lines = []
            for line in free_text.split('\n'):
                if not line.strip(): 
                    temp_wrapped_lines.append("")
                    continue

                current_wrapped_line = ""
                for char in line:
                    test_line = current_wrapped_line + char
                    if temp_draw_for_height_calc.textlength(test_line, font=font_free_text) <= free_text_max_width:
                        current_wrapped_line = test_line
                    else:
                        temp_wrapped_lines.append(current_wrapped_line)
                        current_wrapped_line = char 
                if current_wrapped_line.strip() or current_wrapped_line == "": 
                    temp_wrapped_lines.append(current_wrapped_line)
            free_text_display_lines = temp_wrapped_lines

            if free_text_display_lines:
                for i, line_item in enumerate(free_text_display_lines):
                    line_bbox = temp_draw_for_height_calc.textbbox((0,0), "A", font=font_free_text)
                    line_height_for_calc = line_bbox[3] - line_bbox[1]
                    free_text_area_height_calc += line_height_for_calc
                    if i < len(free_text_display_lines) - 1:
                        free_text_area_height_calc += free_text_line_gap

        total_content_height_needed = (
            title_height + gap_title_band +
            band_name_height + gap_band_photo +
            photo_area_height + gap_photo_schedule +
            total_schedule_height_calc 
        )
        if free_text_area_height_calc > 0:
            total_content_height_needed += gap_schedule_free + free_text_area_height_calc

        if total_content_height_needed <= height:
            break 

        if current_font_size_schedule > min_font_size_schedule:
            current_font_size_schedule = max(min_font_size_schedule, current_font_size_schedule - 2)
        elif current_font_size_free_text > min_font_size_free_text:
            current_font_size_free_text -= 2
        elif current_font_size_band_name > min_font_size_band_name:
            current_font_size_band_name -= 2
        elif current_font_size_title_month > min_font_size_title_month:
            current_font_size_title_month -= 2
        else:
            print("Warning: All font sizes scaled to minimum, but content may still not fit.")
            break

    vertical_margin = (height - total_content_height_needed) / 2
    if vertical_margin < 0:
        vertical_margin = fallback_vertical_padding
        print("Warning: Content too large for A4. Margin set to minimum.")
    elif iteration == max_adjustment_iterations - 1 and total_content_height_needed > height:
         print("Warning: Max adjustment iterations reached. Content may not fit.")

    y_current_offset = vertical_margin

    img = Image.new('RGB', (width, height), color=background_color_hex)
    d = ImageDraw.Draw(img)

    font_title_month = ImageFont.truetype(selected_font_path_for_pil, current_font_size_title_month) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_title_month)
    font_band_name = ImageFont.truetype(selected_font_path_for_pil, current_font_size_band_name) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_band_name)
    font_schedule_render = ImageFont.truetype(selected_font_path_for_pil, current_font_size_schedule) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_schedule)
    font_free_text = ImageFont.truetype(selected_font_path_for_pil, current_font_size_free_text) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_free_text)

    combined_title_text = f"{title_text} {month_display_text}"
    title_text_bbox = d.textbbox((0,0), combined_title_text, font=font_title_month)
    title_text_width = title_text_bbox[2] - title_text_bbox[0]
    title_x = (width - title_text_width) / 2
    d.text((int(title_x), int(y_current_offset)), combined_title_text, fill=text_color_hex, font=font_title_month)
    y_current_offset += (title_text_bbox[3] - title_text_bbox[1]) + gap_title_band

    band_name_text_bbox = d.textbbox((0,0), band_name, font=font_band_name)
    band_name_text_width = band_name_text_bbox[2] - band_name_text_bbox[0]
    band_name_x = (width - band_name_text_width) / 2
    d.text((int(band_name_x), int(y_current_offset)), band_name, fill=text_color_hex, font=font_band_name)
    y_current_offset += (band_name_text_bbox[3] - band_name_text_bbox[1]) + gap_band_photo

    if artist_photo and artist_photo.filename:
        artist_photo.stream.seek(0)
        try:
            artist_photo_img = Image.open(artist_photo.stream).convert("RGBA")

            target_width = artist_photo_max_width * artist_photo_scale_factor

            if artist_photo_img.width > target_width:
                aspect_ratio = target_width / artist_photo_img.width
                artist_photo_img = artist_photo_img.resize((int(target_width), int(artist_photo_img.height * aspect_ratio)), Image.Resampling.LANCZOS)
            photo_x = (width - artist_photo_img.width) / 2
            img.paste(artist_photo_img, (int(photo_x), int(y_current_offset)), artist_photo_img)
            y_current_offset += artist_photo_img.height + gap_photo_schedule
        except Exception as e:
            print(f"Error drawing uploaded image: {e}")
    else:
         print("No artist photo uploaded.")

    schedule_y_start_for_draw = y_current_offset
    schedule_line_height_for_draw = d.textbbox((0,0), "A", font=font_schedule_render)[3] - d.textbbox((0,0), "A", font=font_schedule_render)[1]

    if len(schedules) > SCHEDULE_TWO_COLUMN_THRESHOLD:
        num_rows = math.ceil(len(schedules) / 2)
        col1_items = schedule_items_parsed[:num_rows]
        col2_items = schedule_items_parsed[num_rows:]

        col_total_width = width - (horizontal_padding * 2)
        col_gap_actual = 80
        col_width_per_item = (col_total_width - col_gap_actual) / 2

        for i in range(max(len(col1_items), len(col2_items))):
            current_y_for_draw = int(schedule_y_start_for_draw + i * (schedule_line_height_for_draw + schedule_line_gap))

            if i < len(col1_items):
                date_day_text = col1_items[i]['date_day']
                venue_text = col1_items[i]['venue_text'] 

                date_width = d.textlength(date_day_text, font=font_schedule_render)
                
                x_date_col1 = horizontal_padding
                x_venue_col1 = int(x_date_col1 + date_width + schedule_part_gap)

                d.text((x_date_col1, current_y_for_draw), date_day_text, fill=text_color_hex, font=font_schedule_render)
                d.text((x_venue_col1, current_y_for_draw), venue_text, fill=text_color_hex, font=font_schedule_render)

            if i < len(col2_items):
                date_day_text = col2_items[i]['date_day']
                venue_text = col2_items[i]['venue_text'] 

                date_width = d.textlength(date_day_text, font=font_schedule_render)

                col2_x_start = horizontal_padding + col_width_per_item + col_gap_actual
                x_date_col2 = col2_x_start
                x_venue_col2 = int(x_date_col2 + date_width + schedule_part_gap)

                d.text((int(x_date_col2), current_y_for_draw), date_day_text, fill=text_color_hex, font=font_schedule_render)
                d.text((x_venue_col2, current_y_for_draw), venue_text, fill=text_color_hex, font=font_schedule_render)
    else:
        for i, schedule_item in enumerate(schedule_items_parsed):
            date_day_text = schedule_item['date_day']
            venue_text = schedule_item['venue_text'] 
            current_y_for_draw = int(schedule_y_start_for_draw + i * (schedule_line_height_for_draw + schedule_line_gap))

            date_width = d.textlength(date_day_text, font=font_schedule_render)
            venue_width = d.textlength(venue_text, font=font_schedule_render)

            total_item_width_for_draw = date_width + schedule_part_gap + venue_width

            x_start_item_for_draw = (width - total_item_width_for_draw) / 2

            x_date = x_start_item_for_draw
            x_venue = x_start_item_for_draw + date_width + schedule_part_gap

            d.text((int(x_date), current_y_for_draw), date_day_text, fill=text_color_hex, font=font_schedule_render)
            d.text((int(x_venue), current_y_for_draw), venue_text, fill=text_color_hex, font=font_schedule_render)

    y_current_offset = schedule_y_start_for_draw + total_schedule_height_calc + gap_schedule_free

    current_free_text_y_for_draw = y_current_offset
    if free_text_display_lines:
        for i, wrapped_line_item in enumerate(free_text_display_lines):
            line_width = d.textlength(wrapped_line_item, font=font_free_text)
            line_x = (width - line_width) / 2 
            line_bbox = d.textbbox((0,0), "A", font=font_free_text)
            line_height_for_draw = line_bbox[3] - line_bbox[1]
            d.text((int(line_x), int(current_free_text_y_for_draw)), wrapped_line_item, fill=text_color_hex, font=font_free_text)
            current_free_text_y_for_draw += line_height_for_draw
            if i < len(free_text_display_lines) - 1:
                current_free_text_y_for_draw += free_text_line_gap

    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)

    file_name = f"{band_name}_{month_str}月ライブスケジュール_A4.png"

    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=file_name)


@app.route('/friends')
def friends_page():
    """
    バンドマン太郎の友達（支援バンド紹介）ページを表示します。
    """
    bands_data = load_friends_bands() # JSONからバンド情報を読み込む
    return render_template('friends.html', bands=bands_data) # テンプレートに渡す


if __name__ == '__main__':
     # dataディレクトリが存在しない場合は作成
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    # bands.jsonが存在しない場合は空のリストで初期化（任意、初回起動時のみ）
    if not os.path.exists(BANDS_DATA_FILE):
        with open(BANDS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
            print(f"Created empty {BANDS_DATA_FILE}")
    app.run(debug=True)