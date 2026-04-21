import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from .seeds import seed_initial_data
from .base import Base
from core.database.models import Device, DeviceType,NeuralModel, OptimizedModel, OptimizationRecord, DeploymentRecord, ModelFormat, ModelType
username = "postgres"
userpassword = "1111"
db_url_postgre = f'postgresql://{username}:{userpassword}@localhost:5432/kyrsovaya_db'
db_url_sqlLite='sqlite:///kyrsovaya.db'


def create_db_engine(db_url = db_url_postgre):
  
    return create_engine(db_url, echo=True)

def create_tables(engine):
    
    Base.metadata.create_all(engine)


def ensure_schema_compatibility(engine):
    inspector = inspect(engine)
    if not inspector.has_table("device"):
        return

    existing_columns = {col["name"] for col in inspector.get_columns("device")}
    statements = []
    if "device_type" not in existing_columns:
        statements.append("ALTER TABLE device ADD COLUMN device_type VARCHAR(64) NOT NULL DEFAULT 'android'")
    if "username" not in existing_columns:
        statements.append("ALTER TABLE device ADD COLUMN username VARCHAR(128)")
    if "password" not in existing_columns:
        statements.append("ALTER TABLE device ADD COLUMN password VARCHAR(255)")
    if "port" not in existing_columns:
        statements.append("ALTER TABLE device ADD COLUMN port INTEGER")
    if "cpu_frequency" not in existing_columns:
        statements.append("ALTER TABLE device ADD COLUMN cpu_frequency INTEGER")
    if "gpu_memory" not in existing_columns:
        statements.append("ALTER TABLE device ADD COLUMN gpu_memory INTEGER")

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))

def ensure_lookup_compatibility(engine):
    required_formats = ["onnx", "pb", "h5", "hdf5", "keras", "tflite", "lite", "pt", "pth"]
    required_types = ["general", "cv", "nlp", "audio"]

    with engine.begin() as conn:
        for fmt in required_formats:
            conn.execute(
                text(
                    "INSERT INTO model_format(name) "
                    "SELECT :name WHERE NOT EXISTS (SELECT 1 FROM model_format WHERE lower(name) = lower(:name))"
                ),
                {"name": fmt},
            )
        for model_type in required_types:
            conn.execute(
                text(
                    "INSERT INTO model_type(name) "
                    "SELECT :name WHERE NOT EXISTS (SELECT 1 FROM model_type WHERE lower(name) = lower(:name))"
                ),
                {"name": model_type},
            )

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

def create_database_if_not_exists():
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="postgres", 
            user= username,
            password=userpassword
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
    
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'kyrsovaya_db'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE kyrsovaya_db")
            print("База данных 'kyrsovaya_db' создана!")
        else:
            print("База данных 'kyrsovaya_db' уже существует")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f" Ошибка при создании БД: {e}")


def initialize_database(type="postgre"):
    if type== "postgre":
        create_database_if_not_exists()
    engine = create_db_engine()
    create_tables(engine)
    ensure_schema_compatibility(engine)
    ensure_lookup_compatibility(engine)
    print("Database tables created successfully!")
    print("Created tables: ") 
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
    session = get_session(engine)
    seed_initial_data(session)   
    return engine

if __name__ == "__main__":
    print("Database configuration loaded successfully!")
    engine = create_db_engine()
    print(f"Database engine created: {engine}")
