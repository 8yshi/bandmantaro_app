# blueprints/set_diagram.py

from flask import render_template, Blueprint, request, current_app, redirect, url_for, flash
import os
from utils import find_japanese_fonts, load_friends_bands

set_diagram_bp = Blueprint('set_diagram_bp', __name__, template_folder='templates', static_folder='static')

# UPLOAD_FOLDER や画像生成ロジックは、このインタラクティブなツールでは基本的に不要になります。
# もしサーバーサイドで画像を保存する機能も残したい場合は、別途実装が必要ですが、
# まずはインタラクティブなキャンバスが動くことを優先します。

@set_diagram_bp.route('/set_diagram_maker', methods=['GET', 'POST'])
def set_diagram_form():
    # このツールはフロントエンドで画像を生成するため、
    # バックエンドでは単にテンプレートをレンダリングするだけでOK
    # フォームで送信されたデータを受け取る必要も基本的にはありません。
    
    # ただし、もし font_selection のドロップダウンを動的にしたい場合は
    # find_japanese_fonts() を呼び出してテンプレートに渡すことはできます。
    # このHTMLにはフォント選択のセレクトボックスがないため、これは不要。
    # japanese_font_options = find_japanese_fonts() 
    # default_selected_font_name = japanese_font_options[0][0] if japanese_font_options else None
    
    # 以前のフォームデータ保持変数も不要になります。
    # band_name = ""
    # event_name = ""
    # date = ""
    # member_names = ""
    # notes = ""
    # generated_image_url = None

    return render_template('set_diagram_form.html')
    # もしフォント選択をHTMLで表示するなら、以下のように渡します
    # return render_template('set_diagram_form.html', font_options=japanese_font_options, default_selected_font_name=default_selected_font_name)