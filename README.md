# OMIE API Project

Pipeline de engenharia de dados para extração, transformação e carga (ETL) de dados do ERP OMIE, com orquestração via Apache Airflow e persistência em PostgreSQL.

---

## Objetivo

Automatizar a coleta de dados de negócio do sistema ERP OMIE via API REST, transformar os dados brutos em registros relacionais estruturados e carregá-los em um banco de dados PostgreSQL (camada Bronze), disponibilizando-os para análises posteriores.

Os dados coletados cobrem as principais entidades do ERP: clientes, produtos, pedidos, movimentos financeiros, contas a receber, contas a pagar, notas fiscais de serviço, entre outros — totalizando **13 endpoints** configurados.

---

## Infraestrutura

| Camada | Tecnologia |
|---|---|
| Orquestração | Apache Airflow ≥ 3.2.1 (Astronomer Runtime) |
| Linguagem | Python ≥ 3.13 |
| Banco de dados | PostgreSQL (Render.com) |
| ORM / Driver | SQLAlchemy + psycopg2-binary |
| HTTP Client | Requests + urllib3 (retry automático) |
| Configuração | Pydantic Settings + python-dotenv |
| Contêiner | Docker (Astronomer Runtime 3.2-4) |
| Dependências | Poetry |
| Armazenamento em nuvem | Azure Blob Storage + Delta Lake (disponível) |
| Processamento de dados | Pandas |

---

## Como o projeto funciona

### Arquitetura geral

```
OMIE API (REST)
      │
      ▼
  API Client          ← retry automático (5x, backoff exponencial)
      │
      ▼
  Endpoint Manager    ← lê definições de src/endpoints/data/data.json
      │
      ▼
  Pagination Controller  ← estratégia per_page ou date_range
      │
      ▼
  OMIE Collector      ← orquestra coleta, filtragem e transformação
      │
      ▼
  Database Layer      ← flattening, normalização, upsert no PostgreSQL
      │
      ▼
  Tabelas bronze_*    ← PostgreSQL (Render.com)
      │
      ▼
  Apache Airflow DAG  ← agendamento horário
```

### Módulos principais

#### `src/config/settings.py`
Carrega credenciais e parâmetros de conexão via variáveis de ambiente (`.env`) usando Pydantic Settings. Centraliza `APP_KEY`, `APP_SECRET`, `BASE_URL` da API OMIE e as credenciais do banco de dados.

#### `src/api/api_reponse.py`
- **`APISession`**: gerencia sessões HTTP com retry automático — 5 tentativas, backoff de 0.5 s, ativado nos status 429, 500, 502, 503, 504.
- **`API`**: constrói o payload no formato OMIE (`call`, `app_key`, `app_secret`, `param`) e executa requisições POST.

#### `src/endpoints/endpoint.py` + `data/data.json`
Gerencia os 13 endpoints configurados, cada um com: URL do recurso, ação da API, chave de dados na resposta, estratégia de paginação e página inicial.

#### `src/controllers/pagination.py`
Duas estratégias de paginação:
- **`per_page`**: iteração página a página com rótulos configuráveis.
- **`date_range`**: iteração mês a mês a partir de uma data inicial (usada para extratos financeiros desde 01/01/2024).

#### `src/data_collector/omie_collector.py`
Classe central `OMIECollector` que:
1. Determina o número total de páginas de cada endpoint.
2. Descobre automaticamente a chave da lista de dados na resposta.
3. Remove campos da lista negra (tags, fax, recomendações, etc.).
4. Itera pelas páginas e envia os registros para o banco.

#### `src/database/database.py`
- Achata dicionários aninhados em colunas com nomenclatura `pai_filho`.
- Normaliza nomes de colunas (remove caracteres especiais, aplica lowercase).
- Cria a tabela na primeira página (`REPLACE`) e adiciona colunas dinamicamente nas páginas seguintes (`APPEND`), suportando evolução de esquema sem perda de dados.
- Adiciona metadados em todos os registros: `sistem_source = 'OMIE_API'` e `inserted_at` (timestamp da ingestão).

#### `dags/omie_pipeline.py`
DAG do Airflow com agendamento **horário**, iniciando em 09/05/2026, que executa `OMIECollector().collect_all()` como única tarefa.

