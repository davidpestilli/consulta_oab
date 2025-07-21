import os
import re
import time
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..models.resultado_oab import ResultadoOAB

class DataExtractor:
    """Classe responsável pela extração de dados das páginas"""
    
    def __init__(self, driver, wait, pasta_debug=None):
        self.driver = driver
        self.wait = wait
        self.pasta_debug = pasta_debug

    def definir_pasta_debug(self, pasta_debug: str):
        """Define a pasta onde salvar arquivos de debug"""
        self.pasta_debug = pasta_debug
    
    def extrair_resultado(self, resultado: ResultadoOAB) -> ResultadoOAB:
        """
        Extrai dados do resultado da consulta - VERSÃO SIMPLIFICADA SEM OCR
        
        Args:
            resultado: Objeto ResultadoOAB para preencher
            
        Returns:
            ResultadoOAB atualizado com dados extraídos
        """
        try:
            # Aguardar resultado aparecer
            time.sleep(2)
            
            # Verificar se apareceu mensagem de "não encontrado"
            page_text = self.driver.page_source.lower()
            if 'não encontrado' in page_text or 'nenhum resultado' in page_text:
                resultado.erro = "Inscrição não encontrada"
                print("⚠️ Inscrição não encontrada")
                return resultado
            
            # Buscar todos os elementos de resultado (.row)
            print("🔍 Buscando resultados...")
            elementos_resultado = self.driver.find_elements(By.CSS_SELECTOR, ".row")
            
            elemento_correto = None
            
            # NOVA VALIDAÇÃO: Procurar o elemento que corresponde exatamente à consulta
            for i, elemento in enumerate(elementos_resultado):
                try:
                    # Verificar se contém os subelementos esperados
                    if not elemento.find_elements(By.CSS_SELECTOR, ".rowName, .rowInsc, .rowUf"):
                        continue
                    
                    # Extrair dados dos subelementos
                    nome_elemento = elemento.find_element(By.CSS_SELECTOR, ".rowName span:last-child")
                    insc_elemento = elemento.find_element(By.CSS_SELECTOR, ".rowInsc span:last-child")
                    uf_elemento = elemento.find_element(By.CSS_SELECTOR, ".rowUf span:last-child")
                    
                    inscricao_encontrada = insc_elemento.text.strip()
                    uf_encontrada = uf_elemento.text.strip().upper()
                    nome_encontrado = nome_elemento.text.strip()
                    
                    print(f"🔍 Resultado {i+1}: {inscricao_encontrada}/{uf_encontrada} - {nome_encontrado}")
                    
                    # VALIDAÇÃO CRÍTICA: Verificar se corresponde ao que foi pesquisado
                    if self._validar_correspondencia(resultado.inscricao, resultado.estado, 
                                                   inscricao_encontrada, uf_encontrada):
                        
                        print(f"✅ Correspondência EXATA encontrada! {inscricao_encontrada}/{uf_encontrada}")
                        elemento_correto = elemento
                        
                        # Preencher resultado
                        resultado.nome = nome_encontrado
                        resultado.inscricao_verificada = inscricao_encontrada
                        resultado.estado_verificado = uf_encontrada
                        resultado.sucesso = True
                        
                        break
                    else:
                        print(f"⚠️ Não corresponde: esperado {resultado.inscricao}/{resultado.estado.upper()}")
                        continue
                        
                except Exception as e:
                    print(f"⚠️ Erro ao processar resultado {i+1}: {e}")
                    continue
            
            if elemento_correto:
                print(f"✅ Dados extraídos com sucesso: {resultado.nome}")
            else:
                # Se não encontrou correspondência exata, tentar método antigo como fallback
                print("🔄 Tentando método de fallback...")
                resultado = self._extrair_dados_basicos_fallback(elementos_resultado, resultado)
                
        except Exception as e:
            resultado.erro = f"Erro ao extrair resultado: {str(e)}"
            print(f"❌ Erro na extração: {str(e)}")
            
        return resultado
    
    def _normalizar_numero_oab(self, numero: str) -> str:
        """
        Normaliza número OAB para comparação
        Remove zeros à esquerda e espaços
        
        Args:
            numero: Número a normalizar
            
        Returns:
            Número normalizado
        """
        if not numero:
            return ""
        
        # Remover espaços e converter para string
        numero_limpo = str(numero).strip()
        
        # Remover zeros à esquerda (importante para comparação)
        numero_normalizado = numero_limpo.lstrip('0')
        
        # Se ficou vazio (era só zeros), retornar "0"
        if not numero_normalizado:
            numero_normalizado = "0"
            
        return numero_normalizado
    
    def _validar_correspondencia(self, numero_busca: str, uf_busca: str, 
                               numero_encontrado: str, uf_encontrada: str) -> bool:
        """
        Valida se o resultado encontrado corresponde ao que foi buscado
        
        Args:
            numero_busca: Número que foi pesquisado
            uf_busca: UF que foi pesquisada
            numero_encontrado: Número encontrado no resultado
            uf_encontrada: UF encontrada no resultado
            
        Returns:
            True se corresponde, False caso contrário
        """
        # Normalizar números para comparação (remover zeros à esquerda)
        numero_busca_norm = self._normalizar_numero_oab(numero_busca)
        numero_encontrado_norm = self._normalizar_numero_oab(numero_encontrado)
        
        # Normalizar UFs (maiúsculas e remover espaços)
        uf_busca_norm = uf_busca.strip().upper()
        uf_encontrada_norm = uf_encontrada.strip().upper()
        
        # Comparar
        numeros_iguais = numero_busca_norm == numero_encontrado_norm
        ufs_iguais = uf_busca_norm == uf_encontrada_norm
        
        print(f"🔍 Validação: '{numero_busca_norm}' == '{numero_encontrado_norm}' ? {numeros_iguais}")
        print(f"🔍 Validação: '{uf_busca_norm}' == '{uf_encontrada_norm}' ? {ufs_iguais}")
        
        return numeros_iguais and ufs_iguais
    
    def _extrair_dados_basicos_fallback(self, elementos_resultado, resultado: ResultadoOAB) -> ResultadoOAB:
        """
        Método de fallback para extrair dados quando não há correspondência exata
        Pega o primeiro resultado disponível
        
        Args:
            elementos_resultado: Lista de elementos encontrados
            resultado: Objeto ResultadoOAB para preencher
            
        Returns:
            ResultadoOAB atualizado
        """
        print("🔄 Aplicando método de fallback...")
        
        for i, elemento in enumerate(elementos_resultado):
            try:
                # Verificar se contém os subelementos esperados
                if not elemento.find_elements(By.CSS_SELECTOR, ".rowName, .rowInsc, .rowUf"):
                    continue
                
                # Extrair dados do primeiro resultado válido
                nome_elemento = elemento.find_element(By.CSS_SELECTOR, ".rowName span:last-child")
                insc_elemento = elemento.find_element(By.CSS_SELECTOR, ".rowInsc span:last-child")
                uf_elemento = elemento.find_element(By.CSS_SELECTOR, ".rowUf span:last-child")
                
                nome = nome_elemento.text.strip()
                inscricao = insc_elemento.text.strip()
                uf = uf_elemento.text.strip()
                
                if nome and inscricao and uf:
                    resultado.nome = nome
                    resultado.inscricao_verificada = inscricao
                    resultado.estado_verificado = uf.upper()
                    resultado.sucesso = True
                    
                    print(f"🔄 Dados extraídos via fallback: {nome} ({inscricao}/{uf})")
                    print("⚠️ ATENÇÃO: Dados podem não corresponder exatamente à busca!")
                    break
                    
            except Exception as e:
                print(f"⚠️ Erro no fallback elemento {i+1}: {e}")
                continue
        
        return resultado

    def fechar_modal_imagem(self):
        """Fecha qualquer modal de imagem que possa estar aberto"""
        try:
            # Tenta fechar modal por botão de fechar
            botao_fechar = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "close"))
            )
            botao_fechar.click()
            print("Modal fechado com sucesso")
            
            # Aguarda modal desaparecer
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "modal"))
            )
            
        except Exception as e:
            print(f"Não foi possível fechar modal: {e}")
            
        return


# Manter a classe original para compatibilidade
class ModalExtractorGenerico(DataExtractor):
    """Alias para compatibilidade com código existente"""
    pass
