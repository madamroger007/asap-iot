from flask import Blueprint, render_template, redirect, request, url_for, session, flash, jsonify, current_app
import app.config as config
from app.src.utils import cards,table_rows   
from app.src.routes.validation.login import login_required
from app.src.repositories.data_sensor_repositories import get_all_data_sensors_repository
from app.src.repositories.nohp_repositories import (
    get_all_nomor_hp,
)
main = Blueprint('main', __name__)
@main.route('/')
@login_required
def index():
    data_sensor = get_all_data_sensors_repository()
    if data_sensor is None:
        flash("Data sensor tidak ditemukan.", "danger")
        return redirect(url_for('main.index'))
    return render_template('pages/index.html', cards=cards, table_rows=data_sensor)

@main.route('/whatsapp', methods=['GET'])
@login_required
def whatsapp():
    # Mengambil data jadwal penyiraman dari service
    get_nomor_hp = get_all_nomor_hp()
    if get_nomor_hp is None:
        flash("Nomor WhatsApp tidak ditemukan.", "danger")
        return redirect(url_for('main.index'))
    return render_template('pages/notification/whatapps.html', table_rows=get_nomor_hp)