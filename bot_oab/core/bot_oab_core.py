#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Classe principal do Bot OAB - VERSÃO ATUALIZADA
Sistema de pastas organizadas + Suporte a modal com imagem
"""

import time
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..models.resultado_oab import ResultadoOAB
from ..config.browser_config import BrowserConfig
from ..extractors.data_extractors import DataExtractor
from ..utils.data_exporters import DataExporter

class BotOABCorrigido:
    def __init__(self, headless: bool = False, timeout: int = 15):
        """
        Bot OAB corrigido - VERSÃO 2.0
        
        Args:
            headless: Se True, executa sem interface gráfica
            timeout: Tempo limite para aguardar elementos (segundos)
        """
        self.timeout = timeout
        self.driver = BrowserConfig.setup_driver(headless)
        self.wait = WebDriverWait(self.driver, timeout)
        self.data_exporter = DataExporter()
        
        # 🔧 CORREÇÃO: Configurar DataExtractor com pasta de debug
        pasta_atual = self.data_exporter.obter_pasta_atual()
        self.data_extractor = DataExtractor(self.driver, self.wait, pasta_atual)
        
        print(f"🤖 Bot OAB v2.0 iniciado com sistema de pastas organizadas")
        print(f"📁 Pasta de pesquisas: {self.data_exporter.pasta_pesquisas}")
        print(f"🐛 Debug será salvo em: {pasta_atual}")
        print(f"🖼️ Suporte a modal com imagem: ✅")
        
    def acessar_site(self) -> bool:
        """
        Acessa o site da OAB
        
        Returns:
            True se conseguiu acessar, False caso contrário
        """
        try:
            print("🌐 Acessando site da OAB...")
            self.driver.get("https://cna.oab.org.br/")
            
            # Aguarda a página carregar completamente
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            print("✅ Site carregado com sucesso!")
            return True
            
        except TimeoutException:
            print("❌ Timeout ao carregar o site")
            return False
        except Exception as e:
            print(f"❌ Erro ao acessar site: {str(e)}")
            return False
    
    def consultar_inscricao(self, inscricao: str, estado: str) -> ResultadoOAB:
        """
        Realiza consulta de uma inscrição específica
        VERSÃO ATUALIZADA - Suporte a modal com imagem
        
        Args:
            inscricao: Número da inscrição OAB
            estado: Sigla do estado (ex: "SP", "RJ", "MG")
            
        Returns:
            ResultadoOAB com os dados encontrados
        """
        resultado = ResultadoOAB(inscricao=inscricao, estado=estado)
        
        try:
            print(f"🔍 Consultando OAB {inscricao}/{estado}...")
            
            # 1. Localizar campo de inscrição pelo ID exato
            print("📝 Preenchendo número da inscrição...")
            campo_inscricao = self.wait.until(
                EC.presence_of_element_located((By.ID, "txtInsc"))
            )
            
            # Limpar e inserir número
            campo_inscricao.clear()
            campo_inscricao.send_keys(inscricao)
            print(f"✅ Número {inscricao} inserido")
            
            # 2. Selecionar estado na dropdown pelo ID exato
            print("🗺️ Selecionando estado...")
            dropdown_estado = Select(self.driver.find_element(By.ID, "cmbSeccional"))
            dropdown_estado.select_by_value(estado.upper())
            print(f"✅ Estado {estado} selecionado")
            
            # 3. Clicar no botão de pesquisa pelo ID exato
            print("🔍 Clicando em pesquisar...")
            botao_pesquisa = self.driver.find_element(By.ID, "btnFind")
            botao_pesquisa.click()
            print("✅ Pesquisa executada")
            
            # 4. Aguardar resultado aparecer
            print("⏳ Aguardando resultado...")
            time.sleep(3)
            
            # 5. Verificar se encontrou resultado e extrair dados
            return self.data_extractor.extrair_resultado(resultado)
            
        except TimeoutException:
            resultado.erro = "Timeout - Elemento não encontrado"
            print(f"❌ Timeout na consulta: {inscricao}/{estado}")
            
        except NoSuchElementException as e:
            resultado.erro = f"Elemento não encontrado: {str(e)}"
            print(f"❌ Elemento não encontrado: {inscricao}/{estado}")
            
        except Exception as e:
            resultado.erro = f"Erro inesperado: {str(e)}"
            print(f"❌ Erro na consulta {inscricao}/{estado}: {str(e)}")
            
        return resultado
    
    def consultar_multiplas(self, consultas: List[tuple]) -> List[ResultadoOAB]:
        """
        Realiza múltiplas consultas em lote com salvamento automático
        
        Args:
            consultas: Lista de tuplas (inscricao, estado)
            
        Returns:
            Lista de ResultadoOAB
        """
        resultados = []
        
        print(f"🚀 Iniciando consulta de {len(consultas)} inscrições...")
        
        for i, (inscricao, estado) in enumerate(consultas, 1):
            print(f"\n📋 Consulta {i}/{len(consultas)}")
            
            # Para múltiplas consultas, recarregar página entre consultas
            if i > 1:
                print("🔄 Recarregando página...")
                self.driver.refresh()
                time.sleep(3)
            
            resultado = self.consultar_inscricao(inscricao, estado)
            resultados.append(resultado)
            
            # Log do resultado
            if resultado.sucesso:
                print(f"✅ {resultado.nome} - {resultado.tipo}")
                if resultado.situacao:
                    print(f"   📊 Situação: {resultado.situacao}")
                if resultado.telefone:
                    print(f"   📞 Telefone: {resultado.telefone}")
                if resultado.endereco:
                    print(f"   📍 Endereço: {resultado.endereco}")
            else:
                print(f"❌ {resultado.erro}")
            
            # Pausa entre consultas para não sobrecarregar o servidor
            if i < len(consultas):
                print("⏳ Pausa entre consultas...")
                time.sleep(3)
        
        # Salvar resultados intermediários a cada 5 consultas
        if len(resultados) >= 5 and len(resultados) % 5 == 0:
            print(f"\n💾 Salvando resultados intermediários...")
            self.data_exporter.salvar_json(resultados)
                
        return resultados
    
    def nova_sessao_pesquisa(self):
        """
        Inicia uma nova sessão de pesquisa
        VERSÃO ATUALIZADA - Atualiza pasta de debug no extractor
        """
        self.data_exporter.nova_sessao_pesquisa()
        
        # 🔧 CORREÇÃO: Atualizar pasta de debug no extractor
        nova_pasta = self.data_exporter.obter_pasta_atual()
        self.data_extractor.definir_pasta_debug(nova_pasta)
        
        print(f"🔄 Nova sessão iniciada - pasta: {nova_pasta}")
        print(f"🐛 Debug será salvo em: {nova_pasta}")
    
    # Métodos de compatibilidade (mantidos)
    def salvar_resultados_csv(self, resultados: List[ResultadoOAB], arquivo: str = None):
        """Salva resultados em arquivo CSV - compatibilidade"""
        return self.data_exporter.salvar_csv(resultados, arquivo)
    
    def salvar_resultados_json(self, resultados: List[ResultadoOAB], arquivo: str = None):
        """Salva resultados em arquivo JSON - compatibilidade"""
        return self.data_exporter.salvar_json(resultados, arquivo)
    
    def salvar_todos_formatos(self, resultados: List[ResultadoOAB]):
        """Salva resultados em todos os formatos disponíveis"""
        return self.data_exporter.salvar_todos_formatos(resultados)
    
    def obter_estatisticas_sessao(self, resultados: List[ResultadoOAB]) -> dict:
        """Calcula estatísticas da sessão atual"""
        if not resultados:
            return {"total": 0, "sucessos": 0, "erros": 0, "taxa_sucesso": 0}
        
        sucessos = sum(1 for r in resultados if r.sucesso)
        erros = len(resultados) - sucessos
        taxa_sucesso = (sucessos / len(resultados)) * 100
        
        # Estatísticas por estado
        estados = {}
        for resultado in resultados:
            estado = resultado.estado
            if estado not in estados:
                estados[estado] = {"total": 0, "sucessos": 0}
            
            estados[estado]["total"] += 1
            if resultado.sucesso:
                estados[estado]["sucessos"] += 1
        
        # Tipos de advogados encontrados
        tipos = {}
        for resultado in resultados:
            if resultado.sucesso and resultado.tipo:
                tipo = resultado.tipo
                tipos[tipo] = tipos.get(tipo, 0) + 1
        
        # Dados extraídos vs não extraídos
        com_situacao = sum(1 for r in resultados if r.sucesso and r.situacao)
        com_telefone = sum(1 for r in resultados if r.sucesso and r.telefone)
        com_endereco = sum(1 for r in resultados if r.sucesso and r.endereco)
        
        return {
            "total": len(resultados),
            "sucessos": sucessos,
            "erros": erros,
            "taxa_sucesso": round(taxa_sucesso, 2),
            "por_estado": estados,
            "tipos_encontrados": tipos,
            "detalhes_extraidos": {
                "com_situacao": com_situacao,
                "com_telefone": com_telefone, 
                "com_endereco": com_endereco
            },
            "pasta_atual": self.data_exporter.obter_pasta_atual()
        }
    
    def imprimir_estatisticas(self, resultados: List[ResultadoOAB]):
        """Imprime estatísticas detalhadas da sessão - VERSÃO ATUALIZADA"""
        stats = self.obter_estatisticas_sessao(resultados)
        
        print(f"\n📊 ESTATÍSTICAS DA SESSÃO:")
        print(f"{'='*50}")
        print(f"Total de consultas: {stats['total']}")
        print(f"✅ Sucessos: {stats['sucessos']}")
        print(f"❌ Erros: {stats['erros']}")
        print(f"📈 Taxa de sucesso: {stats['taxa_sucesso']}%")
        
        if stats['por_estado']:
            print(f"\n📍 Por Estado:")
            for estado, dados in stats['por_estado'].items():
                taxa = (dados['sucessos'] / dados['total']) * 100
                print(f"   {estado}: {dados['sucessos']}/{dados['total']} ({taxa:.1f}%)")
        
        if stats['tipos_encontrados']:
            print(f"\n👥 Tipos de Advogados:")
            for tipo, count in stats['tipos_encontrados'].items():
                print(f"   {tipo}: {count}")
        
        # Nova seção: detalhes extraídos
        if stats['sucessos'] > 0:
            detalhes = stats['detalhes_extraidos']
            print(f"\n📋 Dados Detalhados Extraídos:")
            print(f"   🎯 Situação: {detalhes['com_situacao']}/{stats['sucessos']}")
            print(f"   📞 Telefone: {detalhes['com_telefone']}/{stats['sucessos']}")
            print(f"   📍 Endereço: {detalhes['com_endereco']}/{stats['sucessos']}")
            
            if detalhes['com_situacao'] < stats['sucessos']:
                print(f"   ⚠️ {stats['sucessos'] - detalhes['com_situacao']} casos com dados em imagem")
        
        print(f"\n📁 Pasta: {stats['pasta_atual']}")
    
    def fechar(self):
        """Fecha o navegador e mostra informações finais - VERSÃO ATUALIZADA"""
        if self.driver:
            self.driver.quit()
            print("🔒 Navegador fechado")
            
        # Mostrar pasta final onde foram salvos os arquivos
        pasta_atual = self.data_exporter.obter_pasta_atual()
        print(f"📁 Arquivos salvos em: {pasta_atual}")
        
        # Listar arquivos gerados na sessão atual
        import os
        try:
            if os.path.exists(pasta_atual):
                arquivos = os.listdir(pasta_atual)
                if arquivos:
                    print(f"📄 Arquivos gerados ({len(arquivos)}):")
                    for arquivo in sorted(arquivos):
                        tamanho = os.path.getsize(os.path.join(pasta_atual, arquivo))
                        print(f"   • {arquivo} ({tamanho} bytes)")
                        
                    # Separar por tipo
                    screenshots = [f for f in arquivos if f.endswith('.png')]
                    jsons = [f for f in arquivos if f.endswith('.json')]
                    csvs = [f for f in arquivos if f.endswith('.csv')]
                    htmls = [f for f in arquivos if f.endswith('.html')]
                    
                    print(f"\n📊 Resumo por tipo:")
                    if screenshots: print(f"   🖼️ Screenshots: {len(screenshots)}")
                    if jsons: print(f"   📋 JSONs: {len(jsons)}")
                    if csvs: print(f"   📊 CSVs: {len(csvs)}")
                    if htmls: print(f"   🌐 HTMLs: {len(htmls)}")
                    
        except Exception as e:
            print(f"⚠️ Erro ao listar arquivos: {e}")

    def executar_consulta_completa(self, consultas: List[tuple], salvar_automatico: bool = True) -> List[ResultadoOAB]:
        """
        Método de conveniência - VERSÃO ATUALIZADA
        Executa consultas completas com estatísticas e salvamento
        """
        print(f"🚀 Bot OAB v2.0 - Executando consulta completa de {len(consultas)} inscrições...")
        print(f"🖼️ Suporte a modal com imagem ativado")
        
        # Executar consultas
        resultados = self.consultar_multiplas(consultas)
        
        # Mostrar estatísticas
        self.imprimir_estatisticas(resultados)
        
        # Salvar se solicitado
        if salvar_automatico and resultados:
            print(f"\n💾 Salvando resultados...")
            self.salvar_todos_formatos(resultados)
        
        return resultados