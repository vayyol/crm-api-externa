from fastapi import APIRouter, Depends, HTTPException, Body
from dependencies import pegar_sessao
from sqlalchemy.orm import Session
from models import Clientes, EstadosCliente
from schemas import CadastroCliente, DescricaoSchema, EstadoValueSchema
from security import validar_api_key
from security import validar_usuario_integracao
import calendar
from datetime import date, datetime


order_router = APIRouter(prefix="/order", tags=["order"], dependencies=[Depends(validar_api_key)])  



def adicionar_mes(data_base, quantidade_meses):
    mes = data_base.month - 1 + quantidade_meses

    ano = data_base.year + mes // 12

    mes = mes % 12 + 1

    dia = min(data_base.day, calendar.monthrange(ano, mes)[1])

    return date(ano, mes, dia)



@order_router.get("/")
def inicio():
    return {"message": "API online"}



@order_router.get("/teste-usuario")
def teste_usuario(
    usuario_id: str = Depends(validar_usuario_integracao),
):
    return {
        "mensagem": "Token validado!",
        "usuario_id": usuario_id,
    }



@order_router.post("/cadastro-cliente")
async def cadastrar_cliente(schema: CadastroCliente, session: Session = Depends(pegar_sessao), usuario_id: str = Depends(validar_usuario_integracao)):
    cliente = session.query(Clientes).filter(Clientes.telefone == schema.telefone).first()
    if cliente:
        raise HTTPException(status_code=404, detail="Já existe um cliente cadastrado com esse telefone.")

    novo_cliente = Clientes(
        nome=schema.nome,
        email=schema.email,
        telefone=schema.telefone,
        status=schema.status,
        usuario_externo_id=usuario_id
    )

    session.add(novo_cliente)

    session.commit()

    return {"message": "Cliente cadastrado com sucesso."}


@order_router.post("/contato-cliente/{id_client}")
async def contato_cliente(id_client: int, schema: DescricaoSchema, session: Session = Depends(pegar_sessao), usuario_id: str = Depends(validar_usuario_integracao)):
    cliente = session.query(Clientes).filter(Clientes.id == id_client, Clientes.usuario_externo_id == usuario_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    #procura se já existe algum registro de contato aberto para o cliente, caso exista, não é possível registrar um novo contato
    registro_igual = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, 
                                                          EstadosCliente.tipo == "CONTATO", 
                                                          EstadosCliente.status == "ABERTO").first()
    if registro_igual:
        raise HTTPException(status_code=404, detail="Já existe um registro de contato aberto para este cliente.")

    novo_estado = EstadosCliente(
        client_id=id_client,
        tipo="CONTATO",
        status="ABERTO",
        descricao=schema.descricao
    )

    session.add(novo_estado)
    session.commit()

    return {"message": "Contato registrado com sucesso."}

@order_router.post("/interessado-cliente/{id_client}")
async def interessado_cliente(id_client: int, schema: DescricaoSchema, session: Session = Depends(pegar_sessao), usuario_id: str = Depends(validar_usuario_integracao)):
    cliente = session.query(Clientes).filter(Clientes.id == id_client, Clientes.usuario_externo_id == usuario_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    #procura se já existe algum registro de interessado aberto para o cliente, caso exista, não é possível registrar um novo interessado
    registro_igual = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.tipo == "INTERESSADO", EstadosCliente.status == "ABERTO").first()
    if registro_igual:
        raise HTTPException(status_code=404, detail="Já existe um registro de interessado aberto para este cliente.")

    registro_desinteressado = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.tipo == "DESINTERESSADO", EstadosCliente.status == "ABERTO").first()
    if registro_desinteressado:
        registro_desinteressado.status = "FECHADO"

    novo_estado = EstadosCliente(
        client_id=id_client,
        tipo="INTERESSADO",
        status="ABERTO",
        descricao=schema.descricao
    )

    #vendo se existe algum registro de contato aberto para o cliente, caso exista, fecha o registro de contato
    registro = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.tipo == "CONTATO", EstadosCliente.status == "ABERTO").first()
    if registro:
        registro.status = "FECHADO"


    session.add(novo_estado)
    session.commit()

    return {"message": "Estado registrado com sucesso."}


