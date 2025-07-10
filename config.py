#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arquivo de configuração para o Sistema Integrado Bot OAB + Supabase
"""

import os
import re
from typing import Dict, Any, Optional, Tuple

class Config:
    """Classe de configuração centralizada"""
    
    # ===========================================
    # CONFIGURAÇÕES DO SUPABASE
    # ===========================================
    
    # Credenciais do Supabase (fornecidas)
    SUPABASE_URL = "https://rdkvvigjmowtvhxqlrnp.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJka3Z2aWdqbW93dHZoeHFscm5wIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIxNjkwODQsImV4cCI6MjA1Nzc0NTA4NH0.pFn1faGoWsapclNIjVhnD8A754DMiY7dZL9Ig0lDMQ4"
    
    # Nome da tabela no Supabase
    TABELA_ERROS = "erros_processados"
    
    # Colunas da tabela
    COLUNA_ID = "id"
    COLUNA_USUARIOS = "usuario"
    COLUNA_NOME_PROCURADOR = "nome_procurador"
    
    # ===========================================
    # CONFIGURAÇÕES DO BOT OAB
    # ===========================================
    
    # URL do site da OAB
    OAB_URL = "https://cna.oab.org.br/"
    
    # Timeout para operações (em segundos)
    TIMEOUT_NAVEGADOR = 15
    TIMEOUT_CONSULTA = 30
    
    # Modo headless (True = sem interface gráfica)
    HEADLESS_MODE = True
    
    # Intervalo entre consultas (em segundos)
    INTERVALO_CONSULTAS = 2
    
    # Número máximo de tentativas por consulta
    MAX_TENTATIVAS = 3
    
    # ===========================================
    # CONFIGURAÇÕES DE PROCESSAMENTO
    # ===========================================
    
    # Tamanho do lote para processamento
    TAMANHO_LOTE = 50
    
    # Salvar resultados intermediários a cada X registros
    SALVAR_INTERMEDIARIO_A_CADA = 10
    
    # Limites de validação
    MIN_COMPRIMENTO_NOME = 5
    MAX_COMPRIMENTO_NOME = 100
    MIN_DIGITOS_OAB = 4
    MAX_DIGITOS_OAB = 8
    
    # ===========================================
    # CONFIGURAÇÕES DE ARQUIVOS E LOGS
    # ===========================================
    
    # Pasta para logs
    PASTA_LOGS = "logs"
    
    # Pasta para resultados
    PASTA_RESULTADOS = "Pesquisa"
    
    # Pasta para debug
    PASTA_DEBUG = "debug"
    
    # Formato do timestamp para arquivos
    FORMATO_TIMESTAMP = "%Y%m%d_%H%M%S"
    
    # Formato de data para logs
    FORMATO_DATA_LOG = "%d/%m/%Y %H:%M:%S"
    
    # ===========================================
    # CONFIGURAÇÕES DE VALIDAÇÃO
    # ===========================================
    
    # Estados brasileiros válidos
    ESTADOS_VALIDOS = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
        'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 
        'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]
    
    # Palavras que invalidam um nome
    PALAVRAS_INVALIDAS_NOME = [
        'ERRO', 'INVALID', 'NULL', 'NONE', 'UNDEFINED', 
        'INSCRICAO', 'SECCIONAL', 'TELEFONE', 'ENDERECO', 
        'ADVOGADO', 'SITUACAO', 'CONSULTA'
    ]
    
    # Padrões regex para extrair OAB - PADRÃO REAL DO BANCO
    PADROES_OAB = [
        r'^([A-Z]{2})(\d{4,8})$'  # SP388221 (padrão real do banco)
    ]
    
    # Exemplos de registros válidos e inválidos
    EXEMPLOS_VALIDOS = [
        'SP388221',  # São Paulo
        'RJ123456',  # Rio de Janeiro
        'MG987654',  # Minas Gerais
        'PR456789',  # Paraná
    ]
    
    EXEMPLOS_INVALIDOS = [
        'M356437',   # Matrícula de funcionário TJSP
        '123456',    # Número sem estado
        'ABC123',    # Estado inválido
        'SP123',     # Número muito curto
        'SP12345678901',  # Número muito longo
        'SP123ABC',  # Contém letras no número
    ]
    
    # ===========================================
    # CONFIGURAÇÕES DE MENSAGENS
    # ===========================================
    
    # Mensagens de erro padronizadas
    ERRO_OAB_NAO_ENCONTRADA = "Inscrição não encontrada"
    ERRO_FORMATO_INVALIDO = "OAB não encontrada em: {texto}"
    ERRO_NOME_INVALIDO = "Nome inválido após limpeza"
    ERRO_CONEXAO = "Erro de conexão: {erro}"
    ERRO_TIMEOUT = "Timeout na consulta"
    
    # Prefixo para erros no banco
    PREFIXO_ERRO = "ERRO: "
    
    # ===========================================
    # MÉTODOS AUXILIARES
    # ===========================================
    
    @classmethod
    def criar_pastas(cls):
        """Cria as pastas necessárias se não existirem"""
        pastas = [cls.PASTA_LOGS, cls.PASTA_RESULTADOS, cls.PASTA_DEBUG]
        
        for pasta in pastas:
            if not os.path.exists(pasta):
                os.makedirs(pasta)
                print(f"📁 Pasta criada: {pasta}")
    
    @classmethod
    def obter_config_bot(cls) -> Dict[str, Any]:
        """Retorna configurações específicas do bot"""
        return {
            'headless': cls.HEADLESS_MODE,
            'timeout': cls.TIMEOUT_NAVEGADOR,
            'url': cls.OAB_URL,
            'intervalo_consultas': cls.INTERVALO_CONSULTAS,
            'max_tentativas': cls.MAX_TENTATIVAS
        }
    
    @classmethod
    def obter_config_supabase(cls) -> Dict[str, str]:
        """Retorna configurações do Supabase"""
        return {
            'url': cls.SUPABASE_URL,
            'key': cls.SUPABASE_KEY,
            'tabela': cls.TABELA_ERROS,
            'coluna_id': cls.COLUNA_ID,
            'coluna_usuarios': cls.COLUNA_USUARIOS,
            'coluna_nome': cls.COLUNA_NOME_PROCURADOR
        }
    
    @classmethod
    def obter_config_processamento(cls) -> Dict[str, Any]:
        """Retorna configurações de processamento"""
        return {
            'tamanho_lote': cls.TAMANHO_LOTE,
            'salvar_intermediario': cls.SALVAR_INTERMEDIARIO_A_CADA,
            'min_nome': cls.MIN_COMPRIMENTO_NOME,
            'max_nome': cls.MAX_COMPRIMENTO_NOME,
            'min_oab': cls.MIN_DIGITOS_OAB,
            'max_oab': cls.MAX_DIGITOS_OAB
        }
    
    @classmethod
    def validar_estado(cls, estado: str) -> bool:
        """Valida se o estado é válido"""
        return estado.upper() in cls.ESTADOS_VALIDOS
    
    @classmethod
    def validar_usuario_oab(cls, usuarios_str: str) -> bool:
        """
        Valida se o string usuarios representa uma OAB válida
        PADRÃO REAL: SP388221, RJ123456, etc.
        
        Args:
            usuarios_str: String a validar
            
        Returns:
            True se é OAB válida, False caso contrário
        """
        try:
            usuarios_clean = usuarios_str.strip().upper()
            
            # Usar regex para validar padrão
            for padrao in cls.PADROES_OAB:
                match = re.match(padrao, usuarios_clean)
                if match:
                    estado = match.group(1)
                    numero = match.group(2)
                    
                    # Validar estado
                    if estado in cls.ESTADOS_VALIDOS:
                        # Validar tamanho do número
                        if cls.MIN_DIGITOS_OAB <= len(numero) <= cls.MAX_DIGITOS_OAB:
                            return True
            
            return False
            
        except Exception:
            return False
    
    @classmethod
    def extrair_oab_do_usuario(cls, usuarios_str: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrai número OAB e estado do string usuarios
        
        Args:
            usuarios_str: String do banco (ex: SP388221)
            
        Returns:
            Tupla (numero, estado) ou (None, None) se inválido
        """
        try:
            usuarios_clean = usuarios_str.strip().upper()
            
            for padrao in cls.PADROES_OAB:
                match = re.match(padrao, usuarios_clean)
                if match:
                    estado = match.group(1)
                    numero = match.group(2)
                    
                    if (estado in cls.ESTADOS_VALIDOS and 
                        cls.MIN_DIGITOS_OAB <= len(numero) <= cls.MAX_DIGITOS_OAB):
                        return numero, estado
            
            return None, None
            
        except Exception:
            return None, None
    
    @classmethod
    def validar_nome(cls, nome: str) -> bool:
        """Valida se o nome é válido"""
        if not nome or len(nome) < cls.MIN_COMPRIMENTO_NOME or len(nome) > cls.MAX_COMPRIMENTO_NOME:
            return False
        
        # Verificar se não contém palavras inválidas
        nome_upper = nome.upper()
        for palavra in cls.PALAVRAS_INVALIDAS_NOME:
            if palavra in nome_upper:
                return False
        
        # Verificar se tem pelo menos um espaço (nome e sobrenome)
        if ' ' not in nome:
            return False
        
        # Verificar se não tem números
        if any(char.isdigit() for char in nome):
            return False
        
        return True
    
    @classmethod
    def obter_nome_arquivo_log(cls, sufixo: str = "processamento") -> str:
        """Gera nome do arquivo de log"""
        from datetime import datetime
        timestamp = datetime.now().strftime(cls.FORMATO_TIMESTAMP)
        return f"{cls.PASTA_LOGS}/{sufixo}_{timestamp}.log"
    
    @classmethod
    def obter_nome_arquivo_resultado(cls, sufixo: str = "resultados") -> str:
        """Gera nome do arquivo de resultado"""
        from datetime import datetime
        timestamp = datetime.now().strftime(cls.FORMATO_TIMESTAMP)
        return f"{cls.PASTA_RESULTADOS}/{sufixo}_{timestamp}.json"
    
    @classmethod
    def formatar_data_log(cls) -> str:
        """Retorna data formatada para logs"""
        from datetime import datetime
        return datetime.now().strftime(cls.FORMATO_DATA_LOG)
    
    @classmethod
    def imprimir_config(cls):
        """Imprime configurações atuais"""
        print("🔧 CONFIGURAÇÕES ATUAIS:")
        print("=" * 50)
        print(f"🌐 Supabase URL: {cls.SUPABASE_URL}")
        print(f"📋 Tabela: {cls.TABELA_ERROS}")
        print(f"🔗 Site OAB: {cls.OAB_URL}")
        print(f"⏱️ Timeout: {cls.TIMEOUT_NAVEGADOR}s")
        print(f"🖥️ Headless: {cls.HEADLESS_MODE}")
        print(f"⏳ Intervalo: {cls.INTERVALO_CONSULTAS}s")
        print(f"📁 Pasta logs: {cls.PASTA_LOGS}")
        print(f"📁 Pasta resultados: {cls.PASTA_RESULTADOS}")
        print(f"🔍 Estados válidos: {len(cls.ESTADOS_VALIDOS)}")
        print(f"📝 Padrão OAB: {cls.PADROES_OAB[0]}")
        print(f"✅ Exemplos válidos: {', '.join(cls.EXEMPLOS_VALIDOS[:3])}")
        print(f"❌ Exemplos inválidos: {', '.join(cls.EXEMPLOS_INVALIDOS[:3])}")
        print("=" * 50)

