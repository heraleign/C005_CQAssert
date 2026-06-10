from app.database import engine, Base
from app.models import *

def init_database():
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    init_database()
