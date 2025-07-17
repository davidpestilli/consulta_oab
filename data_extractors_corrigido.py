#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Extractors Corrigido - VERSÃO COM DETECÇÃO MELHORADA DE RESULTADOS
Corrige problemas de detecção de resultados que existem mas não são encontrados
"""

import os
import re
import time
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from io import BytesIO
from ..models.resultado_oab import ResultadoOAB

class DataExtractorCorrigido:
    """Classe responsável pela extração de dados das páginas - VERSÃO CORRIGIDA"""
    
    def __init__(self, driver, wait, pasta_debug=None):
        self.driver = driver
        self.wait = wait
        self.pasta_debug = pasta_debug
        
        # Configurar Tesseract OCR
        self._configurar_tesseract()
        
        print("🔧 DataExtractor inicializado com detecção melhorada")

    def _configurar_tesseract(self):
        """Configura o Tesseract OCR"""
        try:
            configs_tesseract = [
                "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",  # Windows
                "/usr/bin/tesseract",  # Linux
                "/opt/homebrew/bin/tesseract",  # macOS
                "tesseract"  # PATH do sistema
            ]
            
            for config in configs_tesseract:
                try:
                    pytesseract.pytesseract.tesseract_cmd = config
                    pytesseract.get_tesseract_version()
                    print(f"✅ Tesseract configurado: {config}")
                    
                    try:
                        idiomas = pytesseract.get_languages()
                        if 'por' in idiomas:
                            self.idioma_ocr = 'por'
                            print("🇧🇷 ✅ Usando idioma PORTUGUÊS")
                        else:
                            self.idioma_ocr = 'eng'
                            print("🇺🇸 ⚠️ Usando idioma inglês")
                    except:
                        self.idioma_ocr = 'eng'
                    
                    return True
                except:
                    continue
            
            print("❌ Tesseract não encontrado!")
            return False
                
        except Exception as e:
            print(f"⚠️ Erro ao configurar Tesseract: {e}")
            self.idioma_ocr = 'eng'
            return False

    def definir_pasta_debug(self, pasta_debug: str):
        """Define a pasta onde salvar arquivos de debug"""
        self.pasta_debug = pasta_debug
    
    def extrair_resultado(self, resultado: ResultadoOAB) -> ResultadoOAB:
        """
        🔧 VERSÃO CORRIGIDA - Extrai dados do resultado da consulta
        Múltiplas estratégias para encontrar resultados
        
        Args:
            resultado: Objeto ResultadoOAB para preencher
            
        Returns:
            ResultadoOAB atualizado com dados extraídos
        """
        try:
            print(f"🔍 Extraindo resultado para OAB {resultado.inscricao}/{resultado.estado}")
            
            # Aguardar página estabilizar
            time.sleep(3)
            
            # 🔧 ESTRATÉGIA 1: Verificar se há mensagem de erro primeiro
            if self._verificar_mensagem_erro():
                resultado.erro = "Inscrição não encontrada"
                print("⚠️ Mensagem de erro detectada na página")
                return resultado
            
            # 🔧 ESTRATÉGIA 2: Buscar resultado usando múltiplos seletores
            elemento_resultado = self._buscar_elemento_resultado()
            
            if elemento_resultado:
                print("✅ Elemento de resultado encontrado!")
                
                # Extrair dados básicos
                resultado = self._extrair_dados_basicos_melhorado(elemento_resultado, resultado)
                
                # 🔧 ESTRATÉGIA 3: Tentar abrir modal de detalhes
                if self._tentar_abrir_detalhes(elemento_resultado):
                    print("🖼️ Modal de detalhes aberto - aplicando OCR...")
                    resultado = self._extrair_dados_modal_ocr(resultado)
                    self._fechar_modal()
                else:
                    print("⚠️ Não conseguiu abrir modal, usando dados básicos")
                
                resultado.sucesso = True
                print(f"✅ Extração concluída: {resultado.nome}")
                
            else:
                # 🔧 ESTRATÉGIA 4: Buscar dados em toda a página
                print("🔍 Elemento específico não encontrado, analisando página completa...")
                
                if self._extrair_dados_pagina_completa(resultado):
                    resultado.sucesso = True
                    print(f"✅ Dados encontrados na página: {resultado.nome}")
                else:
                    resultado.erro = "Nenhum resultado encontrado na página"
                    print("❌ Nenhum dado encontrado na página")
                    
                    # 🔧 DEBUG: Salvar screenshot e HTML para análise
                    self._salvar_debug_pagina(resultado)
            
        except Exception as e:
            resultado.erro = f"Erro ao extrair resultado: {str(e)}"
            print(f"❌ Erro na extração: {str(e)}")
            self._salvar_debug_pagina(resultado)
            
        return resultado
    
    def _verificar_mensagem_erro(self) -> bool:
        """
        🔧 NOVO: Verifica se há mensagens de erro na página
        
        Returns:
            True se encontrou mensagem de erro
        """
        try:
            # Textos que indicam erro
            textos_erro = [
                'não encontrado',
                'nenhum resultado',
                'não foi possível',
                'não localizado',
                'não existe',
                'inválida',
                'erro',
                'without results',
                'no results'
            ]
            
            # Verificar no texto da página
            page_text = self.driver.page_source.lower()
            
            for texto in textos_erro:
                if texto in page_text:
                    print(f"🚫 Erro detectado: '{texto}' encontrado na página")
                    return True
            
            # Verificar elementos específicos de erro
            seletores_erro = [
                '.alert-danger',
                '.error',
                '.warning',
                '.no-results',
                '[class*="error"]',
                '[class*="warning"]'
            ]
            
            for seletor in seletores_erro:
                try:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                    if elementos and any(elem.is_displayed() for elem in elementos):
                        print(f"🚫 Elemento de erro encontrado: {seletor}")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"⚠️ Erro ao verificar mensagens de erro: {e}")
            return False
    
    def _buscar_elemento_resultado(self):
        """
        🔧 VERSÃO MELHORADA: Busca elemento de resultado usando múltiplas estratégias
        
        Returns:
            Elemento encontrado ou None
        """
        try:
            print("🔍 Buscando elemento de resultado...")
            
            # Lista de seletores para tentar (do mais específico ao mais genérico)
            seletores_resultado = [
                # Seletores específicos da OAB
                '.row:has([class*="result"])',
                '.result-item',
                '.search-result',
                '.lawyer-info',
                '.advogado-info',
                
                # Seletores genéricos que podem conter dados
                '.row:contains("Nome:")',
                '.row:contains("Inscrição:")',
                '.row:contains("Tipo:")',
                
                # Bootstrap rows com conteúdo
                '.row:not(:empty)',
                '.container-fluid .row',
                '.panel-body',
                '.card-body',
                
                # Seletores muito genéricos (último recurso)
                'div:contains("Nome:")',
                'div:contains("Inscrição:")',
                '*:contains("Nome:")'
            ]
            
            # Tentar cada seletor
            for i, seletor in enumerate(seletores_resultado):
                try:
                    print(f"   Tentativa {i+1}: {seletor}")
                    
                    if ':contains(' in seletor:
                        # Para seletores :contains, usar XPath
                        xpath_seletor = self._converter_contains_para_xpath(seletor)
                        elementos = self.driver.find_elements(By.XPATH, xpath_seletor)
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
            
            # Se não encontrou nada, tentar busca por texto específico
            print("🔍 Buscando por texto específico...")
            return self._buscar_por_texto_especifico()
            
        except Exception as e:
            print(f"❌ Erro ao buscar elemento de resultado: {e}")
            return None
    
    def _converter_contains_para_xpath(self, seletor_css: str) -> str:
        """Converte seletor CSS com :contains para XPath"""
        try:
            if ':contains("Nome:")' in seletor_css:
                base = seletor_css.split(':contains')[0]
                if base == 'div':
                    return "//div[contains(text(), 'Nome:')]"
                elif base == '*':
                    return "//*[contains(text(), 'Nome:')]"
                else:
                    return f"//{base}[contains(text(), 'Nome:')]"
            elif ':contains("Inscrição:")' in seletor_css:
                base = seletor_css.split(':contains')[0]
                if base == 'div':
                    return "//div[contains(text(), 'Inscrição:')]"
                else:
                    return f"//{base}[contains(text(), 'Inscrição:')]"
            else:
                return "//div[contains(text(), 'Nome:') or contains(text(), 'Inscrição:')]"
        except:
            return "//div[contains(text(), 'Nome:')]"
    
    def _elemento_parece_resultado(self, elemento) -> bool:
        """
        🔧 NOVO: Verifica se um elemento parece conter resultado de advogado
        
        Args:
            elemento: Elemento HTML a verificar
            
        Returns:
            True se parece ser resultado
        """
        try:
            if not elemento.is_displayed():
                return False
            
            texto = elemento.text.strip()
            
            if len(texto) < 10:  # Muito pouco texto
                return False
            
            # Palavras-chave que indicam resultado de advogado
            palavras_chave = [
                'nome:', 'inscri', 'tipo:', 'advogad', 'oab',
                'seccional', 'situação', 'regular', 'ativo'
            ]
            
            texto_lower = texto.lower()
            palavras_encontradas = sum(1 for palavra in palavras_chave if palavra in texto_lower)
            
            # Deve ter pelo menos 2 palavras-chave
            if palavras_encontradas >= 2:
                print(f"   ✅ Elemento válido: {palavras_encontradas} palavras-chave, texto: {texto[:100]}...")
                return True
            
            return False
            
        except Exception as e:
            print(f"   ⚠️ Erro ao verificar elemento: {e}")
            return False
    
    def _buscar_por_texto_especifico(self):
        """
        🔧 NOVO: Busca elemento por texto específico usando XPath
        
        Returns:
            Elemento encontrado ou None
        """
        try:
            xpaths_busca = [
                "//div[contains(text(), 'Nome:')]",
                "//span[contains(text(), 'Nome:')]",
                "//td[contains(text(), 'Nome:')]",
                "//p[contains(text(), 'Nome:')]",
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
            print(f"❌ Erro na busca por texto: {e}")
            return None
    
    def _extrair_dados_pagina_completa(self, resultado: ResultadoOAB) -> bool:
        """
        🔧 NOVO: Extrai dados analisando toda a página quando elemento específico não é encontrado
        
        Args:
            resultado: Objeto ResultadoOAB
            
        Returns:
            True se encontrou dados
        """
        try:
            print("🔍 Analisando página completa...")
            
            # Obter todo o texto da página
            page_text = self.driver.page_source
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            print(f"📄 Texto da página: {len(body_text)} caracteres")
            
            # Salvar HTML para debug
            self._salvar_html_debug(page_text, resultado)
            
            # Buscar padrões de dados
            dados_encontrados = False
            
            # 1. Buscar nome
            nome = self._extrair_nome_do_texto(body_text)
            if nome:
                resultado.nome = nome
                dados_encontrados = True
                print(f"📝 Nome encontrado: {nome}")
            
            # 2. Buscar tipo
            tipo = self._extrair_tipo_do_texto(body_text)
            if tipo:
                resultado.tipo = tipo
                dados_encontrados = True
                print(f"🏷️ Tipo encontrado: {tipo}")
            
            # 3. Buscar situação
            situacao = self._extrair_situacao_do_texto(body_text)
            if situacao:
                resultado.situacao = situacao
                dados_encontrados = True
                print(f"📊 Situação encontrada: {situacao}")
            
            # 4. Buscar telefone
            telefone = self._extrair_telefone_do_texto(body_text)
            if telefone:
                resultado.telefone = telefone
                dados_encontrados = True
                print(f"📞 Telefone encontrado: {telefone}")
            
            # 5. Buscar endereço
            endereco = self._extrair_endereco_do_texto(body_text)
            if endereco:
                resultado.endereco = endereco
                dados_encontrados = True
                print(f"📍 Endereço encontrado: {endereco}")
            
            return dados_encontrados
            
        except Exception as e:
            print(f"❌ Erro ao analisar página completa: {e}")
            return False
    
    def _extrair_nome_do_texto(self, texto: str) -> str:
        """Extrai nome do texto da página"""
        padroes_nome = [
            r'Nome[:\s]*([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ][A-Za-záéíóúàèìòùâêîôûãõçñ\s]{8,80})',
            r'NOME[:\s]*([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ][A-Za-záéíóúàèìòùâêîôûãõçñ\s]{8,80})',
            # Linha que começa com nome em maiúsculas
            r'^([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ]{2,}(?:\s+[A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ]{2,})+)',
        ]
        
        linhas = texto.split('\n')
        
        for padrao in padroes_nome:
            # Buscar em cada linha
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
    
    def _extrair_situacao_do_texto(self, texto: str) -> str:
        """Extrai situação do texto da página"""
        padroes_situacao = [
            r'Situação[:\s]*([A-Za-z\s]{3,20})',
            r'SITUAÇÃO[:\s]*([A-Za-z\s]{3,20})',
            r'(REGULAR|ATIVO|ATIVA|LICENCIADO)',
        ]
        
        for padrao in padroes_situacao:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                situacao = match.group(1).strip()
                if len(situacao) > 2:
                    return situacao.upper()
        
        return ""
    
    def _extrair_telefone_do_texto(self, texto: str) -> str:
        """Extrai telefone do texto da página"""
        padroes_telefone = [
            r'Telefone[:\s]*\((\d{2})\)\s*(\d{4,5})[-\s]?(\d{4})',
            r'\((\d{2})\)\s*(\d{4,5})[-\s]?(\d{4})',
            r'(\d{2})\s+(\d{4,5})[-\s]?(\d{4})',
        ]
        
        for padrao in padroes_telefone:
            match = re.search(padrao, texto)
            if match:
                if len(match.groups()) == 3:
                    ddd, num1, num2 = match.groups()
                    return f"({ddd}) {num1}-{num2}"
        
        return ""
    
    def _extrair_endereco_do_texto(self, texto: str) -> str:
        """Extrai endereço do texto da página"""
        padroes_endereco = [
            r'Endereço[:\s]*([^\n]{10,100})',
            r'ENDEREÇO[:\s]*([^\n]{10,100})',
            r'(RUA\s+[^\n]{10,80})',
            r'(AVENIDA\s+[^\n]{10,80})',
        ]
        
        for padrao in padroes_endereco:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                endereco = match.group(1).strip()
                if len(endereco) > 10:
                    return endereco
        
        return ""
    
    def _validar_nome(self, nome: str) -> bool:
        """Valida se é um nome válido"""
        if not nome or len(nome) < 5 or len(nome) > 100:
            return False
        
        if ' ' not in nome:
            return False
        
        palavras_invalidas = ['INSCRICAO', 'SECCIONAL', 'TELEFONE', 'ENDERECO', 'ADVOGADO', 'SITUACAO']
        if any(palavra in nome.upper() for palavra in palavras_invalidas):
            return False
        
        return True
    
    def _salvar_debug_pagina(self, resultado: ResultadoOAB):
        """Salva debug da página para análise"""
        try:
            if not self.pasta_debug or not os.path.exists(self.pasta_debug):
                return
            
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
            
            # Texto da página
            text_path = os.path.join(
                self.pasta_debug,
                f"debug_texto_{resultado.inscricao}_{resultado.estado}.txt"
            )
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write("TEXTO VISÍVEL DA PÁGINA:\n")
                f.write("="*50 + "\n")
                f.write(self.driver.find_element(By.TAG_NAME, "body").text)
                f.write("\n\n" + "="*50 + "\n")
                f.write("HTML COMPLETO:\n")
                f.write("="*50 + "\n")
                f.write(self.driver.page_source[:5000])  # Primeiros 5000 chars
            print(f"📝 Texto salvo: {os.path.basename(text_path)}")
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar debug: {e}")
    
    def _salvar_html_debug(self, html_content: str, resultado: ResultadoOAB):
        """Salva HTML para debug"""
        try:
            if self.pasta_debug and os.path.exists(self.pasta_debug):
                caminho = os.path.join(
                    self.pasta_debug,
                    f"pagina_completa_{resultado.inscricao}_{resultado.estado}.html"
                )
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"📄 HTML completo salvo: {os.path.basename(caminho)}")
        except Exception as e:
            print(f"⚠️ Erro ao salvar HTML: {e}")
    
    def _extrair_dados_basicos_melhorado(self, elemento, resultado: ResultadoOAB) -> ResultadoOAB:
        """
        🔧 VERSÃO MELHORADA: Extrai dados básicos do elemento de resultado
        """
        try:
            texto_completo = elemento.text
            print(f"📋 Texto do elemento: {texto_completo[:200]}...")
            
            # Buscar nome com múltiplos padrões
            nome_patterns = [
                r'Nome[:\s]*(.+?)(?:\n|Tipo:|Inscri|$)',
                r'NOME[:\s]*(.+?)(?:\n|TIPO:|INSCRI|$)',
                # Nome em linha separada
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
            
            print(f"📋 Dados básicos extraídos: {resultado.nome} - {resultado.tipo}")
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair dados básicos: {e}")
            
        return resultado
    
    def _tentar_abrir_detalhes(self, elemento) -> bool:
        """
        🔧 VERSÃO MELHORADA: Tenta abrir modal de detalhes
        """
        try:
            print("🔍 Tentando abrir modal de detalhes...")
            
            # Estratégias para clicar no elemento
            estrategias = [
                lambda: elemento.click(),
                lambda: self.driver.execute_script("arguments[0].click();", elemento),
                lambda: self.driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", elemento),
            ]
            
            for i, estrategia in enumerate(estrategias, 1):
                try:
                    print(f"   Tentativa {i}...")
                    estrategia()
                    time.sleep(3)  # Aguardar modal carregar
                    
                    # Verificar se modal abriu
                    if self._modal_esta_aberto():
                        print("✅ Modal aberto com sucesso!")
                        return True
                        
                except Exception as e:
                    print(f"   ❌ Falha na tentativa {i}: {str(e)[:50]}...")
                    continue
            
            print("⚠️ Não conseguiu abrir modal")
            return False
            
        except Exception as e:
            print(f"❌ Erro ao tentar abrir detalhes: {e}")
            return False
    
    def _modal_esta_aberto(self) -> bool:
        """Verifica se modal está aberto"""
        try:
            seletores_modal = [
                '.modal.show',
                '.modal[style*="display: block"]',
                '.modal-content',
                '#imgDetail',
                '[id*="modal"]',
                '[class*="modal"]'
            ]
            
            for seletor in seletores_modal:
                try:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                    if elementos and any(elem.is_displayed() for elem in elementos):
                        return True
                except:
                    continue
            
            return False
            
        except:
            return False
    
    def _extrair_dados_modal_ocr(self, resultado: ResultadoOAB) -> ResultadoOAB:
        """
        🔧 VERSÃO MELHORADA: Extrai dados da modal usando OCR
        """
        try:
            print("🖼️ Extraindo dados da modal com OCR...")
            
            # Buscar imagem da modal
            imagem_elemento = self._encontrar_imagem_modal()
            
            if not imagem_elemento:
                print("❌ Imagem da modal não encontrada")
                return resultado
            
            # Obter URL da imagem
            img_url = imagem_elemento.get_attribute('src')
            if not img_url:
                print("❌ URL da imagem não encontrada")
                return resultado
            
            print(f"📥 Baixando imagem: {img_url}")
            
            # Baixar e processar imagem
            imagem_pil = self._baixar_imagem(img_url)
            if not imagem_pil:
                print("❌ Erro ao baixar imagem")
                return resultado
            
            # Salvar para debug
            self._salvar_imagem_debug(imagem_pil, resultado)
            
            # Aplicar OCR
            texto_extraido = self._aplicar_ocr_otimizado(imagem_pil)
            
            if texto_extraido:
                print(f"📝 Texto extraído: {len(texto_extraido)} caracteres")
                
                # Processar texto extraído
                resultado = self._processar_texto_ocr(texto_extraido, resultado)
                
                # Salvar texto para debug
                self._salvar_texto_ocr_debug(texto_extraido, resultado)
            else:
                print("❌ OCR não conseguiu extrair texto")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro na extração OCR da modal: {e}")
            return resultado
    
    def _encontrar_imagem_modal(self):
        """Encontra imagem da modal usando múltiplos seletores"""
        try:
            seletores_imagem = [
                "#imgDetail",
                "img[src*='RenderDetail']",
                ".modal img",
                ".modal-body img",
                ".tab-content img",
                "#divImgDetail img",
                "img[id*='detail']",
                "img[id*='Detail']"
            ]
            
            for seletor in seletores_imagem:
                try:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                    for elemento in elementos:
                        if elemento.is_displayed():
                            src = elemento.get_attribute('src')
                            if src and ('detail' in src.lower() or 'render' in src.lower()):
                                print(f"✅ Imagem encontrada: {seletor}")
                                return elemento
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ Erro ao encontrar imagem: {e}")
            return None
    
    def _baixar_imagem(self, img_url: str) -> Image.Image:
        """Baixa imagem da modal"""
        try:
            # Completar URL se relativa
            if img_url.startswith('/'):
                img_url = "https://cna.oab.org.br" + img_url
            
            # Usar cookies do navegador
            cookies = self.driver.get_cookies()
            session = requests.Session()
            
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://cna.oab.org.br/',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
            }
            
            response = session.get(img_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            imagem = Image.open(BytesIO(response.content))
            print(f"✅ Imagem baixada: {imagem.size}")
            
            return imagem
            
        except Exception as e:
            print(f"❌ Erro ao baixar imagem: {e}")
            return None
    
    def _aplicar_ocr_otimizado(self, imagem: Image.Image) -> str:
        """
        🔧 VERSÃO OTIMIZADA: Aplica OCR na imagem com múltiplas tentativas
        """
        try:
            print("🔍 Aplicando OCR otimizado...")
            
            # Pré-processar imagem
            imagens_processadas = self._preprocessar_imagem_multiplas(imagem)
            
            # Configurações de OCR para tentar
            configuracoes = [
                f'--oem 3 --psm 6 -l {self.idioma_ocr}',
                '--oem 3 --psm 4',
                '--oem 3 --psm 11',
                '--oem 3 --psm 12',
                '--psm 6',
                ''  # Configuração padrão
            ]
            
            melhor_resultado = ""
            melhor_score = 0
            
            for config in configuracoes:
                for nome_img, img_processada in imagens_processadas.items():
                    try:
                        if config:
                            texto = pytesseract.image_to_string(img_processada, config=config)
                        else:
                            texto = pytesseract.image_to_string(img_processada)
                        
                        texto_limpo = self._limpar_texto_ocr(texto)
                        score = self._avaliar_qualidade_ocr(texto_limpo)
                        
                        if score > melhor_score:
                            melhor_resultado = texto_limpo
                            melhor_score = score
                            print(f"   ✅ Novo melhor resultado (score: {score})")
                        
                        if score >= 80:  # Score muito bom
                            break
                            
                    except Exception as e:
                        continue
                
                if melhor_score >= 80:
                    break
            
            print(f"📝 Melhor resultado OCR (score: {melhor_score}): {len(melhor_resultado)} chars")
            return melhor_resultado
            
        except Exception as e:
            print(f"❌ Erro no OCR: {e}")
            return ""
    
    def _preprocessar_imagem_multiplas(self, imagem: Image.Image) -> dict:
        """Cria múltiplas versões processadas da imagem"""
        imagens = {}
        
        try:
            if imagem.mode != 'RGB':
                imagem = imagem.convert('RGB')
            
            # 1. Original redimensionada
            largura, altura = imagem.size
            img_resize = imagem.resize((largura * 2, altura * 2), Image.Resampling.LANCZOS)
            imagens['resize_2x'] = img_resize
            
            # 2. Escala de cinza
            img_gray = img_resize.convert('L')
            imagens['gray'] = img_gray
            
            # 3. Alto contraste
            enhancer = ImageEnhance.Contrast(img_gray)
            img_contrast = enhancer.enhance(2.0)
            imagens['high_contrast'] = img_contrast
            
            # 4. Brightness ajustado
            enhancer_bright = ImageEnhance.Brightness(img_gray)
            img_bright = enhancer_bright.enhance(1.2)
            imagens['bright'] = img_bright
            
            # 5. Sharpening
            img_sharp = img_gray.filter(ImageFilter.SHARPEN)
            imagens['sharp'] = img_sharp
            
            # 6. Versão combinada
            img_combined = img_contrast.filter(ImageFilter.SHARPEN)
            enhancer_final = ImageEnhance.Brightness(img_combined)
            img_final = enhancer_final.enhance(1.1)
            imagens['combined'] = img_final
            
        except Exception as e:
            print(f"⚠️ Erro no pré-processamento: {e}")
            imagens['original'] = imagem
        
        return imagens
    
    def _avaliar_qualidade_ocr(self, texto: str) -> int:
        """Avalia qualidade do texto extraído (0-100)"""
        if not texto or len(texto) < 10:
            return 0
        
        score = 0
        
        # Pontos por comprimento
        if len(texto) >= 50:
            score += 20
        elif len(texto) >= 30:
            score += 10
        
        # Pontos por palavras-chave
        palavras_importantes = ['ADVOGAD', 'INSCRI', 'SECCIONAL', 'SITUA', 'REGULAR', 
                              'ENDERECO', 'TELEFONE', 'PROFISSIONAL']
        
        for palavra in palavras_importantes:
            if palavra in texto.upper():
                score += 8
        
        # Pontos por números (inscrição)
        if re.search(r'\d{3,}', texto):
            score += 15
        
        # Pontos por estrutura
        linhas = [l.strip() for l in texto.split('\n') if l.strip()]
        if len(linhas) >= 5:
            score += 10
        
        # Penalizar caracteres estranhos
        caracteres_estranhos = len(re.findall(r'[^\w\s:()[\].-/áéíóúàèìòùâêîôûãõçñÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ]', texto))
        if caracteres_estranhos > len(texto) * 0.1:
            score -= 20
        
        return min(100, max(0, score))
    
    def _limpar_texto_ocr(self, texto: str) -> str:
        """Limpa texto extraído do OCR"""
        if not texto:
            return ""
        
        # Remover caracteres estranhos
        texto = re.sub(r'[^\w\s:()[\].-/áéíóúàèìòùâêîôûãõçñÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ]', ' ', texto)
        
        # Corrigir espaços múltiplos
        texto = re.sub(r'\s+', ' ', texto)
        
        # Corrigir quebras de linha
        texto = re.sub(r'\n\s*\n', '\n', texto)
        
        # Remover linhas muito curtas
        linhas = texto.split('\n')
        linhas_validas = []
        
        for linha in linhas:
            linha_limpa = linha.strip()
            if len(linha_limpa) > 1:
                linhas_validas.append(linha_limpa)
        
        return '\n'.join(linhas_validas)
    
    def _processar_texto_ocr(self, texto: str, resultado: ResultadoOAB) -> ResultadoOAB:
        """Processa texto extraído do OCR"""
        try:
            print("🔍 Processando texto do OCR...")
            
            # Usar extrator especializado
            extrator = ModalExtractorOCR()
            
            # Nome completo
            nome_melhorado = extrator.extrair_nome_completo(texto)
            if nome_melhorado and len(nome_melhorado) > len(resultado.nome or ''):
                resultado.nome = nome_melhorado
                print(f"✅ Nome atualizado: {resultado.nome}")
            
            # Inscrição
            inscricao_modal = extrator.extrair_inscricao(texto, resultado.inscricao)
            if inscricao_modal:
                resultado.numero_carteira = inscricao_modal
                print(f"✅ Número carteira: {resultado.numero_carteira}")
            
            # Telefones
            telefones = extrator.extrair_telefones(texto)
            if telefones:
                resultado.telefone = telefones
                print(f"✅ Telefones: {resultado.telefone}")
            
            # Endereço
            endereco_prof = extrator.extrair_endereco_profissional(texto)
            if endereco_prof:
                resultado.endereco = endereco_prof
                print(f"✅ Endereço: {resultado.endereco}")
            
            # Situação
            situacao = extrator.extrair_situacao(texto)
            if situacao:
                resultado.situacao = situacao
                print(f"✅ Situação: {resultado.situacao}")
            
            # Email
            email = extrator.extrair_email(texto)
            if email:
                resultado.email = email
                print(f"✅ Email: {resultado.email}")
            
            # Data de inscrição
            data_inscricao = extrator.extrair_data_inscricao(texto)
            if data_inscricao:
                resultado.data_inscricao = data_inscricao
                print(f"✅ Data inscrição: {resultado.data_inscricao}")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro ao processar texto OCR: {e}")
            return resultado
    
    def _salvar_imagem_debug(self, imagem: Image.Image, resultado: ResultadoOAB):
        """Salva imagem para debug"""
        try:
            if self.pasta_debug and os.path.exists(self.pasta_debug):
                caminho = os.path.join(
                    self.pasta_debug, 
                    f"modal_imagem_{resultado.inscricao}_{resultado.estado}.png"
                )
                imagem.save(caminho)
                print(f"🖼️ Imagem salva: {os.path.basename(caminho)}")
        except Exception as e:
            print(f"⚠️ Erro ao salvar imagem: {e}")
    
    def _salvar_texto_ocr_debug(self, texto: str, resultado: ResultadoOAB):
        """Salva texto extraído para debug"""
        try:
            if self.pasta_debug and os.path.exists(self.pasta_debug):
                caminho = os.path.join(
                    self.pasta_debug,
                    f"ocr_texto_{resultado.inscricao}_{resultado.estado}.txt"
                )
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write("TEXTO EXTRAÍDO VIA OCR:\n")
                    f.write("="*50 + "\n")
                    f.write(texto)
                    f.write("\n\n" + "="*50 + "\n")
                    f.write("DADOS PROCESSADOS:\n")
                    f.write(f"Nome: {resultado.nome}\n")
                    f.write(f"Tipo: {resultado.tipo}\n")
                    f.write(f"Situação: {resultado.situacao}\n")
                    f.write(f"Telefone: {resultado.telefone}\n")
                    f.write(f"Endereço: {resultado.endereco}\n")
                    f.write(f"Email: {resultado.email}\n")
                
                print(f"📄 Texto OCR salvo: {os.path.basename(caminho)}")
        except Exception as e:
            print(f"⚠️ Erro ao salvar texto OCR: {e}")
    
    def _fechar_modal(self):
        """Fecha modal de detalhes"""
        try:
            # Botões de fechar
            botoes_fechar = [
                "button.close",
                ".close", 
                "[data-dismiss='modal']",
                "button[onclick*='close']",
                ".modal-header .close",
                "[aria-label='Close']",
                ".btn-close"
            ]
            
            for seletor in botoes_fechar:
                try:
                    botoes = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                    if botoes:
                        botoes[0].click()
                        print("✅ Modal fechada")
                        time.sleep(1)
                        return
                except:
                    continue
            
            # Tentar ESC
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            print("✅ Modal fechada com ESC")
            time.sleep(1)
                
        except Exception as e:
            print(f"⚠️ Erro ao fechar modal: {e}")


class ModalExtractorOCR:
    """Classe para extração de dados do texto extraído via OCR"""
    
    def extrair_nome_completo(self, texto_ocr: str) -> str:
        """Extrai nome completo do texto OCR"""
        padroes_nome = [
            r'^([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ][A-Za-záéíóúàèìòùâêîôûãõçñ\s]{8,60})',
            r'Nome[:\s]*([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ][A-Za-záéíóúàèìòùâêîôûãõçñ\s]{5,60})',
            r'([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ]{2,}(?:\s+[A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ]{2,})+)',
        ]
        
        linhas = texto_ocr.split('\n')
        
        for linha in linhas[:5]:
            linha = linha.strip()
            for padrao in padroes_nome:
                match = re.search(padrao, linha, re.MULTILINE)
                if match:
                    nome = match.group(1).strip()
                    
                    if (8 <= len(nome) <= 60 and 
                        ' ' in nome and 
                        len(nome.split()) >= 2 and
                        not any(palavra in nome.upper() for palavra in 
                               ['INSCRICAO', 'SECCIONAL', 'TELEFONE', 'ENDERECO']) and
                        all(char.isalpha() or char.isspace() or char in 'ÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ' 
                            for char in nome)):
                        return nome
        
        return ""

    def extrair_inscricao(self, texto_ocr: str, inscricao_original: str) -> str:
        """Extrai número da inscrição do texto OCR"""
        padroes_inscricao = [
            r'Inscri[cç][aã]o[:\s]*(\d{4,8})',
            r'N[uú]mero[:\s]*(\d{4,8})',
            rf'({re.escape(inscricao_original)})',
        ]
        
        for padrao in padroes_inscricao:
            match = re.search(padrao, texto_ocr, re.IGNORECASE)
            if match:
                numero = match.group(1)
                if numero.isdigit() and 4 <= len(numero) <= 8:
                    return numero
        
        return inscricao_original

    def extrair_telefones(self, texto_ocr: str) -> str:
        """Extrai telefones do texto OCR"""
        telefones_encontrados = []
        
        try:
            padroes_telefone = [
                r'Telefone\s*Profissional[:\s]*\((\d{2})\)\s*(\d{4,5})[-\s]?(\d{4})',
                r'Telefone[:\s]*\((\d{2})\)\s*(\d{4,5})[-\s]?(\d{4})',
                r'\((\d{2})\)\s*(\d{4,5})[-\s]?(\d{4})',
                r'(\d{2})\s+(\d{4,5})[-\s]?(\d{4})',
            ]
            
            for padrao in padroes_telefone:
                matches = re.finditer(padrao, texto_ocr, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) == 3:
                        ddd, num1, num2 = match.groups()
                        telefone = f"({ddd}) {num1}-{num2}"
                        
                        if (len(ddd) == 2 and ddd.isdigit() and 
                            len(num1) in [4, 5] and num1.isdigit() and 
                            len(num2) == 4 and num2.isdigit()):
                            
                            if telefone not in telefones_encontrados:
                                telefones_encontrados.append(telefone)
            
            return " | ".join(telefones_encontrados) if telefones_encontrados else ""
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair telefones: {e}")
            return ""

    def extrair_endereco_profissional(self, texto_ocr: str) -> str:
        """Extrai endereço profissional do texto OCR"""
        try:
            padroes_endereco = [
                r'Endere[cç]o\s+Profissional[:\s]*([^\n]+?)(?:Telefone|$)',
                r'Endere[cç]o[:\s]*([^\n]+?)(?:Telefone|$)',
                r'(RUA\s+[^,\n]+(?:,\s*N[°º]?\s*\d+)?[^,\n]*)',
                r'(AVENIDA\s+[^,\n]+(?:,\s*N[°º]?\s*\d+)?[^,\n]*)',
            ]
            
            for padrao in padroes_endereco:
                match = re.search(padrao, texto_ocr, re.IGNORECASE)
                if match:
                    endereco = match.group(1).strip()
                    
                    # Limpar telefones do endereço
                    endereco = re.sub(r'Telefone[:\s]*\([0-9\s\)\(-]+', '', endereco, flags=re.IGNORECASE)
                    endereco = re.sub(r'\(\d{2}\)\s*\d{4,5}[-\s]?\d{4}', '', endereco)
                    
                    if 10 <= len(endereco) <= 200:
                        return endereco.strip()
            
            return ""
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair endereço: {e}")
            return ""

    def extrair_situacao(self, texto_ocr: str) -> str:
        """Extrai situação do advogado"""
        padroes_situacao = [
            r'SITUA[CÇ][AÃ]O\s+REGULAR',
            r'REGULAR',
            r'SITUA[CÇ][AÃ]O[:\s]*([A-Z\s]+)',
            r'(ATIVO|ATIVA|LICENCIADO|LICENCIADA)',
        ]
        
        for padrao in padroes_situacao:
            match = re.search(padrao, texto_ocr, re.IGNORECASE)
            if match:
                if padrao in [r'SITUA[CÇ][AÃ]O\s+REGULAR', r'REGULAR']:
                    return 'SITUAÇÃO REGULAR'
                
                situacao = match.group(1) if match.groups() else match.group(0)
                situacao = situacao.strip().upper()
                
                if 'REGULAR' in situacao:
                    return 'SITUAÇÃO REGULAR'
                elif situacao in ['ATIVO', 'ATIVA']:
                    return 'ATIVO'
                elif 4 <= len(situacao) <= 30:
                    return situacao
        
        return ""

    def extrair_email(self, texto_ocr: str) -> str:
        """Extrai email do texto OCR"""
        padroes_email = [
            r'Email[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'E-mail[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        ]
        
        for padrao in padroes_email:
            match = re.search(padrao, texto_ocr, re.IGNORECASE)
            if match:
                email = match.group(1) if match.groups() else match.group(0)
                email = email.strip().lower()
                
                if ('@' in email and '.' in email and 
                    5 <= len(email) <= 100 and
                    not any(char in email for char in [' ', '\n', '\t'])):
                    return email
        
        return ""

    def extrair_data_inscricao(self, texto_ocr: str) -> str:
        """Extrai data de inscrição"""
        padroes_data = [
            r'Data[:\s]*Inscri[cç][aã]o[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            r'Inscrito\s+em[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
        ]
        
        for padrao in padroes_data:
            match = re.search(padrao, texto_ocr, re.IGNORECASE)
            if match:
                data = match.group(1) if match.groups() else match.group(0)
                data = data.strip()
                
                if re.match(r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}', data):
                    return data
        
        return ""