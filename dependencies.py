from models import db
from sqlalchemy.orm import sessionmaker

# teste

def pegar_sessao():
    try:    
        Session = sessionmaker(bind=db)
        session = Session()
        yield session
    finally:
        session.close()



SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=db
)