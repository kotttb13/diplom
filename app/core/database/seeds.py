from core.database.models import ModelFormat, DeviceType


def seed_device_types(session):
    devices_types = [
            DeviceType(name = "Mobile"),
            DeviceType(name = "RaspberryPI")
        ]

        
    existing_types = session.query(DeviceType).count()
    if existing_types==0:
        session.add_all(devices_types)
        return True
    return False    
        

def seed_model_formats(session):
    model_formats = [
            ModelFormat(name="TensorFlow Lite"),
            ModelFormat(name="ONNX")
        ]
    existing_formats = session.query(ModelFormat).count()
    if existing_formats==0:
        session.add_all(model_formats)
        return True
    return False 

def seed_initial_data(session):
    
    try:
        changes = False
        changes|=seed_device_types(session)
        changes|=seed_model_formats(session)
        
        if changes:
            session.commit()

    except Exception as e:
        session.rollback()
        print(f"Ошибка при заполнении данных: {e}")
    finally:
        session.close()
