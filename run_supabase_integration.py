#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar a integração Bot OAB + Supabase
Sistema automatizado para preencher nomes de procuradores
"""

import os
import sys
import time
from datetime import datetime

# Verificar se as dependências estão instaladas
def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    dependencias = [
        ('supabase', 'pip install supabase'),
        ('requests', 'pip install requests'),
        ('selenium', 'pip install selenium'),
        ('PIL', 'pip install pillow'),
        ('pytesseract', 'pip install pytesseract')
    ]
    
    dependencias_faltando = []
    
    for modulo, comando in dependencias:
        try:
            __import__(modulo)
        except ImportError:
            dependencias_faltando.append((modulo, comando))
    
    if dependencias_faltando:
        print("❌ Dependências faltando:")
        for modulo, comando in dependencias_faltando:
            print(f"   {modulo}: {comando}")
        return False
    
    return True

# Importar o sistema integrado
try:
    from bot_oab_supabase import OABSupabaseIntegrator
except ImportError:
    print("❌ Erro: Certifique-se de que o arquivo bot_oab_supabase.py está no mesmo diretório")
    sys.exit(1)

def menu_principal():
    """Exibe o menu principal do sistema"""
    print("\n🤖 Sistema Integrado Bot OAB + Supabase")
    print("=" * 50)
    print("1. Processar registros pendentes (modo automático)")
    print("2. Verificar registros pendentes (apenas contar)")
    print("3. Processar um registro específico")
    print("4. Configurar credenciais do Supabase")
    print("5. Testar conexão com Supabase")
    print("6. Sair")
    print("=" * 50)

def obter_credenciais():
    """Obtém credenciais do Supabase"""
    # Credenciais padrão fornecidas
    url_padrao = "https://rdkvvigjmowtvhxqlrnp.supabase.co"
    key_padrao = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJka3Z2aWdqbW93dHZoeHFscm5wIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIxNjkwODQsImV4cCI6MjA1Nzc0NTA4NH0.pFn1faGoWsapclNIjVhnD8A754DMiY7dZL9Ig0lDMQ4"
    
    print("\n🔑 Configuração do Supabase:")
    print("Pressione Enter para usar as credenciais padrão")
    
    url = input(f"URL do Supabase [{url_padrao}]: ").strip()
    if not url:
        url = url_padrao
    
    key = input(f"Chave Anon [{key_padrao[:20]}...]: ").strip()
    if not key:
        key = key_padrao
    
    return url, key

def processar_automatico():
    """Executa o processamento automático de todos os registros"""
    print("\n🚀 Iniciando processamento automático...")
    
    # Obter credenciais
    url, key = obter_credenciais()
    
    # Confirmar execução
    print(f"\n⚠️ ATENÇÃO: O sistema irá:")
    print(f"   1. Buscar registros com nome_procurador vazio")
    print(f"   2. Consultar cada OAB no site da OAB")
    print(f"   3. Atualizar o banco com os nomes encontrados")
    print(f"   4. Marcar erros para OABs não encontradas")
    
    confirmar = input(f"\nDeseja continuar? (s/n): ").strip().lower()
    if confirmar not in ['s', 'sim', 'y', 'yes']:
        print("❌ Operação cancelada")
        return
    
    # Criar integrador e processar
    integrador = OABSupabaseIntegrator(url, key)
    
    try:
        print(f"\n🕒 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        resultado = integrador.processar_todos_registros()
        
        print(f"\n✅ Processamento concluído!")
        print(f"🕒 Fim: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Salvar log
        salvar_log(resultado)
        
    except KeyboardInterrupt:
        print("\n⏹️ Processamento interrompido pelo usuário")
        
    except Exception as e:
        print(f"❌ Erro durante processamento: {e}")
        
    finally:
        integrador.fechar()

def verificar_pendentes():
    """Verifica quantos registros estão pendentes sem processar"""
    print("\n🔍 Verificando registros pendentes...")
    
    url, key = obter_credenciais()
    
    try:
        from bot_oab_supabase import SupabaseConnector
        
        supabase = SupabaseConnector(url, key)
        registros = supabase.buscar_registros_pendentes()
        
        print(f"\n📊 Resultados:")
        print(f"   Registros pendentes: {len(registros)}")
        
        if registros:
            print(f"   Primeiros 5 registros:")
            for i, reg in enumerate(registros[:5], 1):
                print(f"      {i}. ID: {reg.id} | OAB: {reg.usuarios}")
            
            if len(registros) > 5:
                print(f"      ... e mais {len(registros) - 5} registros")
        
    except Exception as e:
        print(f"❌ Erro ao verificar pendentes: {e}")

def processar_especifico():
    """Processa um registro específico"""
    print("\n🎯 Processamento de registro específico")
    
    try:
        registro_id = int(input("Digite o ID do registro: ").strip())
    except ValueError:
        print("❌ ID inválido")
        return
    
    url, key = obter_credenciais()
    
    try:
        from bot_oab_supabase import SupabaseConnector
        
        supabase = SupabaseConnector(url, key)
        
        # Buscar registro específico
        response = supabase.client.table('erros_processados').select('*').eq('id', registro_id).execute()
        
        if not response.data:
            print(f"❌ Registro {registro_id} não encontrado")
            return
        
        registro_data = response.data[0]
        print(f"\n📋 Registro encontrado:")
        print(f"   ID: {registro_data['id']}")
        print(f"   Usuários: {registro_data['usuario']}")
        print(f"   Nome atual: {registro_data.get('nome_procurador', 'VAZIO')}")
        
        confirmar = input(f"\nDeseja processar este registro? (s/n): ").strip().lower()
        if confirmar not in ['s', 'sim', 'y', 'yes']:
            print("❌ Operação cancelada")
            return
        
        # Processar
        integrador = OABSupabaseIntegrator(url, key)
        
        from bot_oab_supabase import RegistroErro
        registro = RegistroErro(
            id=registro_data['id'],
            usuario=registro_data['usuario'],
            nome_procurador=registro_data.get('nome_procurador')
        )
        
        if integrador.iniciar_bot():
            sucesso = integrador.processar_registro(registro)
            
            if sucesso:
                print(f"✅ Registro processado com sucesso!")
            else:
                print(f"❌ Falha ao processar registro")
        else:
            print(f"❌ Falha ao iniciar bot")
        
        integrador.fechar()
        
    except Exception as e:
        print(f"❌ Erro ao processar registro: {e}")

def testar_conexao():
    """Testa a conexão com o Supabase"""
    print("\n🔗 Testando conexão com Supabase...")
    
    url, key = obter_credenciais()
    
    try:
        from bot_oab_supabase import SupabaseConnector
        
        supabase = SupabaseConnector(url, key)
        
        # Testar consulta simples
        response = supabase.client.table('erros_processados').select('id').limit(1).execute()
        
        print(f"✅ Conexão estabelecida com sucesso!")
        print(f"📊 Tabela acessível: erros_processados")
        
        # Contar registros
        response_count = supabase.client.table('erros_processados').select('id', count='exact').execute()
        total = response_count.count
        
        # Contar pendentes
        response_pending = supabase.client.table('erros_processados').select('id', count='exact').is_('nome_procurador', None).execute()
        pendentes = response_pending.count
        
        print(f"📈 Total de registros: {total}")
        print(f"📋 Registros pendentes: {pendentes}")
        print(f"✅ Registros preenchidos: {total - pendentes}")
        
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        print(f"💡 Verifique as credenciais e a conexão com a internet")

def salvar_log(resultado):
    """Salva log do processamento"""
    try:
        os.makedirs('logs', exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        arquivo_log = f"logs/processamento_supabase_{timestamp}.log"
        
        with open(arquivo_log, 'w', encoding='utf-8') as f:
            f.write(f"Log de Processamento - {datetime.now()}\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total processados: {resultado['total_processados']}\n")
            f.write(f"Sucessos: {resultado['sucessos']}\n")
            f.write(f"Erros: {resultado['erros']}\n")
            f.write(f"Taxa de sucesso: {resultado['taxa_sucesso']:.1f}%\n")
            f.write(f"Tempo total: {resultado['tempo_total_formatado']}\n")
        
        print(f"📄 Log salvo em: {arquivo_log}")
        
    except Exception as e:
        print(f"⚠️ Erro ao salvar log: {e}")

def main():
    """Função principal com menu interativo"""
    if not verificar_dependencias():
        print("\n❌ Instale as dependências necessárias e tente novamente")
        return
    
    while True:
        try:
            menu_principal()
            opcao = input("\nEscolha uma opção (1-6): ").strip()
            
            if opcao == "1":
                processar_automatico()
                
            elif opcao == "2":
                verificar_pendentes()
                
            elif opcao == "3":
                processar_especifico()
                
            elif opcao == "4":
                print("\n🔧 Configuração de credenciais:")
                print("As credenciais são inseridas a cada execução.")
                print("Para alterar permanentemente, edite o arquivo bot_oab_supabase.py")
                
            elif opcao == "5":
                testar_conexao()
                
            elif opcao == "6":
                print("\n👋 Encerrando sistema...")
                break
                
            else:
                print("❌ Opção inválida! Escolha entre 1-6")
            
            # Pausa antes de mostrar menu novamente
            input("\nPressione Enter para continuar...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Sistema encerrado pelo usuário")
            break
            
        except Exception as e:
            print(f"\n❌ Erro inesperado: {e}")
            input("Pressione Enter para continuar...")

if __name__ == "__main__":
    main()