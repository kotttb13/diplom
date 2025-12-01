from core.database.models import ModelFormat, DeviceType, ModelType


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
            ModelFormat(name="onnx"),
            ModelFormat(name="pb"),
            ModelFormat(name="h5"),
            ModelFormat(name="hdf5"),
            ModelFormat(name="keras"),
            ModelFormat(name="tflite"),
            ModelFormat(name="lite")
        ]
    existing_formats = session.query(ModelFormat).count()
    if existing_formats==0:
        session.add_all(model_formats)
        return True
    return False 

def seed_model_types(session):
    model_types = [
            ModelType(name="cv"),
            ModelType(name="nlp")
        ]
    existing_types = session.query(ModelType).count()
    if existing_types==0:
        session.add_all(model_types)
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
