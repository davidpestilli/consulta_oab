#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal para executar o Bot OAB
Sistema de organização em pastas por data/hora
"""

import sys
import os

# Adicionar o diretório atual ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Agora podemos importar o bot
from bot_oab.models.resultado_oab import ResultadoOAB
from bot_oab.core.bot_oab_core import BotOABCorrigido

def main():
    """Função principal para executar o bot"""
    print("🤖 Bot OAB - Consulta de Advogados")
    print("=" * 40)
    
    # Criar instância do bot
    bot = BotOABCorrigido(headless=False, timeout=15)
    
    try:
        # Acessar site
        print("🌐 Acessando site da OAB...")
        if not bot.acessar_site():
            print("❌ Falha ao acessar o site")
            return
            
        # Exemplo de consulta
        inscricao = "147520"
        estado = "SP"
        
        print(f"🔍 Consultando OAB {inscricao}/{estado}...")
        resultado = bot.consultar_inscricao(inscricao, estado)
        
        # Exibir resultado
        print(f"\n📊 RESULTADO:")
        print(f"{'='*50}")
        print(f"👤 Nome: {resultado.nome}")
        print(f"🏷️ Tipo: {resultado.tipo}")
        print(f"📊 Situação: {resultado.situacao}")
        print(f"📞 Telefone: {resultado.telefone}")
        print(f"📍 Endereço: {resultado.endereco}")
        print(f"✅ Sucesso: {resultado.sucesso}")
        
        if resultado.erro:
            print(f"❌ Erro: {resultado.erro}")
        
        # Salvar resultados se bem-sucedida
        if resultado.sucesso:
            print(f"\n💾 Salvando resultados na pasta organizada...")
            
            # O sistema agora salva automaticamente na pasta Pesquisa/data-hora
            arquivos = bot.data_exporter.salvar_todos_formatos([resultado])
            
            print(f"\n📁 Pasta da pesquisa: {bot.data_exporter.obter_pasta_atual()}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Operação cancelada pelo usuário")
        
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🔒 Fechando navegador...")
        bot.fechar()

def consulta_interativa():
    """Função para consulta interativa - CORRIGIDA para salvamento automático"""
    print("🤖 Bot OAB - Consulta Interativa")
    print("=" * 40)
    
    # Solicitar dados do usuário
    inscricao = input("📝 Digite o número da inscrição OAB: ").strip()
    estado = input("🗺️ Digite a sigla do estado (SP, RJ, MG, etc.): ").strip().upper()
    
    if not inscricao or not estado:
        print("❌ Inscrição e estado são obrigatórios!")
        return
    
    # Executar consulta
    bot = BotOABCorrigido(headless=False, timeout=15)
    
    try:
        if not bot.acessar_site():
            print("❌ Falha ao acessar o site")
            return
            
        print(f"🔍 Consultando OAB {inscricao}/{estado}...")
        resultado = bot.consultar_inscricao(inscricao, estado)
        
        # Exibir resultado detalhado
        print(f"\n📊 RESULTADO DA CONSULTA:")
        print(f"{'='*60}")
        print(f"📝 Inscrição: {resultado.inscricao}/{resultado.estado}")
        print(f"👤 Nome: {resultado.nome}")
        print(f"🏷️ Tipo: {resultado.tipo}")
        print(f"📊 Situação: {resultado.situacao}")
        print(f"📞 Telefone: {resultado.telefone}")
        print(f"📍 Endereço: {resultado.endereco}")
        print(f"📧 Email: {resultado.email}")
        print(f"📅 Data Inscrição: {resultado.data_inscricao}")
        print(f"🎫 Nº Carteira: {resultado.numero_carteira}")
        print(f"✅ Sucesso: {resultado.sucesso}")
        
        if resultado.erro:
            print(f"❌ Erro: {resultado.erro}")
        
        if resultado.detalhes_completos:
            print(f"📋 Detalhes: {resultado.detalhes_completos}")
        
        # ✅ CORREÇÃO: Salvar automaticamente se bem-sucedida (removida pergunta desnecessária)
        if resultado.sucesso:
            print(f"\n💾 Salvando resultados automaticamente...")
            arquivos = bot.data_exporter.salvar_todos_formatos([resultado])
            print(f"📁 Pasta: {bot.data_exporter.obter_pasta_atual()}")
            print(f"✅ Arquivos salvos com sucesso!")
        else:
            print(f"\n⚠️ Consulta sem sucesso - nenhum arquivo salvo")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        
    finally:
        bot.fechar()

def consulta_multipla():
    """Função para consultas múltiplas"""
    print("🤖 Bot OAB - Consulta Múltipla")
    print("=" * 40)
    
    # Coletar múltiplas consultas
    consultas = []
    
    print("📝 Digite as consultas (pressione Enter em branco para finalizar):")
    
    while True:
        print(f"\n--- Consulta {len(consultas) + 1} ---")
        inscricao = input("Número da inscrição (ou Enter para finalizar): ").strip()
        
        if not inscricao:
            break
            
        estado = input("Estado (SP, RJ, MG, etc.): ").strip().upper()
        
        if not estado:
            print("❌ Estado é obrigatório!")
            continue
            
        consultas.append((inscricao, estado))
        print(f"✅ {inscricao}/{estado} adicionado")
    
    if not consultas:
        print("❌ Nenhuma consulta adicionada!")
        return
    
    print(f"\n🚀 Preparando para executar {len(consultas)} consultas...")
    input("Pressione Enter para continuar...")
    
    # Executar consultas
    bot = BotOABCorrigido(headless=False, timeout=15)
    
    try:
        if not bot.acessar_site():
            print("❌ Falha ao acessar o site")
            return
        
        # Executar todas as consultas
        resultados = bot.consultar_multiplas(consultas)
        
        # Mostrar resumo
        sucessos = sum(1 for r in resultados if r.sucesso)
        erros = len(resultados) - sucessos
        
        print(f"\n📊 RESUMO DA PESQUISA:")
        print(f"{'='*50}")
        print(f"Total de consultas: {len(resultados)}")
        print(f"✅ Sucessos: {sucessos}")
        print(f"❌ Erros: {erros}")
        
        # ✅ Salvar resultados automaticamente (já feito pelo bot.consultar_multiplas)
        print(f"\n💾 Salvando todos os resultados...")
        arquivos = bot.data_exporter.salvar_todos_formatos(resultados)
        print(f"📁 Pasta: {bot.data_exporter.obter_pasta_atual()}")
        print(f"✅ Todos os arquivos salvos com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        
    finally:
        bot.fechar()

def ver_pesquisas_anteriores():
    """Mostra as pesquisas anteriores"""
    print("🤖 Bot OAB - Pesquisas Anteriores")
    print("=" * 40)
    
    # Criar instância do exportador apenas para listar
    from bot_oab.utils.data_exporters import DataExporter
    exporter = DataExporter()
    
    # Listar pesquisas
    pesquisas = exporter.listar_pesquisas_anteriores()
    
    if not pesquisas:
        print("📁 Nenhuma pesquisa anterior encontrada.")
        return
    
    # Perguntar se quer ver detalhes de alguma
    escolha = input(f"\nDeseja ver detalhes de alguma pesquisa? (1-{min(10, len(pesquisas))} ou 'n'): ").strip()
    
    if escolha.lower() == 'n':
        return
    
    try:
        indice = int(escolha) - 1
        if 0 <= indice < min(10, len(pesquisas)):
            pasta_escolhida = pesquisas[indice]
            caminho_pasta = os.path.join("Pesquisa", pasta_escolhida)
            
            print(f"\n📂 Detalhes da pesquisa: {pasta_escolhida}")
            print(f"{'='*50}")
            
            arquivos = os.listdir(caminho_pasta)
            for arquivo in sorted(arquivos):
                tamanho = os.path.getsize(os.path.join(caminho_pasta, arquivo))
                print(f"📄 {arquivo} ({tamanho} bytes)")
            
            print(f"\n📁 Caminho completo: {caminho_pasta}")
        else:
            print("❌ Número inválido!")
            
    except ValueError:
        print("❌ Digite um número válido!")

if __name__ == "__main__":
    print("🚀 Iniciando Bot OAB...")
    
    # Menu de opções expandido
    opcao = input("""
Escolha uma opção:
1 - Consulta de exemplo (OAB 147520/SP)
2 - Consulta interativa (você digita os dados)
3 - Consulta múltipla (várias consultas em lote)
4 - Ver pesquisas anteriores
5 - Sair

Digite sua opção (1-5): """).strip()
    
    if opcao == "1":
        main()
    elif opcao == "2":
        consulta_interativa()
    elif opcao == "3":
        consulta_multipla()
    elif opcao == "4":
        ver_pesquisas_anteriores()
    elif opcao == "5":
        print("👋 Até logo!")
    else:
        print("❌ Opção inválida! Executando exemplo...")
        main()