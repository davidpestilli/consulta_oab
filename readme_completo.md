# 🤖 Sistema Integrado Bot OAB + Supabase

## 📋 Visão Geral

Sistema automatizado que:
1. **Conecta** ao banco Supabase
2. **Busca** registros com `nome_procurador` vazio na tabela `erros_processados`
3. **Extrai** número OAB da coluna `usuario`
4. **Consulta** nome do advogado no site da OAB
5. **Atualiza** o banco com o nome encontrado
6. **Processa** continuamente até não haver mais registros pendentes

## 🚀 Início Rápido

### 1. Execução Automática (Recomendado)
```bash
python main.py --auto
```

### 2. Execução com Menu Interativo
```bash
python main.py
```

### 3. Execução Direta
```bash
python run_supabase_integration.py
```

## 📦 Instalação

### Dependências Python
```bash
pip install supabase requests selenium pillow pytesseract
```

### Tesseract OCR
- **Windows**: [Download oficial](https://github.com/UB-Mannheim/tesseract/wiki)
- **Linux**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`

### ChromeDriver
- [Download](https://chromedriver.chromium.org/)
- Adicionar ao PATH do sistema

## 📁 Estrutura do Projeto

```
projeto/
├── main.py                         # 🎯 ARQUIVO PRINCIPAL
├── config.py                       # ⚙️ Configurações
├── bot_oab_supabase.py             # 🤖 Sistema integrado
├── run_supabase_integration.py     # 📱 Menu interativo
├── run_bot.py                      # 🔧 Bot original
├── bot_oab/                        # 📚 Módulos do bot
│   ├── core/bot_oab_core.py
│   ├── models/resultado_oab.py
│   ├── extractors/data_extractors.py
│   ├── utils/data_exporters.py
│   └── config/browser_config.py
├── logs/                           # 📄 Logs do sistema
├── Pesquisa/                       # 💾 Resultados salvos
└── debug/                          # 🐛 Arquivos de debug
```

## 🎯 Modos de Execução

### 1. Modo Produção (Padrão)
```bash
python main.py --auto
```
- Execução sem interface gráfica
- Otimizado para velocidade
- Processamento em lotes grandes
- Logs detalhados

### 2. Modo Desenvolvimento
```bash
python main.py
# Escolher opção 2 no menu
```
- Interface gráfica visível
- Timeouts maiores
- Lotes menores para debug
- Salvamento frequente

### 3. Modo Personalizado
```bash
python main.py
# Escolher opção 3 no menu
```
- Configurações padrão
- Balanceado entre velocidade e debug

## 📊 Funcionalidades Principais

### 🔄 Processamento Automático
- Busca automática de registros pendentes
- Processamento em lotes otimizados
- Salvamento automático de progresso
- Recuperação de erros

### 📋 Verificação de Status
- Contagem de registros totais
- Registros pendentes
- Registros preenchidos
- Registros com erro
- Taxa de preenchimento

### 🎯 Processamento Específico
- Processar registro por ID
- Processar lote específico
- Reprocessar registros com erro

### 📄 Relatórios e Logs
- Logs detalhados em tempo real
- Estatísticas completas
- Resultados salvos em JSON
- Histórico de processamentos

## 🔧 Configurações

### Principais Configurações (config.py)
```python
# Timeouts
TIMEOUT_NAVEGADOR = 15          # Timeout do navegador
INTERVALO_CONSULTAS = 2         # Pausa entre consultas

# Processamento
TAMANHO_LOTE = 50              # Registros por lote
SALVAR_INTERMEDIARIO_A_CADA = 10  # Salvar a cada X registros

# Modo de execução
HEADLESS_MODE = True           # Sem interface gráfica
```

### Configurações do Supabase
```python
SUPABASE_URL = "https://rdkvvigjmowtvhxqlrnp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
TABELA_ERROS = "erros_processados"
```

## 📈 Exemplo de Execução

```bash
$ python main.py --auto

🚀 Sistema Integrado Bot OAB + Supabase v2.0
============================================================
📅 Iniciado em: 09/07/2025 14:30:15
🔗 Conectando ao Supabase...
🤖 Inicializando Bot OAB...
📊 Verificando status da tabela...

📈 Status da tabela:
   Total: 1250
   Pendentes: 347
   Preenchidos: 856
   Erros: 47
   Taxa preenchimento: 68.5%

🔄 LOTE 1
========================================
📊 Progresso: 1/50
🔄 Registro 1001: 147520/SP
🔍 Consultando OAB 147520/SP
✅ Sucesso: JOÃO DA SILVA SANTOS
💾 Atualizando registro 1001 com nome: JOÃO DA SILVA SANTOS

📊 Progresso: 2/50
🔄 Registro 1002: 234567/RJ
🔍 Consultando OAB 234567/RJ
✅ Sucesso: MARIA OLIVEIRA COSTA
💾 Atualizando registro 1002 com nome: MARIA OLIVEIRA COSTA

[... processamento continua ...]

🎯 ESTATÍSTICAS FINAIS:
============================================================
📊 Lotes processados: 7
📋 Total de registros: 347
✅ Sucessos: 312
❌ Erros: 35
📈 Taxa de sucesso: 89.9%
⏱️ Tempo total: 28m 45.2s
⚡ Tempo médio por registro: 4.9s
📄 Log completo: logs/processamento_20250709_143015.log
```

## 🛠️ Tratamento de Erros

### Tipos de Erro Identificados
1. **OAB não encontrada** → `"ERRO: Inscrição não encontrada"`
2. **Formato inválido** → `"ERRO: OAB não encontrada em: [texto]"`
3. **Conexão falhou** → `"ERRO: Erro de conexão: [detalhes]"`
4. **Timeout** → `"ERRO: Timeout na consulta"`

### Recuperação Automática
- Registros com erro podem ser reprocessados
- Sistema pula registros já processados
- Progresso é salvo continuamente

## 📊 Padrões de OAB Reconhecidos

**PADRÃO REAL DO BANCO** (baseado na imagem fornecida):

```
✅ FORMATOS VÁLIDOS (serão processados):
- "SP388221" → OAB 388221/SP
- "RJ123456" → OAB 123456/RJ  
- "MG987654" → OAB 987654/MG
- "PR456789" → OAB 456789/PR
- "SC12345"  → OAB 12345/SC

❌ FORMATOS INVÁLIDOS (serão ignorados):
- "M356437"  → Matrícula funcionário TJSP
- "123456"   → Número sem estado
- "ABC123"   → Estado inválido
- "SP123"    → Número muito curto (< 4 dígitos)
- "SP123456789" → Número muito longo (> 8 dígitos)
- "SP123ABC" → Contém letras no número
- "sp388221" → Minúsculo (deve ser maiúsculo)
- "SP 388221" → Com espaço
- "SP-388221" → Com hífen ou barra
```

### 🔍 Validação Automática

O sistema implementa **filtragem inteligente**:

1. **Busca** todos os registros com `nome_procurador` vazio
2. **Filtra** apenas os que seguem o padrão: `[ESTADO][NÚMERO]`
3. **Ignora** matrículas, números sem estado, formatos inválidos
4. **Processa** apenas OABs válidas

### 📈 Exemplo de Filtragem

```bash
📋 Total de registros vazios: 1250
✅ Registros válidos para processar: 847
⚠️ Registros inválidos (ignorados): 403
💡 Registros inválidos incluem: matrículas (M356437), números sem estado, etc.
```

## 🔍 Validação de Dados

### Validação de Número OAB
- 4 a 8 dígitos
- Apenas números
- Estados brasileiros válidos

### Validação de Nome
- Mínimo 5 caracteres
- Máximo 100 caracteres
- Deve conter espaço (nome + sobrenome)
- Não deve conter números
- Não deve conter palavras inválidas

## 📄 Logs e Relatórios

### Arquivo de Log
```
logs/processamento_20250709_143015.log
```

### Conteúdo do Log
```
[14:30:15] Sistema Integrado Bot OAB + Supabase
[14:30:15] Iniciado em: 09/07/2025 14:30:15
[14:30:16] Conexão Supabase estabelecida
[14:30:17] Bot OAB inicializado
[14:30:18] Status tabela: {"total": 1250, "pendentes": 347, ...}
[14:30:20] Iniciando processamento de lote (limite: 50)
[14:30:25] Processando registro 1001: 147520/SP
[14:30:30] SUCESSO: Registro 1001 processado
```

### Arquivo de Resultados
```json
{
  "timestamp": "09/07/2025 15:15:30",
  "estatisticas": {
    "lotes_processados": 7,
    "total_registros": 347,
    "total_sucessos": 312,
    "total_erros": 35,
    "tempo_total": 1725.2,
    "taxa_sucesso": 89.9
  },
  "status_inicial": {
    "total": 1250,
    "pendentes": 347,
    "preenchidos": 856,
    "erros": 47
  },
  "status_final": {
    "total": 1250,
    "pendentes": 35,
    "preenchidos": 1168,
    "erros": 82
  }
}
```

## 🚨 Solução de Problemas

### Erro: "ChromeDriver não encontrado"
```bash
# Verificar se está no PATH
chromedriver --version

# Ou baixar e adicionar ao PATH
```

### Erro: "Tesseract não encontrado"
```bash
# Linux
sudo apt-get install tesseract-ocr

# Windows: baixar e instalar
# macOS
brew install tesseract
```

### Erro: "Conexão com Supabase falhou"
1. Verificar credenciais no `config.py`
2. Verificar conexão com internet
3. Verificar políticas RLS da tabela

### Taxa de Sucesso Baixa
1. Verificar formato dos dados na coluna `usuario`
2. Aumentar `TIMEOUT_NAVEGADOR` no config
3. Aumentar `INTERVALO_CONSULTAS` para evitar bloqueios

## 🔒 Segurança

- ✅ Conexão HTTPS com Supabase
- ✅ Credenciais não expostas em logs
- ✅ Simulação de comportamento humano
- ✅ Rate limiting entre consultas
- ✅ Validação rigorosa de dados

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar logs na pasta `logs/`
2. Executar teste de conexão: `python main.py` → opção 6
3. Verificar configurações no `config.py`
4. Consultar documentação do Selenium/Supabase

## 🎯 Próximos Passos

Após a primeira execução bem-sucedida:
1. Configurar execução automática via cron/task scheduler
2. Implementar notificações por email
3. Criar dashboard web para monitoramento
4. Otimizar performance com processamento paralelo