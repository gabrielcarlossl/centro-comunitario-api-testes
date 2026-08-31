"""
Testes automatizados – Recurso 2: Intercâmbio de Recursos
PUT /communityCenter/exchange
"""

import pytest
import requests
import uuid


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_payload(name_suffix: str, max_people: int, current: int, resources: dict) -> dict:
    return {
        "name": f"Centro {name_suffix} {uuid.uuid4().hex[:6]}",
        "address": f"Rua {name_suffix}, 1",
        "maxNumberOfPeople": max_people,
        "currentNumberOfPeople": current,
        "resources": resources,
    }


class TestExchangeResources:
    """Cenários de teste para intercâmbio de recursos entre centros comunitários."""

    # ------------------------------------------------------------------ #
    #  TC-EX-001: Troca equilibrada em pontos (caso feliz)
    #  Tabela de pontos: médico=4 | voluntário=3 | kit=7 | veículo=5 | cesta=2
    #  Centro A envia: 2 voluntários (3×2=6) + 1 veículo (5) = 11 pts
    #  Centro B envia: 1 médico (4) + 1 kit médico (7) = 11 pts
    # ------------------------------------------------------------------ #
    def test_exchange_balanced_points(self, base_url, headers, create_center):
        """TC-EX-001 - Troca equilibrada em pontos deve retornar 204."""
        id_a = create_center(
            _make_payload(
                "A-Balanced",
                max_people=200,
                current=50,
                resources={"volunteer": 5, "transportVehicle": 3, "doctor": 2},
            )
        )
        id_b = create_center(
            _make_payload(
                "B-Balanced",
                max_people=200,
                current=50,
                resources={"doctor": 4, "medicalSuppliesKit": 4, "volunteer": 2},
            )
        )

        payload = {
            "communityCenter": [
                {
                    "communityCenterId": id_a,
                    "resources": {"volunteer": 2, "transportVehicle": 1},  # 6+5=11 pts
                },
                {
                    "communityCenterId": id_b,
                    "resources": {"doctor": 1, "medicalSuppliesKit": 1},  # 4+7=11 pts
                },
            ]
        }
        resp = requests.put(f"{base_url}/communityCenter/exchange", json=payload, headers=headers)
        assert resp.status_code == 204, (
            f"Esperado 204, obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-EX-002: Troca desequilibrada sem exceção de 90% → deve rejeitar
    # ------------------------------------------------------------------ #
    def test_exchange_unbalanced_normal_centers_rejected(self, base_url, headers, create_center):
        """TC-EX-002 - Troca desequilibrada entre centros com ocupação ≤90% deve retornar 400."""
        id_a = create_center(
            _make_payload("A-Unbalanced", max_people=200, current=50,
                          resources={"doctor": 5, "volunteer": 5})
        )
        id_b = create_center(
            _make_payload("B-Unbalanced", max_people=200, current=50,
                          resources={"basicFoodBasket": 10})
        )

        payload = {
            "communityCenter": [
                {
                    "communityCenterId": id_a,
                    "resources": {"doctor": 1},  # 4 pts
                },
                {
                    "communityCenterId": id_b,
                    "resources": {"basicFoodBasket": 1},  # 2 pts  → desequilíbrio
                },
            ]
        }
        resp = requests.put(f"{base_url}/communityCenter/exchange", json=payload, headers=headers)
        assert resp.status_code == 400, (
            f"Esperado 400 (troca desequilibrada), obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-EX-003: Exceção – centro com >90% de ocupação permite troca desequilibrada
    # ------------------------------------------------------------------ #
    def test_exchange_unbalanced_high_occupation_allowed(self, base_url, headers, create_center):
        """TC-EX-003 - Se um centro tem >90% de ocupação, a troca desequilibrada deve ser aceita (204)."""
        # Centro A: 91% de ocupação (182/200)
        id_a = create_center(
            _make_payload("A-HighOcc", max_people=200, current=182,
                          resources={"doctor": 5, "volunteer": 10})
        )
        id_b = create_center(
            _make_payload("B-Normal", max_people=200, current=50,
                          resources={"basicFoodBasket": 15})
        )

        payload = {
            "communityCenter": [
                {
                    "communityCenterId": id_a,
                    "resources": {"doctor": 1},          # 4 pts
                },
                {
                    "communityCenterId": id_b,
                    "resources": {"basicFoodBasket": 1},  # 2 pts → desequilíbrio PERMITIDO
                },
            ]
        }
        resp = requests.put(f"{base_url}/communityCenter/exchange", json=payload, headers=headers)
        assert resp.status_code == 204, (
            f"Esperado 204 (exceção >90%), obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-EX-004: Apenas um centro no payload → deve rejeitar
    # ------------------------------------------------------------------ #
    def test_exchange_single_center_rejected(self, base_url, headers, create_center):
        """TC-EX-004 - Intercâmbio com apenas 1 centro deve retornar 400."""
        id_a = create_center(
            _make_payload("A-Solo", max_people=100, current=10, resources={"volunteer": 5})
        )

        payload = {
            "communityCenter": [
                {"communityCenterId": id_a, "resources": {"volunteer": 1}}
            ]
        }
        resp = requests.put(f"{base_url}/communityCenter/exchange", json=payload, headers=headers)
        assert resp.status_code == 400, (
            f"Esperado 400 (apenas 1 centro), obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-EX-005: Centro inexistente → deve retornar 404
    # ------------------------------------------------------------------ #
    def test_exchange_nonexistent_center(self, base_url, headers, create_center):
        """TC-EX-005 – Centro inexistente no intercâmbio deve retornar 404."""
        id_real = create_center(
            _make_payload("A-Real", max_people=100, current=10, resources={"volunteer": 5})
        )
        fake_id = str(uuid.uuid4())

        payload = {
            "communityCenter": [
                {"communityCenterId": id_real, "resources": {"volunteer": 1}},
                {"communityCenterId": fake_id, "resources": {"volunteer": 1}},
            ]
        }
        resp = requests.put(f"{base_url}/communityCenter/exchange", json=payload, headers=headers)
        assert resp.status_code == 404, (
            f"Esperado 404, obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-EX-006: Recursos insuficientes no centro de origem
    # ------------------------------------------------------------------ #
    def test_exchange_insufficient_resources(self, base_url, headers, create_center):
        """TC-EX-006 – Tentar ceder mais recursos do que o disponível deve retornar 400."""
        id_a = create_center(
            _make_payload("A-Poor", max_people=100, current=10, resources={"doctor": 1})
        )
        id_b = create_center(
            _make_payload("B-Rich", max_people=100, current=10,
                          resources={"medicalSuppliesKit": 3})
        )

        payload = {
            "communityCenter": [
                {"communityCenterId": id_a, "resources": {"doctor": 5}},          # mais do que tem
                {"communityCenterId": id_b, "resources": {"medicalSuppliesKit": 2}},  # 14pts vs 20pts
            ]
        }
        resp = requests.put(f"{base_url}/communityCenter/exchange", json=payload, headers=headers)
        assert resp.status_code == 400, (
            f"Esperado 400 (recursos insuficientes), obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-EX-007: Intercâmbio registra histórico
    # ------------------------------------------------------------------ #
    def test_exchange_creates_historic(self, base_url, headers, create_center):
        """TC-EX-007 – Após intercâmbio bem-sucedido, o histórico dos centros deve conter a negociação."""
        id_a = create_center(
            _make_payload("A-Hist", max_people=200, current=50,
                          resources={"volunteer": 10, "transportVehicle": 5})
        )
        id_b = create_center(
            _make_payload("B-Hist", max_people=200, current=50,
                          resources={"doctor": 5, "medicalSuppliesKit": 3})
        )

        # Troca equilibrada: 2 voluntários (6) + 1 veículo (5) = 11 pts vs 1 médico (4) + 1 kit (7) = 11 pts
        exchange_payload = {
            "communityCenter": [
                {"communityCenterId": id_a, "resources": {"volunteer": 2, "transportVehicle": 1}},
                {"communityCenterId": id_b, "resources": {"doctor": 1, "medicalSuppliesKit": 1}},
            ]
        }
        resp = requests.put(f"{base_url}/communityCenter/exchange",
                            json=exchange_payload, headers=headers)
        assert resp.status_code == 204

        # Verifica histórico do centro A
        hist_resp = requests.get(
            f"{base_url}/communityCenter/{id_a}/historic",
            params={"initDate": "20200101000000", "finishDate": "20991231235959"},
            headers=headers,
        )
        assert hist_resp.status_code == 200
        data = hist_resp.json()
        assert data.get("totalElements", 0) >= 1, (
            "Histórico do centro A deve ter ao menos 1 negociação após o intercâmbio"
        )

    # ------------------------------------------------------------------ #
    #  TC-EX-008: Sem apiKey → 401
    # ------------------------------------------------------------------ #
    def test_exchange_without_api_key(self, base_url, create_center):
        """TC-EX-008 – Intercâmbio sem apiKey deve retornar 401."""
        payload = {
            "communityCenter": [
                {"communityCenterId": str(uuid.uuid4()), "resources": {"volunteer": 1}},
                {"communityCenterId": str(uuid.uuid4()), "resources": {"volunteer": 1}},
            ]
        }
        resp = requests.put(
            f"{base_url}/communityCenter/exchange",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 401, (
            f"Esperado 401, obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-EX-009: Recurso com valor zero na troca
    # ------------------------------------------------------------------ #
    def test_exchange_resource_value_zero(self, base_url, headers, create_center):
        """TC-EX-009 – Quantidade 0 em resource da troca deve ser rejeitada (mínimo é 1)."""
        id_a = create_center(
            _make_payload("A-Zero", max_people=100, current=10, resources={"volunteer": 5})
        )
        id_b = create_center(
            _make_payload("B-Zero", max_people=100, current=10, resources={"basicFoodBasket": 5})
        )

        payload = {
            "communityCenter": [
                {"communityCenterId": id_a, "resources": {"volunteer": 0}},
                {"communityCenterId": id_b, "resources": {"basicFoodBasket": 0}},
            ]
        }
        resp = requests.put(f"{base_url}/communityCenter/exchange", json=payload, headers=headers)
        assert resp.status_code == 400, (
            f"Esperado 400 (quantidade 0 inválida), obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-EX-010: Payload sem campo 'communityCenter'
    # ------------------------------------------------------------------ #
    def test_exchange_missing_community_center_field(self, base_url, headers):
        """TC-EX-010 – Payload sem a chave 'communityCenter' deve retornar 400."""
        resp = requests.put(
            f"{base_url}/communityCenter/exchange",
            json={"data": []},
            headers=headers,
        )
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}. Corpo: {resp.text}"
        )

