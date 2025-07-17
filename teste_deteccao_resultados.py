#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste e Diagnóstico - Detecção de Resultados OAB
Identifica e corrige problemas onde resultados existentes não são detectados
"""

import os
import sys
import time
from datetime import datetime

# Adicionar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bot_oab_core_corrigido import BotOABCorrigido
    print("✅ Usando BotOABCorrigido")
except ImportError:
    from bot_oab.core.bot_oab_core import BotOABCorrigido
    print("⚠️ Usando BotOABCorrigido padrão (fallback)")

def testar_oabs_conhecidas():
    """Testa OABs que sabemos que existem"""
    
    # Lista de OABs para testar (que você verificou manualmente)
    oabs_teste = [
        ("147520", "SP"),  # OAB comum de teste
        ("123456", "RJ"),  # Substitua por uma OAB que você verificou
        ("234567", "MG"),  # Substitua por uma OAB que você verificou
        ("345678", "PR"),  # Substitua por uma OAB que você verificou
    ]
    
    print("🧪 TESTE DE DETECÇÃO DE RESULTADOS")
    print("=" * 60)
    print(f"📅 Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🔍 Testando {len(oabs_teste)} OABs conhecidas...")
    
    bot = BotOABCorrigido(headless=False, timeout=20)  # Interface visível para debug
    
    try:
        # Verificar conectividade
        if not bot.acessar_site():
            print("❌ Falha ao acessar site - abortando testes")
            return
        
        # Teste de conectividade
        print(f"\n🔗 TESTE DE CONECTIVIDADE")
        print("-" * 40)
        if bot.verificar_conectividade_site():
            print("✅ Site está funcionando corretamente")
        else:
            print("❌ Problemas de conectividade detectados")
            return
        
        # Teste com consulta conhecida
        print(f"\n🧪 TESTE DE CONSULTA CONHECIDA")
        print("-" * 40)
        if not bot.teste_consulta_conhecida():
            print("❌ Teste básico falhou - investigando...")
            return
        
        # Testes individuais
        resultados_teste = []
        
        for i, (inscricao, estado) in enumerate(oabs_teste, 1):
            print(f"\n{'='*60}")
            print(f"🔍 TESTE {i}/{len(oabs_teste)}: OAB {inscricao}/{estado}")
            print("-" * 60)
            
            try:
                # Executar consulta
                resultado = bot.consultar_inscricao(inscricao, estado)
                resultados_teste.append(resultado)
                
                # Análise do resultado
                if resultado.sucesso:
                    print(f"✅ SUCESSO: {resultado.nome}")
                    print(f"   🏷️ Tipo: {resultado.tipo}")
                    if resultado.situacao:
                        print(f"   📊 Situação: {resultado.situacao}")
                    if resultado.telefone:
                        print(f"   📞 Telefone: {resultado.telefone}")
                    if resultado.endereco:
                        print(f"   📍 Endereço: {resultado.endereco}")
                else:
                    print(f"❌ FALHA: {resultado.erro}")
                    
                    # Fazer diagnóstico detalhado
                    print(f"\n🔍 DIAGNÓSTICO DETALHADO:")
                    diagnostico = bot.diagnosticar_problema_consulta(inscricao, estado)
                    
                    # Sugestões baseadas no diagnóstico
                    if not diagnostico.get('resultado_encontrado', False):
                        print(f"\n💡 POSSÍVEIS CAUSAS:")
                        print(f"   • OAB pode realmente não existir")
                        print(f"   • Site pode estar com problemas temporários")
                        print(f"   • Formato da OAB pode estar incorreto")
                        print(f"   • Sistema de detecção precisa ser aprimorado")
                
                # Pausa entre testes
                if i < len(oabs_teste):
                    print(f"\n⏳ Aguardando 5 segundos antes do próximo teste...")
                    time.sleep(5)
                
            except Exception as e:
                print(f"❌ Erro inesperado no teste {i}: {e}")
                continue
        
        # Relatório final
        print(f"\n📊 RELATÓRIO FINAL DOS TESTES")
        print("=" * 60)
        
        sucessos = sum(1 for r in resultados_teste if r.sucesso)
        total = len(resultados_teste)
        taxa_sucesso = (sucessos / total * 100) if total > 0 else 0
        
        print(f"Total de testes: {total}")
        print(f"✅ Sucessos: {sucessos}")
        print(f"❌ Falhas: {total - sucessos}")
        print(f"📈 Taxa de sucesso: {taxa_sucesso:.1f}%")
        
        # Análise das falhas
        falhas = [r for r in resultados_teste if not r.sucesso]
        if falhas:
            print(f"\n⚠️ ANÁLISE DAS FALHAS:")
            for falha in falhas:
                print(f"   • {falha.inscricao}/{falha.estado}: {falha.erro}")
        
        # Salvar resultados
        if resultados_teste:
            bot.salvar_todos_formatos(resultados_teste)
            print(f"\n💾 Resultados salvos para análise")
        
        # Recomendações
        print(f"\n💡 RECOMENDAÇÕES:")
        if taxa_sucesso >= 80:
            print(f"   ✅ Sistema funcionando bem ({taxa_sucesso:.1f}% de sucesso)")
        elif taxa_sucesso >= 50:
            print(f"   ⚠️ Sistema com problemas moderados ({taxa_sucesso:.1f}% de sucesso)")
            print(f"   • Verificar se OABs de teste realmente existem")
            print(f"   • Aumentar timeouts se necessário")
            print(f"   • Verificar estabilidade da conexão")
        else:
            print(f"   ❌ Sistema com problemas graves ({taxa_sucesso:.1f}% de sucesso)")
            print(f"   • Verificar se site da OAB está funcionando")
            print(f"   • Verificar seletores CSS/XPath")
            print(f"   • Considerar atualizar sistema de detecção")
    
    except KeyboardInterrupt:
        print(f"\n⏹️ Testes interrompidos pelo usuário")
    
    except Exception as e:
        print(f"❌ Erro inesperado nos testes: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        bot.fechar()
        print(f"\n🔒 Testes finalizados")

def testar_oab_especifica():
    """Testa uma OAB específica com diagnóstico completo"""
    
    print("🔍 TESTE DE OAB ESPECÍFICA")
    print("=" * 40)
    
    # Solicitar dados do usuário
    inscricao = input("Digite o número da inscrição OAB: ").strip()
    estado = input("Digite a sigla do estado (SP, RJ, etc.): ").strip().upper()
    
    if not inscricao or not estado:
        print("❌ Inscrição e estado são obrigatórios!")
        return
    
    print(f"\n🔍 Testando OAB {inscricao}/{estado} com diagnóstico completo...")
    
    bot = BotOABCorrigido(headless=False, timeout=20)
    
    try:
        if not bot.acessar_site():
            print("❌ Falha ao acessar site")
            return
        
        # Fazer diagnóstico completo
        print(f"\n🔧 EXECUTANDO DIAGNÓSTICO COMPLETO...")
        diagnostico = bot.diagnosticar_problema_consulta(inscricao, estado)
        
        # Tentar consulta normal
        print(f"\n🔍 EXECUTANDO CONSULTA NORMAL...")
        resultado = bot.consultar_inscricao(inscricao, estado)
        
        # Resultados
        print(f"\n📊 RESULTADO DA CONSULTA:")
        if resultado.sucesso:
            print(f"✅ SUCESSO: {resultado.nome}")
            print(f"   🏷️ Tipo: {resultado.tipo}")
            if resultado.situacao:
                print(f"   📊 Situação: {resultado.situacao}")
            if resultado.telefone:
                print(f"   📞 Telefone: {resultado.telefone}")
            if resultado.endereco:
                print(f"   📍 Endereço: {resultado.endereco}")
            if resultado.email:
                print(f"   📧 Email: {resultado.email}")
        else:
            print(f"❌ FALHA: {resultado.erro}")
        
        # Comparar com verificação manual
        print(f"\n❓ VERIFICAÇÃO MANUAL:")
        resposta = input(f"Você consegue ver dados desta OAB manualmente no site? (s/n): ").strip().lower()
        
        if resposta in ['s', 'sim', 'y', 'yes']:
            if not resultado.sucesso:
                print(f"⚠️ PROBLEMA IDENTIFICADO: Bot não detectou resultado que existe manualmente")
                print(f"💡 Isso indica problema no sistema de detecção")
                
                # Solicitar dados manuais para comparação
                print(f"\nPor favor, digite os dados que você vê manualmente:")
                nome_manual = input("Nome do advogado: ").strip()
                tipo_manual = input("Tipo (Advogado/Advogada): ").strip()
                
                print(f"\n📋 DADOS MANUAIS INFORMADOS:")
                print(f"   Nome: {nome_manual}")
                print(f"   Tipo: {tipo_manual}")
                
                print(f"\n🔧 RECOMENDAÇÕES PARA CORREÇÃO:")
                print(f"   • Verificar seletores CSS/XPath usados para detectar resultados")
                print(f"   • Aumentar tempo de espera após pesquisa")
                print(f"   • Verificar se resultado aparece em modal ou iframe")
                print(f"   • Analisar HTML da página salvo para debug")
                print(f"   • Considerar usar OCR se resultado for imagem")
            else:
                print(f"✅ SISTEMA FUNCIONANDO: Bot detectou resultado corretamente")
        else:
            if resultado.sucesso:
                print(f"⚠️ FALSO POSITIVO: Bot detectou resultado que não existe")
                print(f"💡 Isso indica problema na validação de dados")
            else:
                print(f"✅ RESULTADO CORRETO: OAB realmente não existe")
        
        # Salvar resultado para análise
        bot.salvar_todos_formatos([resultado])
        print(f"\n💾 Resultado salvo para análise")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        bot.fechar()

def analisar_pagina_resultado():
    """Analisa a estrutura da página de resultado para melhorar detecção"""
    
    print("🔍 ANÁLISE DA ESTRUTURA DA PÁGINA")
    print("=" * 50)
    
    inscricao = input("Digite uma OAB que você sabe que existe: ").strip()
    estado = input("Estado: ").strip().upper()
    
    if not inscricao or not estado:
        print("❌ Dados obrigatórios!")
        return
    
    bot = BotOABCorrigido(headless=False, timeout=20)
    
    try:
        if not bot.acessar_site():
            print("❌ Falha ao acessar site")
            return
        
        # Executar consulta
        print(f"🔍 Executando consulta {inscricao}/{estado}...")
        
        # Preencher campos manualmente para análise
        from selenium.webdriver.support.ui import Select
        
        campo_inscricao = bot.driver.find_element(By.ID, "txtInsc")
        campo_inscricao.clear()
        campo_inscricao.send_keys(inscricao)
        
        dropdown_estado = Select(bot.driver.find_element(By.ID, "cmbSeccional"))
        dropdown_estado.select_by_value(estado)
        
        botao_pesquisa = bot.driver.find_element(By.ID, "btnFind")
        botao_pesquisa.click()
        
        # Aguardar resultado
        time.sleep(5)
        
        print(f"📄 Analisando estrutura da página...")
        
        # Salvar página completa
        pasta_debug = bot.data_exporter.obter_pasta_atual()
        
        # HTML completo
        html_file = f"{pasta_debug}/analise_pagina_{inscricao}_{estado}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(bot.driver.page_source)
        print(f"📄 HTML salvo: {html_file}")
        
        # Screenshot
        screenshot_file = f"{pasta_debug}/analise_screenshot_{inscricao}_{estado}.png"
        bot.driver.save_screenshot(screenshot_file)
        print(f"📸 Screenshot salvo: {screenshot_file}")
        
        # Texto visível
        body_text = bot.driver.find_element(By.TAG_NAME, "body").text
        text_file = f"{pasta_debug}/analise_texto_{inscricao}_{estado}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("TEXTO VISÍVEL DA PÁGINA:\n")
            f.write("=" * 50 + "\n")
            f.write(body_text)
        print(f"📝 Texto salvo: {text_file}")
        
        # Analisar elementos
        print(f"\n🔍 ANÁLISE DE ELEMENTOS:")
        
        # Verificar elementos comuns
        seletores_teste = [
            ('.row', 'Elementos .row'),
            ('.container', 'Elementos .container'),
            ('.result', 'Elementos .result'),
            ('[class*="result"]', 'Elementos com "result" na classe'),
            ('div:contains("Nome")', 'Divs contendo "Nome"'),
            ('*:contains("Advogado")', 'Elementos contendo "Advogado"'),
        ]
        
        from selenium.webdriver.common.by import By
        
        for seletor, descricao in seletores_teste:
            try:
                if ':contains(' in seletor:
                    # Converter para XPath
                    if seletor.startswith('div:'):
                        xpath = "//div[contains(text(), 'Nome')]"
                    else:
                        xpath = "//*[contains(text(), 'Advogado')]"
                    elementos = bot.driver.find_elements(By.XPATH, xpath)
                else:
                    elementos = bot.driver.find_elements(By.CSS_SELECTOR, seletor)
                
                print(f"   {descricao}: {len(elementos)} encontrados")
                
                # Mostrar alguns elementos encontrados
                for i, elem in enumerate(elementos[:3]):
                    try:
                        if elem.is_displayed():
                            texto = elem.text.strip()[:100]
                            print(f"      [{i+1}] Visível: {texto}")
                        else:
                            print(f"      [{i+1}] Oculto")
                    except:
                        print(f"      [{i+1}] Erro ao ler")
                        
            except Exception as e:
                print(f"   {descricao}: Erro - {e}")
        
        # Buscar por texto específico
        print(f"\n🔍 BUSCA POR TEXTO ESPECÍFICO:")
        textos_busca = ['nome:', 'inscri', 'tipo:', 'advogad', 'seccional']
        
        for texto in textos_busca:
            if texto.lower() in body_text.lower():
                print(f"   ✅ '{texto}' encontrado na página")
                
                # Encontrar linha específica
                linhas = body_text.split('\n')
                for i, linha in enumerate(linhas):
                    if texto.lower() in linha.lower():
                        print(f"      Linha {i+1}: {linha.strip()[:100]}")
                        break
            else:
                print(f"   ❌ '{texto}' NÃO encontrado")
        
        # Verificar se há modal
        print(f"\n🔍 VERIFICAÇÃO DE MODAL:")
        seletores_modal = [
            '.modal',
            '[class*="modal"]',
            '[id*="modal"]',
            '#imgDetail'
        ]
        
        modal_encontrado = False
        for seletor in seletores_modal:
            try:
                elementos = bot.driver.find_elements(By.CSS_SELECTOR, seletor)
                if elementos:
                    print(f"   Modal encontrado: {seletor} ({len(elementos)} elementos)")
                    modal_encontrado = True
                    
                    # Tentar clicar no primeiro resultado para abrir modal
                    if seletor == '.modal' and not modal_encontrado:
                        # Procurar elemento clicável
                        rows = bot.driver.find_elements(By.CSS_SELECTOR, '.row')
                        for row in rows:
                            if 'nome' in row.text.lower():
                                print(f"   Tentando clicar em resultado para abrir modal...")
                                bot.driver.execute_script("arguments[0].click();", row)
                                time.sleep(3)
                                break
            except:
                continue
        
        if not modal_encontrado:
            print(f"   ❌ Nenhum modal detectado")
        
        print(f"\n💡 PRÓXIMOS PASSOS:")
        print(f"   1. Analise os arquivos salvos em: {pasta_debug}")
        print(f"   2. Identifique os seletores corretos para os dados")
        print(f"   3. Verifique se resultado aparece em modal")
        print(f"   4. Atualize o sistema de detecção com os seletores corretos")
        
        input(f"\nPressione Enter para continuar (deixe a página aberta para análise manual)...")
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        resposta = input(f"Fechar navegador? (s/n): ").strip().lower()
        if resposta in ['s', 'sim', 'y', 'yes']:
            bot.fechar()
        else:
            print(f"Navegador mantido aberto para análise manual")

def menu_principal():
    """Menu principal de testes"""
    
    while True:
        print(f"\n🧪 SISTEMA DE TESTE E DIAGNÓSTICO - DETECÇÃO OAB")
        print("=" * 60)
        print("1. Testar OABs conhecidas (teste automático)")
        print("2. Testar OAB específica (com diagnóstico)")
        print("3. Analisar estrutura da página (para desenvolvedores)")
        print("4. Executar teste rápido de conectividade")
        print("5. Sair")
        print("=" * 60)
        
        try:
            opcao = input("Escolha uma opção (1-5): ").strip()
            
            if opcao == "1":
                testar_oabs_conhecidas()
                
            elif opcao == "2":
                testar_oab_especifica()
                
            elif opcao == "3":
                analisar_pagina_resultado()
                
            elif opcao == "4":
                print(f"\n🔗 Teste rápido de conectividade...")
                bot = BotOABCorrigido(headless=True, timeout=10)
                try:
                    if bot.verificar_conectividade_site():
                        print("✅ Site está funcionando")
                    else:
                        print("❌ Problemas detectados")
                finally:
                    bot.fechar()
                    
            elif opcao == "5":
                print("👋 Encerrando testes...")
                break
                
            else:
                print("❌ Opção inválida! Escolha entre 1-5")
            
            if opcao in ["1", "2", "3"]:
                input(f"\nPressione Enter para continuar...")
                
        except KeyboardInterrupt:
            print(f"\n\n👋 Testes encerrados pelo usuário")
            break
            
        except Exception as e:
            print(f"\n❌ Erro inesperado: {e}")
            input("Pressione Enter para continuar...")

def main():
    """Função principal"""
    print("🚀 Sistema de Teste e Diagnóstico - Bot OAB")
    print("=" * 60)
    print("🎯 Objetivo: Identificar e corrigir problemas de detecção de resultados")
    print("💡 Use este sistema quando resultados existem manualmente mas o bot não detecta")
    print("=" * 60)
    
    try:
        menu_principal()
    except KeyboardInterrupt:
        print(f"\n\n👋 Sistema encerrado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()