# Configuração de desenvolvimento/debug
class DevConfig(Config):
    """Configurações para desenvolvimento"""
    
    HEADLESS_MODE = False  # Mostrar navegador
    TIMEOUT_NAVEGADOR = 30  # Timeout maior
    INTERVALO_CONSULTAS = 5  # Intervalo maior
    TAMANHO_LOTE = 5  # Lotes menores
    SALVAR_INTERMEDIARIO_A_CADA = 2  # Salvar mais frequentemente

# Configuração de produção
class ProdConfig(Config):
    """Configurações para produção"""
    
    HEADLESS_MODE = True  # Sem interface
    TIMEOUT_NAVEGADOR = 15  # Timeout otimizado
    INTERVALO_CONSULTAS = 2  # Intervalo otimizado
    TAMANHO_LOTE = 100  # Lotes maiores
    SALVAR_INTERMEDIARIO_A_CADA = 25  # Salvar menos frequentemente

# Configuração ativa (alterar conforme necessário)
CONFIGURACAO_ATIVA = Config  # Usar Config, DevConfig ou ProdConfig

def obter_config():
    """Retorna a configuração ativa"""
    return CONFIGURACAO_ATIVA()

# Inicializar pastas ao importar
if __name__ == "__main__":
    Config.criar_pastas()
    Config.imprimir_config()
