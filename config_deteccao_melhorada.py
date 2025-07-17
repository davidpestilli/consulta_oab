#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações para Detecção Melhorada de Resultados OAB
Parâmetros otimizados para resolver problemas de detecção
"""

class ConfigDeteccaoMelhorada:
    """Configurações específicas para melhorar a detecção de resultados"""
    
    # ===========================================
    # TIMEOUTS E ESPERAS
    # ===========================================
    
    # Tempo para aguardar após clicar em pesquisar (segundos)
    TIMEOUT_APOS_PESQUISA = 6  # Aumentado de 3 para 6
    
    # Tempo para aguardar carregamento da página (segundos)
    TIMEOUT_CARREGAMENTO_PAGINA = 15
    
    # Tempo para aguardar modal abrir (segundos)
    TIMEOUT_MODAL = 5
    
    # Número máximo de tentativas para encontrar resultado
    MAX_TENTATIVAS_DETECCAO = 3
    
    # Intervalo entre tentativas (segundos)
    INTERVALO_TENTATIVAS = 2
    
    # ===========================================
    # SELETORES MELHORADOS PARA DETECÇÃO
    # ===========================================
    
    # Seletores para encontrar elementos de resultado (ordem de prioridade)
    SELETORES_RESULTADO = [
        # Seletores específicos primeiro
        '.row:has([class*="result"])',
        '.result-item',
        '.search-result',
        '.lawyer-info',
        '.advogado-info',
        
        # Seletores por conteúdo
        '.row:contains("Nome:")',
        '.row:contains("Inscrição:")',
        '.row:contains("Tipo:")',
        
        # Seletores Bootstrap
        '.container-fluid .row:not(:empty)',
        '.panel-body:not(:empty)',
        '.card-body:not(:empty)',
        
        # Seletores genéricos (último recurso)
        '.row:not(:empty)',
        'div[class*="result"]',
        'div[id*="result"]'
    ]
    
    # XPaths para busca por texto
    XPATHS_TEXTO = [
        "//div[contains(text(), 'Nome:')]",
        "//span[contains(text(), 'Nome:')]",
        "//td[contains(text(), 'Nome:')]",
        "//p[contains(text(), 'Nome:')]",
        "//*[contains(text(), 'Nome:') and string-length(text()) > 10]",
        "//div[contains(text(), 'Inscrição:')]",
        "//*[contains(text(), 'Inscrição:')]",
        "//div[contains(., 'Advogado') or contains(., 'Advogada')]",
        "//*[contains(text(), 'OAB') and contains(text(), 'SP')]"
    ]
    
    # Seletores para detectar mensagens de erro
    SELETORES_ERRO = [
        '.alert-danger',
        '.error',
        '.warning',
        '.no-results',
        '[class*="error"]',
        '[class*="warning"]',
        '[class*="danger"]',
        '.message-error',
        '#error-message'
    ]
    
    # Textos que indicam erro ou ausência de resultado
    TEXTOS_ERRO = [
        'não encontrado',
        'nenhum resultado',
        'não foi possível',
        'não localizado',
        'não existe',
        'inválida',
        'erro',
        'without results',
        'no results',
        'not found',
        'invalid',
        'nenhum registro'
    ]
    
    # ===========================================
    # CONFIGURAÇÕES DE MODAL
    # ===========================================
    
    # Seletores para detectar modal aberto
    SELETORES_MODAL = [
        '.modal.show',
        '.modal[style*="display: block"]',
        '.modal-content',
        '#imgDetail',
        '[id*="modal"][style*="display: block"]',
        '[class*="modal"][style*="display: block"]',
        '.popup',
        '.overlay'
    ]
    
    # Seletores para imagem dentro do modal
    SELETORES_IMAGEM_MODAL = [
        "#imgDetail",
        "img[src*='RenderDetail']",
        ".modal img[src*='detail']",
        ".modal-body img",
        ".tab-content img",
        "#divImgDetail img",
        "img[id*='detail']",
        "img[id*='Detail']",
        "img[src*='aspx']"
    ]
    
    # Seletores para fechar modal
    SELETORES_FECHAR_MODAL = [
        "button.close",
        ".close", 
        "[data-dismiss='modal']",
        "button[onclick*='close']",
        ".modal-header .close",
        "[aria-label='Close']",
        ".btn-close",
        ".modal-close",
        "[class*='close']"
    ]
    
    # ===========================================
    # CONFIGURAÇÕES DE VALIDAÇÃO
    # ===========================================
    
    # Palavras-chave que indicam resultado válido
    PALAVRAS_CHAVE_RESULTADO = [
        'nome:', 'inscri', 'tipo:', 'advogad', 'oab',
        'seccional', 'situação', 'regular', 'ativo',
        'telefone', 'endereço', 'profissional'
    ]
    
    # Número mínimo de palavras-chave para considerar resultado válido
    MIN_PALAVRAS_CHAVE = 2
    
    # Comprimento mínimo do texto para ser considerado resultado
    MIN_COMPRIMENTO_TEXTO = 20
    
    # Palavras que invalidam um resultado
    PALAVRAS_INVALIDAS = [
        'javascript:', 'function(', 'document.',
        'window.', 'alert(', 'console.',
        'undefined', 'null', 'NaN'
    ]
    
    # ===========================================
    # CONFIGURAÇÕES DE OCR
    # ===========================================
    
    # Configurações do Tesseract para OCR
    CONFIGURACOES_OCR = [
        '--oem 3 --psm 6 -l por',  # Português primeiro
        '--oem 3 --psm 6 -l eng',  # Inglês como fallback
        '--oem 3 --psm 4 -l por',  # Modo coluna única
        '--oem 3 --psm 11 -l por', # Texto esparso
        '--oem 3 --psm 12 -l por', # Texto esparso com orientação
        '--psm 6',                 # Bloco uniforme
        '--psm 8',                 # Palavra única
        ''                         # Padrão
    ]
    
    # Score mínimo para aceitar resultado do OCR
    MIN_SCORE_OCR = 30
    
    # ===========================================
    # CONFIGURAÇÕES DE DEBUG
    # ===========================================
    
    # Salvar arquivos de debug automaticamente
    SALVAR_DEBUG_AUTOMATICO = True
    
    # Tipos de debug a salvar
    TIPOS_DEBUG = [
        'screenshot',  # Screenshot da página
        'html',        # HTML completo
        'texto',       # Texto visível
        'elementos'    # Lista de elementos encontrados
    ]
    
    # Salvar debug mesmo quando encontra resultado
    DEBUG_SEMPRE = True  # False = só salva quando há erro
    
    # ===========================================
    # ESTRATÉGIAS DE BUSCA
    # ===========================================
    
    # Estratégias para buscar resultado (ordem de tentativa)
    ESTRATEGIAS_BUSCA = [
        'seletores_especificos',  # Tentar seletores específicos primeiro
        'busca_por_texto',        # Buscar por texto específico
        'analise_completa',       # Analisar página inteira
        'busca_em_modal',         # Tentar abrir e analisar modal
        'ocr_se_disponivel'       # Usar OCR como último recurso
    ]
    
    # ===========================================
    # CONFIGURAÇÕES ESPECÍFICAS DO SITE OAB
    # ===========================================
    
    # URL base do site
    URL_OAB = "https://cna.oab.org.br/"
    
    # IDs dos elementos do formulário
    ID_CAMPO_INSCRICAO = "txtInsc"
    ID_DROPDOWN_ESTADO = "cmbSeccional"
    ID_BOTAO_PESQUISA = "btnFind"
    
    # Aguardar estes elementos estarem presentes antes de continuar
    ELEMENTOS_OBRIGATORIOS = [
        (ID_CAMPO_INSCRICAO, "Campo de inscrição"),
        (ID_DROPDOWN_ESTADO, "Dropdown de estado"),
        (ID_BOTAO_PESQUISA, "Botão de pesquisa")
    ]
    
    # ===========================================
    # MÉTODOS AUXILIARES
    # ===========================================
    
    @classmethod
    def obter_config_timeouts(cls) -> dict:
        """Retorna configurações de timeout"""
        return {
            'apos_pesquisa': cls.TIMEOUT_APOS_PESQUISA,
            'carregamento': cls.TIMEOUT_CARREGAMENTO_PAGINA,
            'modal': cls.TIMEOUT_MODAL,
            'max_tentativas': cls.MAX_TENTATIVAS_DETECCAO,
            'intervalo_tentativas': cls.INTERVALO_TENTATIVAS
        }
    
    @classmethod
    def obter_config_seletores(cls) -> dict:
        """Retorna configurações de seletores"""
        return {
            'resultado': cls.SELETORES_RESULTADO,
            'erro': cls.SELETORES_ERRO,
            'modal': cls.SELETORES_MODAL,
            'imagem_modal': cls.SELETORES_IMAGEM_MODAL,
            'fechar_modal': cls.SELETORES_FECHAR_MODAL,
            'xpaths_texto': cls.XPATHS_TEXTO
        }
    
    @classmethod
    def obter_config_validacao(cls) -> dict:
        """Retorna configurações de validação"""
        return {
            'palavras_chave': cls.PALAVRAS_CHAVE_RESULTADO,
            'min_palavras': cls.MIN_PALAVRAS_CHAVE,
            'min_texto': cls.MIN_COMPRIMENTO_TEXTO,
            'palavras_invalidas': cls.PALAVRAS_INVALIDAS,
            'textos_erro': cls.TEXTOS_ERRO
        }
    
    @classmethod
    def obter_config_ocr(cls) -> dict:
        """Retorna configurações de OCR"""
        return {
            'configuracoes': cls.CONFIGURACOES_OCR,
            'min_score': cls.MIN_SCORE_OCR
        }
    
    @classmethod
    def obter_config_debug(cls) -> dict:
        """Retorna configurações de debug"""
        return {
            'automatico': cls.SALVAR_DEBUG_AUTOMATICO,
            'tipos': cls.TIPOS_DEBUG,
            'sempre': cls.DEBUG_SEMPRE
        }
    
    @classmethod
    def validar_elemento_resultado(cls, elemento_texto: str) -> bool:
        """
        Valida se um texto de elemento parece ser resultado válido
        
        Args:
            elemento_texto: Texto do elemento
            
        Returns:
            True se parece ser resultado válido
        """
        if not elemento_texto or len(elemento_texto) < cls.MIN_COMPRIMENTO_TEXTO:
            return False
        
        # Verificar palavras inválidas
        texto_lower = elemento_texto.lower()
        for palavra in cls.PALAVRAS_INVALIDAS:
            if palavra in texto_lower:
                return False
        
        # Contar palavras-chave
        palavras_encontradas = 0
        for palavra in cls.PALAVRAS_CHAVE_RESULTADO:
            if palavra in texto_lower:
                palavras_encontradas += 1
        
        return palavras_encontradas >= cls.MIN_PALAVRAS_CHAVE
    
    @classmethod
    def detectar_erro_na_pagina(cls, texto_pagina: str) -> bool:
        """
        Detecta se há mensagem de erro na página
        
        Args:
            texto_pagina: Texto da página
            
        Returns:
            True se detectou erro
        """
        texto_lower = texto_pagina.lower()
        
        for texto_erro in cls.TEXTOS_ERRO:
            if texto_erro in texto_lower:
                return True
        
        return False
    
    @classmethod
    def imprimir_configuracoes(cls):
        """Imprime configurações atuais"""
        print("🔧 CONFIGURAÇÕES DE DETECÇÃO MELHORADA:")
        print("=" * 60)
        print(f"⏱️ Timeout após pesquisa: {cls.TIMEOUT_APOS_PESQUISA}s")
        print(f"🔄 Máximo de tentativas: {cls.MAX_TENTATIVAS_DETECCAO}")
        print(f"🎯 Seletores de resultado: {len(cls.SELETORES_RESULTADO)}")
        print(f"❌ Seletores de erro: {len(cls.SELETORES_ERRO)}")
        print(f"🖼️ Seletores de modal: {len(cls.SELETORES_MODAL)}")
        print(f"📋 Palavras-chave: {len(cls.PALAVRAS_CHAVE_RESULTADO)}")
        print(f"🔍 XPaths de texto: {len(cls.XPATHS_TEXTO)}")
        print(f"📊 OCR configurações: {len(cls.CONFIGURACOES_OCR)}")
        print(f"🐛 Debug automático: {cls.SALVAR_DEBUG_AUTOMATICO}")
        print("=" * 60)


# Configuração específica para modo de desenvolvimento
class ConfigDebugMode(ConfigDeteccaoMelhorada):
    """Configurações para modo de debug/desenvolvimento"""
    
    # Timeouts maiores para análise manual
    TIMEOUT_APOS_PESQUISA = 10
    TIMEOUT_CARREGAMENTO_PAGINA = 30
    MAX_TENTATIVAS_DETECCAO = 5
    
    # Debug mais detalhado
    DEBUG_SEMPRE = True
    TIPOS_DEBUG = ['screenshot', 'html', 'texto', 'elementos', 'console']
    
    # Pausas para análise manual
    PAUSA_PARA_ANALISE = True
    TEMPO_PAUSA = 3


# Configuração para modo de produção
class ConfigProducaoOtimizada(ConfigDeteccaoMelhorada):
    """Configurações otimizadas para produção"""
    
    # Timeouts otimizados
    TIMEOUT_APOS_PESQUISA = 4
    TIMEOUT_CARREGAMENTO_PAGINA = 10
    MAX_TENTATIVAS_DETECCAO = 2
    
    # Debug mínimo
    DEBUG_SEMPRE = False
    TIPOS_DEBUG = ['screenshot']  # Só screenshot em caso de erro
    
    # Menos validações para maior velocidade
    MIN_PALAVRAS_CHAVE = 1


def obter_config_por_modo(modo: str = 'normal'):
    """
    Retorna configuração baseada no modo
    
    Args:
        modo: 'normal', 'debug' ou 'producao'
        
    Returns:
        Classe de configuração apropriada
    """
    if modo == 'debug':
        return ConfigDebugMode
    elif modo == 'producao':
        return ConfigProducaoOtimizada
    else:
        return ConfigDeteccaoMelhorada


if __name__ == "__main__":
    # Exemplo de uso
    config = ConfigDeteccaoMelhorada()
    config.imprimir_configuracoes()
    
    print(f"\n🧪 Testando validação:")
    
    # Teste de validação
    textos_teste = [
        "Nome: JOÃO DA SILVA SANTOS Tipo: ADVOGADO Inscrição: 123456/SP",
        "Nenhum resultado encontrado",
        "javascript:void(0)",
        "Nome: MARIA OLIVEIRA Advogada Seccional: RJ Situação: Regular"
    ]
    
    for texto in textos_teste:
        resultado = config.validar_elemento_resultado(texto)
        print(f"   {'✅' if resultado else '❌'} {texto[:50]}...")
    
    print(f"\n🔍 Testando detecção de erro:")
    
    textos_erro_teste = [
        "A consulta não retornou nenhum resultado",
        "Nome: JOÃO DA SILVA SANTOS",
        "Erro: Inscrição não encontrada",
        "Advogado encontrado com sucesso"
    ]
    
    for texto in textos_erro_teste:
        erro = config.detectar_erro_na_pagina(texto)
        print(f"   {'❌' if erro else '✅'} {texto}")