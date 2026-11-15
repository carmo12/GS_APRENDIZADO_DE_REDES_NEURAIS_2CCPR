# Roubo ou furto? Classificação de ocorrências em São Paulo com MLP

**Global Solution — Aprendizado Profundo com Redes Neurais Convolucionais**
Segurança pública inteligente em São Paulo · classificação de ocorrências com MLP

## 🔗 Aplicação web

**https://carmo12.github.io/gs-mlp-roubo-furto-sp/**

Você escolhe região, bairro, tipo de local, período, dia da semana e marca do celular, e a MLP devolve a classe estimada
(**roubo** ou **furto**) com as probabilidades de cada uma. A página roda inteira no navegador, com os pesos da rede treinada.
Se o link ainda não estiver no ar, siga a seção [Publicar a aplicação](#publicar-a-aplicação-github-pages) ou abra `docs/index.html` direto no navegador.

## Integrantes

| Nome | RM |
|---|---|
| João Carmo Cassu de Castro | 567030 |
| Luiz Gustavo de Almeida | 566613 |

## Objetivo

Treinar, comparar e selecionar uma **Multilayer Perceptron (MLP)** que, a partir das características de uma subtração de celular
**já registrada ou hipotética** na capital paulista, estime se ela é mais compatível com **roubo** (art. 157) ou com **furto** (art. 155).

> O modelo **não** prevê se um crime vai acontecer e **não** calcula risco de um lugar ou horário. Ele estima o **tipo** de uma ocorrência dadas as suas características.
> Exemplo de leitura correta: *"considerando que uma ocorrência aconteceu em Pinheiros, em via pública, numa sexta à noite, com um iPhone, o modelo atribui 59% à classe roubo e 41% à classe furto"*.

---

## Dados

| Item | Detalhe |
|---|---|
| **Fonte pública** | Secretaria da Segurança Pública de SP (SSP-SP) — Portal de Estatísticas → **Consultas** → *Bases de Dados* → **Celulares subtraídos → 2025**: <https://www.ssp.sp.gov.br/estatistica/consultas> |
| **Arquivo** | `CelularesSubtraidos_2025.xlsx` — link direto: <https://www.ssp.sp.gov.br/assets/estatistica/transparencia/baseDados/celularesSub/CelularesSubtraidos_2025.xlsx> (≈108 MB, 383.635 linhas, 55 colunas; baixado em 15/11/2026) |
| **Período** | Fatos ocorridos em 2025 |
| **Recorte geográfico** | `NOME_MUNICIPIO_CIRC = "S.PAULO"`, o município da delegacia de **circunscrição**, ou seja, do **local do fato**. Não usamos o local de registro do BO. |
| **Rótulo** | `RUBRICA`: `Furto (art. 155)` → furto (0) · `Roubo (art. 157)` → roubo (1) |
| **Limpeza** | Um registro por BO (`NOME_DELEGACIA` + `ANO_BO` + `NUM_BO`), já que a planilha tem uma linha por objeto. Removidos os 44 BOs que tinham roubo e furto ao mesmo tempo. |
| **Tamanho** | 159.750 BOs únicos → **amostra estratificada de 20.000** (63,1% furto / 36,9% roubo) |
| **Atributos (entradas)** | `regiao` (8 seccionais), `bairro` (40 mais frequentes + "Outro"), `tipo_local`, `periodo` (madrugada/manhã/tarde/noite/incerta), `dia_semana`, `marca_celular` → **75 entradas One-Hot** |
| **Excluídos** | A própria `RUBRICA` e campos que a revelam (*data leakage*): `DESCR_CONDUTA`, `DESDOBRAMENTO`, `DESC_LEI`, `CIRCUNSTANCIA`. Também saíram campos que só existem depois do registro (autoria, flagrante, quem apresentou) e dados que localizam pessoas ou endereços exatos (logradouro, número, CEP, latitude/longitude, nº do BO). |

### Como obter e preparar os dados
1. Baixe `CelularesSubtraidos_2025.xlsx` pelo link acima e salve em `data/`. O arquivo não está no repositório porque passa do limite de 100 MB do GitHub.
2. Rode:
   ```bash
   python preparar_dados.py data/CelularesSubtraidos_2025.xlsx
   ```
   Isso gera `data/ocorrencias_sp_2025.csv`, que **já está no repositório**. O notebook roda mesmo sem a planilha original.

---

## Estrutura do repositório

```
gs-mlp-roubo-furto-sp/
├── README.md
├── requirements.txt
├── preparar_dados.py                 # recorte, rótulo, deduplicação e amostra (fonte -> CSV)
├── notebook_mlp_roubo_furto.ipynb    # exploração, pré-processamento, 4 MLPs, métricas, curvas, matriz de confusão
├── gerar_app.py                      # embute os pesos exportados na página web
├── data/
│   └── ocorrencias_sp_2025.csv       # amostra de 20.000 BOs usada no treinamento
├── modelo/
│   ├── mlp_roubo_furto.keras         # modelo treinado (Keras)
│   ├── preprocessamento.json         # categorias do One-Hot + mapa bairro→região
│   ├── resultados_validacao.csv      # comparação das 4 arquiteturas
│   └── resultado_teste.csv           # avaliação final do modelo escolhido
├── figuras/                          # gráficos gerados pelo notebook e prints da aplicação
├── app/template.html                 # código-fonte da aplicação web
├── docs/
│   ├── index.html                    # aplicação web pronta (GitHub Pages)
│   └── modelo.json                   # pesos + vocabulário exportados do Keras
└── relatorio/
    └── Relatorio_MLP_Roubo_Furto.pdf # relatório técnico (10 slides)
```

## Como executar

```bash
# 1) ambiente
python -m venv .venv
# Windows: .venv\Scripts\activate   |  Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# 2) (opcional) refazer a amostra a partir da planilha original
python preparar_dados.py data/CelularesSubtraidos_2025.xlsx

# 3) treinar e avaliar: abra e execute todas as células do notebook
jupyter notebook notebook_mlp_roubo_furto.ipynb
#    -> salva modelo/mlp_roubo_furto.keras, docs/modelo.json e gera docs/index.html

# 4) testar a aplicação localmente: abra docs/index.html no navegador (duplo clique)
```

O treinamento das 4 arquiteturas leva cerca de 1 a 2 minutos em CPU. As sementes estão fixas (`42`), então os resultados se reproduzem.

### Publicar a aplicação (GitHub Pages)
1. No GitHub, abra o repositório e vá em **Settings → Pages**.
2. Em **Build and deployment**, escolha **Source: Deploy from a branch**, **Branch: `main`** e a pasta **`/docs`**, e clique em **Save**.
3. Em 1 ou 2 minutos a página fica no ar em `https://<seu-usuario>.github.io/gs-mlp-roubo-furto-sp/`.

---

## Modelo

**Pré-processamento:** divisão estratificada de 70% para treino, 15% para validação e 15% para teste. Os agrupamentos de categorias raras e o `OneHotEncoder` são ajustados **só no treino**.
Não houve escalonamento, porque todas as entradas já são 0/1. Usamos `class_weight` (roubo pesa 1,7×) para compensar o desbalanceamento.

**Configuração comum:** camadas ocultas `Dense` com **ReLU**, saída `Dense(1, sigmoid)` = P(roubo), perda **binary cross-entropy**,
otimizador **Adam**, **batch size 64** e limiar de decisão 0,5.

### Arquiteturas comparadas (conjunto de validação)

| # | Arquitetura | Parâmetros | Épocas | Acurácia | Precision | Recall | **F1 (roubo)** | Acc. treino | Diagnóstico |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Rasa: 16, LR 0,001 | 1.233 | 30 | 0,667 | 0,539 | 0,693 | 0,606 | 0,699 | equilibrada |
| 2 | Média: 64→32 + Dropout 0,3 + EarlyStopping | 6.977 | 11 | 0,672 | 0,543 | 0,700 | 0,612 | 0,699 | equilibrada |
| 3 | Profunda: 256→128→64, sem regularização | 60.673 | 60 | 0,639 | 0,509 | 0,651 | 0,571 | 0,798 | **overfitting** (perda de validação 0,57 → 1,91) |
| 4 | **Média + Dropout 0,3 + L2 1e-4 + LR 0,0005 + EarlyStopping** ✅ | 6.977 | 15 | **0,677** | **0,550** | **0,701** | **0,616** | 0,693 | equilibrada, menor gap |

**Critério de escolha:** maior **F1 da classe roubo na validação**, porque a base é desbalanceada e um modelo que sempre dissesse "furto" teria 63% de acurácia.
O empate seria resolvido pela menor diferença entre treino e validação. O teste foi usado **uma única vez**, no modelo escolhido.

### Resultado final no teste (modelo 4)

| Acurácia | Precision (roubo) | Recall (roubo) | F1 (roubo) | F1-macro |
|---:|---:|---:|---:|---:|
| **0,684** | 0,556 | 0,723 | 0,628 | 0,677 |

Matriz de confusão (teste, 3.000 BOs): 1.252 furtos e 801 roubos corretos; 640 furtos classificados como roubo; 307 roubos classificados como furto.
Como linha de base, uma regressão logística ficou com acurácia de 0,671 e F1-macro de 0,667. A MLP é um pouco melhor no geral e empata no F1 de roubo.

### Principais conclusões
- **Transporte público** (metrô/trem/ônibus) e a região **Centro** puxam fortemente para **furto**. **Via pública na periferia**, **noite/madrugada** e **veículo em movimento** puxam para **roubo**.
- Mais neurônios **não** ajudaram: a rede profunda decorou o treino (overfitting). Dropout, L2 e EarlyStopping foram decisivos.
- O teto de cerca de 68% vem **dos atributos**: em via pública (3/4 da base) roubo e furto ficam perto de 50/50 com as mesmas características.

### Limitações
- A base é **bruta** e, segundo a própria SSP, não é estatística oficial. Há grafias diferentes, campos `NULL` e dois sistemas (R.D.O. e S.P.J.) que registram o horário de formas distintas.
- Só cobre **celulares** e depende de a vítima registrar o BO (há subnotificação).
- O modelo descreve o tipo de uma ocorrência. Ele **não** deve ser usado para prever crimes nem para decisões sobre pessoas ou lugares.
