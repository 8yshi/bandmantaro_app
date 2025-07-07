from flask import Flask, render_template, request, send_file
import os
import io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import math
import platform

app = Flask(__name__)

# アップロードされたファイルを一時的に保存するフォルダ
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- 日本語フォントをサーバー上で見つけるための関数 ---
def find_japanese_fonts():
    found_fonts = {} # 辞書を使ってフォントファミリー名をキーに、パスを値にする
    # Flaskアプリのルートディレクトリからfontsフォルダを探索
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
                        font = ImageFont.truetype(file_path, 10)
                        font_family_name = font.getname()[0] # フォントファミリー名を取得
                        
                        # 日本語フォントのキーワードでフィルタリング
                        if any(keyword in font_family_name.lower() or keyword in file_name.lower() for keyword in japanese_font_keywords):
                            # 同じファミリー名のフォントが既に登録されているかチェック
                            if font_family_name not in found_fonts:
                                # まだ登録されていない場合、このフォント（例: 最初に見つかったRegularなど）を登録
                                found_fonts[font_family_name] = file_path
                            else:
                                # 既に登録されている場合でも、より「Regular」に近いものがあれば更新
                                # これは簡易的なロジックで、より堅牢なフォント選択が必要な場合は複雑化します
                                if "regular" in file_name.lower() and "regular" not in os.path.basename(found_fonts[font_family_name]).lower():
                                    found_fonts[font_family_name] = file_path
                                elif "jp-regular" in file_name.lower() and "jp-regular" not in os.path.basename(found_fonts[font_family_name]).lower():
                                     found_fonts[font_family_name] = file_path

                    except Exception as e:
                        # print(f"Error loading font {file_path}: {e}") # デバッグ用にコメントアウト解除しても良い
                        pass # 読み込めないフォントは無視
    
    # 辞書を (フォント名, パス) のタプルのリストに変換し、ソート
    # ここで、ユーザーに表示されるフォント名をより分かりやすく調整することも可能
    # 例: "NotoSansJP-Regular" -> "Noto Sans JP"
    final_font_list = []
    for name, path in found_fonts.items():
        # 表示名を調整する例 (必要であれば)
        display_name = name.replace("_", " ") # アンダースコアをスペースに
        display_name = display_name.replace("  ", " ") # 重複スペースを削除
        if "Noto Sans JP" in display_name and "Noto Sans JP" not in [n for n,p in final_font_list]: # 既にNoto Sans JPが追加済みかチェック
            final_font_list.append(("Noto Sans JP", path))
        elif "Noto Serif JP" in display_name and "Noto Serif JP" not in [n for n,p in final_font_list]: # 既にNoto Serif JPが追加済みかチェック
             final_font_list.append(("Noto Serif JP", path))
        elif "Dela Gothic One" in display_name and "Dela Gothic One" not in [n for n,p in final_font_list]:
            final_font_list.append(("Dela Gothic One", path))
        elif "M PLUS Rounded 1c" in display_name and "M PLUS Rounded 1c" not in [n for n,p in final_font_list]:
            final_font_list.append(("M PLUS Rounded 1c", path))
        else:
            final_font_list.append((display_name, path)) # その他のフォント

    # フォント名をアルファベット順にソート
    final_font_list.sort(key=lambda x: x[0].lower())


    # フォントが見つからない場合のフォールバック（表示用）
    if not final_font_list:
        final_font_list.append(("（日本語フォントが見つかりません）", None))

    return final_font_list


@app.route('/')
def home():
    """
    トップメニューページを表示します。
    """
    return render_template('index.html') # 新しいindex.htmlをレンダリング