### Transformação dos dados

```
JSON aninhado (resposta OMIE)
  → filtragem de campos da lista negra
  → achatamento de dicionários aninhados
  → normalização dos nomes de colunas
  → adição de metadados (source, timestamp)
  → serialização como TEXT
  → PostgreSQL (tabela bronze_<recurso>)
```

---

## Endpoints coletados

| Recurso OMIE | Ação | Estratégia | Tabela destino |
|---|---|---|---|
| `geral/clientes/` | ListarClientes | per_page | `bronze_clientes` |
| `geral/cidades/` | PesquisarCidades | per_page | `bronze_cidades` |
| `geral/categorias/` | ListarCategorias | per_page | `bronze_categorias` |
| `geral/empresas/` | ListarEmpresas | per_page | `bronze_empresas` |
| `geral/departamentos/` | ListarDepartamentos | per_page | `bronze_departamentos` |
| `geral/contacorrente/` | ListarContasCorrentes | per_page | `bronze_contacorrente` |
| `geral/produtos/` | ListarProdutos | per_page | `bronze_produtos` |
| `produtos/pedido/` | ListarPedidos | per_page | `bronze_pedidos` |
| `financas/mf/` | ListarMovimentos | per_page | `bronze_movimentos` |
| `financas/contareceber/` | ListarContasReceber | per_page | `bronze_contareceber` |
| `financas/contapagar/` | ListarContasPagar | per_page | `bronze_contapagar` |
| `financas/extrato/` | ListarExtrato | date_range (desde 01/2024) | `bronze_extrato` |
| `servicos/nfse/` | ListarNFSEs | per_page | `bronze_nfe` |

---

## Estrutura de diretórios

```
OMIEAPIProject/
├── dags/
│   └── omie_pipeline.py        # DAG do Airflow
├── src/
│   ├── api/
│   │   └── api_reponse.py      # Cliente HTTP com retry
│   ├── config/
│   │   └── settings.py         # Configurações via Pydantic
│   ├── controllers/
│   │   └── pagination.py       # Estratégias de paginação
│   ├── data_collector/
│   │   └── omie_collector.py   # Orquestrador da coleta
│   ├── database/
│   │   └── database.py         # Persistência no PostgreSQL
│   └── endpoints/
│       ├── endpoint.py
│       └── data/data.json      # Definição dos endpoints
├── main.py                     # Execução direta (sem Airflow)
├── Dockerfile                  # Astronomer Runtime
├── pyproject.toml              # Dependências (Poetry)
└── .env                        # Credenciais (não versionado)
```

---

## Como executar

### Pré-requisitos

- Python 3.13+
- Docker (para execução com Airflow)
- Astronomer CLI (`astro`)
- Credenciais OMIE (`APP_KEY`, `APP_SECRET`) e PostgreSQL no arquivo `.env`

### Variáveis de ambiente (`.env`)

```env
APP_KEY=<sua_app_key>
APP_SECRET=<seu_app_secret>
BASE_URL=https://app.omie.com.br/api/v1
DB_USER=<usuario>
DB_PASS=<senha>
DB_HOST=<host>
DB_PORT=5432
DB_NAME=<banco>
```

### Execução local (sem Airflow)

```bash
pip install poetry
poetry install
python main.py
```

### Execução com Airflow (Astronomer)

```bash
astro dev start
```

Acesse o Airflow em `http://localhost:8080` e ative a DAG `OMIE_collector_pipeline`.

---

## Resultados obtidos

- **13 tabelas Bronze** criadas e populadas automaticamente no PostgreSQL, uma por endpoint OMIE.
- **Evolução de esquema automática**: novas colunas são adicionadas dinamicamente sem recriar as tabelas nem perder dados históricos.
- **Resiliência a falhas de API**: o sistema se recupera automaticamente de erros temporários (rate limiting, indisponibilidade), sem intervenção manual.
- **Rastreabilidade total**: cada registro possui `sistem_source` e `inserted_at`, permitindo auditoria de origem e horário de ingestão.
- **Coleta histórica de extratos financeiros**: dados mensais desde janeiro de 2024 coletados via paginação por intervalo de datas.
- **Execução horária automatizada**: o pipeline roda sem intervenção via Apache Airflow, garantindo dados atualizados continuamente.