@order_router.post("/desinteressado-cliente/{id_client}")
async def desinteressado_cliente(id_client: int, schema: DescricaoSchema, session: Session = Depends(pegar_sessao), usuario_id: str = Depends(validar_usuario_integracao)):
    cliente = session.query(Clientes).filter(Clientes.id == id_client, Clientes.usuario_externo_id == usuario_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    #procura se já existe algum registro de desinteressado aberto para o cliente, caso exista, não é possível registrar um novo desinteressado
    registro_igual = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.tipo == "DESINTERESSADO", EstadosCliente.status == "ABERTO").first()
    if registro_igual:
        raise HTTPException(status_code=404, detail="Já existe um registro de desinteressado aberto para este cliente.")

    
    #procurando se foi atribuido o estado de interessado para o cliente, caso não tenha sido atribuido, não é possível registrar desinteresse, 
    #caso tenha sido atribuido, fecha o registro de interessado e cria um novo registro de desinteressado
    registro_interessado = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.tipo == "INTERESSADO", EstadosCliente.status == "ABERTO").first()
    if not registro_interessado:
        raise HTTPException(status_code=404, detail="Não é possível registrar desinteresse para este cliente.")
    registro_interessado.status = "FECHADO"

    novo_estado = EstadosCliente(
        client_id=id_client,
        tipo="DESINTERESSADO",
        status="ABERTO",
        descricao=schema.descricao
    )

    session.add(novo_estado)
    session.commit()

    return {"message": "Estado registrado com sucesso."}

@order_router.post("/proposta-cliente/{id_client}")
async def proposta_cliente(id_client: int, schema: EstadoValueSchema, session: Session = Depends(pegar_sessao), usuario_id: str = Depends(validar_usuario_integracao)):
    cliente = session.query(Clientes).filter(Clientes.id == id_client, Clientes.usuario_externo_id == usuario_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    #procura se já existe algum registro de proposta aberto para o cliente, caso exista, fecha a antiga proposta
    registro_igual = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.tipo == "PROPOSTA", EstadosCliente.status == "ABERTO").first()
    if registro_igual:
        registro_igual.status = "FECHADO"

    novo_estado = EstadosCliente(
        client_id=id_client,
        tipo="PROPOSTA",
        status="ABERTO",
        descricao=schema.descricao,
        forma_pagamento=schema.forma_pagamento,
        valor_unitario=schema.valor_total / schema.quantidade if schema.quantidade else None,
        quantidade=schema.quantidade,
        valor_total=schema.valor_total,
        data_vencimento=schema.data_vencimento
    )

    session.add(novo_estado)
    session.commit()

    return {"message": "Proposta registrada com sucesso."}

@order_router.post("/venda-nao-realizada/{id_client}")
async def venda_nao_realizada(id_client: int, schema: DescricaoSchema, session: Session = Depends(pegar_sessao), usuario_id: str = Depends(validar_usuario_integracao)):
    cliente = session.query(Clientes).filter(Clientes.id == id_client, Clientes.usuario_externo_id == usuario_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    #procura se já existe algum registro de venda não realizada aberto para o cliente, caso exista, fecha o antigo registro
    registro_igual = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.tipo == "VENDA_NAO_REALIZADA", EstadosCliente.status == "ABERTO").first()
    if registro_igual:
        raise HTTPException(status_code=404, detail="Já existe um registro de venda não realizada aberto para este cliente.")

    registro_proposta = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.tipo == "PROPOSTA", EstadosCliente.status == "ABERTO").first()
    if registro_proposta:
        registro_proposta.status = "FECHADO"

    registro_interessado = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.tipo == "INTERESSADO", EstadosCliente.status == "ABERTO").first()
    if registro_interessado:
        registro_interessado.status = "FECHADO"

    #existe um pequeno problema aqui, caso exista um registrode venda realizada aberto, ainda assim o usuario pode registrar venda não realizada
    #isso não sera impedido, pois mesmo com uma venda realizada aberta, o usuario pode registrar venda não realizada, 
    # pois a venda realizada pode ser de outro produto, e a venda não realizada pode ser de outro produto, 
    # então não é possivel impedir que o usuario registre venda não realizada mesmo com uma venda realizada aberta

    novo_estado = EstadosCliente(
        client_id=id_client,
        tipo="VENDA_NAO_REALIZADA",
        status="ABERTO",
        descricao=schema.descricao
    )

    session.add(novo_estado)
    session.commit()

    return {"message": "Estado de venda não realizada registrado com sucesso."}

