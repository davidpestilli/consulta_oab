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
        
        # Se ficou vazio (só tinha zeros), manter um zero
        if not numero_normalizado:
            numero_normalizado = '0'
            
        return numero_normalizado
    
    def _validar_correspondencia(self, numero_pesquisado: str, estado_pesquisado: str, 
                                numero_encontrado: str, estado_encontrado: str) -> bool:
        """
        Valida se os dados encontrados correspondem ao que foi pesquisado
        
        Args:
            numero_pesquisado: Número OAB pesquisado
            estado_pesquisado: Estado pesquisado
            numero_encontrado: Número encontrado no resultado
            estado_encontrado: Estado encontrado no resultado
            
        Returns:
            True se correspondem, False caso contrário
        """
        try:
            # Normalizar números para comparação
            num_pesq_norm = self._normalizar_numero_oab(numero_pesquisado)
            num_enc_norm = self._normalizar_numero_oab(numero_encontrado)
            
            # Normalizar estados
            estado_pesq_norm = estado_pesquisado.strip().upper()
            estado_enc_norm = estado_encontrado.strip().upper()
            
            # Verificar correspondência
            numeros_iguais = num_pesq_norm == num_enc_norm
            estados_iguais = estado_pesq_norm == estado_enc_norm
            
            print(f"🔍 Validação: {num_pesq_norm}/{estado_pesq_norm} vs {num_enc_norm}/{estado_enc_norm}")
            print(f"   Números: {'✅' if numeros_iguais else '❌'} | Estados: {'✅' if estados_iguais else '❌'}")
            
            return numeros_iguais and estados_iguais
            
        except Exception as e:
            print(f"⚠️ Erro na validação de correspondência: {e}")
            return False

    def _extrair_dados_basicos_fallback(self, elementos_resultado: list, resultado: ResultadoOAB) -> ResultadoOAB:
        """
        Método de fallback usando extração de texto básica (método antigo)
        
        Args:
            elementos_resultado: Lista de elementos .row encontrados
            resultado: Objeto ResultadoOAB
            
        Returns:
            ResultadoOAB atualizado
        """
        try:
            print("🔄 Usando método de fallback...")
            
            for i, elemento in enumerate(elementos_resultado):
                # Verificar se contém dados de advogado (tem nome e inscrição)
                texto = elemento.text
                if "Nome:" in texto and "Inscrição:" in texto:
                    print(f"🔍 Fallback - processando resultado {i+1}")
                    
                    # Extrair usando regex (método antigo)
                    nome_match = re.search(r'Nome:\s*(.+?)(?:\n|Tipo:|Inscrição:)', texto)
                    if nome_match:
                        resultado.nome = nome_match.group(1).strip()
                        resultado.sucesso = True
                        print(f"✅ Fallback - nome extraído: {resultado.nome}")
                        break
            
            if not resultado.sucesso:
                resultado.erro = "Nenhum resultado válido encontrado (fallback)"
                print("❌ Fallback também falhou")
                
        except Exception as e:
            resultado.erro = f"Erro no fallback: {str(e)}"
            print(f"❌ Erro no fallback: {e}")
            
        return resultado

    def _extrair_dados_basicos(self, elemento: object, resultado: ResultadoOAB) -> ResultadoOAB:
        """
        Extrai dados básicos do elemento de resultado
        
        Args:
            elemento: Elemento HTML do resultado
            resultado: Objeto ResultadoOAB
            
        Returns:
            ResultadoOAB atualizado
        """
        try:
            texto_completo = elemento.text
            
            # Buscar nome
            nome_match = re.search(r'Nome:\s*(.+?)(?:\n|Tipo:)', texto_completo)
            if nome_match:
                resultado.nome = nome_match.group(1).strip()
            
            # Buscar tipo
            tipo_match = re.search(r'Tipo:\s*(.+?)(?:\n|Inscrição:)', texto_completo)
            if tipo_match:
                resultado.tipo = tipo_match.group(1).strip()
            
            print(f"📋 Dados básicos extraídos: {resultado.nome} - {resultado.tipo}")
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair dados básicos: {e}")
            
        return resultado
    
    # ==========================================
    # MÉTODOS DE OCR REMOVIDOS
    # Sistema simplificado não usa mais OCR
    # ==========================================
    
    def _fechar_modal(self):
        """Método para fechar modal - mantido para compatibilidade"""
        try:
            # Tentar fechar modal se estiver aberto
            botoes_fechar = [
                "button.close",
                ".modal-header .close",
                ".btn-close",
                "[aria-label='Close']"
            ]
            
            for seletor in botoes_fechar:
                try:
                    botao = self.driver.find_element(By.CSS_SELECTOR, seletor)
                    if botao.is_displayed():
                        botao.click()
                        time.sleep(1)
                        print("✅ Modal fechado")
                        return
                except:
                    continue
                    
            # Se não encontrou botão, tentar ESC
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
            print("✅ Modal fechado via ESC")
            
        except Exception as e:
            print(f"⚠️ Erro ao fechar modal: {e}")
    
    # FIM DA CLASSE DataExtractor
            seletores_imagem = [
                "#imgDetail",  # ID específico da OAB
                "img[src*='RenderDetail']",  # Imagem com RenderDetail na URL
                ".tab-content img",  # Imagem dentro do tab-content
                "#divImgDetail img",  # Imagem dentro do div de detalhes
            ]
            
            for seletor in seletores_imagem:
                try:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                    for elemento in elementos:
                        src = elemento.get_attribute('src')
                        if src and ('RenderDetail' in src or 'detail' in src.lower()):
                            imagem_elemento = elemento
                            img_url = src
                            print(f"✅ Imagem encontrada: {seletor}")
                            break
                    if imagem_elemento:
                        break
                except:
                    continue
            
            if not imagem_elemento or not img_url:
                print("❌ Imagem do modal não encontrada")
                return resultado
            
            # 2. Baixar e processar a imagem
            print("📥 Baixando imagem do modal...")
            imagem_pil = self._baixar_imagem(img_url)
            
            if not imagem_pil:
                print("❌ Erro ao baixar imagem")
                return resultado
            
            # 3. Salvar imagem para debug
            self._salvar_imagem_debug(imagem_pil, resultado)
            
            # 4. Aplicar OCR para extrair texto
            print("🔍 Aplicando OCR na imagem...")
            texto_extraido = self._aplicar_ocr_universal(imagem_pil)
            
            if not texto_extraido:
                print("❌ OCR não conseguiu extrair texto")
                return resultado
            
            # 5. Processar texto extraído
            print("📋 Processando texto extraído...")
            resultado = self._processar_texto_ocr(texto_extraido, resultado)
            
            # 6. Salvar texto extraído para debug
            self._salvar_texto_ocr_debug(texto_extraido, resultado)
            
            resultado.detalhes_completos = "Dados extraídos da imagem via OCR"
            print("🎉 Extração da imagem via OCR concluída!")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro na extração via OCR: {str(e)}")
            resultado.erro = f"Erro no OCR: {str(e)}"
            return resultado
    
    def _baixar_imagem(self, img_url: str) -> Image.Image:
        """
        Baixa a imagem do modal
        
        Args:
            img_url: URL da imagem
            
        Returns:
            Objeto PIL.Image ou None
        """
        try:
            # Se a URL é relativa, completar com o domínio
            if img_url.startswith('/'):
                img_url = "https://cna.oab.org.br" + img_url
            
            # Usar cookies do navegador para manter a sessão
            cookies = self.driver.get_cookies()
            session = requests.Session()
            
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            # Headers para parecer um navegador real
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://cna.oab.org.br/',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
            }
            
            response = session.get(img_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Converter para PIL Image
            imagem = Image.open(BytesIO(response.content))
            print(f"✅ Imagem baixada: {imagem.size}")
            
            return imagem
            
        except Exception as e:
            print(f"❌ Erro ao baixar imagem: {e}")
            return None
    
    def _aplicar_ocr_universal(self, imagem: Image.Image) -> str:
        """
        Aplica OCR na imagem - VERSÃO UNIVERSAL sem dependência de idioma
        
        Args:
            imagem: Objeto PIL.Image
            
        Returns:
            Texto extraído ou string vazia
        """
        try:
            print(f"🔍 Aplicando OCR com idioma: {getattr(self, 'idioma_ocr', 'eng')}")
            
            # Lista de configurações para tentar (do mais específico ao mais genérico)
            configuracoes = [
                # Configuração ideal com idioma específico
                f'--oem 3 --psm 6 -l {getattr(self, "idioma_ocr", "eng")} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789áéíóúàèìòùâêîôûãõçñÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ:()[].-/ ',
                
                # Configuração sem whitelist
                f'--oem 3 --psm 6 -l {getattr(self, "idioma_ocr", "eng")}',
                
                # Configuração básica apenas com inglês
                '--oem 3 --psm 6 -l eng',
                
                # Configuração minimalista
                '--psm 6',
                
                # Sem configuração (padrão)
                ''
            ]
            
            # Pré-processar imagem para múltiplas tentativas
            imagens_processadas = self._preprocessar_imagem_multiplas(imagem)
            
            melhor_resultado = ""
            melhor_score = 0
            
            # Tentar diferentes combinações de configuração + pré-processamento
            for config in configuracoes:
                for nome_img, img_processada in imagens_processadas.items():
                    try:
                        print(f"   🧪 Testando: {config or 'padrão'} + {nome_img}")
                        
                        if config:
                            texto = pytesseract.image_to_string(img_processada, config=config)
                        else:
                            texto = pytesseract.image_to_string(img_processada)
                        
                        # Limpar e avaliar resultado
                        texto_limpo = self._limpar_texto_ocr(texto)
                        score = self._avaliar_qualidade_ocr(texto_limpo)
                        
                        print(f"      Score: {score} ({len(texto_limpo)} chars)")
                        
                        if score > melhor_score:
                            melhor_resultado = texto_limpo
                            melhor_score = score
                            print(f"      ✅ Novo melhor resultado!")
                        
                        # Se já temos um resultado muito bom, não precisa continuar
                        if score >= 80:
                            break
                            
                    except Exception as e:
                        print(f"      ❌ Erro: {str(e)[:50]}...")
                        continue
                
                if melhor_score >= 80:
                    break
            
            print(f"📝 Melhor resultado OCR (score: {melhor_score}): {len(melhor_resultado)} caracteres")
            return melhor_resultado
            
        except Exception as e:
            print(f"❌ Erro geral no OCR: {e}")
            return ""
    
    def _preprocessar_imagem_multiplas(self, imagem: Image.Image) -> dict:
        """
        Cria múltiplas versões pré-processadas da imagem
        
        Args:
            imagem: Imagem original
            
        Returns:
            Dict com diferentes versões processadas
        """
        imagens = {}
        
        try:
            # Converter para RGB se necessário
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
            
            # 6. Versão combinada (melhor qualidade)
            img_combined = img_contrast.filter(ImageFilter.SHARPEN)
            enhancer_final = ImageEnhance.Brightness(img_combined)
            img_final = enhancer_final.enhance(1.1)
            imagens['combined'] = img_final
            
            print(f"🔧 Criadas {len(imagens)} versões da imagem")
            
        except Exception as e:
            print(f"⚠️ Erro no pré-processamento: {e}")
            # Fallback: pelo menos a original
            imagens['original'] = imagem
        
        return imagens
    
    def _avaliar_qualidade_ocr(self, texto: str) -> int:
        """
        Avalia a qualidade do texto extraído por OCR
        
        Args:
            texto: Texto extraído
            
        Returns:
            Score de 0-100
        """
        if not texto or len(texto) < 10:
            return 0
        
        score = 0
        
        # Pontos por comprimento (mínimo esperado)
        if len(texto) >= 50:
            score += 20
        elif len(texto) >= 30:
            score += 10
        
        # Pontos por palavras-chave importantes
        palavras_importantes = ['ADVOGAD', 'INSCRI', 'SECCIONAL', 'SITUA', 'REGULAR', 
                              'ENDERECO', 'TELEFONE', 'PROFISSIONAL']
        
        for palavra in palavras_importantes:
            if palavra in texto.upper():
                score += 8
        
        # Pontos por ter números (inscrição)
        if re.search(r'\d{3,}', texto):
            score += 15
        
        # Pontos por ter estrutura (linhas)
        linhas = [l.strip() for l in texto.split('\n') if l.strip()]
        if len(linhas) >= 5:
            score += 10
        
        # Penalizar se tem muitos caracteres estranhos
        caracteres_estranhos = len(re.findall(r'[^\w\s:()[\].-/áéíóúàèìòùâêîôûãõçñÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ]', texto))
        if caracteres_estranhos > len(texto) * 0.1:  # Mais de 10% de caracteres estranhos
            score -= 20
        
        return min(100, max(0, score))
    
    def _limpar_texto_ocr(self, texto: str) -> str:
        """
        Limpa e normaliza o texto extraído do OCR
        
        Args:
            texto: Texto bruto do OCR
            
        Returns:
            Texto limpo
        """
        if not texto:
            return ""
        
        # Remover caracteres muito estranhos
        texto = re.sub(r'[^\w\s:()[\].-/áéíóúàèìòùâêîôûãõçñÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ]', ' ', texto)
        
        # Corrigir múltiplos espaços
        texto = re.sub(r'\s+', ' ', texto)
        
        # Corrigir quebras de linha múltiplas
        texto = re.sub(r'\n\s*\n', '\n', texto)
        
        # Remover linhas muito curtas ou apenas com espaços
        linhas = texto.split('\n')
        linhas_validas = []
        
        for linha in linhas:
            linha_limpa = linha.strip()
            if len(linha_limpa) > 1:  # Manter linhas com pelo menos 2 caracteres
                linhas_validas.append(linha_limpa)
        
        return '\n'.join(linhas_validas)
    
    def _corrigir_nomes_brasileiros(self, texto: str) -> str:
        """
        🇧🇷 NOVA FUNCIONALIDADE: Corrige nomes brasileiros "emendados" pelo OCR
        
        Args:
            texto: Texto com possíveis nomes emendados
            
        Returns:
            Texto com nomes corrigidos
        """
        try:
            # Lista de nomes/sobrenomes brasileiros comuns para detectar junções
            nomes_comuns = [
                # Nomes masculinos comuns
                'ANTONIO', 'JOSE', 'FRANCISCO', 'CARLOS', 'PAULO', 'PEDRO', 'LUCAS', 'LUIZ', 'MARCOS', 'LUIS',
                'JOAO', 'RICARDO', 'BRUNO', 'DANIEL', 'EDUARDO', 'RAFAEL', 'FELIPE', 'FABIO', 'ANDRE', 'JORGE',
                'DIEGO', 'GUSTAVO', 'FERNANDO', 'RODRIGO', 'LEANDRO', 'TIAGO', 'SERGIO', 'ADRIANO', 'ALEXANDRE',
                
                # Nomes femininos comuns  
                'MARIA', 'ANA', 'FRANCISCA', 'ANTONIA', 'ADRIANA', 'JULIANA', 'MARCIA', 'FERNANDA', 'PATRICIA',
                'ALINE', 'SANDRA', 'CAMILA', 'AMANDA', 'BRUNA', 'JESSICA', 'LETICIA', 'JULIA', 'LUCIANA', 'DENISE',
                'CARLA', 'BEATRIZ', 'CRISTINA', 'MONICA', 'SABRINA', 'CAROLINA', 'GABRIELA', 'LARISSA', 'NATALIA',
                
                # Sobrenomes comuns
                'SILVA', 'SANTOS', 'OLIVEIRA', 'SOUZA', 'RODRIGUES', 'FERREIRA', 'ALVES', 'PEREIRA', 'LIMA',
                'GOMES', 'COSTA', 'RIBEIRO', 'MARTINS', 'CARVALHO', 'ALMEIDA', 'LOPES', 'SOARES', 'FERNANDES',
                'VIEIRA', 'BARBOSA', 'ROCHA', 'DIAS', 'MONTEIRO', 'MENDES', 'RAMOS', 'MOREIRA', 'ARAUJO',
                'MARIANO', 'NUNES', 'NETO', 'JUNIOR', 'FILHO', 'PETRAROLLI', 'TASSINARI'
            ]
            
            linhas = texto.split('\n')
            linhas_corrigidas = []
            
            for linha in linhas:
                linha_corrigida = linha
                
                # Procurar por sequências de nomes emendados
                for nome in nomes_comuns:
                    if len(nome) >= 4:  # Só processar nomes com 4+ letras
                        # Padrão: NOMESOBRENOME -> NOME SOBRENOME
                        # Ex: BRUNOPETRAROLLI -> BRUNO PETRAROLLI
                        padrao = rf'\b([A-Z]+?)({nome})([A-Z]+?)\b'
                        
                        def separar_nome(match):
                            inicio = match.group(1)
                            meio = match.group(2)
                            fim = match.group(3)
                            
                            # Só separar se início tem pelo menos 3 letras e fim tem pelo menos 2
                            if len(inicio) >= 3 and len(fim) >= 2:
                                return f"{inicio} {meio} {fim}"
                            else:
                                return match.group(0)  # Retornar original se não faz sentido
                        
                        linha_corrigida = re.sub(padrao, separar_nome, linha_corrigida)
                
                # Padrões específicos para casos comuns
                # Ex: MARIANOSS -> MARIANO SS
                linha_corrigida = re.sub(r'([A-Z]{6,})([A-Z]{2})\b', r'\1 \2', linha_corrigida)
                
                # Ex: BRUNOPETRAROLLI -> BRUNO PETRAROLLI (nomes longos)
                # Detectar sequências muito longas e tentar quebrar em pontos lógicos
                palavras = linha_corrigida.split()
                palavras_corrigidas = []
                
                for palavra in palavras:
                    if len(palavra) > 12 and palavra.isupper():  # Palavra muito longa em maiúsculas
                        # Tentar quebrar em nomes conhecidos
                        palavra_quebrada = self._quebrar_palavra_longa(palavra, nomes_comuns)
                        palavras_corrigidas.append(palavra_quebrada)
                    else:
                        palavras_corrigidas.append(palavra)
                
                linha_corrigida = ' '.join(palavras_corrigidas)
                linhas_corrigidas.append(linha_corrigida)
            
            texto_corrigido = '\n'.join(linhas_corrigidas)
            
            # Log se houve correções
            if texto_corrigido != texto:
                print("🇧🇷 Nomes brasileiros corrigidos:")
                linhas_orig = texto.split('\n')
                linhas_corr = texto_corrigido.split('\n')
                
                for i, (orig, corr) in enumerate(zip(linhas_orig, linhas_corr)):
                    if orig != corr:
                        print(f"   '{orig}' → '{corr}'")
            
            return texto_corrigido
            
        except Exception as e:
            print(f"⚠️ Erro na correção de nomes: {e}")
            return texto
    
    def _quebrar_palavra_longa(self, palavra: str, nomes_comuns: list) -> str:
        """
        Quebra uma palavra muito longa em nomes menores
        
        Args:
            palavra: Palavra longa (ex: "BRUNOPETRAROLLIMARIANOS")
            nomes_comuns: Lista de nomes conhecidos
            
        Returns:
            Palavra quebrada (ex: "BRUNO PETRAROLLI MARIANO S")
        """
        try:
            if len(palavra) <= 12:
                return palavra
            
            # Tentar encontrar combinações de nomes dentro da palavra
            melhor_quebra = palavra
            melhor_score = 0
            
            # Testar diferentes pontos de quebra
            for i in range(3, len(palavra) - 2):
                for j in range(i + 3, len(palavra) - 1):
                    parte1 = palavra[:i]
                    parte2 = palavra[i:j] 
                    parte3 = palavra[j:]
                    
                    # Contar quantas partes são nomes conhecidos
                    score = 0
                    if parte1 in nomes_comuns: score += 3
                    if parte2 in nomes_comuns: score += 3  
                    if parte3 in nomes_comuns: score += 3
                    
                    # Bonus por tamanhos razoáveis
                    if 3 <= len(parte1) <= 10: score += 1
                    if 3 <= len(parte2) <= 10: score += 1
                    if 2 <= len(parte3) <= 10: score += 1
                    
                    if score > melhor_score:
                        melhor_score = score
                        melhor_quebra = f"{parte1} {parte2} {parte3}"
            
            # Se não encontrou boa quebra, tentar quebra simples no meio
            if melhor_score == 0 and len(palavra) > 15:
                meio = len(palavra) // 2
                # Procurar uma vogal próxima ao meio para quebrar
                for offset in range(-2, 3):
                    pos = meio + offset
                    if 0 < pos < len(palavra) - 1:
                        if palavra[pos].lower() in 'aeiou':
                            melhor_quebra = f"{palavra[:pos]} {palavra[pos:]}"
                            break
            
            return melhor_quebra
            
        except Exception:
            return palavra
    
    def _processar_texto_ocr(self, texto: str, resultado: ResultadoOAB) -> ResultadoOAB:
        """
        Processa o texto extraído do OCR e preenche o resultado
        
        Args:
            texto: Texto extraído do OCR
            resultado: Objeto ResultadoOAB
            
        Returns:
            ResultadoOAB atualizado
        """
        try:
            print("🔍 Processando texto do OCR...")
            
            # Usar o ModalExtractorOCR adaptado
            extrator = ModalExtractorOCR()
            
            # Nome completo (melhorar se necessário)
            nome_melhorado = extrator.extrair_nome_completo(texto)
            if nome_melhorado and len(nome_melhorado) > len(resultado.nome):
                resultado.nome = nome_melhorado
                print(f"✅ Nome atualizado: {resultado.nome}")
            
            # Inscrição
            inscricao_modal = extrator.extrair_inscricao(texto, resultado.inscricao)
            if inscricao_modal:
                resultado.numero_carteira = inscricao_modal
                print(f"✅ Número carteira: {resultado.numero_carteira}")
            
            # ✅ CORREÇÃO: Separar telefone e endereço adequadamente
            # Telefones PRIMEIRO
            telefones = extrator.extrair_telefones(texto)
            if telefones:
                resultado.telefone = telefones
                print(f"✅ Telefones: {resultado.telefone}")
            
            # Endereço SEM telefone
            endereco_prof = extrator.extrair_endereco_profissional(texto)
            if endereco_prof:
                resultado.endereco = endereco_prof
                print(f"✅ Endereço profissional: {resultado.endereco}")
            
            # Seccional (adicionar ao endereço se necessário)
            seccional = extrator.extrair_seccional(texto, resultado.estado)
            if seccional and seccional != resultado.estado.upper():
                if resultado.endereco:
                    resultado.endereco = f"Seccional: {seccional} | {resultado.endereco}"
                else:
                    resultado.endereco = f"Seccional: {seccional}"
                print(f"✅ Seccional: {seccional}")
            
            # Subseção (adicionar ao endereço se necessário)
            subsecao = extrator.extrair_subsecao(texto)
            if subsecao:
                if resultado.endereco:
                    resultado.endereco = f"{resultado.endereco} | Subseção: {subsecao}"
                else:
                    resultado.endereco = f"Subseção: {subsecao}"
                print(f"✅ Subseção: {subsecao}")
            
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
        """Salva a imagem para debug"""
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
        """Salva o texto extraído para debug"""
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
                    f.write(f"Carteira: {resultado.numero_carteira}\n")
                    f.write(f"Data Inscrição: {resultado.data_inscricao}\n")
                
                print(f"📄 Texto OCR salvo: {os.path.basename(caminho)}")
        except Exception as e:
            print(f"⚠️ Erro ao salvar texto OCR: {e}")
    
    def _fechar_modal(self):
        """Fecha a modal de detalhes"""
        try:
            # Buscar botões de fechar
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
    """Classe para extração de dados do texto extraído via OCR - VERSÃO CORRIGIDA"""
    
    def extrair_nome_completo(self, texto_ocr: str) -> str:
        """Extrai nome completo do texto OCR"""
        padroes_nome = [
            # Nome em linha separada (comum em OCR)
            r'^([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ][A-Za-záéíóúàèìòùâêîôûãõçñ\s]{8,60})$',
            # Nome após algum identificador
            r'Nome[:\s]*([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ][A-Za-záéíóúàèìòùâêîôûãõçñ\s]{5,60})',
            # Padrão específico para OCR - nome em maiúsculas
            r'([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ]{2,}(?:\s+[A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ]{2,})+)',
        ]
        
        linhas = texto_ocr.split('\n')
        
        # Buscar nas primeiras linhas (onde geralmente está o nome)
        for linha in linhas[:5]:
            linha = linha.strip()
            for padrao in padroes_nome:
                match = re.search(padrao, linha, re.MULTILINE)
                if match:
                    nome = match.group(1).strip()
                    
                    # Validações específicas para OCR
                    if (8 <= len(nome) <= 60 and 
                        ' ' in nome and 
                        len(nome.split()) >= 2 and
                        not any(palavra in nome.upper() for palavra in 
                               ['INSCRICAO', 'SECCIONAL', 'TELEFONE', 'ENDERECO', 'ADVOGADO', 'SITUACAO']) and
                        all(char.isalpha() or char.isspace() or char in 'ÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ' 
                            for char in nome)):
                        return nome
        
        return ""

    def extrair_inscricao(self, texto_ocr: str, inscricao_original: str) -> str:
        """Extrai número da inscrição do texto OCR"""
        padroes_inscricao = [
            r'Inscri[cç][aã]o[:\s]*(\d{4,8})',
            r'N[uú]mero[:\s]*(\d{4,8})',
            r'Inscri[cç][aã]o\s+(\d{4,8})',
            # Buscar a inscrição original no texto
            rf'({re.escape(inscricao_original)})',
        ]
        
        for padrao in padroes_inscricao:
            match = re.search(padrao, texto_ocr, re.IGNORECASE)
            if match:
                numero = match.group(1)
                if numero.isdigit() and 4 <= len(numero) <= 8:
                    return numero
        
        return inscricao_original

    def extrair_seccional(self, texto_ocr: str, estado_original: str) -> str:
        """Extrai seccional do texto OCR"""
        padroes_seccional = [
            r'Seccional[:\s]*([A-Z]{2})',
            r'Seccional\s+([A-Z]{2})',
            r'UF[:\s]*([A-Z]{2})',
            # Buscar estado original
            rf'({re.escape(estado_original.upper())})',
        ]
        
        for padrao in padroes_seccional:
            match = re.search(padrao, texto_ocr, re.IGNORECASE)
            if match:
                seccional = match.group(1).upper()
                if len(seccional) == 2 and seccional.isalpha():
                    return seccional
        
        return estado_original.upper()

    def extrair_subsecao(self, texto_ocr: str) -> str:
        """Extrai subseção do texto OCR"""
        padroes_subsecao = [
            r'Subse[cç][aã]o[:\s]*([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ][A-Za-záéíóúàèìòùâêîôûãõçñ\s]+?)(?:\n|$)',
            r'Subse[cç][aã]o\s+([A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑ\s]+)',
            # Padrões específicos para cidades conhecidas
            r'(PRESIDENTE\s+PRUDENTE|SAO\s+PAULO|RIO\s+DE\s+JANEIRO|BELO\s+HORIZONTE|PRESIDENTE\s+VENCESLAU)',
        ]
        
        for padrao in padroes_subsecao:
            match = re.search(padrao, texto_ocr, re.IGNORECASE)
            if match:
                subsecao = match.group(1).strip()
                
                if (5 <= len(subsecao) <= 50 and
                    not any(palavra in subsecao.upper() for palavra in 
                           ['TELEFONE', 'EMAIL', 'ENDERECO', 'SITUACAO'])):
                    return subsecao
        
        return ""

    def extrair_endereco_profissional(self, texto_ocr: str) -> str:
        """
        ✅ CORREÇÃO: Extrai endereço profissional LIMPO (sem telefone)
        """
        try:
            # Procurar por padrões de endereço
            padroes_endereco = [
                # Endereço após "Endereço Profissional"
                r'Endere[cç]o\s+Profissional[:\s]*([^\n]+?)(?:Telefone|$)',
                r'Endere[cç]o[:\s]*([^\n]+?)(?:Telefone|$)',
                # Padrão direto de endereço (RUA, AVENIDA, etc.)
                r'(RUA\s+[^,\n]+(?:,\s*N[°º]?\s*\d+)?[^,\n]*(?:,\s*[^,\n]+)*)',
                r'(AVENIDA\s+[^,\n]+(?:,\s*N[°º]?\s*\d+)?[^,\n]*(?:,\s*[^,\n]+)*)',
                r'(ALAMEDA\s+[^,\n]+(?:,\s*N[°º]?\s*\d+)?[^,\n]*(?:,\s*[^,\n]+)*)',
            ]
            
            for padrao in padroes_endereco:
                match = re.search(padrao, texto_ocr, re.IGNORECASE)
                if match:
                    endereco = match.group(1).strip()
                    
                    # ✅ LIMPAR telefones do endereço
                    endereco = self._limpar_telefones_do_endereco(endereco)
                    
                    # ✅ LIMPAR situação do endereço
                    endereco = self._limpar_situacao_do_endereco(endereco)
                    
                    # Verificar se ainda é um endereço válido
                    if 10 <= len(endereco) <= 200 and any(palavra in endereco.upper() for palavra in ['RUA', 'AVENIDA', 'ALAMEDA', 'CENTRO', 'SP', 'CEP']):
                        return self._formatar_endereco(endereco)
            
            # Se não encontrou nada específico, buscar por "Não informado"
            if re.search(r'(N[aã]o\s+informado)', texto_ocr, re.IGNORECASE):
                return "Não informado"
            
            return ""
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair endereço: {e}")
            return ""
    
    def _limpar_telefones_do_endereco(self, endereco: str) -> str:
        """Remove telefones do endereço"""
        # Padrões de telefone para remover
        padroes_telefone = [
            r'Telefone\s*Profissional[:\s]*\([0-9\s\)\(-]+',
            r'Telefone[:\s]*\([0-9\s\)\(-]+',
            r'\(\d{2}\)\s*\d{4,5}[-\s]?\d{4}',
            r'\d{2}\s+\d{4,5}[-\s]?\d{4}',
            r'TelefoneProfissional[:\s]*\([0-9\s\)\(-]+',
        ]
        
        for padrao in padroes_telefone:
            endereco = re.sub(padrao, '', endereco, flags=re.IGNORECASE)
        
        return endereco.strip()
    
    def _limpar_situacao_do_endereco(self, endereco: str) -> str:
        """Remove informações de situação do endereço"""
        padroes_situacao = [
            r':SITUACAOREGULAR:?',
            r'SITUACAO\s*REGULAR',
            r'SITUACAO[:\s]*REGULAR',
            r':SITUACAO[:\s]*',
        ]
        
        for padrao in padroes_situacao:
            endereco = re.sub(padrao, '', endereco, flags=re.IGNORECASE)
        
        return endereco.strip()
    
    def _formatar_endereco(self, endereco: str) -> str:
        """Formata o endereço de forma mais legível"""
        # Corrigir espaçamentos
        endereco = re.sub(r'\s+', ' ', endereco)
        
        # Adicionar vírgulas onde necessário
        endereco = re.sub(r'(N[°º]?\s*\d+)', r', \1, ', endereco)
        endereco = re.sub(r'\s*,\s*,\s*', ', ', endereco)  # Remover vírgulas duplas
        
        # Corrigir alguns padrões comuns
        endereco = re.sub(r'\.N(\d+)', r', N° \1', endereco)
        endereco = re.sub(r'(\d{5})(\d{3})', r'\1-\2', endereco)  # Formato CEP
        
        return endereco.strip()

    def extrair_telefones(self, texto_ocr: str) -> str:
        """
        ✅ CORREÇÃO: Extrai APENAS telefones de forma mais precisa
        """
        telefones_encontrados = []
        
        try:
            # Padrões específicos para telefones
            padroes_telefone = [
                # Telefone com identificação
                r'Telefone\s*Profissional[:\s]*\((\d{2})\)\s*(\d{4,5})[-\s]?(\d{4})',
                r'Telefone[:\s]*\((\d{2})\)\s*(\d{4,5})[-\s]?(\d{4})',
                r'TelefoneProfissional[:\s]*\((\d{2})\)\s*(\d{4,5})[-\s]?(\d{4})',
                
                # Padrões numéricos diretos
                r'\((\d{2})\)\s*(\d{4,5})[-\s]?(\d{4})',
                r'(\d{2})\s+(\d{4,5})[-\s]?(\d{4})',
                
                # Caso especial das imagens: telefone "colado"
                r'TelefoneProfissional\s*\((\d{2})\)(\d{4,5})\s*(\d{4})',
            ]
            
            for padrao in padroes_telefone:
                matches = re.finditer(padrao, texto_ocr, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) == 3:  # DDD + número + final
                        ddd, num1, num2 = match.groups()
                        telefone = f"({ddd}) {num1}-{num2}"
                        
                        # Validar se é um telefone válido
                        if (len(ddd) == 2 and ddd.isdigit() and 
                            len(num1) in [4, 5] and num1.isdigit() and 
                            len(num2) == 4 and num2.isdigit()):
                            
                            if telefone not in telefones_encontrados:
                                telefones_encontrados.append(telefone)
                                print(f"📞 Telefone extraído: {telefone}")
            
            # Verificar se há indicação de "não informado"
            if not telefones_encontrados:
                padroes_nao_informado = [
                    r'Telefone[:\s]*N[aã]o\s+informado',
                    r'N[aã]o\s+informado.*telefone',
                ]
                
                for padrao in padroes_nao_informado:
                    if re.search(padrao, texto_ocr, re.IGNORECASE):
                        return "Não informado"
            
            return " | ".join(telefones_encontrados) if telefones_encontrados else ""
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair telefones: {e}")
            return ""

    def extrair_situacao(self, texto_ocr: str) -> str:
        """Extrai situação do advogado do texto OCR"""
        padroes_situacao = [
            r'SITUA[CÇ][AÃ]O\s+REGULAR',
            r'REGULAR',
            r'SITUA[CÇ][AÃ]O[:\s]*([A-Z\s]+)',
            r'Situa[cç][aã]o[:\s]*([A-Za-z\s]+)',
            r'(ATIVO|ATIVA|LICENCIADO|LICENCIADA)',
        ]
        
        for padrao in padroes_situacao:
            match = re.search(padrao, texto_ocr, re.IGNORECASE)
            if match:
                if padrao in [r'SITUA[CÇ][AÃ]O\s+REGULAR', r'REGULAR']:
                    return 'SITUAÇÃO REGULAR'
                
                situacao = match.group(1) if match.groups() else match.group(0)
                situacao = situacao.strip().upper()
                
                # Padronizar situações conhecidas
                if 'REGULAR' in situacao:
                    return 'SITUAÇÃO REGULAR'
                elif situacao in ['ATIVO', 'ATIVA']:
                    return 'ATIVO'
                elif 'LICENCIAD' in situacao:
                    return 'LICENCIADO'
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
                
                # Validação de email
                if ('@' in email and '.' in email and 
                    5 <= len(email) <= 100 and
                    not any(char in email for char in [' ', '\n', '\t'])):
                    return email
        
        return ""

    def fechar_modal_imagem(self):
        """Fecha qualquer modal de imagem que possa estar aberto"""
        try:
            # Tenta fechar modal por botão de fechar
            botao_fechar = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "close"))
            )
            botao_fechar.click()
            self.logger.info("Modal fechado com sucesso")
            
            # Aguarda modal desaparecer
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "modal"))
            )
            
        except Exception as e:
            self.logger.warning(f"Não foi possível fechar modal: {e}")
            
        return


# Manter a classe original para compatibilidade
class ModalExtractorGenerico(DataExtractor):
    """Alias para compatibilidade com código existente"""
    pass
    """Classe mantida para compatibilidade - herda de ModalExtractorOCR"""
    pass