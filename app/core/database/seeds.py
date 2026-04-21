from core.database.models import ModelFormat, DeviceType, ModelType


def seed_device_types(session):
    devices_types = [
            DeviceType(name = "android"),
            DeviceType(name = "raspberry_pi"),
            DeviceType(name = "linux")
        ]

        
    existing_types = session.query(DeviceType).count()
    if existing_types==0:
        session.add_all(devices_types)
        return True
    return False    
        

def seed_model_formats(session):
    required_formats = ["onnx", "pb", "h5", "hdf5", "keras", "tflite", "lite", "pt", "pth"]
    existing_formats = {row[0].lower() for row in session.query(ModelFormat.name).all()}
    missing = [ModelFormat(name=name) for name in required_formats if name not in existing_formats]
    if missing:
        session.add_all(missing)
        return True
    return False

def seed_model_types(session):
    required_types = ["general", "cv", "nlp", "audio"]
    existing_types = {row[0].lower() for row in session.query(ModelType.name).all()}
    missing = [ModelType(name=name) for name in required_types if name not in existing_types]
    if missing:
        session.add_all(missing)
        return True
    return False


def seed_initial_data(session):
    
    try:
        changes = False
        changes|=seed_device_types(session)
        changes|=seed_model_formats(session)
        changes|=seed_model_types(session)
        
        if changes:
            session.commit()

    except Exception as e:
        session.rollback()
        print(f"Ошибка при заполнении данных: {e}")
    finally:
        session.close()