else:
    # Criar pastas automaticamente ao importar
    Config.criar_pastas()

# Configuração de desenvolvimento/debug
class DevConfig(Config):
    """Configurações para desenvolvimento"""
    
    HEADLESS_MODE = False  # Mostrar navegador
    TIMEOUT_NAVEGADOR = 30  # Timeout maior
    INTERVALO_CONSULTAS = 5  # Intervalo maior
    TAMANHO_LOTE = 5  # Lotes menores
    SALVAR_INTERMEDIARIO_A_CADA = 2  # Salvar mais frequentemente

# Configuração de produção
class ProdConfig(Config):
    """Configurações para produção"""
    
    HEADLESS_MODE = True  # Sem interface
    TIMEOUT_NAVEGADOR = 15  # Timeout otimizado
    INTERVALO_CONSULTAS = 2  # Intervalo otimizado
    TAMANHO_LOTE = 100  # Lotes maiores
    SALVAR_INTERMEDIARIO_A_CADA = 25  # Salvar menos frequentemente

# Configuração ativa (alterar conforme necessário)
CONFIGURACAO_ATIVA = Config  # Usar Config, DevConfig ou ProdConfig

def obter_config():
    """Retorna a configuração ativa"""
    return CONFIGURACAO_ATIVA()

# Inicializar pastas ao importar
if __name__ == "__main__":
    Config.criar_pastas()
    Config.imprimir_config()
else:
    # Criar pastas automaticamente ao importar
    Config.criar_pastas()