@app.route('/flyer_maker')
def flyer_maker_form():
    """
    フライヤー作成フォームページを表示します。
    """
    # 月の選択肢を生成
    month_options = [str(i) for i in range(1, 13)]
    current_month = str(datetime.now().month)

    # 日付の選択肢を生成（現在の月の最終日まで）
    today = datetime.now()
    current_year = today.year
    try:
        if int(current_month) == 12:
            last_day_of_month = datetime(current_year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day_of_month = datetime(current_year, int(current_month) + 1, 1) - timedelta(days=1)
    except ValueError:
        last_day_of_month = (datetime(today.year, today.month, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    date_options = [str(i) for i in range(1, last_day_of_month.day + 1)]
    day_of_week_options = ["(月)", "(火)", "(水)", "(木)", "(金)", "(土)", "(日)"]

    # --- フォント選択肢を渡す ---
    japanese_fonts = find_japanese_fonts()
    # render_templateに渡すのは (表示名, パス) のタプルのリスト
    # デフォルトの選択は最初のフォントにする（もしあれば）
    default_selected_font_name = japanese_fonts[0][0] if japanese_fonts and japanese_fonts[0][1] else "（日本語フォントが見つかりません）"
    default_selected_font_path = japanese_fonts[0][1] if japanese_fonts and japanese_fonts[0][1] else "" # パスも渡す

    return render_template('flyer_form.html', # リネームしたflyer_form.htmlをレンダリング
                           month_options=month_options,
                           current_month=current_month,
                           date_options=date_options,
                           current_date=str(today.day),
                           day_of_week_options=day_of_week_options,
                           current_day_of_week=day_of_week_options[(today.weekday()) % 7],
                           japanese_font_options=[{'name': name, 'path': path} for name, path in japanese_fonts], # 表示名とパスの辞書リストを渡す
                           default_selected_font_name=default_selected_font_name,
                           default_selected_font_path=default_selected_font_path
                           )


@app.route('/generate', methods=['POST'])
def generate_flyer():
    """
    フォームからデータを受け取り、フライヤー画像を生成して返します。
    """
    band_name = request.form['band_name']
    month_str = request.form['month']
    free_text = request.form['free_text']
    artist_photo = request.files.get('artist_photo')
    artist_photo_scale_factor = float(request.form.get('photo_scale', 0.7)) # デフォルトは0.7
    
    # --- フォームから選択されたフォントパスを取得 ---
    selected_font_path = request.form.get('selected_font_path')
    if selected_font_path == "None": # Noneが文字列として送られてくる可能性があるため
        selected_font_path = None

    schedules = []
    schedule_count = int(request.form['schedule_count'])
    for i in range(schedule_count):
        venue = request.form.get(f'venue_{i}', '').strip()
        date = request.form.get(f'date_{i}', '').strip()
        day_of_week = request.form.get(f'day_of_week_{i}', '').strip()
        if venue and date and day_of_week:
            schedules.append(f"{date}{day_of_week} {venue}")

    if not schedules:
        return "ライブスケジュールが入力されていません。", 400

    # --- A4サイズと解像度（固定） ---
    width = 2480
    height = 3508

    # --- 各種テキスト定義 ---
    title_text = "Live Schedule"
    month_display_text = f"{month_str}月"

    # --- フォント読み込み ---
    # selected_font_path が None または存在しない場合はデフォルトフォントを使用
    if not selected_font_path or not os.path.exists(selected_font_path):
        print(f"Warning: Selected font file not found at {selected_font_path}. Using default font.")
        # selected_font_path を None にして、ImageFont.truetype() がデフォルトフォントを使うようにする
        selected_font_path_for_pil = None
    else:
        selected_font_path_for_pil = selected_font_path


    # --- 初期フォントサイズ ---
    initial_font_size_title_month = 210
    initial_font_size_band_name = 180
    initial_font_size_free_text = 72
    initial_font_size_schedule = 120

    # --- 最小フォントサイズ ---
    min_font_size_title_month = 120
    min_font_size_band_name = 100
    min_font_size_free_text = 40
    min_font_size_schedule = 45

    current_font_size_title_month = initial_font_size_title_month
    current_font_size_band_name = initial_font_size_band_name
    current_font_size_schedule = initial_font_size_schedule
    current_font_size_free_text = initial_font_size_free_text

    # --- 余白など (固定) ---
    horizontal_padding = 120
    fallback_vertical_padding = 30
    gap_title_band = 100
    gap_band_photo = 80
    gap_photo_schedule = 80
    schedule_line_gap = 40
    gap_schedule_free = 80
    free_text_line_gap = 20
    schedule_part_gap = 60

    SCHEDULE_TWO_COLUMN_THRESHOLD = 4

    max_adjustment_iterations = 150

    total_content_height_needed = 0

    # フォントサイズ調整ループ (flyermaker.pyからの主要ロジック)
    for iteration in range(max_adjustment_iterations):
        try:
            # selected_font_path_for_pil を使用
            font_title_month = ImageFont.truetype(selected_font_path_for_pil, current_font_size_title_month) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_title_month)
            font_band_name = ImageFont.truetype(selected_font_path_for_pil, current_font_size_band_name) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_band_name)
            temp_font_schedule_for_check = ImageFont.truetype(selected_font_path_for_pil, current_font_size_schedule) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_schedule)
            font_free_text = ImageFont.truetype(selected_font_path_for_pil, current_font_size_free_text) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_free_text)

        except Exception as e:
            print(f"Font loading error during adjustment: {e}. Using default font.")
            font_title_month = ImageFont.load_default().font_variant(size=current_font_size_title_month)
            font_band_name = ImageFont.load_default().font_variant(size=current_font_size_band_name)
            temp_font_schedule_for_check = ImageFont.load_default().font_variant(size=current_font_size_schedule)
            font_free_text = ImageFont.load_default().font_variant(size=current_font_size_free_text)

        temp_draw_for_height_calc = ImageDraw.Draw(Image.new('RGB', (1, 1)))

        combined_title_text = f"{title_text} {month_display_text}"
        title_height = temp_draw_for_height_calc.textbbox((0,0), combined_title_text, font=font_title_month)[3] - temp_draw_for_height_calc.textbbox((0,0), combined_title_text, font=font_title_month)[1]

        band_name_height = temp_draw_for_height_calc.textbbox((0,0), band_name, font=font_band_name)[3] - temp_draw_for_height_calc.textbbox((0,0), band_name, font=font_band_name)[1]

        artist_photo_height = 0
        artist_photo_max_width = width - (horizontal_padding * 2)
        if artist_photo and artist_photo.filename:
            # アップロードされたファイルをメモリ上で処理
            try:
                # stream.seek(0) は generate_flyer の冒頭で一度行うだけで良い
                artist_photo_img_temp = Image.open(artist_photo.stream).convert("RGBA")
                target_width = artist_photo_max_width * artist_photo_scale_factor
                if artist_photo_img_temp.width > target_width:
                    aspect_ratio = target_width / artist_photo_img_temp.width
                    resized_height = int(artist_photo_img_temp.height * aspect_ratio)
                    artist_photo_height = resized_height
                else:
                    artist_photo_height = artist_photo_img_temp.height
            except Exception as e:
                print(f"Error processing uploaded image: {e}")
                # エラー時は画像を無視
        photo_area_height = artist_photo_height

        total_schedule_height_calc = 0
        min_schedule_font_size_for_width = initial_font_size_schedule

        schedule_items_parsed = []
        for s in schedules:
            parts = s.split(' ', 1)
            date_day = parts[0]
            venue = parts[1] if len(parts) > 1 else ""
            schedule_items_parsed.append({'date_day': date_day, 'venue': venue})

        for s_item in schedule_items_parsed:
            date_day_text = s_item['date_day']
            venue_text = s_item['venue']

            temp_check_font_size = min_schedule_font_size_for_width

            while temp_check_font_size >= min_font_size_schedule:
                temp_check_font = ImageFont.truetype(selected_font_path_for_pil, temp_check_font_size) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=temp_check_font_size)
                date_width = temp_draw_for_height_calc.textlength(date_day_text, font=temp_check_font)
                venue_width = temp_draw_for_height_calc.textlength(venue_text, font=temp_check_font)

                if len(schedules) > SCHEDULE_TWO_COLUMN_THRESHOLD:
                    col_total_width = width - (horizontal_padding * 2)
                    col_gap_actual = 80
                    col_width_per_item = (col_total_width - col_gap_actual) / 2
                    current_item_total_width = date_width + schedule_part_gap + venue_width
                    if current_item_total_width <= col_width_per_item:
                        break
                else:
                    current_item_total_width = date_width + schedule_part_gap + venue_width
                    if current_item_total_width <= (width - (horizontal_padding * 2)):
                        break

                temp_check_font_size -= 1

            min_schedule_font_size_for_width = min(min_schedule_font_size_for_width, temp_check_font_size)

        current_font_size_schedule = min(current_font_size_schedule, min_schedule_font_size_for_width)
        current_font_size_schedule = max(min_font_size_schedule, current_font_size_schedule)

        font_schedule_for_calc_height = ImageFont.truetype(selected_font_path_for_pil, current_font_size_schedule) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_schedule)
        schedule_line_base_height = temp_draw_for_height_calc.textbbox((0,0), "A", font=font_schedule_for_calc_height)[3] - temp_draw_for_height_calc.textbbox((0,0), "A", font=font_schedule_for_calc_height)[1]

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
                words = line.split(' ')
                current_wrapped_line = ""
                for word in words:
                    test_line = current_wrapped_line + (" " if current_wrapped_line else "") + word
                    if temp_draw_for_height_calc.textlength(test_line, font=font_free_text) <= free_text_max_width:
                        current_wrapped_line = test_line
                    else:
                        if current_wrapped_line:
                            temp_wrapped_lines.append(current_wrapped_line)
                        current_wrapped_line = word
                if current_wrapped_line.strip():
                    temp_wrapped_lines.append(current_wrapped_line.strip())
            free_text_display_lines = temp_wrapped_lines

            if free_text_display_lines:
                for i, line_item in enumerate(free_text_display_lines):
                    line_height_for_calc = temp_draw_for_height_calc.textbbox((0,0), "A", font=font_free_text)[3] - temp_draw_for_height_calc.textbbox((0,0), "A", font=font_free_text)[1]
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
            print("Warning: Font size scaled to minimum, but content may still not fit.")
            break

    vertical_margin = (height - total_content_height_needed) / 2
    if vertical_margin < 0:
        vertical_margin = fallback_vertical_padding
        print("Warning: Content too large for A4. Margin set to minimum.")
    elif iteration == max_adjustment_iterations - 1 and total_content_height_needed > height:
         print("Warning: Max adjustment iterations reached. Content may not fit.")

    y_current_offset = vertical_margin

    # --- 画像の描画 ---
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    d = ImageDraw.Draw(img)

    # 描画時のフォントサイズは調整後のものを使用
    font_title_month = ImageFont.truetype(selected_font_path_for_pil, current_font_size_title_month) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_title_month)
    font_band_name = ImageFont.truetype(selected_font_path_for_pil, current_font_size_band_name) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_band_name)
    font_schedule_render = ImageFont.truetype(selected_font_path_for_pil, current_font_size_schedule) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_schedule)
    font_free_text = ImageFont.truetype(selected_font_path_for_pil, current_font_size_free_text) if selected_font_path_for_pil else ImageFont.load_default().font_variant(size=current_font_size_free_text)


    title_width = d.textlength(title_text, font=font_title_month)
    month_width = d.textlength(month_display_text, font=font_title_month)
    combined_width = title_width + 60 + month_width
    start_x = (width - combined_width) / 2
    d.text((int(start_x), int(y_current_offset)), title_text, fill=(255, 255, 255), font=font_title_month)
    d.text((int(start_x + title_width + 60), int(y_current_offset)), month_display_text, fill=(255, 255, 255), font=font_title_month)
    y_current_offset += title_height + gap_title_band

    band_name_text_width = d.textlength(band_name, font=font_band_name)
    start_x = (width - band_name_text_width) / 2
    d.text((int(start_x), int(y_current_offset)), band_name, fill=(255, 255, 255), font=font_band_name)
    y_current_offset += band_name_height + gap_band_photo

    if artist_photo and artist_photo.filename:
        try:
            # stream.seek(0) は generate_flyer の冒頭で一度行うだけで良い
            artist_photo.stream.seek(0) # ストリームの読み取り位置を先頭に戻す (再読込に備える)
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
    elif artist_photo and not artist_photo.filename: # ファイルが選択されていないが、オブジェクトは存在する場合
        pass # 何もしない
    else: # ファイルがアップロードされていない場合
         print("No artist photo uploaded.")


    schedule_y_start_for_draw = y_current_offset
    schedule_line_height_for_draw = d.textbbox((0,0), "A", font=font_schedule_render)[3] - d.textbbox((0,0), "A", font=font_schedule_render)[1]

    if len(schedules) > SCHEDULE_TWO_COLUMN_THRESHOLD:
        num_rows = math.ceil(len(schedules) / 2)
        col1_items = schedule_items_parsed[:num_rows]
        col2_items = schedule_items_parsed[num_rows:]

        col_total_width = width - (horizontal_padding * 2)
        col_gap_actual = 80

        for i in range(max(len(col1_items), len(col2_items))):
            current_y_for_draw = int(schedule_y_start_for_draw + i * (schedule_line_height_for_draw + schedule_line_gap))

            if i < len(col1_items):
                date_day_text = col1_items[i]['date_day']
                venue_text = col1_items[i]['venue']

                date_width = d.textlength(date_day_text, font=font_schedule_render)
                x_venue = int(horizontal_padding + date_width + schedule_part_gap)

                d.text((horizontal_padding, current_y_for_draw), date_day_text, fill=(255, 255, 255), font=font_schedule_render)
                d.text((x_venue, current_y_for_draw), venue_text, fill=(255, 255, 255), font=font_schedule_render)

            if i < len(col2_items):
                date_day_text = col2_items[i]['date_day']
                venue_text = col2_items[i]['venue']

                date_width = d.textlength(date_day_text, font=font_schedule_render)

                col2_x_start = horizontal_padding + col_total_width / 2 + col_gap_actual / 2 
                x_venue_col2 = int(col2_x_start + date_width + schedule_part_gap)

                d.text((int(col2_x_start), current_y_for_draw), date_day_text, fill=(255, 255, 255), font=font_schedule_render)
                d.text((x_venue_col2, current_y_for_draw), venue_text, fill=(255, 255, 255), font=font_schedule_render)
    else:
        for i, schedule_item in enumerate(schedule_items_parsed):
            date_day_text = schedule_item['date_day']
            venue_text = schedule_item['venue']
            current_y_for_draw = int(schedule_y_start_for_draw + i * (schedule_line_height_for_draw + schedule_line_gap))

            date_width = d.textlength(date_day_text, font=font_schedule_render)
            venue_width = d.textlength(venue_text, font=font_schedule_render)

            total_item_width_for_draw = date_width + schedule_part_gap + venue_width

            x_start_item_for_draw = (width - total_item_width_for_draw) / 2

            x_date = x_start_item_for_draw
            x_venue = x_start_item_for_draw + date_width + schedule_part_gap

            d.text((int(x_date), current_y_for_draw), date_day_text, fill=(255, 255, 255), font=font_schedule_render)
            d.text((int(x_venue), current_y_for_draw), venue_text, fill=(255, 255, 255), font=font_schedule_render)

    y_current_offset = schedule_y_start_for_draw + total_schedule_height_calc + gap_schedule_free

    current_free_text_y_for_draw = y_current_offset
    if free_text_display_lines:
        for i, wrapped_line_item in enumerate(free_text_display_lines):
            line_width = d.textlength(wrapped_line_item, font=font_free_text)
            line_x = (width - line_width) / 2
            line_height_for_draw = d.textbbox((0,0), "A", font=font_free_text)[3] - d.textbbox((0,0), "A", font=font_free_text)[1]
            d.text((int(line_x), int(current_free_text_y_for_draw)), wrapped_line_item, fill=(255, 255, 255), font=font_free_text)
            current_free_text_y_for_draw += line_height_for_draw
            if i < len(free_text_display_lines) - 1:
                current_free_text_y_for_draw += free_text_line_gap

    # 画像をメモリに保存し、レスポンスとして返す
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)

    # ファイル名を生成
    file_name = f"{band_name}_{month_str}月ライブスケジュール_A4.png"

    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=file_name)

if __name__ == '__main__':
    # 開発時にはデバッグモードを有効にすると便利です
    # 本番環境（Render.com）では無効にしてください
    app.run(debug=True)