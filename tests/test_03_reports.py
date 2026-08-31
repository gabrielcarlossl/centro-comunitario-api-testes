"""
Testes automatizados - Recurso 3: Relatórios
  GET /communityCenter/highOccupation
  GET /communityCenter/averageResources
  GET /communityCenter/{id}/historic
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


# =========================================================================
# 3.A - highOccupation
# =========================================================================
class TestHighOccupationReport:
    """Cenários de teste para GET /communityCenter/highOccupation."""

    # ------------------------------------------------------------------ #
    #  TC-HO-001: Centro acima de 90% aparece no relatório
    # ------------------------------------------------------------------ #
    def test_high_occupation_center_listed(self, base_url, headers, create_center):
        """TC-HO-001 - Centro com >90% de ocupação deve aparecer no relatório."""
        # 182 / 200 = 91%
        id_high = create_center(
            _make_payload("HighOcc", max_people=200, current=182, resources={"volunteer": 2})
        )
        resp = requests.get(f"{base_url}/communityCenter/highOccupation", headers=headers)
        assert resp.status_code == 200, f"Esperado 200, obtido {resp.status_code}"
        content = resp.json().get("content", [])
        ids_found = [c["communityCenterId"] for c in content]
        assert id_high in ids_found, (
            f"Centro {id_high} com 91% de ocupacao nao apareceu no relatorio highOccupation"
        )

    # ------------------------------------------------------------------ #
    #  TC-HO-002: Centro com exatamente 90% NAO deve aparecer (> e nao >=)
    # ------------------------------------------------------------------ #
    def test_high_occupation_exactly_90_not_listed(self, base_url, headers, create_center):
        """TC-HO-002 - Centro com exatamente 90% de ocupação NAO deve aparecer no relatório."""
        # 90 / 100 = 90% -> nao deve aparecer
        id_90 = create_center(
            _make_payload("Exactly90", max_people=100, current=90, resources={"volunteer": 1})
        )
        resp = requests.get(f"{base_url}/communityCenter/highOccupation", headers=headers)
        assert resp.status_code == 200
        content = resp.json().get("content", [])
        ids_found = [c["communityCenterId"] for c in content]
        assert id_90 not in ids_found, (
            "Centro com exatamente 90% nao deveria estar no relatorio highOccupation"
        )

    # ------------------------------------------------------------------ #
    #  TC-HO-003: Centro abaixo de 90% nao aparece
    # ------------------------------------------------------------------ #
    def test_high_occupation_low_center_not_listed(self, base_url, headers, create_center):
        """TC-HO-003 - Centro com 50% de ocupação NAO deve aparecer no relatório."""
        id_low = create_center(
            _make_payload("LowOcc", max_people=200, current=100, resources={"volunteer": 1})
        )
        resp = requests.get(f"{base_url}/communityCenter/highOccupation", headers=headers)
        assert resp.status_code == 200
        content = resp.json().get("content", [])
        ids_found = [c["communityCenterId"] for c in content]
        assert id_low not in ids_found, (
            "Centro com 50% de ocupacao nao deveria estar no relatorio highOccupation"
        )

    # ------------------------------------------------------------------ #
    #  TC-HO-004: Resposta possui estrutura de paginação
    # ------------------------------------------------------------------ #
    def test_high_occupation_pagination_structure(self, base_url, headers):
        """TC-HO-004 - Resposta deve ter campos de paginação obrigatórios."""
        resp = requests.get(f"{base_url}/communityCenter/highOccupation", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        for field in ("page", "size", "totalElements", "totalPages", "content"):
            assert field in body, f"Campo '{field}' ausente na resposta de paginacao"

    # ------------------------------------------------------------------ #
    #  TC-HO-005: Sem apiKey -> 401
    # ------------------------------------------------------------------ #
    def test_high_occupation_without_api_key(self, base_url):
        """TC-HO-005 - Requisição sem apiKey deve retornar 401."""
        resp = requests.get(f"{base_url}/communityCenter/highOccupation")
        assert resp.status_code == 401, (
            f"Esperado 401, obtido {resp.status_code}"
        )

    # ------------------------------------------------------------------ #
    #  TC-HO-006: Parâmetros de paginação customizados funcionam
    # ------------------------------------------------------------------ #
    def test_high_occupation_custom_page_size(self, base_url, headers):
        """TC-HO-006 - pageSize personalizado deve ser respeitado."""
        resp = requests.get(
            f"{base_url}/communityCenter/highOccupation",
            params={"page": 0, "pageSize": 2},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body.get("content", [])) <= 2, (
            "O numero de itens na pagina nao deve exceder o pageSize solicitado"
        )


# =========================================================================
# 3.B - averageResources
# =========================================================================
class TestAverageResourcesReport:
    """Cenários de teste para GET /communityCenter/averageResources."""

    # ------------------------------------------------------------------ #
    #  TC-AR-001: Resposta retorna objeto averageResources
    # ------------------------------------------------------------------ #
    def test_average_resources_returns_object(self, base_url, headers, create_center):
        """TC-AR-001 - Resposta deve conter o campo 'averageResources' com as médias."""
        create_center(
            _make_payload("AvgRes", max_people=100, current=10,
                          resources={"doctor": 2, "volunteer": 4})
        )
        resp = requests.get(f"{base_url}/communityCenter/averageResources", headers=headers)
        assert resp.status_code == 200, f"Esperado 200, obtido {resp.status_code}"
        body = resp.json()
        assert "averageResources" in body, "Campo 'averageResources' ausente na resposta"
        assert isinstance(body["averageResources"], dict), "'averageResources' deve ser um objeto"

    # ------------------------------------------------------------------ #
    #  TC-AR-002: Sem apiKey -> 401
    # ------------------------------------------------------------------ #
    def test_average_resources_without_api_key(self, base_url):
        """TC-AR-002 - Sem apiKey deve retornar 401."""
        resp = requests.get(f"{base_url}/communityCenter/averageResources")
        assert resp.status_code == 401

    # ------------------------------------------------------------------ #
    #  TC-AR-003: Médias sao numericas e nao negativas
    # ------------------------------------------------------------------ #
    def test_average_resources_values_non_negative(self, base_url, headers, create_center):
        """TC-AR-003 - Todos os valores em 'averageResources' devem ser numéricos e >= 0."""
        create_center(
            _make_payload("AvgCheck", max_people=100, current=20,
                          resources={"volunteer": 6, "basicFoodBasket": 10})
        )
        resp = requests.get(f"{base_url}/communityCenter/averageResources", headers=headers)
        assert resp.status_code == 200
        averages = resp.json().get("averageResources", {})
        for resource, value in averages.items():
            assert isinstance(value, (int, float)), (
                f"Media do recurso '{resource}' deve ser numerica, obtido {type(value)}"
            )
            assert value >= 0, f"Media do recurso '{resource}' nao pode ser negativa: {value}"


# =========================================================================
# 3.C - historic
# =========================================================================
class TestHistoricReport:
    """Cenários de teste para GET /communityCenter/{id}/historic."""

    # ------------------------------------------------------------------ #
    #  TC-HI-001: Histórico retorna após intercâmbio realizado
    # ------------------------------------------------------------------ #
    def test_historic_after_exchange(self, base_url, headers, create_center):
        """TC-HI-001 - Após intercâmbio, o histórico deve conter a negociação."""
        id_a = create_center(
            _make_payload("HI-A", max_people=200, current=50,
                          resources={"volunteer": 10, "transportVehicle": 5})
        )
        id_b = create_center(
            _make_payload("HI-B", max_people=200, current=50,
                          resources={"doctor": 5, "medicalSuppliesKit": 3})
        )

        # Troca equilibrada: 2 voluntarios(6) + 1 veiculo(5) = 11 pts vs 1 medico(4) + 1 kit(7) = 11 pts
        exchange = {
            "communityCenter": [
                {"communityCenterId": id_a, "resources": {"volunteer": 2, "transportVehicle": 1}},
                {"communityCenterId": id_b, "resources": {"doctor": 1, "medicalSuppliesKit": 1}},
            ]
        }
        ex_resp = requests.put(
            f"{base_url}/communityCenter/exchange", json=exchange, headers=headers
        )
        assert ex_resp.status_code == 204

        hist_resp = requests.get(
            f"{base_url}/communityCenter/{id_a}/historic",
            params={"initDate": "20200101000000", "finishDate": "20991231235959"},
            headers=headers,
        )
        assert hist_resp.status_code == 200
        body = hist_resp.json()
        assert body.get("totalElements", 0) >= 1, (
            "Deveria haver ao menos 1 negociacao no historico apos intercambio"
        )

    # ------------------------------------------------------------------ #
    #  TC-HI-002: Filtro por intervalo de datas excluindo negociacoes
    # ------------------------------------------------------------------ #
    def test_historic_date_filter_excludes_records(self, base_url, headers, create_center):
        """TC-HI-002 - Filtro de data que nao abrange a negociação deve retornar 0 registros."""
        id_a = create_center(
            _make_payload("HI-DateA", max_people=200, current=50,
                          resources={"volunteer": 10, "transportVehicle": 5})
        )
        id_b = create_center(
            _make_payload("HI-DateB", max_people=200, current=50,
                          resources={"doctor": 5, "medicalSuppliesKit": 3})
        )

        exchange = {
            "communityCenter": [
                {"communityCenterId": id_a, "resources": {"volunteer": 2, "transportVehicle": 1}},
                {"communityCenterId": id_b, "resources": {"doctor": 1, "medicalSuppliesKit": 1}},
            ]
        }
        requests.put(f"{base_url}/communityCenter/exchange", json=exchange, headers=headers)

        # Periodo de 2000 a 2010 - nao deve ter registros
        hist_resp = requests.get(
            f"{base_url}/communityCenter/{id_a}/historic",
            params={"initDate": "20000101000000", "finishDate": "20100101000000"},
            headers=headers,
        )
        assert hist_resp.status_code == 200
        body = hist_resp.json()
        assert body.get("totalElements", 0) == 0, (
            "Filtro de periodo anterior as negociacoes deveria retornar 0 registros"
        )

    # ------------------------------------------------------------------ #
    #  TC-HI-003: Centro inexistente -> 404
    # ------------------------------------------------------------------ #
    def test_historic_nonexistent_center(self, base_url, headers):
        """TC-HI-003 - Histórico de centro inexistente deve retornar 404."""
        fake_id = str(uuid.uuid4())
        resp = requests.get(
            f"{base_url}/communityCenter/{fake_id}/historic",
            params={"initDate": "20200101000000", "finishDate": "20991231235959"},
            headers=headers,
        )
        assert resp.status_code == 404, (
            f"Esperado 404 para centro inexistente, obtido {resp.status_code}"
        )

    # ------------------------------------------------------------------ #
    #  TC-HI-004: initDate ausente -> 400
    # ------------------------------------------------------------------ #
    def test_historic_missing_init_date(self, base_url, headers, create_center):
        """TC-HI-004 - Omitir 'initDate' deve retornar 400 (campo obrigatório)."""
        cid = create_center(
            _make_payload("HI-MissingDate", max_people=100, current=10,
                          resources={"volunteer": 1})
        )
        resp = requests.get(
            f"{base_url}/communityCenter/{cid}/historic",
            params={"finishDate": "20991231235959"},
            headers=headers,
        )
        assert resp.status_code == 400, (
            f"Esperado 400 (initDate ausente), obtido {resp.status_code}"
        )

    # ------------------------------------------------------------------ #
    #  TC-HI-005: finishDate ausente -> 400
    # ------------------------------------------------------------------ #
    def test_historic_missing_finish_date(self, base_url, headers, create_center):
        """TC-HI-005 - Omitir 'finishDate' deve retornar 400."""
        cid = create_center(
            _make_payload("HI-MissingFinish", max_people=100, current=10,
                          resources={"volunteer": 1})
        )
        resp = requests.get(
            f"{base_url}/communityCenter/{cid}/historic",
            params={"initDate": "20200101000000"},
            headers=headers,
        )
        assert resp.status_code == 400, (
            f"Esperado 400 (finishDate ausente), obtido {resp.status_code}"
        )

    # ------------------------------------------------------------------ #
    #  TC-HI-006: Formato de data invalido -> 400
    # ------------------------------------------------------------------ #
    def test_historic_invalid_date_format(self, base_url, headers, create_center):
        """TC-HI-006 - Datas em formato inválido (nao YYYYMMDDHHmmss) devem retornar 400."""
        cid = create_center(
            _make_payload("HI-BadDate", max_people=100, current=10, resources={"volunteer": 1})
        )
        resp = requests.get(
            f"{base_url}/communityCenter/{cid}/historic",
            params={"initDate": "2020-01-01", "finishDate": "2099-12-31"},
            headers=headers,
        )
        assert resp.status_code == 400, (
            f"Esperado 400 (formato de data invalido), obtido {resp.status_code}"
        )

    # ------------------------------------------------------------------ #
    #  TC-HI-007: Sem apiKey -> 401
    # ------------------------------------------------------------------ #
    def test_historic_without_api_key(self, base_url):
        """TC-HI-007 - Histórico sem apiKey deve retornar 401."""
        cid = "qualquer-id"
        resp = requests.get(
            f"{base_url}/communityCenter/{cid}/historic",
            params={"initDate": "20200101000000", "finishDate": "20991231235959"},
        )
        assert resp.status_code == 401, (
            f"Esperado 401, obtido {resp.status_code}"
        )

    # ------------------------------------------------------------------ #
    #  TC-HI-008: Resposta possui estrutura de paginação
    # ------------------------------------------------------------------ #
    def test_historic_pagination_structure(self, base_url, headers, create_center):
        """TC-HI-008 - Resposta do histórico deve conter campos de paginação."""
        cid = create_center(
            _make_payload("HI-Page", max_people=100, current=10, resources={"volunteer": 1})
        )
        resp = requests.get(
            f"{base_url}/communityCenter/{cid}/historic",
            params={"initDate": "20200101000000", "finishDate": "20991231235959"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        for field in ("page", "size", "totalElements", "totalPages", "content"):
            assert field in body, f"Campo de paginacao '{field}' ausente na resposta"
