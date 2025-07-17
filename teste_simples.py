#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema integrado Bot OAB + Supabase
Automatiza o preenchimento de nomes de procuradores na tabela erros_processados
"""

import os
import sys
import time
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

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
    
    def buscar_registros_pendentes(self) -> List[RegistroErro]:
        """
        Busca registros com nome_procurador vazio E que sejam OABs válidas
        FILTRO: Apenas registros que começam com estado válido (ex: SP388221)
        IGNORA: Matrículas como M356437, números simples, etc.
        
        Returns:
            Lista de registros que precisam ser preenchidos
        """
        try:
            print("🔍 Buscando registros com nome_procurador vazio...")
            
            response = self.client.table('erros_processados').select('*').is_('nome_procurador', None).execute()
            
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
            print(f"💾 Atualizando registro {registro_id} com nome: {nome_procurador}")
            
            response = self.client.table('erros_processados').update({
                'nome_procurador': nome_procurador
            }).eq('id', registro_id).execute()
            
            if response.data:
                print(f"✅ Registro {registro_id} atualizado com sucesso")
                return True
            else:
                print(f"❌ Falha ao atualizar registro {registro_id}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao atualizar registro {registro_id}: {e}")
            return False
    
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
            print(f"⚠️ Marcando erro para registro {registro_id}: {erro}")
            
            response = self.client.table('erros_processados').update({
                'nome_procurador': f"ERRO: {erro}"
            }).eq('id', registro_id).execute()
            
            return response.data is not None
            
        except Exception as e:
            print(f"❌ Erro ao marcar erro: {e}")
            return False

class OABSupabaseIntegrator:
    """Classe principal que integra o Bot OAB com Supabase"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Inicializa o integrador
        
        Args:
            supabase_url: URL do Supabase
            supabase_key: Chave de API do Supabase
        """
        self.supabase = SupabaseConnector(supabase_url, supabase_key)
        self.bot_oab = None
        self.estatisticas = {
            'total_processados': 0,
            'sucessos': 0,
            'erros': 0,
            'tempo_inicio': time.time()
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
                print(f"⚠️ Registro muito curto: {usuarios_str}")
                return None, None
            
            possivel_estado = usuarios_clean[:2]
            
            if possivel_estado not in estados_validos:
                print(f"⚠️ Não é OAB válida (não começa com estado): {usuarios_str}")
                return None, None
            
            # VALIDAÇÃO 2: Resto deve ser número
            resto = usuarios_clean[2:]
            
            if not resto.isdigit():
                print(f"⚠️ Não é OAB válida (não é número após estado): {usuarios_str}")
                return None, None
            
            # VALIDAÇÃO 3: Número deve ter tamanho apropriado
            if len(resto) < 4 or len(resto) > 8:
                print(f"⚠️ Número OAB inválido (tamanho {len(resto)}): {usuarios_str}")
                return None, None
            
            estado = possivel_estado
            numero = resto
            
            print(f"✅ OAB válida extraída: {numero}/{estado} (de: {usuarios_str})")
            return numero, estado
            
        except Exception as e:
            print(f"❌ Erro ao extrair OAB: {e}")
            return None, None
    
    def processar_registro(self, registro: RegistroErro) -> bool:
        """
        Processa um registro individual
        
        Args:
            registro: Registro a ser processado
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            print(f"\n📋 Processando registro {registro.id}")
            
            # Extrair número OAB e estado
            numero_oab, estado = self.extrair_numero_oab(registro.usuario)

            if not numero_oab or not estado:
                erro = f"OAB não encontrada em: {registro.usuario}"
                self.supabase.marcar_erro_consulta(registro.id, erro)
                self.estatisticas['erros'] += 1
                return False
            
            print(f"🔍 Consultando OAB {numero_oab}/{estado}")
            
            # Realizar consulta no CNA
            resultado = self.bot_oab.consultar_inscricao(numero_oab, estado)
            
            if resultado.sucesso and resultado.nome:
                # Limpar e validar nome
                nome_limpo = self.limpar_nome(resultado.nome)
                
                if nome_limpo:
                    # Atualizar no banco
                    if self.supabase.atualizar_nome_procurador(registro.id, nome_limpo):
                        print(f"✅ Sucesso: {nome_limpo}")
                        self.estatisticas['sucessos'] += 1
                        return True
                    else:
                        print(f"❌ Falha ao salvar no banco")
                        self.estatisticas['erros'] += 1
                        return False
                else:
                    erro = "Nome inválido após limpeza"
                    self.supabase.marcar_erro_consulta(registro.id, erro)
                    self.estatisticas['erros'] += 1
                    return False
            else:
                # Marcar erro na consulta
                erro = resultado.erro or "Consulta sem sucesso"
                self.supabase.marcar_erro_consulta(registro.id, erro)
                self.estatisticas['erros'] += 1
                return False
                
        except Exception as e:
            print(f"❌ Erro ao processar registro {registro.id}: {e}")
            self.supabase.marcar_erro_consulta(registro.id, str(e))
            self.estatisticas['erros'] += 1
            return False
    
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
            not any(palavra in nome.upper() for palavra in ['ERRO', 'INVALID', 'NULL', 'NONE'])):
            return nome
        
        return ""
    
    def processar_todos_registros(self) -> Dict:
        """
        Processa todos os registros pendentes
        
        Returns:
            Dicionário com estatísticas do processamento
        """
        print("🚀 Iniciando processamento de registros pendentes...")
        
        # Buscar registros pendentes
        registros = self.supabase.buscar_registros_pendentes()
        
        if not registros:
            print("✅ Não há registros pendentes para processar")
            return self.obter_estatisticas()
        
        # Iniciar bot se necessário
        if not self.bot_oab and not self.iniciar_bot():
            print("❌ Falha ao iniciar bot. Abortando...")
            return self.obter_estatisticas()
        
        # Processar cada registro
        for i, registro in enumerate(registros, 1):
            print(f"\n{'='*60}")
            print(f"📊 Progresso: {i}/{len(registros)} registros")
            print(f"🔄 Registro {registro.id}: {registro.usuario}")


            
            try:
                self.processar_registro(registro)
                self.estatisticas['total_processados'] += 1
                
                # Pausa entre consultas para não sobrecarregar o servidor
                if i < len(registros):
                    print("⏳ Aguardando 2 segundos...")
                    time.sleep(2)
                
            except KeyboardInterrupt:
                print("\n⏹️ Processamento interrompido pelo usuário")
                break
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
                continue
        
        # Mostrar estatísticas finais
        self.imprimir_estatisticas()
        
        return self.obter_estatisticas()
    
    def obter_estatisticas(self) -> Dict:
        """
        Retorna estatísticas do processamento
        
        Returns:
            Dicionário com estatísticas
        """
        tempo_total = time.time() - self.estatisticas['tempo_inicio']
        
        return {
            'total_processados': self.estatisticas['total_processados'],
            'sucessos': self.estatisticas['sucessos'],
            'erros': self.estatisticas['erros'],
            'tempo_total_segundos': tempo_total,
            'tempo_total_formatado': self.formatar_tempo(tempo_total),
            'taxa_sucesso': (self.estatisticas['sucessos'] / max(1, self.estatisticas['total_processados'])) * 100
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
        """Imprime estatísticas finais do processamento"""
        stats = self.obter_estatisticas()
        
        print(f"\n🎯 ESTATÍSTICAS FINAIS:")
        print(f"{'='*60}")
        print(f"📊 Total processados: {stats['total_processados']}")
        print(f"✅ Sucessos: {stats['sucessos']}")
        print(f"❌ Erros: {stats['erros']}")
        print(f"📈 Taxa de sucesso: {stats['taxa_sucesso']:.1f}%")
        print(f"⏱️ Tempo total: {stats['tempo_total_formatado']}")
        
        if stats['total_processados'] > 0:
            tempo_medio = stats['tempo_total_segundos'] / stats['total_processados']
            print(f"⚡ Tempo médio por registro: {tempo_medio:.1f}s")
    
    def fechar(self):
        """Fecha conexões e limpa recursos"""
        if self.bot_oab:
            self.bot_oab.fechar()
        print("🔒 Recursos liberados")

# Função principal para usar o sistema
def main():
    """Função principal para executar o sistema integrado"""
    print("🚀 Sistema Integrado Bot OAB + Supabase")
    print("=" * 60)
    
    # Configurações do Supabase
    SUPABASE_URL = "https://rdkvvigjmowtvhxqlrnp.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJka3Z2aWdqbW93dHZoeHFscm5wIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIxNjkwODQsImV4cCI6MjA1Nzc0NTA4NH0.pFn1faGoWsapclNIjVhnD8A754DMiY7dZL9Ig0lDMQ4"
    
    # Criar integrador
    integrador = OABSupabaseIntegrator(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Executar processamento
        resultado = integrador.processar_todos_registros()
        
        print(f"\n🎉 Processamento concluído!")
        print(f"📊 Resultados: {resultado['sucessos']} sucessos, {resultado['erros']} erros")
        
    except KeyboardInterrupt:
        print("\n⏹️ Operação cancelada pelo usuário")
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        integrador.fechar()

if __name__ == "__main__":
    main()