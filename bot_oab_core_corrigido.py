#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot OAB Core Standalone - VERSÃO EXECUTÁVEL DIRETA
Corrige problemas onde resultados existentes não eram detectados
"""

import os
import sys
import time
from typing import List

# Adicionar o diretório atual ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# Imports diretos (sem relativos)
try:
    from bot_oab.models.resultado_oab import ResultadoOAB
    from bot_oab.config.browser_config import BrowserConfig
    from bot_oab.utils.data_exporters import DataExporter
    print("✅ Imports do bot_oab funcionando")
except ImportError as e:
    print(f"⚠️ Erro nos imports do bot_oab: {e}")
    print("🔧 Usando implementações inline...")
    
    # Implementações inline caso não encontre os módulos
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
    
    class BrowserConfig:
        @staticmethod
        def setup_driver(headless: bool = False) -> webdriver.Chrome:
            options = Options()
            
            if headless:
                options.add_argument('--headless')
                
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
            }
            options.add_experimental_option("prefs", prefs)
            
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
    
    class DataExporter:
        def __init__(self):
            self.pasta_pesquisas = "Pesquisa"
            self.pasta_atual = None
            
        def obter_pasta_atual(self):
            if self.pasta_atual is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self.pasta_atual = os.path.join(self.pasta_pesquisas, timestamp)
                
                if not os.path.exists(self.pasta_atual):
                    os.makedirs(self.pasta_atual, exist_ok=True)
            
            return self.pasta_atual
        
        def salvar_json(self, resultados):
            pass  # Implementação simplificada
        
        def salvar_todos_formatos(self, resultados):
            pass  # Implementação simplificada

# Implementação do extrator melhorado inline
class DataExtractorMelhorado:
    """Extrator de dados com detecção melhorada"""
    
    def __init__(self, driver, wait, pasta_debug=None):
        self.driver = driver
        self.wait = wait
        self.pasta_debug = pasta_debug
        
        print("🔧 DataExtractor melhorado inicializado")

    def extrair_resultado(self, resultado: ResultadoOAB) -> ResultadoOAB:
        """Extrai dados com detecção melhorada"""
        try:
            print(f"🔍 Extraindo resultado para OAB {resultado.inscricao}/{resultado.estado}")
            
            # Aguardar página estabilizar
            time.sleep(4)
            
            # Estratégia 1: Verificar se há mensagem de erro
            if self._verificar_mensagem_erro():
                resultado.erro = "Inscrição não encontrada"
                print("⚠️ Mensagem de erro detectada na página")
                return resultado
            
            # Estratégia 2: Buscar resultado usando múltiplos seletores
            elemento_resultado = self._buscar_elemento_resultado()
            
            if elemento_resultado:
                print("✅ Elemento de resultado encontrado!")
                resultado = self._extrair_dados_basicos_melhorado(elemento_resultado, resultado)
                resultado.sucesso = True
                print(f"✅ Extração concluída: {resultado.nome}")
            else:
                # Estratégia 3: Analisar página completa
                print("🔍 Elemento específico não encontrado, analisando página completa...")
                
                if self._extrair_dados_pagina_completa(resultado):
                    resultado.sucesso = True
                    print(f"✅ Dados encontrados na página: {resultado.nome}")
                else:
                    resultado.erro = "Nenhum resultado encontrado na página"
                    print("❌ Nenhum dado encontrado na página")
                    
                    # Debug: Salvar página para análise
                    self._salvar_debug_pagina(resultado)
            
        except Exception as e:
            resultado.erro = f"Erro ao extrair resultado: {str(e)}"
            print(f"❌ Erro na extração: {str(e)}")
            self._salvar_debug_pagina(resultado)
            
        return resultado
    
    def _verificar_mensagem_erro(self) -> bool:
        """Verifica se há mensagens de erro na página"""
        try:
            textos_erro = [
                'não encontrado', 'nenhum resultado', 'não foi possível',
                'não localizado', 'não existe', 'inválida', 'erro'
            ]
            
            page_text = self.driver.page_source.lower()
            
            for texto in textos_erro:
                if texto in page_text:
                    print(f"🚫 Erro detectado: '{texto}' encontrado na página")
                    return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Erro ao verificar mensagens de erro: {e}")
            return False
    
    def _buscar_elemento_resultado(self):
        """Busca elemento de resultado usando múltiplas estratégias"""
        try:
            print("🔍 Buscando elemento de resultado...")
            
            # Lista de seletores para tentar
            seletores_resultado = [
                '.row:not(:empty)',
                '.container-fluid .row',
                '.panel-body',
                '.card-body',
                'div:contains("Nome:")',
                'div:contains("Inscrição:")',
                '*:contains("Nome:")'
            ]
            
            # Tentar cada seletor
            for i, seletor in enumerate(seletores_resultado):
                try:
                    print(f"   Tentativa {i+1}: {seletor}")
                    
                    if ':contains(' in seletor:
                        # Usar XPath para seletores com :contains
                        xpath = "//div[contains(text(), 'Nome:')]"
                        elementos = self.driver.find_elements(By.XPATH, xpath)
                    else:
                        elementos = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                    
                    # Filtrar elementos visíveis e com conteúdo relevante
                    for elemento in elementos:
                        if self._elemento_parece_resultado(elemento):
                            print(f"✅ Elemento encontrado com: {seletor}")
                            return elemento
                            
                except Exception as e:
                    print(f"   ❌ Erro com seletor {seletor}: {str(e)[:50]}...")
                    continue
            
            # Buscar por texto específico usando XPath
            print("🔍 Buscando por texto específico...")
            xpaths_busca = [
                "//div[contains(text(), 'Nome:')]",
                "//span[contains(text(), 'Nome:')]",
                "//*[contains(text(), 'Nome:')]",
                "//div[contains(text(), 'Inscrição:')]",
                "//*[contains(text(), 'Inscrição:')]"
            ]
            
            for xpath in xpaths_busca:
                try:
                    elementos = self.driver.find_elements(By.XPATH, xpath)
                    for elemento in elementos:
                        if self._elemento_parece_resultado(elemento):
                            print(f"✅ Encontrado por XPath: {xpath}")
                            return elemento
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ Erro ao buscar elemento de resultado: {e}")
            return None
    
    def _elemento_parece_resultado(self, elemento) -> bool:
        """Verifica se um elemento parece conter resultado de advogado"""
        try:
            if not elemento.is_displayed():
                return False
            
            texto = elemento.text.strip()
            
            if len(texto) < 10:
                return False
            
            # Palavras-chave que indicam resultado
            palavras_chave = [
                'nome:', 'inscri', 'tipo:', 'advogad', 'oab',
                'seccional', 'situação', 'regular', 'ativo'
            ]
            
            texto_lower = texto.lower()
            palavras_encontradas = sum(1 for palavra in palavras_chave if palavra in texto_lower)
            
            if palavras_encontradas >= 2:
                print(f"   ✅ Elemento válido: {palavras_encontradas} palavras-chave")
                return True
            
            return False
            
        except Exception as e:
            print(f"   ⚠️ Erro ao verificar elemento: {e}")
            return False
    
    def _extrair_dados_pagina_completa(self, resultado: ResultadoOAB) -> bool:
        """Extrai dados analisando toda a página"""
        try:
            print("🔍 Analisando página completa...")
            
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            print(f"📄 Texto da página: {len(body_text)} caracteres")
            
            # Buscar padrões de dados
            dados_encontrados = False
            
            # Buscar nome
            nome = self._extrair_nome_do_texto(body_text)
            if nome:
                resultado.nome = nome
                dados_encontrados = True
                print(f"📝 Nome encontrado: {nome}")
            
            # Buscar tipo
            tipo = self._extrair_tipo_do_texto(body_text)
            if tipo:
                resultado.tipo = tipo
                dados_encontrados = True
                print(f"🏷️ Tipo encontrado: {tipo}")
            
            return dados_encontrados
            
        except Exception as e:
            print(f"❌ Erro ao analisar página completa: {e}")
            return False
    
    def _extrair_nome_do_texto(self, texto: str) -> str:
        """Extrai nome do texto da página"""
        import re
        
        padroes_nome = [
            r'Nome[:\s]*([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ][A-Za-záéíóúàèìòùâêîôûãõçñ\s]{8,80})',
            r'NOME[:\s]*([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ][A-Za-záéíóúàèìòùâêîôûãõçñ\s]{8,80})',
            r'^([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ]{2,}(?:\s+[A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ]{2,})+)',
        ]
        
        linhas = texto.split('\n')
        
        for padrao in padroes_nome:
            for linha in linhas[:10]:  # Primeiras 10 linhas
                linha = linha.strip()
                match = re.search(padrao, linha, re.MULTILINE)
                if match:
                    nome = match.group(1).strip()
                    if self._validar_nome(nome):
                        return nome
        
        return ""
    
    def _extrair_tipo_do_texto(self, texto: str) -> str:
        """Extrai tipo do texto da página"""
        import re
        
        padroes_tipo = [
            r'Tipo[:\s]*([A-Za-z\s]{5,30})',
            r'TIPO[:\s]*([A-Za-z\s]{5,30})',
            r'(ADVOGADO|ADVOGADA)',
        ]
        
        for padrao in padroes_tipo:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                tipo = match.group(1).strip()
                if len(tipo) > 3:
                    return tipo
        
        return ""
    
    def _validar_nome(self, nome: str) -> bool:
        """Valida se é um nome válido"""
        if not nome or len(nome) < 5 or len(nome) > 100:
            return False
        
        if ' ' not in nome:
            return False
        
        palavras_invalidas = ['INSCRICAO', 'SECCIONAL', 'TELEFONE', 'ENDERECO']
        if any(palavra in nome.upper() for palavra in palavras_invalidas):
            return False
        
        return True
    
    def _extrair_dados_basicos_melhorado(self, elemento, resultado: ResultadoOAB) -> ResultadoOAB:
        """Extrai dados básicos do elemento"""
        try:
            import re
            
            texto_completo = elemento.text
            print(f"📋 Texto do elemento: {texto_completo[:200]}...")
            
            # Buscar nome
            nome_patterns = [
                r'Nome[:\s]*(.+?)(?:\n|Tipo:|Inscri|$)',
                r'NOME[:\s]*(.+?)(?:\n|TIPO:|INSCRI|$)',
                r'\n([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ][A-Za-záéíóúàèìòùâêîôûãõçñ\s]{8,80})\n',
            ]
            
            for pattern in nome_patterns:
                match = re.search(pattern, texto_completo)
                if match:
                    nome = match.group(1).strip()
                    if self._validar_nome(nome):
                        resultado.nome = nome
                        break
            
            # Buscar tipo
            tipo_patterns = [
                r'Tipo[:\s]*(.+?)(?:\n|Inscri|$)',
                r'TIPO[:\s]*(.+?)(?:\n|INSCRI|$)',
            ]
            
            for pattern in tipo_patterns:
                match = re.search(pattern, texto_completo)
                if match:
                    tipo = match.group(1).strip()
                    if len(tipo) > 3 and len(tipo) < 50:
                        resultado.tipo = tipo
                        break
            
            print(f"📋 Dados extraídos: {resultado.nome} - {resultado.tipo}")
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair dados básicos: {e}")
            
        return resultado
    
    def _salvar_debug_pagina(self, resultado: ResultadoOAB):
        """Salva debug da página para análise"""
        try:
            if not self.pasta_debug:
                self.pasta_debug = "debug"
            
            if not os.path.exists(self.pasta_debug):
                os.makedirs(self.pasta_debug, exist_ok=True)
            
            # Screenshot
            screenshot_path = os.path.join(
                self.pasta_debug,
                f"debug_pagina_{resultado.inscricao}_{resultado.estado}.png"
            )
            self.driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot salvo: {os.path.basename(screenshot_path)}")
            
            # HTML da página
            html_path = os.path.join(
                self.pasta_debug,
                f"debug_pagina_{resultado.inscricao}_{resultado.estado}.html"
            )
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print(f"📄 HTML salvo: {os.path.basename(html_path)}")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar debug: {e}")


class BotOABCorrigidoStandalone:
    """Bot OAB com detecção melhorada - Versão Standalone"""
    
    def __init__(self, headless: bool = False, timeout: int = 15):
        """Inicializa o bot"""
        self.timeout = timeout
        self.driver = BrowserConfig.setup_driver(headless)
        self.wait = WebDriverWait(self.driver, timeout)
        self.data_exporter = DataExporter()
        
        # Usar extrator melhorado
        pasta_atual = self.data_exporter.obter_pasta_atual()
        self.data_extractor = DataExtractorMelhorado(self.driver, self.wait, pasta_atual)
        
        print(f"🤖 Bot OAB Standalone v2.1 - DETECÇÃO MELHORADA")
        print(f"📁 Debug será salvo em: {pasta_atual}")
        
    def acessar_site(self) -> bool:
        """Acessa o site da OAB"""
        try:
            print("🌐 Acessando site da OAB...")
            self.driver.get("https://cna.oab.org.br/")
            
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Verificar elementos principais
            try:
                campo_inscricao = self.wait.until(
                    EC.presence_of_element_located((By.ID, "txtInsc"))
                )
                dropdown_estado = self.driver.find_element(By.ID, "cmbSeccional")
                botao_pesquisa = self.driver.find_element(By.ID, "btnFind")
                
                print("✅ Site carregado e elementos principais encontrados!")
                return True
                
            except TimeoutException:
                print("⚠️ Elementos principais não encontrados, mas site carregou")
                return True
            
        except Exception as e:
            print(f"❌ Erro ao acessar site: {str(e)}")
            return False
    
    def consultar_inscricao(self, inscricao: str, estado: str) -> ResultadoOAB:
        """Consulta com detecção melhorada"""
        resultado = ResultadoOAB(inscricao=inscricao, estado=estado)
        
        try:
            print(f"🔍 Consultando OAB {inscricao}/{estado} com detecção melhorada...")
            
            # 1. Limpar campos anteriores
            self._limpar_campos_anteriores()
            
            # 2. Preencher campo de inscrição
            print("📝 Preenchendo número da inscrição...")
            campo_inscricao = self.wait.until(
                EC.element_to_be_clickable((By.ID, "txtInsc"))
            )
            
            campo_inscricao.clear()
            time.sleep(0.5)
            campo_inscricao.send_keys(inscricao)
            print(f"✅ Número {inscricao} inserido")
            
            # 3. Selecionar estado
            print("🗺️ Selecionando estado...")
            dropdown_estado = Select(self.driver.find_element(By.ID, "cmbSeccional"))
            dropdown_estado.select_by_value(estado.upper())
            print(f"✅ Estado {estado} selecionado")
            
            # 4. Aguardar um momento
            time.sleep(1)
            
            # 5. Clicar no botão de pesquisa
            print("🔍 Executando pesquisa...")
            botao_pesquisa = self.driver.find_element(By.ID, "btnFind")
            botao_pesquisa.click()
            print("✅ Pesquisa executada")
            
            # 6. Aguardar resultado
            print("⏳ Aguardando resultado...")
            time.sleep(5)  # Aguardar mais tempo
            
            # 7. Extrair resultado
            print("🔧 Iniciando extração com sistema melhorado...")
            resultado = self.data_extractor.extrair_resultado(resultado)
            
            # 8. Log do resultado
            if resultado.sucesso:
                print(f"✅ SUCESSO: {resultado.nome}")
                if resultado.tipo:
                    print(f"   🏷️ Tipo: {resultado.tipo}")
            else:
                print(f"❌ ERRO: {resultado.erro}")
            
            return resultado
            
        except Exception as e:
            resultado.erro = f"Erro inesperado: {str(e)}"
            print(f"❌ Erro na consulta {inscricao}/{estado}: {str(e)}")
            
        return resultado
    
    def _limpar_campos_anteriores(self):
        """Limpa campos de consulta anterior"""
        try:
            campo_inscricao = self.driver.find_element(By.ID, "txtInsc")
            campo_inscricao.clear()
            
            try:
                dropdown_estado = Select(self.driver.find_element(By.ID, "cmbSeccional"))
                dropdown_estado.select_by_index(0)
            except:
                pass
                
            print("🧹 Campos anteriores limpos")
            
        except Exception as e:
            print(f"⚠️ Erro ao limpar campos: {e}")
    
    def teste_consulta_conhecida(self) -> bool:
        """Testa com uma consulta conhecida"""
        try:
            print("🧪 Executando teste com consulta conhecida...")
            
            resultado_teste = self.consultar_inscricao("147520", "SP")
            
            if resultado_teste.sucesso:
                print(f"✅ Teste PASSOU: {resultado_teste.nome}")
                return True
            else:
                print(f"❌ Teste FALHOU: {resultado_teste.erro}")
                return False
                
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
            return False
    
    def fechar(self):
        """Fecha o navegador"""
        if self.driver:
            self.driver.quit()
            print("🔒 Navegador fechado")


def main():
    """Função principal para testar o bot"""
    print("🚀 Bot OAB Standalone - Teste de Detecção Melhorada")
    print("=" * 60)
    
    # Solicitar dados do usuário
    inscricao = input("Digite o número da inscrição OAB: ").strip()
    estado = input("Digite a sigla do estado (SP, RJ, etc.): ").strip().upper()
    
    if not inscricao or not estado:
        print("❌ Inscrição e estado são obrigatórios!")
        return
    
    # Criar bot
    bot = BotOABCorrigidoStandalone(headless=False, timeout=20)  # Interface visível
    
    try:
        # Acessar site
        if not bot.acessar_site():
            print("❌ Falha ao acessar site")
            return
        
        # Executar consulta
        resultado = bot.consultar_inscricao(inscricao, estado)
        
        # Exibir resultado detalhado
        print(f"\n📊 RESULTADO DA CONSULTA:")
        print(f"{'='*60}")
        print(f"📝 Inscrição: {resultado.inscricao}/{resultado.estado}")
        print(f"👤 Nome: {resultado.nome}")
        print(f"🏷️ Tipo: {resultado.tipo}")
        print(f"✅ Sucesso: {resultado.sucesso}")
        
        if resultado.erro:
            print(f"❌ Erro: {resultado.erro}")
        
        # Comparar com verificação manual
        print(f"\n❓ VERIFICAÇÃO MANUAL:")
        resposta = input(f"Você consegue ver dados desta OAB manualmente no site? (s/n): ").strip().lower()
        
        if resposta in ['s', 'sim', 'y', 'yes']:
            if not resultado.sucesso:
                print(f"⚠️ PROBLEMA IDENTIFICADO: Bot não detectou resultado que existe manualmente")
                print(f"💡 Verifique os arquivos de debug salvos para análise")
                print(f"📁 Pasta de debug: {bot.data_extractor.pasta_debug}")
            else:
                print(f"✅ SISTEMA FUNCIONANDO: Bot detectou resultado corretamente")
        else:
            if resultado.sucesso:
                print(f"⚠️ FALSO POSITIVO: Bot detectou resultado que não existe")
            else:
                print(f"✅ RESULTADO CORRETO: OAB realmente não existe")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Teste interrompido pelo usuário")
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        bot.fechar()


if __name__ == "__main__":
    main()