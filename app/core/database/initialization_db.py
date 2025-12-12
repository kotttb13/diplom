import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .seeds import seed_initial_data
from .base import Base
from core.database.models import Device, DeviceType,NeuralModel, OptimizedModel, OptimizationRecord, DeploymentRecord, ModelFormat
username = "postgres"
userpassword = "1111"
db_url_postgre = f'postgresql://{username}:{userpassword}@localhost:5432/kyrsovaya_db'
db_url_sqlLite='sqlite:///kyrsovaya.db'


def create_db_engine(db_url = db_url_postgre):
  
    return create_engine(db_url, echo=True)

def create_tables(engine):
    
    Base.metadata.create_all(engine)

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
