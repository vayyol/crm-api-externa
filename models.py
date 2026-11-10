from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, func, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
import os
from datetime import datetime

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Construct the SQLAlchemy connection string
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

db = create_engine(DATABASE_URL)

Base = declarative_base()


class Clientes(Base):
    __tablename__ = "clientes"

    id = Column("id", Integer, primary_key=True, auto_increment=True)
    nome = Column("nome", String, nullable=True)
    email = Column("email", String, nullable=True, unique=True)
    telefone = Column("telefone", String, nullable=True, unique=True)
    status = Column("status", Boolean, default=False)
    usuario_externo_id = Column("usuario_externo_id", String(36), nullable=True)
    created_at = Column("created_at", DateTime, server_default=func.now())

    def __init__(self, nome, email, telefone, status=False, usuario_externo_id=None):
        self.nome = nome
        self.email = email
        self.telefone = telefone
        self.status = status
        self.usuario_externo_id = usuario_externo_id

class EstadosCliente(Base):
    __tablename__ = "estados_cliente"

    id = Column("id", Integer, primary_key=True, auto_increment=True)
    client_id = Column("client_id", Integer, ForeignKey("clientes.id"), nullable=False)
    tipo = Column("tipo", String, nullable=False)
    status = Column("status", String, nullable=False)
    descricao = Column("descricao", Text, nullable=True)
    forma_pagamento = Column("forma_pagamento", String, nullable=True)
    valor_unitario = Column("valor_unitario", DECIMAL, nullable=True)
    quantidade = Column("quantidade", Integer, nullable=True)
    valor_total = Column("valor_total", DECIMAL, nullable=True)
    quant_quitada = Column("quant_quitada", Integer, nullable=True)
    data_vencimento = Column("data_vencimento", DateTime, nullable=True)
    estado_anterior = Column("estado_anterior", Integer, ForeignKey("estados_cliente.id"), nullable=True)
    created_at = Column("created_at", DateTime, server_default=func.now())

    def __init__(self, client_id, tipo, status, descricao=None, forma_pagamento=None, valor_unitario=None, quantidade=None, valor_total=None, quant_quitada=None, data_vencimento=None, estado_anterior=None):
        self.client_id = client_id
        self.tipo = tipo
        self.status = status
        self.descricao = descricao
        self.forma_pagamento = forma_pagamento
        self.valor_unitario = valor_unitario
        self.quantidade = quantidade
        self.valor_total = valor_total
        self.quant_quitada = quant_quitada
        self.data_vencimento = data_vencimento
        self.estado_anterior = estado_anterior