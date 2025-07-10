#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Principal - Integração Bot OAB + Supabase
Versão otimizada com configurações centralizadas
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import List, Dict, Optional

# Adicionar o diretório atual ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Verificar dependências
def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    dependencias = [
        'supabase', 'requests', 'selenium', 'PIL', 'pytesseract'
    ]
    
    faltando = []
    for dep in dependencias:
        try:
            __import__(dep)
        except ImportError:
            faltando.append(dep)
    
    if faltando:
        print("❌ Dependências faltando:")
        for dep in faltando:
            print(f"   pip install {dep}")
        return False
    return True

# Importar após verificação
if not verificar_dependencias():
    sys.exit(1)

try:
    from config import Config, DevConfig, ProdConfig
    from bot_oab_supabase import OABSupabaseIntegrator, SupabaseConnector, RegistroErro
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("Certifique-se de que todos os arquivos estão no mesmo diretório")
    sys.exit(1)

class SistemaIntegrado:
    """Sistema principal que gerencia toda a integração"""
    
    def __init__(self, config_class=Config):
        """
        Inicializa o sistema
        
        Args:
            config_class: Classe de configuração a usar
        """
        self.config = config_class()
        self.integrador = None
        self.supabase = None
        self.log_arquivo = None
        
        # Criar pastas necessárias
        self.config.criar_pastas()
        
        # Inicializar log
        self._inicializar_log()
        
        print(f"🚀 Sistema Integrado Bot OAB + Supabase v2.0")
        print(f"📅 Iniciado em: {self.config.formatar_data_log()}")
        
    def _inicializar_log(self):
        """Inicializa o arquivo de log"""
        try:
            self.log_arquivo = self.config.obter_nome_arquivo_log()
            with open(self.log_arquivo, 'w', encoding='utf-8') as f:
                f.write(f"Sistema Integrado Bot OAB + Supabase\n")
                f.write(f"Iniciado em: {self.config.formatar_data_log()}\n")
                f.write("=" * 60 + "\n\n")
            print(f"📄 Log será salvo em: {self.log_arquivo}")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar log: {e}")
    
    def _log(self, mensagem: str):
        """Escreve mensagem no log"""
        try:
            if self.log_arquivo:
                with open(self.log_arquivo, 'a', encoding='utf-8') as f:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    f.write(f"[{timestamp}] {mensagem}\n")
        except Exception as e:
            print(f"⚠️ Erro ao escrever log: {e}")
    
    def inicializar_conexoes(self) -> bool:
        """Inicializa conexões com Supabase e Bot OAB"""
        try:
            # Inicializar Supabase
            print("🔗 Conectando ao Supabase...")
            self.supabase = SupabaseConnector(
                self.config.SUPABASE_URL,
                self.config.SUPABASE_KEY
            )
            self._log("Conexão Supabase estabelecida")
            
            # Inicializar integrador
            print("🤖 Inicializando Bot OAB...")
            self.integrador = OABSupabaseIntegrator(
                self.config.SUPABASE_URL,
                self.config.SUPABASE_KEY
            )
            self._log("Bot OAB inicializado")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inicializar conexões: {e}")
            self._log(f"ERRO: Falha na inicialização - {e}")
            return False
    
    def verificar_status_tabela(self) -> Dict:
        """Verifica status da tabela no Supabase"""
        try:
            print("📊 Verificando status da tabela...")
            
            # Total de registros
            response_total = self.supabase.client.table(self.config.TABELA_ERROS).select('id', count='exact').execute()
            total = response_total.count
            
            # Registros pendentes
            response_pendentes = self.supabase.client.table(self.config.TABELA_ERROS).select('id', count='exact').is_(self.config.COLUNA_NOME_PROCURADOR, None).execute()
            pendentes = response_pendentes.count
            
            # Registros com erro
            response_erros = self.supabase.client.table(self.config.TABELA_ERROS).select('id', count='exact').like(self.config.COLUNA_NOME_PROCURADOR, f'{self.config.PREFIXO_ERRO}%').execute()
            erros = response_erros.count
            
            # Registros preenchidos
            preenchidos = total - pendentes - erros
            
            status = {
                'total': total,
                'pendentes': pendentes,
                'preenchidos': preenchidos,
                'erros': erros,
                'taxa_preenchimento': (preenchidos / total * 100) if total > 0 else 0
            }
            
            print(f"📈 Status da tabela:")
            print(f"   Total: {total}")
            print(f"   Pendentes: {pendentes}")
            print(f"   Preenchidos: {preenchidos}")
            print(f"   Erros: {erros}")
            print(f"   Taxa preenchimento: {status['taxa_preenchimento']:.1f}%")
            
            self._log(f"Status tabela: {json.dumps(status)}")
            
            return status
            
        except Exception as e:
            print(f"❌ Erro ao verificar status: {e}")
            self._log(f"ERRO: Falha ao verificar status - {e}")
            return {}
    
    def processar_lote(self, limite: int = None) -> Dict:
        """
        Processa um lote de registros
        
        Args:
            limite: Número máximo de registros a processar
            
        Returns:
            Estatísticas do processamento
        """
        if not limite:
            limite = self.config.TAMANHO_LOTE
            
        try:
            print(f"🔄 Processando lote de até {limite} registros...")
            self._log(f"Iniciando processamento de lote (limite: {limite})")
            
            # Buscar registros pendentes
            registros = self.supabase.buscar_registros_pendentes()
            
            if not registros:
                print("✅ Nenhum registro pendente encontrado")
                self._log("Nenhum registro pendente encontrado")
                return {'total': 0, 'processados': 0, 'sucessos': 0, 'erros': 0}
            
            # Limitar quantidade
            registros = registros[:limite]
            
            # Inicializar bot se necessário
            if not self.integrador.bot_oab:
                print("🤖 Iniciando bot OAB...")
                if not self.integrador.iniciar_bot():
                    print("❌ Falha ao iniciar bot")
                    self._log("ERRO: Falha ao iniciar bot")
                    return {'erro': 'Falha ao iniciar bot'}
            
            # Processar registros
            estatisticas = {
                'total': len(registros),
                'processados': 0,
                'sucessos': 0,
                'erros': 0,
                'tempo_inicio': time.time()
            }
            
            for i, registro in enumerate(registros, 1):
                print(f"\n{'='*50}")
                print(f"📊 Progresso: {i}/{len(registros)}")
                print(f"🔄 Registro {registro.id}: {registro.usuario}")

                self._log(f"Processando registro {registro.id}: {registro.usuario}")
                
                try:
                    sucesso = self.integrador.processar_registro(registro)
                    
                    if sucesso:
                        estatisticas['sucessos'] += 1
                        self._log(f"SUCESSO: Registro {registro.id} processado")
                    else:
                        estatisticas['erros'] += 1
                        self._log(f"ERRO: Falha ao processar registro {registro.id}")
                    
                    estatisticas['processados'] += 1
                    
                    # Salvar intermediário
                    if i % self.config.SALVAR_INTERMEDIARIO_A_CADA == 0:
                        self._salvar_resultado_intermediario(estatisticas)
                    
                    # Pausa entre consultas
                    if i < len(registros):
                        time.sleep(self.config.INTERVALO_CONSULTAS)
                        
                except KeyboardInterrupt:
                    print("\n⏹️ Processamento interrompido pelo usuário")
                    self._log("Processamento interrompido pelo usuário")
                    break
                    
                except Exception as e:
                    print(f"❌ Erro inesperado no registro {registro.id}: {e}")
                    self._log(f"ERRO: Exceção no registro {registro.id} - {e}")
                    estatisticas['erros'] += 1
                    estatisticas['processados'] += 1
                    continue
            
            # Calcular estatísticas finais
            estatisticas['tempo_total'] = time.time() - estatisticas['tempo_inicio']
            estatisticas['taxa_sucesso'] = (estatisticas['sucessos'] / max(1, estatisticas['processados'])) * 100
            
            self._log(f"Lote concluído: {json.dumps(estatisticas)}")
            
            return estatisticas
            
        except Exception as e:
            print(f"❌ Erro no processamento do lote: {e}")
            self._log(f"ERRO: Falha no processamento do lote - {e}")
            return {'erro': str(e)}
    
    def _salvar_resultado_intermediario(self, estatisticas: Dict):
        """Salva resultado intermediário"""
        try:
            arquivo = self.config.obter_nome_arquivo_resultado("intermediario")
            
            resultado = {
                'timestamp': self.config.formatar_data_log(),
                'estatisticas': estatisticas,
                'config': {
                    'timeout': self.config.TIMEOUT_NAVEGADOR,
                    'intervalo': self.config.INTERVALO_CONSULTAS,
                    'headless': self.config.HEADLESS_MODE
                }
            }
            
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Resultado intermediário salvo")
            self._log(f"Resultado intermediário salvo em: {arquivo}")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar resultado intermediário: {e}")
            self._log(f"ERRO: Falha ao salvar intermediário - {e}")
    
    def processar_todos(self) -> Dict:
        """Processa todos os registros pendentes"""
        try:
            print("🚀 Iniciando processamento de todos os registros pendentes...")
            self._log("Iniciando processamento completo")
            
            # Verificar status inicial
            status_inicial = self.verificar_status_tabela()
            
            if status_inicial.get('pendentes', 0) == 0:
                print("✅ Nenhum registro pendente para processar")
                return status_inicial
            
            # Processar em lotes
            estatisticas_total = {
                'lotes_processados': 0,
                'total_registros': 0,
                'total_sucessos': 0,
                'total_erros': 0,
                'tempo_inicio': time.time()
            }
            
            lote_numero = 1
            
            while True:
                print(f"\n🔄 LOTE {lote_numero}")
                print("=" * 40)
                
                resultado_lote = self.processar_lote()
                
                if resultado_lote.get('erro'):
                    print(f"❌ Erro no lote {lote_numero}: {resultado_lote['erro']}")
                    break
                
                if resultado_lote.get('total', 0) == 0:
                    print("✅ Todos os registros foram processados")
                    break
                
                # Atualizar estatísticas
                estatisticas_total['lotes_processados'] += 1
                estatisticas_total['total_registros'] += resultado_lote.get('processados', 0)
                estatisticas_total['total_sucessos'] += resultado_lote.get('sucessos', 0)
                estatisticas_total['total_erros'] += resultado_lote.get('erros', 0)
                
                print(f"📊 Lote {lote_numero} concluído:")
                print(f"   Processados: {resultado_lote.get('processados', 0)}")
                print(f"   Sucessos: {resultado_lote.get('sucessos', 0)}")
                print(f"   Erros: {resultado_lote.get('erros', 0)}")
                
                lote_numero += 1
                
                # Pausa entre lotes
                if resultado_lote.get('total', 0) == self.config.TAMANHO_LOTE:
                    print(f"⏳ Pausa entre lotes...")
                    time.sleep(5)
                else:
                    break
            
            # Calcular estatísticas finais
            estatisticas_total['tempo_total'] = time.time() - estatisticas_total['tempo_inicio']
            estatisticas_total['taxa_sucesso'] = (estatisticas_total['total_sucessos'] / max(1, estatisticas_total['total_registros'])) * 100
            
            # Verificar status final
            status_final = self.verificar_status_tabela()
            
            # Salvar resultado final
            self._salvar_resultado_final(estatisticas_total, status_inicial, status_final)
            
            return estatisticas_total
            
        except Exception as e:
            print(f"❌ Erro no processamento completo: {e}")
            self._log(f"ERRO: Falha no processamento completo - {e}")
            return {'erro': str(e)}
    
    def _salvar_resultado_final(self, estatisticas: Dict, status_inicial: Dict, status_final: Dict):
        """Salva resultado final completo"""
        try:
            arquivo = self.config.obter_nome_arquivo_resultado("final")
            
            resultado = {
                'timestamp': self.config.formatar_data_log(),
                'estatisticas': estatisticas,
                'status_inicial': status_inicial,
                'status_final': status_final,
                'config_utilizada': {
                    'timeout': self.config.TIMEOUT_NAVEGADOR,
                    'intervalo': self.config.INTERVALO_CONSULTAS,
                    'headless': self.config.HEADLESS_MODE,
                    'tamanho_lote': self.config.TAMANHO_LOTE
                }
            }
            
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Resultado final salvo em: {arquivo}")
            self._log(f"Resultado final salvo em: {arquivo}")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar resultado final: {e}")
            self._log(f"ERRO: Falha ao salvar resultado final - {e}")
    
    def imprimir_estatisticas_finais(self, estatisticas: Dict):
        """Imprime estatísticas finais formatadas"""
        print(f"\n🎯 ESTATÍSTICAS FINAIS:")
        print("=" * 60)
        
        if estatisticas.get('erro'):
            print(f"❌ Erro: {estatisticas['erro']}")
            return
        
        print(f"📊 Lotes processados: {estatisticas.get('lotes_processados', 0)}")
        print(f"📋 Total de registros: {estatisticas.get('total_registros', 0)}")
        print(f"✅ Sucessos: {estatisticas.get('total_sucessos', 0)}")
        print(f"❌ Erros: {estatisticas.get('total_erros', 0)}")
        print(f"📈 Taxa de sucesso: {estatisticas.get('taxa_sucesso', 0):.1f}%")
        
        tempo_total = estatisticas.get('tempo_total', 0)
        if tempo_total > 0:
            print(f"⏱️ Tempo total: {self._formatar_tempo(tempo_total)}")
            
            if estatisticas.get('total_registros', 0) > 0:
                tempo_medio = tempo_total / estatisticas['total_registros']
                print(f"⚡ Tempo médio por registro: {tempo_medio:.1f}s")
        
        print(f"📄 Log completo: {self.log_arquivo}")
        
        # Verificar status final
        print(f"\n📊 Status final da tabela:")
        status_final = self.verificar_status_tabela()
    
    def _formatar_tempo(self, segundos: float) -> str:
        """Formata tempo em formato legível"""
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
    
    def fechar(self):
        """Fecha todas as conexões"""
        try:
            if self.integrador:
                self.integrador.fechar()
            
            if self.log_arquivo:
                self._log("Sistema encerrado")
                print(f"📄 Log final salvo em: {self.log_arquivo}")
            
            print("🔒 Sistema encerrado com sucesso")
            
        except Exception as e:
            print(f"⚠️ Erro ao fechar sistema: {e}")

