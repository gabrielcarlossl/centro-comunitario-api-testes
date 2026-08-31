# Guia de Testes de Performance e Carga (Locust) — Community Center API

Este módulo implementa **testes não funcionais de performance, carga e estresse** para a **Community Center API**, utilizando o framework **Locust** (Python).


## Cenários Simulados no `locustfile.py`

O script simula o comportamento concorrente de múltiplos usuários virtuais distribuídos pelas seguintes operações ponderadas por peso (*weight*):

| Operação / Endpoint | Método | Peso | Finalidade |
|---|---|---|---|
| **`GET /communityCenter/highOccupation`** | `GET` | 4 (Alto) | Simula dashboards e telas de monitoramento consultando centros lotados (>90%). |
| **`GET /communityCenter/averageResources`** | `GET` | 3 (Médio) | Avalia a performance da agregação de dados e cálculo de médias no banco. |
| **`GET /communityCenter` (Paginado)** | `GET` | 3 (Médio) | Consulta listagem de centros com filtros e ordenação (`sort=-name`). |
| **`PUT /communityCenter/{id}/currentNumberOfPeople`** | `PUT` | 2 (Médio) | Simula operadores de campo atualizando a ocupação de pessoas em tempo real. |
| **`GET /communityCenter/{id}/historic`** | `GET` | 1 (Baixo) | Consulta histórica de transações com filtro por range de datas. |
| **`POST /communityCenter` + `DELETE`** | `POST/DEL` | 1 (Baixo) | Testa a vazão de escrita e exclusão mantendo o ambiente limpo. |

> **Isolamento de Dados:** Cada usuário virtual cria um centro comunitário exclusivo no `on_start` e garante a exclusão no `on_stop`, evitando poluição de dados na AWS.

---

## Executar os Testes de Carga

### Pré-requisito
Ative e instale dependências:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

### Opção 1: Modo Interativo com Interface Web (Recomendado)

Inicie o Locust apontando para o arquivo de teste:
```bash
locust -f performance/locustfile.py --host https://cj98hakmf0.execute-api.us-east-1.amazonaws.com/phoebus-apps
```

1. Abra o navegador em: **`http://localhost:8089`**
2. Configure os parâmetros do teste:
   * **Number of users:** `20` (Usuários virtuais simultâneos)
   * **Ramp-up (spawn rate):** `2` (Usuários adicionados por segundo)
3. Clique em **"Start swarming"** e acompanhe os gráficos em tempo real de:
   * **RPS (Requisições por segundo)**
   * **Tempos de resposta (Percentis: Médio, 95% e 99%)**
   * **Taxa de falhas e códigos de retorno HTTP**

---

### Opção 2: Modo Linha de Comando / CI-CD (Headless)

* **Teste de Carga Rápido (Smoke Test - 5 usuários por 30 segundos):**
  ```bash
  locust -f performance/locustfile.py --headless -u 5 -r 1 -t 30s \
    --host https://cj98hakmf0.execute-api.us-east-1.amazonaws.com/phoebus-apps
  ```

* **Teste de Estresse (20 usuários por 1 minuto com geração de relatório HTML):**
  ```bash
  locust -f performance/locustfile.py --headless -u 20 -r 2 -t 1m \
    --host https://cj98hakmf0.execute-api.us-east-1.amazonaws.com/phoebus-apps \
    --html performance/relatorio_performance.html
  ```

---

### Opção 3: Executar apenas Tags Específicas

Você pode filtrar a carga para testar apenas leitura, relatórios ou escrita:

* **Apenas Relatórios:**
  ```bash
  locust -f performance/locustfile.py --tags reports --headless -u 10 -r 2 -t 30s \
    --host https://cj98hakmf0.execute-api.us-east-1.amazonaws.com/phoebus-apps
  ```

* **Apenas Operações de Escrita / Mutação:**
  ```bash
  locust -f performance/locustfile.py --tags write --headless -u 5 -r 1 -t 30s \
    --host https://cj98hakmf0.execute-api.us-east-1.amazonaws.com/phoebus-apps
  ```

---

## Quality Gates e SLAs de Performance

Ao final da execução headless, o script calcula automaticamente o cumprimento dos seguintes SLAs:

| Métrica | Limite SLA Recomendado | Objetivo |
|---|---|---|
| **Taxa de Erro (Fail Ratio)** | `< 2.0%` | Garantir alta disponibilidade dos endpoints. |
| **Latência Percentil 95 (p95)** | `< 1000 ms` | 95% das requisições devem responder em menos de 1 segundo. |
| **Latência Percentil 99 (p99)** | `< 2000 ms` | Casos extremos de lentidão não devem ultrapassar 2 segundos. |
| **Throughput Médio** | `> 5.0 req/s` | Capacidade de vazão do API Gateway. |
