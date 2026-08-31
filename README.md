# Community Center API - Documentação e automação de testes

Projeto de testes funcionais e automação para a **Community Center API**.

---

## Estrutura do Projeto

```text
├── performance/                               # Testes de Carga e Performance (Locust)
│   ├── locustfile.py
│   └── GUIA_TESTES_PERFORMANCE.md
├── postman/                                   # Collection e Environment Postman
│   ├── Community_Center_API.postman_collection.json
│   └── Community_Center_Env.postman_environment.json
├── swagger.yml                                # Documentação OpenAPI 3.0
├── requirements.txt                           # Dependências do projeto de automação Python
└── tests/                                     # Automação completa em Python / pytest
    ├── __init__.py
    ├── conftest.py                            # Fixtures de sessão, URLs e teardown automático
    ├── test_01_create_community_center.py     # Testes para criação de centros (12 cenários)
    ├── test_02_exchange_resources.py          # Testes para intercâmbio e regra dos 90% (10 cenários)
    ├── test_03_reports.py                     # Testes para relatórios de ocupação, médias e histórico (16 cenários)
    └── test_04_occupancy_and_delete.py        # Testes para atualização de ocupação, deleção e listagem (11 cenários)
```

---

## Como Executar os Testes Automatizados (Python / pytest)

### 1. Pré-requisitos
- Python 3.8+ instalado (`python3`)
- `python3-pip` e `python3-venv` (no Linux/Ubuntu/Mint: `sudo apt install python3-pip python3-venv`)

### 2. Criar ambiente virtual e instalar dependências
Recomenda-se criar um ambiente virtual para isolar as dependências do projeto:

```bash
# Criar e ativar o ambiente virtual (Linux/macOS)
python3 -m venv .venv
source .venv/bin/activate

# Instalar as dependências
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente (`API_KEY` e `BASE_URL`)
Você pode configurar as variáveis criando um arquivo `.env` na raiz do projeto (recomendado) ou exportando no ambiente:

- **Opção A (Arquivo `.env` - Recomendado):**
  Copie o arquivo de exemplo e preencha as variáveis:
  ```bash
  cp .env.example .env
  ```
  Conteúdo do `.env`:
  ```env
  API_KEY=SUA_API_KEY_AQUI
  BASE_URL=https://api-url.example.com
  ```

- **Opção B (Variáveis de ambiente no terminal):**
  ```bash
  export API_KEY="SUA_API_KEY_AQUI"
  export BASE_URL="https://api-url.example.com"
  ```

### 4. Executar os testes

- **Executar todos os testes:**
  ```bash
  pytest tests/ -v
  ```

- **Executar um módulo específico:**
  ```bash
  pytest tests/test_01_create_community_center.py -v
  pytest tests/test_02_exchange_resources.py -v
  pytest tests/test_03_reports.py -v
  pytest tests/test_04_occupancy_and_delete.py -v
  ```

- **Gerar relatório HTML de execução:**
  ```bash
  pip install pytest-html
  pytest tests/ -v --html=relatorio_testes.html --self-contained-html
  ```

---

## Como Importar e Executar a Collection no Postman

O projeto já possui uma collection completa e arquivo de variáveis de ambiente prontos para uso no diretório `postman/`:
- `postman/Community_Center_API.postman_collection.json`
- `postman/Community_Center_Env.postman_environment.json`

### Passo a passo para importar no Postman:
1. Abra o **Postman**.
2. Clique no botão **Import** (canto superior esquerdo).
3. Selecione ou arraste os dois arquivos da pasta `postman/`.
4. No canto superior direito do Postman, selecione o ambiente **"Community Center API - Environment"**.
5. Edite o ambiente para colocar a sua **`apiKey`** real no valor inicial/atual.
6. Para rodar todos os testes em sequência automática:
   - Clique com o botão direito na Collection importada -> **Run Collection** (ou via Newman: `npx newman run postman/Community_Center_API.postman_collection.json -e postman/Community_Center_Env.postman_environment.json`).

---

## Testes de Performance e Carga (Locust)

O projeto inclui suíte completa de **testes não funcionais** utilizando o framework **Locust** na pasta `performance/`.

### 1. Executar com Interface Web Gráfica (Recomendado):
```bash
locust -f performance/locustfile.py --host https://cj98hakmf0.execute-api.us-east-1.amazonaws.com/phoebus-apps
```
Acesse **`http://localhost:8089`** no navegador para configurar usuários virtuais e acompanhar gráficos em tempo real de RPS, latência (p95/p99) e taxa de falhas.

### 2. Executar em modo Linha de Comando (CI/CD - Headless):
```bash
# Executa 10 usuários virtuais por 30 segundos gerando relatório HTML
locust -f performance/locustfile.py --headless -u 10 -r 2 -t 30s \
  --host https://cj98hakmf0.execute-api.us-east-1.amazonaws.com/phoebus-apps \
  --html performance/relatorio_performance.html
```

---

## Cobertura dos Cenários de Teste

- **Cadastro de Centros (`POST /communityCenter`):** Casos felizes, campos obrigatórios, regras de capacidade e validação de recursos negativos.
- **Intercâmbio de Recursos (`PUT /communityCenter/exchange`):** Trocas equilibradas por tabela de pontos, rejeição de trocas desbalanceadas e exceção da regra dos >90% de ocupação.
- **Relatórios (`GET`):** Centros com ocupação >90%, cálculo de médias e consulta de histórico por range de datas (`YYYYMMDDHHmmss`).
- **Ocupação e Deleção (`PUT` e `DELETE`):** Atualização de lotação (inclusive limite e zero), exclusão e verificação de idempotência (404 após remoção).
- **Performance e Carga (Locust):** Concorrência, vazão (RPS), percentis de resposta e validação de SLAs.
