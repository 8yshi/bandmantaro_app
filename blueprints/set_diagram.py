# blueprints/set_diagram.py

from flask import render_template, Blueprint, request, current_app, redirect, url_for, flash
import os
from utils import find_japanese_fonts, load_friends_bands

set_diagram_bp = Blueprint('set_diagram_bp', __name__, template_folder='templates', static_folder='static')


@set_diagram_bp.route('/set_diagram_maker', methods=['GET', 'POST'])
def set_diagram_form():


    return render_template('set_diagram_form.html')
  