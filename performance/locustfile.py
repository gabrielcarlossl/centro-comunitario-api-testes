"""
Teste de Performance e Carga — Community Center API
Framework: Locust (Python)
"""

import os
import uuid
import random
from dotenv import load_dotenv
from locust import HttpUser, task, between, events, tag

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://cj98hakmf0.execute-api.us-east-1.amazonaws.com/phoebus-apps")
API_KEY = os.getenv("API_KEY", "")


class CommunityCenterLoadTestUser(HttpUser):
    """
    Simula um operador de centro comunitário / analista de emergência interagindo
    concorrentemente com a API da Phoebus.
    """
    # Tempo de espera realista entre tarefas (1 a 3 segundos)
    wait_time = between(1, 3)

    def on_start(self):
        """
        Setup executado quando cada usuário virtual é inicializado.
        Cria um centro comunitário exclusivo para o usuário realizar operações.
        """
        self.headers = {
            "apiKey": API_KEY,
            "Content-Type": "application/json"
        }
        self.created_center_ids = []
        self.primary_center_id = None

        # Criação do centro principal para operações do usuário virtual
        payload = {
            "name": f"Centro Perf {uuid.uuid4().hex[:6]}",
            "address": "Av. Performance Locust, 100",
            "maxNumberOfPeople": 300,
            "currentNumberOfPeople": 100,
            "resources": {
                "doctor": random.randint(2, 6),
                "volunteer": random.randint(5, 20),
                "medicalSuppliesKit": random.randint(3, 10),
                "transportVehicle": random.randint(1, 5),
                "basicFoodBasket": random.randint(10, 50),
            }
        }

        with self.client.post(
            "/communityCenter",
            json=payload,
            headers=self.headers,
            name="[SETUP] POST /communityCenter",
            catch_response=True
        ) as resp:
            if resp.status_code == 201:
                try:
                    self.primary_center_id = resp.json().get("communityCenterId")
                    if self.primary_center_id:
                        self.created_center_ids.append(self.primary_center_id)
                        resp.success()
                except Exception as e:
                    resp.failure(f"Erro ao parsear JSON no setup: {e}")
            else:
                resp.failure(f"Falha no setup: HTTP {resp.status_code} - {resp.text}")

    def on_stop(self):
        """
        Teardown executado quando o usuário virtual finaliza a execução.
        Exclui todos os centros criados pelo usuário para manter o ambiente limpo.
        """
        for cid in self.created_center_ids:
            self.client.delete(
                f"/communityCenter/{cid}",
                headers=self.headers,
                name="[TEARDOWN] DELETE /communityCenter/{id}"
            )

    # ─────────────────────────────────────────────────────────────────
    # TAREFAS DE LEITURA E RELATÓRIOS (ALTO VOLUME DE ACESSOS)
    # ─────────────────────────────────────────────────────────────────

    @tag('read', 'reports')
    @task(4)
    def get_high_occupation_report(self):
        """Consulta relatório de centros com alta ocupação (>90%)."""
        with self.client.get(
            "/communityCenter/highOccupation?page=0&pageSize=10",
            headers=self.headers,
            name="GET /communityCenter/highOccupation",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Erro ao consultar alta ocupação: HTTP {resp.status_code}")

    @tag('read', 'reports')
    @task(3)
    def get_average_resources_report(self):
        """Consulta médias de recursos disponíveis por centro."""
        with self.client.get(
            "/communityCenter/averageResources",
            headers=self.headers,
            name="GET /communityCenter/averageResources",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 404:
                # 404 é esperado caso nenhum centro exista para a chave
                resp.success()
            else:
                resp.failure(f"Erro ao consultar médias: HTTP {resp.status_code}")

    @tag('read', 'list')
    @task(3)
    def list_community_centers(self):
        """Listagem paginada de centros comunitários."""
        page = random.choice([0, 1])
        with self.client.get(
            f"/communityCenter?page={page}&pageSize=10&sort=-name",
            headers=self.headers,
            name="GET /communityCenter (Paginado)",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Erro na listagem: HTTP {resp.status_code}")

    @tag('read', 'historic')
    @task(1)
    def get_center_historic(self):
        """Consulta o histórico de negociações de um centro."""
        if not self.primary_center_id:
            return

        params = {
            "initDate": "20200101000000",
            "finishDate": "20301231235959",
            "page": 0,
            "pageSize": 10
        }
        with self.client.get(
            f"/communityCenter/{self.primary_center_id}/historic",
            params=params,
            headers=self.headers,
            name="GET /communityCenter/{id}/historic",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Erro no histórico: HTTP {resp.status_code}")

    # ─────────────────────────────────────────────────────────────────
    # TAREFAS DE ESCRITA E MUTAÇÃO (ATUALIZAÇÃO CONCORRENTE)
    # ─────────────────────────────────────────────────────────────────

    @tag('write', 'occupancy')
    @task(2)
    def update_occupancy(self):
        """Simula atualização concorrente de ocupação de pessoas."""
        if not self.primary_center_id:
            return

        new_people = random.randint(10, 250)
        payload = {"currentNumberOfPeople": new_people}

        with self.client.put(
            f"/communityCenter/{self.primary_center_id}/currentNumberOfPeople",
            json=payload,
            headers=self.headers,
            name="PUT /communityCenter/{id}/currentNumberOfPeople",
            catch_response=True
        ) as resp:
            if resp.status_code in [200, 204]:
                resp.success()
            else:
                resp.failure(f"Erro ao atualizar ocupação: HTTP {resp.status_code}")

    @tag('write', 'lifecycle')
    @task(1)
    def create_and_delete_temporary_center(self):
        """Ciclo completo de criação e exclusão rápida para testar vazão de escrita."""
        payload = {
            "name": f"Centro Temp {uuid.uuid4().hex[:6]}",
            "address": "Rua Temporária, 50",
            "maxNumberOfPeople": 150,
            "currentNumberOfPeople": 20,
            "resources": {"volunteer": 5, "basicFoodBasket": 10}
        }

        # Criação
        with self.client.post(
            "/communityCenter",
            json=payload,
            headers=self.headers,
            name="POST /communityCenter",
            catch_response=True
        ) as resp:
            if resp.status_code == 201:
                try:
                    temp_id = resp.json().get("communityCenterId")
                    if temp_id:
                        resp.success()
                        # Exclusão imediata
                        self.client.delete(
                            f"/communityCenter/{temp_id}",
                            headers=self.headers,
                            name="DELETE /communityCenter/{id}"
                        )
                except Exception as e:
                    resp.failure(f"Erro ao capturar ID temporário: {e}")
            else:
                resp.failure(f"Falha ao criar centro temporário: HTTP {resp.status_code}")


# ─────────────────────────────────────────────────────────────────────
# QUALITY GATES / VALIDAÇÃO DE SLA NO TÉRMINO DO TESTE
# ─────────────────────────────────────────────────────────────────────
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Executado ao final do teste de carga para avaliar os Quality Gates de performance.
    """
    stats = environment.stats.total
    if stats.num_requests > 0:
        p95 = stats.get_response_time_percentile(0.95)
        p99 = stats.get_response_time_percentile(0.99)
        fail_ratio = stats.fail_ratio * 100

        print("\n" + "=" * 65)
        print("RELATÓRIO FINAL DE QUALITY GATES (SLA DE PERFORMANCE)")
        print("=" * 65)
        print(f"Total de Requisições: {stats.num_requests}")
        print(f"Taxa de Erro:         {fail_ratio:.2f}% (Limite SLA: < 2.0%)")
        print(f"Latência Percentil 95 (p95): {p95:.1f} ms (Limite SLA: < 1000 ms)")
        print(f"Latência Percentil 99 (p99): {p99:.1f} ms (Limite SLA: < 2000 ms)")
        print(f"Throughput Médio (RPS):      {stats.current_rps:.1f} req/s")
        print("=" * 65 + "\n")