def menu_principal():
    """Menu principal interativo"""
    print("\n🚀 Sistema Integrado Bot OAB + Supabase")
    print("=" * 50)
    print("1. Processar todos os registros pendentes")
    print("2. Processar um lote específico")
    print("3. Verificar status da tabela")
    print("4. Processar registro específico por ID")
    print("5. Configurações do sistema")
    print("6. Testar conexões")
    print("7. Sair")
    print("=" * 50)

def executar_menu():
    """Executa o menu principal"""
    sistema = None
    
    try:
        # Escolher configuração
        print("🔧 Escolha o modo de execução:")
        print("1. Produção (headless, otimizado)")
        print("2. Desenvolvimento (com interface, debug)")
        print("3. Personalizado")
        
        modo = input("Modo (1-3): ").strip()
        
        if modo == "1":
            sistema = SistemaIntegrado(ProdConfig)
        elif modo == "2":
            sistema = SistemaIntegrado(DevConfig)
        else:
            sistema = SistemaIntegrado(Config)
        
        # Inicializar conexões
        if not sistema.inicializar_conexoes():
            print("❌ Falha ao inicializar. Encerrando...")
            return
        
        # Loop do menu
        while True:
            menu_principal()
            opcao = input("Escolha uma opção (1-7): ").strip()
            
            if opcao == "1":
                print("\n🚀 Processando todos os registros...")
                resultado = sistema.processar_todos()
                sistema.imprimir_estatisticas_finais(resultado)
                
            elif opcao == "2":
                try:
                    limite = int(input("Tamanho do lote: ").strip())
                    resultado = sistema.processar_lote(limite)
                    print(f"\n📊 Resultado do lote:")
                    print(f"   Processados: {resultado.get('processados', 0)}")
                    print(f"   Sucessos: {resultado.get('sucessos', 0)}")
                    print(f"   Erros: {resultado.get('erros', 0)}")
                except ValueError:
                    print("❌ Número inválido")
                    
            elif opcao == "3":
                sistema.verificar_status_tabela()
                
            elif opcao == "4":
                try:
                    registro_id = int(input("ID do registro: ").strip())
                    # Implementar processamento específico
                    print(f"🔄 Processando registro {registro_id}...")
                except ValueError:
                    print("❌ ID inválido")
                    
            elif opcao == "5":
                sistema.config.imprimir_config()
                
            elif opcao == "6":
                print("🔗 Testando conexões...")
                sistema.verificar_status_tabela()
                
            elif opcao == "7":
                print("👋 Encerrando...")
                break
                
            else:
                print("❌ Opção inválida")
            
            input("\nPressione Enter para continuar...")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Sistema interrompido pelo usuário")
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        
    finally:
        if sistema:
            sistema.fechar()

def main():
    """Função principal"""
    print("🚀 Sistema Integrado Bot OAB + Supabase v2.0")
    print("=" * 60)
    
    # Verificar se deve executar direto ou com menu
    if len(sys.argv) > 1:
        if sys.argv[1] == "--auto":
            # Execução automática
            sistema = SistemaIntegrado(ProdConfig)
            
            try:
                if sistema.inicializar_conexoes():
                    resultado = sistema.processar_todos()
                    sistema.imprimir_estatisticas_finais(resultado)
                else:
                    print("❌ Falha na inicialização")
                    
            finally:
                sistema.fechar()
        else:
            print("Uso: python main.py [--auto]")
    else:
        # Menu interativo
        executar_menu()

if __name__ == "__main__":
    main()