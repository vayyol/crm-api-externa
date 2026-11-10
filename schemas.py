from pydantic import BaseModel
from decimal import Decimal
from typing import Optional, List, Text
from datetime import date, datetime


class CadastroCliente(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: str
    status: Optional[bool] = True

    class Config:
        from_attributes = True

class DescricaoSchema(BaseModel):
    descricao: Optional[str] = None

    class Config:
        from_attributes = True

class EstadoValueSchema(BaseModel):
    descricao: Optional[str] = None
    forma_pagamento: Optional[str] = None
    quantidade: Optional[int] = None
    valor_total: Optional[Decimal] = None
    quant_quitada: Optional[int] = None
    data_vencimento: Optional[date] = None

    class Config:
        from_attributes = True