from flask import Blueprint, render_template, redirect, request, url_for, session, flash, jsonify, current_app
import app.config as config
from app.src.repositories.nohp_repositories import (
    create_nomor_hp,
    delete_nomor_hp
)


notification = Blueprint('notification', __name__)

@notification.route('/api/add-wa-number', methods=['POST'])
def add_wa_number():
    try:
        data = request.get_json()
        wa_number = data.get('wa_number')

        if not wa_number:
            return jsonify({'success': False, 'error': 'Nomor WA tidak boleh kosong'}), 400
        create_nomor_hp(wa_number)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@notification.route('/api/delete-wa-number/<int:id>', methods=['DELETE'])
def delete_wa_number(id):
    try:
        print(id)
        delete_nomor_hp(id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500