"""
Models package
Centraliza todos os models da aplicação
"""
from models.user import Usuario
from models.sala import Sala
from models.evento import Evento
from models.inscricao import Inscricao
from models.pre_authorized_user import PreAuthorizedUser

__all__ = [
    'Usuario',
    'Sala',
    'Evento',
    'Inscricao',
    'PreAuthorizedUser'
]