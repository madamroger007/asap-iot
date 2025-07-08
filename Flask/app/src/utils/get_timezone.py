from datetime import datetime
import pytz

WIB = pytz.timezone('Asia/Jakarta')

def get_timezone():
    return datetime.now(WIB)
