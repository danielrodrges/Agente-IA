"""
Serviço para gerenciar variáveis de ferramentas.
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from ferramenta.ferramenta_variavel_model import FerramentaVariavel
from ferramenta.ferramenta_variavel_schema import (
    FerramentaVariavelCriar,
    FerramentaVariavelAtualizar
)


class FerramentaVariavelService:
    """Serviço para gerenciar variáveis de ferramentas."""

    @staticmethod
    def listar_por_ferramenta(db: Session, ferramenta_id: int) -> List[FerramentaVariavel]:
        """Lista todas as variáveis de uma ferramenta."""
        return db.query(FerramentaVariavel).filter(
            FerramentaVariavel.ferramenta_id == ferramenta_id
        ).all()

    @staticmethod
    def obter_por_id(db: Session, variavel_id: int) -> Optional[FerramentaVariavel]:
        """Obtém uma variável pelo ID."""
        return db.query(FerramentaVariavel).filter(
            FerramentaVariavel.id == variavel_id
        ).first()

    @staticmethod
    def obter_por_chave(
        db: Session,
        ferramenta_id: int,
        chave: str
    ) -> Optional[FerramentaVariavel]:
        """Obtém uma variável específica de uma ferramenta."""
        return db.query(FerramentaVariavel).filter(
            FerramentaVariavel.ferramenta_id == ferramenta_id,
            FerramentaVariavel.chave == chave
        ).first()

    @staticmethod
    def criar(db: Session, variavel: FerramentaVariavelCriar) -> FerramentaVariavel:
        """Cria uma nova variável."""
        # Verificar se já existe variável com mesma chave
        existe = FerramentaVariavelService.obter_por_chave(
            db, variavel.ferramenta_id, variavel.chave
        )
        if existe:
            raise ValueError(
                f"Já existe uma variável '{variavel.chave}' para esta ferramenta"
            )
        
        db_variavel = FerramentaVariavel(**variavel.model_dump())
        db.add(db_variavel)
        db.commit()
        db.refresh(db_variavel)
        return db_variavel

    @staticmethod
    def atualizar(
        db: Session,
        variavel_id: int,
        variavel: FerramentaVariavelAtualizar
    ) -> Optional[FerramentaVariavel]:
        """Atualiza uma variável existente."""
        db_variavel = FerramentaVariavelService.obter_por_id(db, variavel_id)
        if not db_variavel:
            return None

        update_data = variavel.model_dump(exclude_unset=True)
        for campo, valor in update_data.items():
            setattr(db_variavel, campo, valor)

        db.commit()
        db.refresh(db_variavel)
        return db_variavel

    @staticmethod
    def deletar(db: Session, variavel_id: int) -> bool:
        """Deleta uma variável."""
        db_variavel = FerramentaVariavelService.obter_por_id(db, variavel_id)
        if not db_variavel:
            return False

        db.delete(db_variavel)
        db.commit()
        return True

    @staticmethod
    def obter_variaveis_como_dict(
        db: Session,
        ferramenta_id: int
    ) -> Dict[str, str]:
        """
        Retorna todas as variáveis de uma ferramenta como dicionário.
        Útil para substituição de variáveis.
        """
        variaveis = FerramentaVariavelService.listar_por_ferramenta(db, ferramenta_id)
        return {var.chave: var.valor for var in variaveis}

    @staticmethod
    def definir_variaveis_padrao(
        db: Session,
        ferramenta_id: int,
        variaveis: Dict[str, Any]
    ):
        """
        Define múltiplas variáveis de uma vez.
        Atualiza se já existe, cria se não existe.
        """
        for chave, config in variaveis.items():
            # Permitir passar string simples ou dict com configurações
            if isinstance(config, str):
                valor = config
                tipo = "string"
                descricao = None
                is_secret = True
            else:
                valor = config.get("valor", "")
                tipo = config.get("tipo", "string")
                descricao = config.get("descricao")
                is_secret = config.get("is_secret", True)
            
            # Verificar se já existe
            existe = FerramentaVariavelService.obter_por_chave(
                db, ferramenta_id, chave
            )
            
            if existe:
                # Atualizar
                existe.valor = valor
                existe.tipo = tipo
                existe.descricao = descricao
                existe.is_secret = is_secret
            else:
                # Criar
                nova_variavel = FerramentaVariavel(
                    ferramenta_id=ferramenta_id,
                    chave=chave,
                    valor=valor,
                    tipo=tipo,
                    descricao=descricao,
                    is_secret=is_secret
                )
                db.add(nova_variavel)
        
        db.commit()