@order_router.post("/venda-realizada/{id_client}")
async def venda_realizada(id_client: int, schema: EstadoValueSchema, session: Session = Depends(pegar_sessao), usuario_id: str = Depends(validar_usuario_integracao)):
    cliente = session.query(Clientes).filter(Clientes.id == id_client, Clientes.usuario_externo_id == usuario_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    #procura se já existe algum registro de venda não realizada aberto para o cliente, caso exista, fecha o antigo registro
    registro = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.tipo == "VENDA_NAO_REALIZADA", EstadosCliente.status == "ABERTO").first()
    if registro:
        registro.status = "FECHADO"

    registro_proposta = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.tipo == "PROPOSTA", EstadosCliente.status == "ABERTO").first()
    if registro_proposta:
        registro_proposta.status = "FECHADO"

    registro_interessado = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.tipo == "INTERESSADO", EstadosCliente.status == "ABERTO").first()
    if registro_interessado:
        registro_interessado.status = "FECHADO"

    if schema.quant_quitada == schema.quantidade:
        status_venda = "FECHADO"
    else:
        status_venda = "ABERTO"


    novo_estado = EstadosCliente(
        client_id=id_client,
        tipo="VENDA_REALIZADA",
        status=status_venda,
        descricao=schema.descricao,
        forma_pagamento=schema.forma_pagamento,
        valor_unitario=schema.valor_total / schema.quantidade if schema.quantidade else None,
        quantidade=schema.quantidade,
        valor_total=schema.valor_total,
        quant_quitada=schema.quant_quitada,
        data_vencimento=schema.data_vencimento
    )

    session.add(novo_estado)
    session.commit()

    return {"message": "Estado de venda realizada registrado com sucesso."}

