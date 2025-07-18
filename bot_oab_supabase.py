#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema integrado Bot OAB + Supabase - VERSÃO COM CACHE OTIMIZADO
Automatiza o preenchimento de nomes de procuradores na tabela erros_processados
COM SISTEMA DE CACHE PARA EVITAR CONSULTAS DUPLICADAS
"""

import os
import sys
import time
import re
import json
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

# Importar bibliotecas necessárias
try:
    from supabase import create_client, Client
    import requests
except ImportError:
    print("❌ Dependências não encontradas. Instale com:")
    print("pip install supabase requests")
    sys.exit(1)

# Adicionar o diretório atual ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar o bot OAB existente
from bot_oab.models.resultado_oab import ResultadoOAB
from bot_oab.core.bot_oab_core import BotOABCorrigido

@dataclass
class RegistroErro:
    """Classe para representar um registro da tabela erros_processados"""
    id: int
    usuario: str  # Número OAB
    nome_procurador: Optional[str] = None
    # Outros campos podem ser adicionados conforme necessário

@dataclass
class ResultadoCache:
    """Classe para representar um resultado em cache"""
    numero_oab: str
    estado: str
    nome: Optional[str] = None
    erro: Optional[str] = None
    sucesso: bool = False
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class CacheConsultas:
    """
    Sistema de cache para consultas OAB - EVITA CONSULTAS DUPLICADAS
    Mantém resultados de consultas anteriores para reutilização
    """
    
    def __init__(self, expirar_apos_horas: int = 24):
        """
        Inicializa o sistema de cache
        
        Args:
            expirar_apos_horas: Horas após as quais o cache expira (0 = nunca expira)
        """
        self.cache: Dict[str, ResultadoCache] = {}  # chave: "NUMERO/ESTADO"
        self.expirar_apos = timedelta(hours=expirar_apos_horas) if expirar_apos_horas > 0 else None
        
        # Estatísticas
        self.estatisticas = {
            'consultas_cache': 0,      # Quantas vezes usou cache
            'consultas_novas': 0,      # Quantas consultas novas foram feitas
            'cache_hits': 0,           # Sucessos do cache
            'cache_misses': 0,         # Cache miss (não tinha no cache)
            'duplicatas_evitadas': 0   # Consultas duplicadas evitadas
        }
        
        print("🔄 Sistema de cache inicializado")
        if self.expirar_apos:
            print(f"⏰ Cache expira após: {expirar_apos_horas}h")
        else:
            print("♾️ Cache nunca expira (válido por toda a sessão)")
    
    def _gerar_chave(self, numero_oab: str, estado: str) -> str:
        """Gera chave única para o cache"""
        return f"{numero_oab.strip()}/{estado.strip().upper()}"
    
    def _cache_expirado(self, resultado: ResultadoCache) -> bool:
        """Verifica se o resultado do cache expirou"""
        if not self.expirar_apos:
            return False
        
        return datetime.now() - resultado.timestamp > self.expirar_apos
    
    def consultar_cache(self, numero_oab: str, estado: str) -> Optional[ResultadoCache]:
        """
        Consulta o cache para um número OAB
        
        Args:
            numero_oab: Número da OAB
            estado: Estado da OAB
            
        Returns:
            ResultadoCache se encontrado e válido, None caso contrário
        """
        chave = self._gerar_chave(numero_oab, estado)
        
        if chave in self.cache:
            resultado = self.cache[chave]
            
            # Verificar se expirou
            if self._cache_expirado(resultado):
                print(f"⏰ Cache expirado para {chave}")
                del self.cache[chave]
                self.estatisticas['cache_misses'] += 1
                return None
            
            print(f"🎯 Cache HIT: {chave} → {resultado.nome or resultado.erro}")
            self.estatisticas['cache_hits'] += 1
            self.estatisticas['consultas_cache'] += 1
            return resultado
        else:
            self.estatisticas['cache_misses'] += 1
            return None
    
    def salvar_cache(self, numero_oab: str, estado: str, resultado: ResultadoOAB):
        """
        Salva resultado no cache
        
        Args:
            numero_oab: Número da OAB
            estado: Estado da OAB  
            resultado: Resultado da consulta
        """
        chave = self._gerar_chave(numero_oab, estado)
        
        resultado_cache = ResultadoCache(
            numero_oab=numero_oab,
            estado=estado,
            nome=resultado.nome if resultado.sucesso else None,
            erro=resultado.erro if not resultado.sucesso else None,
            sucesso=resultado.sucesso
        )
        
        self.cache[chave] = resultado_cache
        self.estatisticas['consultas_novas'] += 1
        
        print(f"💾 Cache SAVE: {chave} → {resultado_cache.nome or resultado_cache.erro}")
    
    def contar_duplicatas(self, lista_oabs: List[Tuple[str, str]]) -> Dict[str, int]:
        """
        Conta quantas vezes cada OAB aparece na lista
        
        Args:
            lista_oabs: Lista de tuplas (numero, estado)
            
        Returns:
            Dict com contagem de cada OAB
        """
        contagem = defaultdict(int)
        
        for numero, estado in lista_oabs:
            chave = self._gerar_chave(numero, estado)
            contagem[chave] += 1
        
        return dict(contagem)
    
    def calcular_economia(self, lista_oabs: List[Tuple[str, str]]) -> Dict[str, int]:
        """
        Calcula economia potencial com o cache
        
        Args:
            lista_oabs: Lista de tuplas (numero, estado)
            
        Returns:
            Dict com estatísticas de economia
        """
        contagem = self.contar_duplicatas(lista_oabs)
        
        total_consultas_sem_cache = len(lista_oabs)
        consultas_unicas = len(contagem)
        duplicatas_evitadas = total_consultas_sem_cache - consultas_unicas
        economia_percentual = (duplicatas_evitadas / total_consultas_sem_cache * 100) if total_consultas_sem_cache > 0 else 0
        
        return {
            'total_registros': total_consultas_sem_cache,
            'consultas_unicas': consultas_unicas,
            'duplicatas_evitadas': duplicatas_evitadas,
            'economia_percentual': economia_percentual,
            'oabs_duplicadas': {k: v for k, v in contagem.items() if v > 1}
        }
    
    def imprimir_estatisticas(self):
        """Imprime estatísticas do cache"""
        total_consultas = self.estatisticas['consultas_cache'] + self.estatisticas['consultas_novas']
        
        print(f"\n📊 ESTATÍSTICAS DO CACHE:")
        print(f"{'='*50}")
        print(f"🎯 Cache Hits: {self.estatisticas['cache_hits']}")
        print(f"❌ Cache Misses: {self.estatisticas['cache_misses']}")
        print(f"💾 Consultas em cache: {self.estatisticas['consultas_cache']}")
        print(f"🔍 Consultas novas: {self.estatisticas['consultas_novas']}")
        print(f"⚡ Duplicatas evitadas: {self.estatisticas['duplicatas_evitadas']}")
        
        if total_consultas > 0:
            taxa_cache = (self.estatisticas['consultas_cache'] / total_consultas * 100)
            print(f"📈 Taxa de cache: {taxa_cache:.1f}%")
        
        print(f"🗃️ Entradas no cache: {len(self.cache)}")
    
    def limpar_cache(self):
        """Limpa todo o cache"""
        self.cache.clear()
        print("🗑️ Cache limpo")
    
    def salvar_cache_arquivo(self, arquivo: str = "cache_oab.json"):
        """Salva cache em arquivo para persistência"""
        try:
            dados_cache = {}
            for chave, resultado in self.cache.items():
                dados_cache[chave] = {
                    'numero_oab': resultado.numero_oab,
                    'estado': resultado.estado,
                    'nome': resultado.nome,
                    'erro': resultado.erro,
                    'sucesso': resultado.sucesso,
                    'timestamp': resultado.timestamp.isoformat()
                }
            
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump({
                    'cache': dados_cache,
                    'estatisticas': self.estatisticas
                }, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Cache salvo em: {arquivo}")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar cache: {e}")
    
    def carregar_cache_arquivo(self, arquivo: str = "cache_oab.json"):
        """Carrega cache de arquivo"""
        try:
            if not os.path.exists(arquivo):
                print(f"📁 Arquivo de cache não encontrado: {arquivo}")
                return
            
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            # Carregar cache
            cache_dados = dados.get('cache', {})
            for chave, item in cache_dados.items():
                resultado = ResultadoCache(
                    numero_oab=item['numero_oab'],
                    estado=item['estado'],
                    nome=item.get('nome'),
                    erro=item.get('erro'),
                    sucesso=item.get('sucesso', False),
                    timestamp=datetime.fromisoformat(item['timestamp'])
                )
                
                # Verificar se não expirou
                if not self._cache_expirado(resultado):
                    self.cache[chave] = resultado
            
            # Carregar estatísticas
            if 'estatisticas' in dados:
                self.estatisticas.update(dados['estatisticas'])
            
            print(f"📂 Cache carregado: {len(self.cache)} entradas válidas")
            
        except Exception as e:
            print(f"⚠️ Erro ao carregar cache: {e}")

class SupabaseConnector:
    """Classe para gerenciar conexão com Supabase"""
    
    def __init__(self, url: str, key: str):
        """
        Inicializa a conexão com Supabase
        
        Args:
            url: URL do Supabase
            key: Chave de API do Supabase
        """
        self.url = url
        self.key = key
        self.client: Client = create_client(url, key)
        print(f"🔗 Conectado ao Supabase: {url}")
    
    def buscar_registros_pendentes(self, limite: Optional[int] = None) -> List[RegistroErro]:
        """
        Busca registros com nome_procurador vazio E que sejam OABs válidas
        FILTRO: Apenas registros que começam com estado válido (ex: SP388221)
        IGNORA: Matrículas como M356437, números simples, etc.
        
        Args:
            limite: Número máximo de registros a buscar
            
        Returns:
            Lista de registros que precisam ser preenchidos
        """
        try:
            print("🔍 Buscando registros com nome_procurador vazio...")
            
            query = self.client.table('erros_processados').select('*').is_('nome_procurador', None)
            
            if limite:
                query = query.limit(limite)
            
            response = query.execute()
            
            if not response.data:
                print("✅ Nenhum registro pendente encontrado")
                return []
            
            registros_validos = []
            registros_invalidos = 0
            
            estados_validos = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
                             'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 
                             'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
            
            for item in response.data:
                usuario = item['usuario']
                
                # VALIDAÇÃO: Verificar se é OAB válida
                if self._is_oab_valida(usuario, estados_validos):
                    registro = RegistroErro(
                        id=item['id'],
                        usuario=usuario,
                        nome_procurador=item.get('nome_procurador')
                    )
                    registros_validos.append(registro)
                else:
                    registros_invalidos += 1
            
            print(f"📋 Total de registros vazios: {len(response.data)}")
            print(f"✅ Registros válidos para processar: {len(registros_validos)}")
            print(f"⚠️ Registros inválidos (ignorados): {registros_invalidos}")
            
            if registros_invalidos > 0:
                print(f"💡 Registros inválidos incluem: matrículas (M356437), números sem estado, etc.")
            
            return registros_validos
            
        except Exception as e:
            print(f"❌ Erro ao buscar registros: {e}")
            return []
    
    def _is_oab_valida(self, usuarios_str: str, estados_validos: List[str]) -> bool:
        """
        Verifica se a string usuarios representa uma OAB válida
        
        Args:
            usuarios_str: String a verificar
            estados_validos: Lista de estados válidos
            
        Returns:
            True se é OAB válida, False caso contrário
        """
        try:
            usuarios_clean = usuarios_str.strip().upper()
            
            # Deve ter pelo menos 5 caracteres (estado + 3 dígitos mínimo)
            if len(usuarios_clean) < 5:
                return False
            
            # Deve começar com estado válido (2 letras)
            possivel_estado = usuarios_clean[:2]
            if possivel_estado not in estados_validos:
                return False
            
            # Resto deve ser número
            resto = usuarios_clean[2:]
            if not resto.isdigit():
                return False
            
            # Número deve ter tamanho apropriado
            if len(resto) < 4 or len(resto) > 8:
                return False
            
            return True
            
        except Exception:
            return False
    
    def atualizar_nome_procurador(self, registro_id: int, nome_procurador: str) -> bool:
        """
        Atualiza o nome do procurador no banco
        
        Args:
            registro_id: ID do registro
            nome_procurador: Nome a ser inserido
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            response = self.client.table('erros_processados').update({
                'nome_procurador': nome_procurador
            }).eq('id', registro_id).execute()
            
            if response.data:
                return True
            else:
                print(f"❌ Falha ao atualizar registro {registro_id}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao atualizar registro {registro_id}: {e}")
            return False
    
    def atualizar_multiplos_registros(self, registro_ids: List[int], nome_procurador: str) -> int:
        """
        Atualiza múltiplos registros com o mesmo nome
        
        Args:
            registro_ids: Lista de IDs para atualizar
            nome_procurador: Nome a ser inserido
            
        Returns:
            Número de registros atualizados com sucesso
        """
        sucessos = 0
        
        for registro_id in registro_ids:
            if self.atualizar_nome_procurador(registro_id, nome_procurador):
                sucessos += 1
        
        return sucessos
    
    def marcar_erro_consulta(self, registro_id: int, erro: str) -> bool:
        """
        Marca um registro como erro de consulta
        
        Args:
            registro_id: ID do registro
            erro: Descrição do erro
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            response = self.client.table('erros_processados').update({
                'nome_procurador': f"ERRO: {erro}"
            }).eq('id', registro_id).execute()
            
            return response.data is not None
            
        except Exception as e:
            print(f"❌ Erro ao marcar erro: {e}")
            return False
    
    def marcar_erro_multiplos(self, registro_ids: List[int], erro: str) -> int:
        """
        Marca múltiplos registros com o mesmo erro
        
        Args:
            registro_ids: Lista de IDs para marcar como erro
            erro: Descrição do erro
            
        Returns:
            Número de registros marcados com sucesso
        """
        sucessos = 0
        
        for registro_id in registro_ids:
            if self.marcar_erro_consulta(registro_id, erro):
                sucessos += 1
        
        return sucessos

class OABSupabaseIntegrator:
    """Classe principal que integra o Bot OAB com Supabase - VERSÃO COM CACHE"""
    
    def __init__(self, supabase_url: str, supabase_key: str, usar_cache_persistente: bool = True):
        """
        Inicializa o integrador
        
        Args:
            supabase_url: URL do Supabase
            supabase_key: Chave de API do Supabase
            usar_cache_persistente: Se deve salvar/carregar cache de arquivo
        """
        self.supabase = SupabaseConnector(supabase_url, supabase_key)
        self.bot_oab = None
        
        # 🔄 NOVO: Sistema de cache
        self.cache = CacheConsultas(expirar_apos_horas=24)
        self.usar_cache_persistente = usar_cache_persistente
        
        # Carregar cache persistente se habilitado
        if self.usar_cache_persistente:
            self.cache.carregar_cache_arquivo()
        
        self.estatisticas = {
            'total_processados': 0,
            'sucessos': 0,
            'erros': 0,
            'tempo_inicio': time.time(),
            'consultas_evitadas': 0,  # NOVO: consultas evitadas pelo cache
            'registros_duplicados': 0  # NOVO: registros com OAB duplicada
        }
    
    def iniciar_bot(self) -> bool:
        """
        Inicializa o bot OAB
        
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            print("🤖 Iniciando Bot OAB...")
            self.bot_oab = BotOABCorrigido(headless=True, timeout=15)
            
            if not self.bot_oab.acessar_site():
                print("❌ Falha ao acessar site da OAB")
                return False
            
            print("✅ Bot OAB iniciado e site acessado")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar bot: {e}")
            return False
    
    def extrair_numero_oab(self, usuarios_str: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrai número OAB e estado da string usuarios
        PADRÃO REAL DO BANCO: SP388221, RJ123456, etc.
        
        Args:
            usuarios_str: String contendo informações do usuário
            
        Returns:
            Tupla (numero_oab, estado) ou (None, None) se não encontrar
        """
        try:
            # Limpar string
            usuarios_clean = usuarios_str.strip().upper()
            
            # VALIDAÇÃO 1: Deve começar com estado válido (2 letras)
            estados_validos = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
                             'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 
                             'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
            
            # Verificar se começa com estado válido
            if len(usuarios_clean) < 3:
                return None, None
            
            possivel_estado = usuarios_clean[:2]
            
            if possivel_estado not in estados_validos:
                return None, None
            
            # VALIDAÇÃO 2: Resto deve ser número
            resto = usuarios_clean[2:]
            
            if not resto.isdigit():
                return None, None
            
            # VALIDAÇÃO 3: Número deve ter tamanho apropriado
            if len(resto) < 4 or len(resto) > 8:
                return None, None
            
            estado = possivel_estado
            numero = resto
            
            # REGRA ESPECIAL: Remover zero inicial se existir
            if numero.startswith('0') and len(numero) > 1:
                numero_original = numero
                numero = numero.lstrip('0')
                
                # Verificar se restou algum número após remover zeros
                if not numero:
                    print(f"⚠️ Número inválido (só zeros): {usuarios_str}")
                    return None, None
                
                print(f"🔧 Zero inicial removido: {numero_original} → {numero}")
            
            return numero, estado
            
        except Exception as e:
            return None, None
    
    def agrupar_registros_por_oab(self, registros: List[RegistroErro]) -> Dict[str, List[RegistroErro]]:
        """
        NOVO: Agrupa registros por número OAB para evitar consultas duplicadas
        
        Args:
            registros: Lista de registros
            
        Returns:
            Dict onde chave é "NUMERO/ESTADO" e valor é lista de registros
        """
        grupos = defaultdict(list)
        registros_invalidos = []
        
        for registro in registros:
            numero_oab, estado = self.extrair_numero_oab(registro.usuario)
            
            if numero_oab and estado:
                chave = f"{numero_oab}/{estado}"
                grupos[chave].append(registro)
            else:
                registros_invalidos.append(registro)
        
        # Log de agrupamento
        if grupos:
            print(f"\n📊 AGRUPAMENTO POR OAB:")
            print(f"✅ OABs únicas: {len(grupos)}")
            print(f"📋 Total de registros: {sum(len(lista) for lista in grupos.values())}")
            
            # Mostrar OABs com mais registros
            oabs_duplicadas = {k: len(v) for k, v in grupos.items() if len(v) > 1}
            if oabs_duplicadas:
                print(f"🔄 OABs com registros duplicados: {len(oabs_duplicadas)}")
                
                # Mostrar top 5 mais duplicadas
                top_duplicadas = sorted(oabs_duplicadas.items(), key=lambda x: x[1], reverse=True)[:5]
                for oab, count in top_duplicadas:
                    print(f"   {oab}: {count} registros")
                
                total_duplicatas = sum(count - 1 for count in oabs_duplicadas.values())
                print(f"⚡ Consultas que serão evitadas: {total_duplicatas}")
                self.estatisticas['consultas_evitadas'] = total_duplicatas
                self.estatisticas['registros_duplicados'] = sum(oabs_duplicadas.values())
        
        if registros_invalidos:
            print(f"⚠️ Registros com OAB inválida: {len(registros_invalidos)}")
        
        return dict(grupos)
    
    def contem_palavra_advogado(self, nome: str) -> bool:
        """
        Verifica se o nome contém a palavra 'advogado' ou suas variações
        
        Args:
            nome: Nome a ser verificado
            
        Returns:
            True se contém palavra 'advogado' ou variações, False caso contrário
        """
        if not nome:
            return False
        
        nome_upper = nome.upper()
        
        # Variações da palavra advogado
        variacoes_advogado = [
            'ADVOGADO', 'ADVOGADA', 'ADVOGADOS', 'ADVOGADAS',
            'ADV.', 'ADV', 'ADVOG.', 'ADVOG',
            'ADVOGAD', 'ADVOCAC', 'ADVOCACIA'
        ]
        
        for variacao in variacoes_advogado:
            if variacao in nome_upper:
                return True
        
        return False
    
    def processar_oab_unica(self, numero_oab: str, estado: str) -> ResultadoOAB:
        """
        NOVO: Processa uma OAB única, usando cache se disponível
        
        Args:
            numero_oab: Número da OAB
            estado: Estado da OAB
            
        Returns:
            ResultadoOAB com o resultado
        """
        # 1. Verificar cache primeiro
        resultado_cache = self.cache.consultar_cache(numero_oab, estado)
        
        if resultado_cache:
            # Usar resultado do cache
            resultado = ResultadoOAB(inscricao=numero_oab, estado=estado)
            
            if resultado_cache.sucesso:
                resultado.nome = resultado_cache.nome
                resultado.sucesso = True
                print(f"📋 Cache: {numero_oab}/{estado} → {resultado_cache.nome}")
            else:
                resultado.erro = resultado_cache.erro
                resultado.sucesso = False
                print(f"📋 Cache: {numero_oab}/{estado} → ERRO: {resultado_cache.erro}")
            
            return resultado
        
        # 2. Cache miss - fazer consulta real
        print(f"🔍 Consultando OAB {numero_oab}/{estado} (nova consulta)")
        
        max_tentativas = 3  # Máximo de tentativas para refazer a consulta
        tentativa_atual = 0
        
        while tentativa_atual < max_tentativas:
            tentativa_atual += 1
            
            try:
                if tentativa_atual > 1:
                    print(f"🔄 Tentativa {tentativa_atual}/{max_tentativas} - Refazendo consulta...")
                    time.sleep(1)  # Pausa entre tentativas
                
                resultado = self.bot_oab.consultar_inscricao(numero_oab, estado)
                
                # Verificar se o nome contém palavra "advogado"
                if resultado.sucesso and resultado.nome:
                    if self.contem_palavra_advogado(resultado.nome):
                        print(f"⚠️ Nome inválido detectado (contém 'advogado'): {resultado.nome}")
                        
                        if tentativa_atual < max_tentativas:
                            print(f"🔄 Refazendo consulta - tentativa {tentativa_atual + 1}")
                            continue  # Refazer a consulta
                        else:
                            print(f"❌ Máximo de tentativas atingido. Marcando como erro.")
                            resultado.sucesso = False
                            resultado.erro = f"Nome inválido após {max_tentativas} tentativas: {resultado.nome}"
                    else:
                        print(f"✅ Nome válido extraído: {resultado.nome}")
                
                # 3. Salvar no cache (tanto sucesso quanto erro)
                self.cache.salvar_cache(numero_oab, estado, resultado)
                
                return resultado
                
            except Exception as e:
                print(f"❌ Erro na tentativa {tentativa_atual}: {e}")
                
                if tentativa_atual >= max_tentativas:
                    # Criar resultado de erro após esgotar tentativas
                    resultado = ResultadoOAB(inscricao=numero_oab, estado=estado)
                    resultado.erro = f"Erro na consulta após {max_tentativas} tentativas: {str(e)}"
                    resultado.sucesso = False
                    
                    # Salvar erro no cache também
                    self.cache.salvar_cache(numero_oab, estado, resultado)
                    
                    return resultado
                else:
                    continue  # Tentar novamente
        
        # Fallback (não deveria chegar aqui)
        resultado = ResultadoOAB(inscricao=numero_oab, estado=estado)
        resultado.erro = "Erro inesperado no processamento"
        resultado.sucesso = False
        return resultado
    
    def processar_grupo_registros(self, oab_key: str, registros: List[RegistroErro]) -> bool:
        """
        NOVO: Processa um grupo de registros com a mesma OAB
        
        Args:
            oab_key: Chave da OAB (formato: "NUMERO/ESTADO")
            registros: Lista de registros com a mesma OAB
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            print(f"\n🔄 Processando grupo: {oab_key} ({len(registros)} registros)")
            
            # Extrair número e estado
            numero_oab, estado = oab_key.split('/')
            
            # Fazer uma única consulta para todos os registros do grupo
            resultado = self.processar_oab_unica(numero_oab, estado)
            
            registro_ids = [reg.id for reg in registros]
            
            if resultado.sucesso and resultado.nome:
                # Limpar e validar nome
                nome_limpo = self.limpar_nome(resultado.nome)
                
                if nome_limpo:
                    # Atualizar TODOS os registros do grupo
                    sucessos = self.supabase.atualizar_multiplos_registros(registro_ids, nome_limpo)
                    
                    print(f"✅ Sucesso: {nome_limpo}")
                    print(f"💾 Atualizados: {sucessos}/{len(registros)} registros")
                    
                    self.estatisticas['sucessos'] += sucessos
                    return True
                else:
                    erro = "Nome inválido após limpeza"
                    erros_marcados = self.supabase.marcar_erro_multiplos(registro_ids, erro)
                    
                    print(f"❌ Erro: {erro}")
                    print(f"🚫 Marcados como erro: {erros_marcados}/{len(registros)} registros")
                    
                    self.estatisticas['erros'] += erros_marcados
                    return False
            else:
                # Marcar erro para todos os registros do grupo
                erro = resultado.erro or "Consulta sem sucesso"
                erros_marcados = self.supabase.marcar_erro_multiplos(registro_ids, erro)
                
                print(f"❌ Erro: {erro}")
                print(f"🚫 Marcados como erro: {erros_marcados}/{len(registros)} registros")
                
                self.estatisticas['erros'] += erros_marcados
                return False
                
        except Exception as e:
            print(f"❌ Erro ao processar grupo {oab_key}: {e}")
            
            # Marcar erro para todos
            registro_ids = [reg.id for reg in registros]
            erros_marcados = self.supabase.marcar_erro_multiplos(registro_ids, str(e))
            self.estatisticas['erros'] += erros_marcados
            
            return False
    
    def processar_todos_registros(self, limite: Optional[int] = None) -> Dict:
        """
        NOVO: Processa todos os registros pendentes com sistema de cache otimizado
        
        Args:
            limite: Número máximo de registros a processar
            
        Returns:
            Dicionário com estatísticas do processamento
        """
        print("🚀 Iniciando processamento de registros pendentes COM CACHE OTIMIZADO...")
        
        # 1. Buscar registros pendentes
        registros = self.supabase.buscar_registros_pendentes(limite)
        
        if not registros:
            print("✅ Não há registros pendentes para processar")
            return self.obter_estatisticas()
        
        # 2. Agrupar registros por OAB única
        grupos_oab = self.agrupar_registros_por_oab(registros)
        
        if not grupos_oab:
            print("❌ Nenhum registro com OAB válida encontrado")
            return self.obter_estatisticas()
        
        # 3. Calcular economia esperada
        todas_oabs = []
        for oab_key, regs in grupos_oab.items():
            numero, estado = oab_key.split('/')
            todas_oabs.extend([(numero, estado)] * len(regs))
        
        economia = self.cache.calcular_economia(todas_oabs)
        
        print(f"\n💡 ECONOMIA ESPERADA:")
        print(f"📊 Total de registros: {economia['total_registros']}")
        print(f"🔍 Consultas únicas necessárias: {economia['consultas_unicas']}")
        print(f"⚡ Consultas evitadas: {economia['duplicatas_evitadas']}")
        print(f"📈 Economia: {economia['economia_percentual']:.1f}%")
        
        # 4. Iniciar bot se necessário
        if not self.bot_oab and not self.iniciar_bot():
            print("❌ Falha ao iniciar bot. Abortando...")
            return self.obter_estatisticas()
        
        # 5. Processar cada grupo de OAB
        total_grupos = len(grupos_oab)
        grupos_processados = 0
        
        for i, (oab_key, registros_grupo) in enumerate(grupos_oab.items(), 1):
            print(f"\n{'='*60}")
            print(f"📊 Progresso: {i}/{total_grupos} grupos OAB")
            
            try:
                self.processar_grupo_registros(oab_key, registros_grupo)
                self.estatisticas['total_processados'] += len(registros_grupo)
                grupos_processados += 1
                
                # Pausa entre consultas para não sobrecarregar o servidor
                if i < total_grupos:
                    print("⏳ Aguardando 2 segundos...")
                    time.sleep(2)
                
            except KeyboardInterrupt:
                print("\n⏹️ Processamento interrompido pelo usuário")
                break
            except Exception as e:
                print(f"❌ Erro inesperado no grupo {oab_key}: {e}")
                self.estatisticas['erros'] += len(registros_grupo)
                continue
        
        # 6. Salvar cache persistente se habilitado
        if self.usar_cache_persistente:
            self.cache.salvar_cache_arquivo()
        
        # 7. Mostrar estatísticas finais
        self.imprimir_estatisticas()
        self.cache.imprimir_estatisticas()
        
        return self.obter_estatisticas()
    
    def limpar_nome(self, nome: str) -> str:
        """
        Limpa e valida o nome do advogado
        
        Args:
            nome: Nome bruto
            
        Returns:
            Nome limpo ou string vazia se inválido
        """
        if not nome:
            return ""
        
        # Remover espaços extras
        nome = re.sub(r'\s+', ' ', nome.strip())
        
        # Validar se é um nome válido
        if (len(nome) >= 5 and 
            len(nome) <= 100 and 
            ' ' in nome and 
            not any(char.isdigit() for char in nome) and
            not any(palavra in nome.upper() for palavra in ['ERRO', 'INVALID', 'NULL', 'NONE']) and
            not self.contem_palavra_advogado(nome)):  # NOVA VALIDAÇÃO: Não deve conter "advogado"
            return nome
        
        return ""
    
    def obter_estatisticas(self) -> Dict:
        """
        Retorna estatísticas do processamento
        
        Returns:
            Dicionário com estatísticas
        """
        tempo_total = time.time() - self.estatisticas['tempo_inicio']
        
        # Calcular estatísticas do cache
        total_consultas_reais = self.cache.estatisticas['consultas_novas']
        total_consultas_evitadas = self.estatisticas['consultas_evitadas']
        
        return {
            'total_processados': self.estatisticas['total_processados'],
            'sucessos': self.estatisticas['sucessos'],
            'erros': self.estatisticas['erros'],
            'tempo_total_segundos': tempo_total,
            'tempo_total_formatado': self.formatar_tempo(tempo_total),
            'taxa_sucesso': (self.estatisticas['sucessos'] / max(1, self.estatisticas['total_processados'])) * 100,
            
            # NOVAS ESTATÍSTICAS DE CACHE
            'consultas_reais': total_consultas_reais,
            'consultas_evitadas': total_consultas_evitadas,
            'registros_duplicados': self.estatisticas['registros_duplicados'],
            'economia_percentual': (total_consultas_evitadas / max(1, total_consultas_reais + total_consultas_evitadas)) * 100,
            'cache_hits': self.cache.estatisticas['cache_hits'],
            'cache_misses': self.cache.estatisticas['cache_misses'],
            'entradas_cache': len(self.cache.cache)
        }
    
    def formatar_tempo(self, segundos: float) -> str:
        """
        Formata tempo em segundos para formato legível
        
        Args:
            segundos: Tempo em segundos
            
        Returns:
            Tempo formatado (ex: "2m 30s")
        """
        if segundos < 60:
            return f"{segundos:.1f}s"
        elif segundos < 3600:
            minutos = int(segundos // 60)
            segundos_restantes = segundos % 60
            return f"{minutos}m {segundos_restantes:.1f}s"
        else:
            horas = int(segundos // 3600)
            minutos = int((segundos % 3600) // 60)
            return f"{horas}h {minutos}m"
    
    def imprimir_estatisticas(self):
        """Imprime estatísticas finais do processamento - VERSÃO COM CACHE"""
        stats = self.obter_estatisticas()
        
        print(f"\n🎯 ESTATÍSTICAS FINAIS:")
        print(f"{'='*60}")
        print(f"📊 Total processados: {stats['total_processados']}")
        print(f"✅ Sucessos: {stats['sucessos']}")
        print(f"❌ Erros: {stats['erros']}")
        print(f"📈 Taxa de sucesso: {stats['taxa_sucesso']:.1f}%")
        print(f"⏱️ Tempo total: {stats['tempo_total_formatado']}")
        
        # NOVAS ESTATÍSTICAS DE CACHE
        print(f"\n🔄 OTIMIZAÇÃO COM CACHE:")
        print(f"🔍 Consultas reais ao site OAB: {stats['consultas_reais']}")
        print(f"⚡ Consultas evitadas (duplicatas): {stats['consultas_evitadas']}")
        print(f"📈 Economia de consultas: {stats['economia_percentual']:.1f}%")
        print(f"👥 Registros com OAB duplicada: {stats['registros_duplicados']}")
        
        if stats['total_processados'] > 0:
            tempo_medio = stats['tempo_total_segundos'] / stats['consultas_reais'] if stats['consultas_reais'] > 0 else 0
            print(f"⚡ Tempo médio por consulta real: {tempo_medio:.1f}s")
            
            # Calcular tempo economizado
            if stats['consultas_evitadas'] > 0 and tempo_medio > 0:
                tempo_economizado = stats['consultas_evitadas'] * tempo_medio
                print(f"⏰ Tempo economizado: {self.formatar_tempo(tempo_economizado)}")
    
    def processar_registro_especifico(self, registro_id: int) -> bool:
        """
        NOVO: Processa um registro específico usando cache
        
        Args:
            registro_id: ID do registro a processar
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Buscar registro específico
            response = self.supabase.client.table('erros_processados').select('*').eq('id', registro_id).execute()
            
            if not response.data:
                print(f"❌ Registro {registro_id} não encontrado")
                return False
            
            registro_data = response.data[0]
            registro = RegistroErro(
                id=registro_data['id'],
                usuario=registro_data['usuario'],
                nome_procurador=registro_data.get('nome_procurador')
            )
            
            print(f"📋 Processando registro específico: {registro_id}")
            print(f"🔍 OAB: {registro.usuario}")
            
            # Extrair OAB
            numero_oab, estado = self.extrair_numero_oab(registro.usuario)
            
            if not numero_oab or not estado:
                erro = f"OAB não encontrada em: {registro.usuario}"
                self.supabase.marcar_erro_consulta(registro.id, erro)
                print(f"❌ {erro}")
                return False
            
            # Iniciar bot se necessário
            if not self.bot_oab and not self.iniciar_bot():
                print("❌ Falha ao iniciar bot")
                return False
            
            # Processar usando cache
            resultado = self.processar_oab_unica(numero_oab, estado)
            
            if resultado.sucesso and resultado.nome:
                nome_limpo = self.limpar_nome(resultado.nome)
                
                if nome_limpo:
                    if self.supabase.atualizar_nome_procurador(registro.id, nome_limpo):
                        print(f"✅ Sucesso: {nome_limpo}")
                        return True
                    else:
                        print(f"❌ Falha ao salvar no banco")
                        return False
                else:
                    erro = "Nome inválido após limpeza"
                    self.supabase.marcar_erro_consulta(registro.id, erro)
                    print(f"❌ {erro}")
                    return False
            else:
                erro = resultado.erro or "Consulta sem sucesso"
                self.supabase.marcar_erro_consulta(registro.id, erro)
                print(f"❌ {erro}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao processar registro {registro_id}: {e}")
            return False
    
    def limpar_cache_expirado(self):
        """NOVO: Remove entradas expiradas do cache"""
        cache_limpo = {}
        removidos = 0
        
        for chave, resultado in self.cache.cache.items():
            if not self.cache._cache_expirado(resultado):
                cache_limpo[chave] = resultado
            else:
                removidos += 1
        
        self.cache.cache = cache_limpo
        
        if removidos > 0:
            print(f"🧹 Cache limpo: {removidos} entradas expiradas removidas")
            print(f"📊 Entradas restantes: {len(self.cache.cache)}")
    
    def estatisticas_cache(self) -> Dict:
        """NOVO: Retorna estatísticas detalhadas do cache"""
        return {
            'entradas_ativas': len(self.cache.cache),
            'cache_hits': self.cache.estatisticas['cache_hits'],
            'cache_misses': self.cache.estatisticas['cache_misses'],
            'consultas_novas': self.cache.estatisticas['consultas_novas'],
            'consultas_cache': self.cache.estatisticas['consultas_cache'],
            'taxa_hit': (self.cache.estatisticas['cache_hits'] / 
                        max(1, self.cache.estatisticas['cache_hits'] + self.cache.estatisticas['cache_misses'])) * 100,
            'duplicatas_evitadas': self.cache.estatisticas['duplicatas_evitadas']
        }
    
    def fechar(self):
        """Fecha conexões e limpa recursos - VERSÃO COM CACHE"""
        try:
            # Salvar cache se habilitado
            if self.usar_cache_persistente:
                self.cache.salvar_cache_arquivo()
                print("💾 Cache salvo em arquivo")
            
            # Fechar bot
            if self.bot_oab:
                self.bot_oab.fechar()
            
            # Imprimir estatísticas finais do cache
            print(f"\n📊 ESTATÍSTICAS FINAIS DO CACHE:")
            stats_cache = self.estatisticas_cache()
            print(f"🗃️ Entradas no cache: {stats_cache['entradas_ativas']}")
            print(f"🎯 Taxa de acerto: {stats_cache['taxa_hit']:.1f}%")
            print(f"⚡ Duplicatas evitadas: {stats_cache['duplicatas_evitadas']}")
            
            print("🔒 Recursos liberados")
            
        except Exception as e:
            print(f"⚠️ Erro ao fechar: {e}")

# Função principal para usar o sistema
def main():
    """Função principal para executar o sistema integrado COM CACHE"""
    print("🚀 Sistema Integrado Bot OAB + Supabase - VERSÃO COM CACHE OTIMIZADO")
    print("=" * 70)
    
    # Configurações do Supabase
    SUPABASE_URL = "https://rdkvvigjmowtvhxqlrnp.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJka3Z2aWdqbW93dHZoeHFscm5wIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIxNjkwODQsImV4cCI6MjA1Nzc0NTA4NH0.pFn1faGoWsapclNIjVhnD8A754DMiY7dZL9Ig0lDMQ4"
    
    # Criar integrador COM CACHE
    integrador = OABSupabaseIntegrator(SUPABASE_URL, SUPABASE_KEY, usar_cache_persistente=True)
    
    try:
        # Executar processamento
        resultado = integrador.processar_todos_registros()
        
        print(f"\n🎉 Processamento concluído!")
        print(f"📊 Resultados: {resultado['sucessos']} sucessos, {resultado['erros']} erros")
        print(f"⚡ Economia: {resultado['economia_percentual']:.1f}% de consultas evitadas")
        
    except KeyboardInterrupt:
        print("\n⏹️ Operação cancelada pelo usuário")
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        integrador.fechar()

def exemplo_uso_cache():
    """Exemplo de como usar o sistema com cache"""
    print("📝 Exemplo de uso do sistema com cache:")
    print("=" * 50)
    
    # Inicializar integrador
    integrador = OABSupabaseIntegrator(
        "sua_url_supabase", 
        "sua_chave_supabase",
        usar_cache_persistente=True
    )
    
    try:
        # Processar registros específicos
        print("🔍 Processando registro específico...")
        sucesso = integrador.processar_registro_especifico(123)
        
        if sucesso:
            print("✅ Registro processado com sucesso!")
        
        # Limpar cache expirado
        print("🧹 Limpando cache expirado...")
        integrador.limpar_cache_expirado()
        
        # Ver estatísticas do cache
        stats = integrador.estatisticas_cache()
        print(f"📊 Taxa de acerto do cache: {stats['taxa_hit']:.1f}%")
        
    finally:
        integrador.fechar()

if __name__ == "__main__":
    main()