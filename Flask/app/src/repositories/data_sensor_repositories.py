from typing import List, Dict, Any
from app.src.model.schemas.data_sensor import DataSensor  # Pastikan Anda memiliki model DataSensor yang sudah didefinisikan
from app import db


def get_all_data_sensors_repository() -> List[DataSensor]:
    return DataSensor.query.all()

def get_data_sensor_by_id_repository(data_sensor_id: int) -> DataSensor:
    return DataSensor.query.get(data_sensor_id)

def create_data_sensor_repository(data: Dict[str, Any]) -> DataSensor:
    data_sensor = DataSensor(**data)
    db.session.add(data_sensor)
    db.session.commit()
    return data_sensor

def delete_old_data_sensor_repository(tanggal_batas):
    from app.src.model.schemas.data_sensor import DataSensor
    from app import db

    deleted = DataSensor.query.filter(DataSensor.dibuat_sejak < tanggal_batas).delete()
    db.session.commit()
    return deleted

def delete_data_sensor_repository(data_sensor_id: int) -> bool:
    data_sensor = DataSensor.query.get(data_sensor_id)
    if data_sensor:
        db.session.delete(data_sensor)
        db.session.commit()
        return True
    return False
