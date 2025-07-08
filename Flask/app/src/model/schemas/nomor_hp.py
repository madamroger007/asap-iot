from app import db
from app.src.utils.get_timezone import get_timezone


class NomorHP(db.Model):
    __tablename__ = 'nomor_hp'
    id = db.Column(db.Integer, primary_key=True)
    nomor_hp = db.Column(db.String(15), unique=True, nullable=False)
    dibuat_sejak = db.Column(db.DateTime(timezone=True), default=get_timezone)
    diubah_sejak = db.Column(db.DateTime(timezone=True), default=get_timezone, onupdate=get_timezone)