#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelos de dados para o Bot OAB
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ResultadoOAB:
    inscricao: str
    estado: str
    nome: str = ""
    tipo: str = ""
    situacao: str = ""
    endereco: str = ""
    telefone: str = ""
    email: str = ""
    data_inscricao: str = ""
    numero_carteira: str = ""
    erro: str = ""
    sucesso: bool = False
    detalhes_completos: str = ""