@order_router.post("/quitar-venda/{id_client}/{id_venda}/{quant_quitada}")
async def quitar_venda(id_client: int, id_venda: int, quant_quitada: int, session: Session = Depends(pegar_sessao), usuario_id: str = Depends(validar_usuario_integracao)):
    cliente = session.query(Clientes).filter(Clientes.id == id_client, Clientes.usuario_externo_id == usuario_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
 
    #procura se já existe algum registro de venda realizada aberto para o cliente, caso exista, fecha o antigo registro
    registro = session.query(EstadosCliente).filter(EstadosCliente.client_id == id_client, EstadosCliente.id == id_venda, EstadosCliente.tipo=="VENDA_REALIZADA").first()
    if not registro:
        raise HTTPException(status_code=404, detail="Não existe um registro de venda realizada para este cliente.")
    if registro.status != "ABERTO":
        raise HTTPException(status_code=404, detail="O registro de venda realizada não está aberto.")
 
    #verifica se a quantidade quitada é maior que a quantidade total da venda, caso seja, retorna erro
    if quant_quitada > registro.quantidade:
        raise HTTPException(status_code=404, detail="A quantidade quitada não pode ser maior que a quantidade total da venda.")
    if quant_quitada+registro.quant_quitada > registro.quantidade:
        raise HTTPException(status_code=404, detail="A quantidade quitada não pode ser maior que a quantidade total da venda.")
    if quant_quitada <= 0:
        raise HTTPException(status_code=404, detail="A quantidade quitada deve ser maior que zero.")
 
    registro.quant_quitada += quant_quitada
 
    #verifica se a quantidade quitada é igual a quantidade total da venda, caso seja, fecha o registro de venda realizada
    if registro.quant_quitada == registro.quantidade:
        registro.status = "FECHADO"
    elif registro.data_vencimento:
        # Ainda há parcelas a pagar: avança a data de vencimento para a próxima parcela,
        # um mês para cada parcela quitada agora.
        atual = registro.data_vencimento
        nova_data = adicionar_mes(
            atual.date() if isinstance(atual, datetime) else atual,
            quant_quitada
        )
 
        if isinstance(atual, datetime):
            registro.data_vencimento = datetime.combine(
                nova_data,
                atual.time(),
                tzinfo=atual.tzinfo
            )
        else:
            registro.data_vencimento = nova_data
 
    session.commit()
 
    return {"message": "Venda quitada com sucesso."}
 

@order_router.get("/listar-clientes")
async def listar_clientes(session: Session = Depends(pegar_sessao), usuario_id: str = Depends(validar_usuario_integracao)):
    clientes = session.query(Clientes).filter(Clientes.usuario_externo_id == usuario_id).all()

    if not clientes:
        raise HTTPException(
            status_code=404,
            detail="Nenhum cliente cadastrado para este usuário."
        )

    return [
        {
            "id": cliente.id,
            "nome": cliente.nome,
            "email": cliente.email,
            "telefone": cliente.telefone,
            "status": cliente.status,
        }
        for cliente in clientes
    ]




@order_router.get("/listar-estados/{id_client}")
def listar_estados_cliente( id_client: int, session: Session = Depends(pegar_sessao), usuario_id: str = Depends(validar_usuario_integracao)
):
    cliente = session.query(Clientes).filter(
        Clientes.id == id_client,
        Clientes.usuario_externo_id == usuario_id
    ).first()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    estados = session.query(EstadosCliente).filter(
        EstadosCliente.client_id == id_client
    ).order_by(EstadosCliente.created_at.desc()).all()

    return [
        {
            "id": estado.id,
            "client_id": estado.client_id,
            "tipo": estado.tipo,
            "status": estado.status,
            "descricao": estado.descricao,
            "forma_pagamento": estado.forma_pagamento,
            "valor_unitario": estado.valor_unitario,
            "quantidade": estado.quantidade,
            "valor_total": estado.valor_total,
            "quant_quitada": estado.quant_quitada,
            "data_vencimento": estado.data_vencimento,
            "estado_anterior": estado.estado_anterior,
            "created_at": estado.created_at
        }
        for estado in estados
    ]


@order_router.get("/listar-clientes-estados")
def listar_clientes_estados(
    session: Session = Depends(pegar_sessao),
    usuario_id: str = Depends(validar_usuario_integracao)
):
    clientes = session.query(Clientes).filter(
        Clientes.usuario_externo_id == usuario_id
    ).all()

    resultado = []

    for cliente in clientes:
        estados = session.query(EstadosCliente).filter(
            EstadosCliente.client_id == cliente.id
        ).order_by(EstadosCliente.created_at.desc()).all()

        resultado.append({
            "id": cliente.id,
            "nome": cliente.nome,
            "email": cliente.email,
            "telefone": cliente.telefone,
            "status": cliente.status,
            "created_at": cliente.created_at,
            "estados": [
                {
                    "id": estado.id,
                    "tipo": estado.tipo,
                    "status": estado.status,
                    "descricao": estado.descricao,
                    "forma_pagamento": estado.forma_pagamento,
                    "valor_unitario": estado.valor_unitario,
                    "quantidade": estado.quantidade,
                    "valor_total": estado.valor_total,
                    "quant_quitada": estado.quant_quitada,
                    "data_vencimento": estado.data_vencimento,
                    "estado_anterior": estado.estado_anterior,
                    "created_at": estado.created_at
                }
                for estado in estados
            ]
        })

    return resultado


@order_router.get("/consultar-estado/{id_estado}")
def consultar_estado(
    id_estado: int,
    session: Session = Depends(pegar_sessao),
    usuario_id: str = Depends(validar_usuario_integracao)
):
    estado = session.query(EstadosCliente).join(
        Clientes,
        EstadosCliente.client_id == Clientes.id
    ).filter(
        EstadosCliente.id == id_estado,
        Clientes.usuario_externo_id == usuario_id
    ).first()

    if not estado:
        raise HTTPException(status_code=404, detail="Estado não encontrado")

    return {
        "id": estado.id,
        "client_id": estado.client_id,
        "tipo": estado.tipo,
        "status": estado.status,
        "descricao": estado.descricao,
        "forma_pagamento": estado.forma_pagamento,
        "valor_unitario": estado.valor_unitario,
        "quantidade": estado.quantidade,
        "valor_total": estado.valor_total,
        "quant_quitada": estado.quant_quitada,
        "data_vencimento": estado.data_vencimento,
        "estado_anterior": estado.estado_anterior,
        "created_at": estado.created_at
    }



#NOVAS ROTAS PARA O DASHBOARD -------------------------

@order_router.post("/fechar-estado/{id_estado}")
async def fechar_estado(
    id_estado: int,
    session: Session = Depends(pegar_sessao),
    usuario_id: str = Depends(validar_usuario_integracao)
):
    estado = session.query(EstadosCliente).join(
        Clientes,
        EstadosCliente.client_id == Clientes.id
    ).filter(
        EstadosCliente.id == id_estado,
        Clientes.usuario_externo_id == usuario_id
    ).first()

    if not estado:
        raise HTTPException(status_code=404, detail="Estado não encontrado.")

    if estado.status != "ABERTO":
        raise HTTPException(status_code=404, detail="Este estado não está aberto.")

    if estado.tipo == "VENDA_REALIZADA":
        raise HTTPException(status_code=404, detail="Utilize a rota de quitar ou cancelar venda.")

    estado.status = "FECHADO"

    session.commit()

    return {"message": "Estado fechado com sucesso."}


@order_router.post("/cancelar-venda/{id_client}/{id_venda}")
async def cancelar_venda(
    id_client: int,
    id_venda: int,
    session: Session = Depends(pegar_sessao),
    usuario_id: str = Depends(validar_usuario_integracao)
):
    cliente = session.query(Clientes).filter(
        Clientes.id == id_client,
        Clientes.usuario_externo_id == usuario_id
    ).first()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    registro = session.query(EstadosCliente).filter(
        EstadosCliente.client_id == id_client,
        EstadosCliente.id == id_venda,
        EstadosCliente.tipo == "VENDA_REALIZADA"
    ).first()

    if not registro:
        raise HTTPException(status_code=404, detail="Não existe uma venda registrada para este cliente.")

    if registro.status != "ABERTO":
        raise HTTPException(status_code=404, detail="Esta venda não está aberta.")

    registro.status = "CANCELADO"

    session.commit()

    return {"message": "Venda cancelada com sucesso."}



@order_router.get("/dashboard-acompanhamento")
def dashboard_acompanhamento(
    session: Session = Depends(pegar_sessao),
    usuario_id: str = Depends(validar_usuario_integracao)
):
    hoje = date.today()
 
    registros = session.query(EstadosCliente, Clientes).join(
        Clientes,
        EstadosCliente.client_id == Clientes.id
    ).filter(
        Clientes.usuario_externo_id == usuario_id,
        EstadosCliente.status == "ABERTO",
        EstadosCliente.tipo != "VENDA_REALIZADA"
    ).order_by(EstadosCliente.created_at.asc()).all()
 
    estados_abertos = []
 
    for estado, cliente in registros:
 
        data_criacao = estado.created_at.date() if isinstance(estado.created_at, datetime) else estado.created_at
 
        dias_aberto = (hoje - data_criacao).days
 
        estados_abertos.append({
            "id": estado.id,
            "client_id": cliente.id,
            "nome": cliente.nome,
            "telefone": cliente.telefone,
            "email": cliente.email,
            "tipo": estado.tipo,
            "status": estado.status,
            "descricao": estado.descricao,
            "created_at": estado.created_at,
            "dias_aberto": dias_aberto
        })
 
 
    vendas = session.query(EstadosCliente, Clientes).join(
        Clientes,
        EstadosCliente.client_id == Clientes.id
    ).filter(
        Clientes.usuario_externo_id == usuario_id,
        EstadosCliente.tipo == "VENDA_REALIZADA",
        EstadosCliente.status == "ABERTO"
    ).order_by(EstadosCliente.data_vencimento.asc()).all()
 
    pagamentos = []
 
    for venda, cliente in vendas:
 
        quant_quitada = venda.quant_quitada or 0
 
        if venda.data_vencimento:
 
            # A data_vencimento salva já é a data da PRÓXIMA parcela.
            # Ela é avançada em um mês a cada quitação (ver quitar_venda),
            # então aqui ela é usada exatamente como está.
            data_proximo_vencimento = venda.data_vencimento.date() if isinstance(venda.data_vencimento, datetime) else venda.data_vencimento
 
            proxima_parcela = quant_quitada + 1
 
            dias_vencimento = (data_proximo_vencimento - hoje).days
 
            if dias_vencimento < 0:
                situacao = "ATRASADO"
            elif dias_vencimento == 0:
                situacao = "VENCE_HOJE"
            else:
                situacao = "A_VENCER"
 
        else:
            proxima_parcela = quant_quitada + 1
            data_proximo_vencimento = None
            dias_vencimento = None
            situacao = "SEM_VENCIMENTO"
 
 
        pagamentos.append({
            "id_venda": venda.id,
            "client_id": cliente.id,
            "nome": cliente.nome,
            "telefone": cliente.telefone,
            "email": cliente.email,
            "descricao": venda.descricao,
            "quantidade": venda.quantidade,
            "quant_quitada": quant_quitada,
            "proxima_parcela": proxima_parcela,
            "valor_parcela": venda.valor_unitario,
            "valor_total": venda.valor_total,
            "data_vencimento": data_proximo_vencimento,
            "dias_vencimento": dias_vencimento,
            "situacao": situacao
        })
 
 
    return {
        "estados_abertos": estados_abertos,
        "pagamentos": pagamentos
    }


# ROTAS PARA EDITAR CLIENTES -------------------------

@order_router.put("/editar-nome-cliente/{id_client}")
async def editar_nome_cliente(
    id_client: int,
    nome: str = Body(..., embed=True),
    session: Session = Depends(pegar_sessao),
    usuario_id: str = Depends(validar_usuario_integracao)
):
    cliente = session.query(Clientes).filter(
        Clientes.id == id_client,
        Clientes.usuario_externo_id == usuario_id
    ).first()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    if not nome.strip():
        raise HTTPException(status_code=400, detail="O nome não pode ser vazio.")

    cliente.nome = nome.strip()

    session.commit()

    return {"message": "Nome do cliente atualizado com sucesso."}


@order_router.put("/editar-telefone-cliente/{id_client}")
async def editar_telefone_cliente(
    id_client: int,
    telefone: str = Body(..., embed=True),
    session: Session = Depends(pegar_sessao),
    usuario_id: str = Depends(validar_usuario_integracao)
):
    cliente = session.query(Clientes).filter(
        Clientes.id == id_client,
        Clientes.usuario_externo_id == usuario_id
    ).first()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    if not telefone.strip():
        raise HTTPException(status_code=400, detail="O telefone não pode ser vazio.")

    telefone_existente = session.query(Clientes).filter(
        Clientes.telefone == telefone,
        Clientes.id != id_client
    ).first()

    if telefone_existente:
        raise HTTPException(status_code=400, detail="Já existe um cliente cadastrado com esse telefone.")

    cliente.telefone = telefone.strip()

    session.commit()

    return {"message": "Telefone do cliente atualizado com sucesso."}


@order_router.put("/ativar-cliente/{id_client}")
async def ativar_cliente(
    id_client: int,
    session: Session = Depends(pegar_sessao),
    usuario_id: str = Depends(validar_usuario_integracao)
):
    cliente = session.query(Clientes).filter(
        Clientes.id == id_client,
        Clientes.usuario_externo_id == usuario_id
    ).first()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    cliente.status = True

    session.commit()

    return {"message": "Cliente ativado com sucesso."}


@order_router.put("/desativar-cliente/{id_client}")
async def desativar_cliente(
    id_client: int,
    session: Session = Depends(pegar_sessao),
    usuario_id: str = Depends(validar_usuario_integracao)
):
    cliente = session.query(Clientes).filter(
        Clientes.id == id_client,
        Clientes.usuario_externo_id == usuario_id
    ).first()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    cliente.status = False

    session.commit()

    return {"message": "Cliente desativado com sucesso."}


@order_router.put("/editar-email-cliente/{id_client}")
async def editar_email_cliente(
    id_client: int,
    email: str = Body(..., embed=True),
    session: Session = Depends(pegar_sessao),
    usuario_id: str = Depends(validar_usuario_integracao)
):
    cliente = session.query(Clientes).filter(
        Clientes.id == id_client,
        Clientes.usuario_externo_id == usuario_id
    ).first()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    if not email.strip():
        raise HTTPException(status_code=400, detail="O e-mail não pode ser vazio.")

    cliente.email = email.strip()

    session.commit()

    return {"message": "E-mail do cliente atualizado com sucesso."}