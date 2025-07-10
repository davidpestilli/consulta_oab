#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitários para exportação de dados em diferentes formatos
Sistema de pastas organizadas por data e horário
"""

import csv
import json
import os
from datetime import datetime
from typing import List
from ..models.resultado_oab import ResultadoOAB

class DataExporter:
    """Classe responsável pela exportação de dados com organização em pastas"""
    
    def __init__(self):
        """Inicializa o exportador e cria a estrutura de pastas"""
        self.pasta_pesquisas = "Pesquisa"
        self.pasta_atual = None
        self._criar_pasta_pesquisa()
    
    def _criar_pasta_pesquisa(self):
        """Cria a pasta principal de pesquisas se não existir"""
        if not os.path.exists(self.pasta_pesquisas):
            os.makedirs(self.pasta_pesquisas)
            print(f"📁 Pasta criada: {self.pasta_pesquisas}")
    
    def _obter_pasta_atual(self):
        """Obtém ou cria a pasta para a pesquisa atual baseada na data/hora"""
        if self.pasta_atual is None:
            # Formato: YYYY-MM-DD_HH-MM-SS
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.pasta_atual = os.path.join(self.pasta_pesquisas, timestamp)
            
            # Criar a pasta se não existir
            if not os.path.exists(self.pasta_atual):
                os.makedirs(self.pasta_atual)
                print(f"📁 Pasta de pesquisa criada: {self.pasta_atual}")
        
        return self.pasta_atual
    
    def _gerar_nome_arquivo(self, resultado: ResultadoOAB, extensao: str):
        """Gera nome do arquivo baseado na inscrição e estado"""
        nome_base = f"OAB_{resultado.inscricao}_{resultado.estado}"
        
        # Se há nome do advogado, incluir nas primeiras palavras
        if resultado.nome:
            # Pegar primeiras duas palavras do nome e limpar caracteres especiais
            palavras_nome = resultado.nome.split()[:2]
            nome_limpo = "_".join(palavra.replace(" ", "").replace("/", "").replace("\\", "") 
                                for palavra in palavras_nome if palavra.isalpha())
            if nome_limpo:
                nome_base += f"_{nome_limpo}"
        
        return f"{nome_base}.{extensao}"
    
    def salvar_csv(self, resultados: List[ResultadoOAB], arquivo: str = None):
        """
        Salva resultados em arquivo CSV na pasta da pesquisa atual
        
        Args:
            resultados: Lista de ResultadoOAB
            arquivo: Nome do arquivo (opcional, será gerado automaticamente se não fornecido)
        """
        pasta_destino = self._obter_pasta_atual()
        
        # Se não foi fornecido nome de arquivo, gerar automaticamente
        if arquivo is None:
            if len(resultados) == 1:
                arquivo = self._gerar_nome_arquivo(resultados[0], "csv")
            else:
                timestamp = datetime.now().strftime("%H-%M-%S")
                arquivo = f"pesquisa_multipla_{timestamp}.csv"
        
        caminho_completo = os.path.join(pasta_destino, arquivo)
        
        with open(caminho_completo, 'w', newline='', encoding='utf-8') as csvfile:
            campos = ['inscricao', 'estado', 'nome', 'tipo', 'situacao', 
                     'endereco', 'telefone', 'email', 'data_inscricao', 
                     'numero_carteira', 'sucesso', 'erro', 'detalhes_completos']
            
            writer = csv.DictWriter(csvfile, fieldnames=campos)
            writer.writeheader()
            
            for resultado in resultados:
                writer.writerow({
                    'inscricao': resultado.inscricao,
                    'estado': resultado.estado,
                    'nome': resultado.nome,
                    'tipo': resultado.tipo,
                    'situacao': resultado.situacao,
                    'endereco': resultado.endereco,
                    'telefone': resultado.telefone,
                    'email': resultado.email,
                    'data_inscricao': resultado.data_inscricao,
                    'numero_carteira': resultado.numero_carteira,
                    'sucesso': resultado.sucesso,
                    'erro': resultado.erro,
                    'detalhes_completos': resultado.detalhes_completos
                })
                
        print(f"💾 CSV salvo em: {caminho_completo}")
        return caminho_completo
    
    def salvar_json(self, resultados: List[ResultadoOAB], arquivo: str = None):
        """
        Salva resultados em arquivo JSON na pasta da pesquisa atual
        
        Args:
            resultados: Lista de ResultadoOAB
            arquivo: Nome do arquivo (opcional, será gerado automaticamente se não fornecido)
        """
        pasta_destino = self._obter_pasta_atual()
        
        # Se não foi fornecido nome de arquivo, gerar automaticamente
        if arquivo is None:
            if len(resultados) == 1:
                arquivo = self._gerar_nome_arquivo(resultados[0], "json")
            else:
                timestamp = datetime.now().strftime("%H-%M-%S")
                arquivo = f"pesquisa_multipla_{timestamp}.json"
        
        caminho_completo = os.path.join(pasta_destino, arquivo)
        
        dados = {
            'metadata': {
                'data_pesquisa': datetime.now().isoformat(),
                'total_resultados': len(resultados),
                'resultados_com_sucesso': sum(1 for r in resultados if r.sucesso),
                'resultados_com_erro': sum(1 for r in resultados if not r.sucesso)
            },
            'resultados': []
        }
        
        for resultado in resultados:
            dados['resultados'].append({
                'inscricao': resultado.inscricao,
                'estado': resultado.estado,
                'nome': resultado.nome,
                'tipo': resultado.tipo,
                'situacao': resultado.situacao,
                'endereco': resultado.endereco,
                'telefone': resultado.telefone,
                'email': resultado.email,
                'data_inscricao': resultado.data_inscricao,
                'numero_carteira': resultado.numero_carteira,
                'sucesso': resultado.sucesso,
                'erro': resultado.erro,
                'detalhes_completos': resultado.detalhes_completos
            })
            
        with open(caminho_completo, 'w', encoding='utf-8') as jsonfile:
            json.dump(dados, jsonfile, ensure_ascii=False, indent=2)
            
        print(f"💾 JSON salvo em: {caminho_completo}")
        return caminho_completo
    
    def salvar_relatorio_txt(self, resultados: List[ResultadoOAB]):
        """
        Salva um relatório em texto simples com resumo da pesquisa
        
        Args:
            resultados: Lista de ResultadoOAB
        """
        pasta_destino = self._obter_pasta_atual()
        timestamp = datetime.now().strftime("%H-%M-%S")
        arquivo = f"relatorio_pesquisa_{timestamp}.txt"
        caminho_completo = os.path.join(pasta_destino, arquivo)
        
        with open(caminho_completo, 'w', encoding='utf-8') as txtfile:
            txtfile.write("=" * 60 + "\n")
            txtfile.write("          RELATÓRIO DE PESQUISA OAB\n")
            txtfile.write("=" * 60 + "\n\n")
            
            # Informações gerais
            txtfile.write(f"Data/Hora da Pesquisa: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n")
            txtfile.write(f"Total de Consultas: {len(resultados)}\n")
            txtfile.write(f"Consultas com Sucesso: {sum(1 for r in resultados if r.sucesso)}\n")
            txtfile.write(f"Consultas com Erro: {sum(1 for r in resultados if not r.sucesso)}\n\n")
            
            # Detalhes de cada resultado
            for i, resultado in enumerate(resultados, 1):
                txtfile.write(f"\n{'-' * 40}\n")
                txtfile.write(f"CONSULTA {i}: OAB {resultado.inscricao}/{resultado.estado}\n")
                txtfile.write(f"{'-' * 40}\n")
                
                if resultado.sucesso:
                    txtfile.write(f"✅ SUCESSO\n")
                    txtfile.write(f"Nome: {resultado.nome}\n")
                    txtfile.write(f"Tipo: {resultado.tipo}\n")
                    txtfile.write(f"Situação: {resultado.situacao}\n")
                    txtfile.write(f"Telefone: {resultado.telefone}\n")
                    txtfile.write(f"Endereço: {resultado.endereco}\n")
                    if resultado.detalhes_completos:
                        txtfile.write(f"Observações: {resultado.detalhes_completos}\n")
                else:
                    txtfile.write(f"❌ ERRO\n")
                    txtfile.write(f"Motivo: {resultado.erro}\n")
        
        print(f"📄 Relatório salvo em: {caminho_completo}")
        return caminho_completo
    
    def salvar_todos_formatos(self, resultados: List[ResultadoOAB]):
        """
        Salva os resultados em todos os formatos disponíveis
        
        Args:
            resultados: Lista de ResultadoOAB
            
        Returns:
            dict: Caminhos dos arquivos salvos
        """
        print(f"\n💾 Salvando resultados em todos os formatos...")
        
        arquivos_salvos = {
            'csv': self.salvar_csv(resultados),
            'json': self.salvar_json(resultados),
            'relatorio': self.salvar_relatorio_txt(resultados)
        }
        
        print(f"\n✅ Todos os arquivos salvos na pasta: {self._obter_pasta_atual()}")
        print(f"📁 Arquivos gerados:")
        for formato, caminho in arquivos_salvos.items():
            print(f"   {formato.upper()}: {os.path.basename(caminho)}")
        
        return arquivos_salvos
    
    def nova_sessao_pesquisa(self):
        """Inicia uma nova sessão de pesquisa (nova pasta com timestamp)"""
        self.pasta_atual = None
        print(f"🔄 Nova sessão de pesquisa iniciada")
    
    def obter_pasta_atual(self):
        """Retorna o caminho da pasta atual de pesquisa"""
        return self._obter_pasta_atual()
    
    def listar_pesquisas_anteriores(self):
        """Lista todas as pesquisas anteriores"""
        if not os.path.exists(self.pasta_pesquisas):
            print("📁 Nenhuma pesquisa anterior encontrada")
            return []
        
        pastas = [pasta for pasta in os.listdir(self.pasta_pesquisas) 
                 if os.path.isdir(os.path.join(self.pasta_pesquisas, pasta))]
        
        pastas.sort(reverse=True)  # Mais recentes primeiro
        
        print(f"\n📂 Pesquisas anteriores encontradas ({len(pastas)}):")
        for i, pasta in enumerate(pastas[:10], 1):  # Mostrar apenas as 10 mais recentes
            caminho_pasta = os.path.join(self.pasta_pesquisas, pasta)
            arquivos = len([f for f in os.listdir(caminho_pasta) 
                          if os.path.isfile(os.path.join(caminho_pasta, f))])
            print(f"   {i}. {pasta} ({arquivos} arquivos)")
        
        if len(pastas) > 10:
            print(f"   ... e mais {len(pastas) - 10} pesquisas")
        
        return pastas