"""
Testes automatizados - Atualização de Ocupação, Remoção e Listagem
  PUT  /communityCenter/{id}/currentNumberOfPeople
  DELETE /communityCenter/{id}
  GET  /communityCenter
"""

import pytest
import requests
import uuid


def _make_payload(name_suffix: str, max_people: int, current: int, resources: dict) -> dict:
    return {
        "name": f"Centro {name_suffix} {uuid.uuid4().hex[:6]}",
        "address": f"Rua {name_suffix}, 1",
        "maxNumberOfPeople": max_people,
        "currentNumberOfPeople": current,
        "resources": resources,
    }


# =========================================================================
# Atualização de Ocupação
# =========================================================================
class TestUpdateOccupancy:
    """Cenários de teste para PUT /communityCenter/{id}/currentNumberOfPeople."""

    # ------------------------------------------------------------------ #
    #  TC-UO-001: Atualização válida
    # ------------------------------------------------------------------ #
    def test_update_occupancy_success(self, base_url, headers, create_center):
        """TC-UO-001 - Atualização válida de ocupação deve retornar 204."""
        cid = create_center(
            _make_payload("UO-Valid", max_people=200, current=50, resources={"volunteer": 3})
        )
        resp = requests.put(
            f"{base_url}/communityCenter/{cid}/currentNumberOfPeople",
            json={"currentNumberOfPeople": 120},
            headers=headers,
        )
        assert resp.status_code == 204, (
            f"Esperado 204, obtido {resp.status_code}. Body: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-UO-002: Ocupação acima do máximo
    # ------------------------------------------------------------------ #
    def test_update_occupancy_exceeds_max(self, base_url, headers, create_center):
        """TC-UO-002 - Ocupação acima do máximo deve retornar 400."""
        cid = create_center(
            _make_payload("UO-Exceed", max_people=100, current=50, resources={"volunteer": 1})
        )
        resp = requests.put(
            f"{base_url}/communityCenter/{cid}/currentNumberOfPeople",
            json={"currentNumberOfPeople": 150},
            headers=headers,
        )
        assert resp.status_code == 400, (
            f"Esperado 400 (excede maximo), obtido {resp.status_code}"
        )

    # ------------------------------------------------------------------ #
    #  TC-UO-003: Zerar ocupação (0 pessoas)
    # ------------------------------------------------------------------ #
    def test_update_occupancy_to_zero(self, base_url, headers, create_center):
        """TC-UO-003 - Zerar ocupação (0 pessoas) deve ser permitido (retornar 204)."""
        cid = create_center(
            _make_payload("UO-Zero", max_people=100, current=50, resources={"volunteer": 1})
        )
        resp = requests.put(
            f"{base_url}/communityCenter/{cid}/currentNumberOfPeople",
            json={"currentNumberOfPeople": 0},
            headers=headers,
        )
        assert resp.status_code == 204, f"Esperado 204, obtido {resp.status_code}"

    # ------------------------------------------------------------------ #
    #  TC-UO-004: Ocupação negativa
    # ------------------------------------------------------------------ #
    def test_update_occupancy_negative(self, base_url, headers, create_center):
        """TC-UO-004 - Ocupação negativa deve retornar 400."""
        cid = create_center(
            _make_payload("UO-Negative", max_people=100, current=50, resources={"volunteer": 1})
        )
        resp = requests.put(
            f"{base_url}/communityCenter/{cid}/currentNumberOfPeople",
            json={"currentNumberOfPeople": -10},
            headers=headers,
        )
        assert resp.status_code == 400, f"Esperado 400 (negativo), obtido {resp.status_code}"

    # ------------------------------------------------------------------ #
    #  TC-UO-005: Centro inexistente -> 404
    # ------------------------------------------------------------------ #
    def test_update_occupancy_nonexistent_center(self, base_url, headers):
        """TC-UO-005 - Atualizar centro inexistente deve retornar 404."""
        fake_id = str(uuid.uuid4())
        resp = requests.put(
            f"{base_url}/communityCenter/{fake_id}/currentNumberOfPeople",
            json={"currentNumberOfPeople": 10},
            headers=headers,
        )
        assert resp.status_code == 404, f"Esperado 404, obtido {resp.status_code}"

    # ------------------------------------------------------------------ #
    #  TC-UO-006: Sem apiKey -> 401
    # ------------------------------------------------------------------ #
    def test_update_occupancy_without_api_key(self, base_url):
        """TC-UO-006 - Sem apiKey deve retornar 401."""
        fake_id = str(uuid.uuid4())
        resp = requests.put(
            f"{base_url}/communityCenter/{fake_id}/currentNumberOfPeople",
            json={"currentNumberOfPeople": 10},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 401, f"Esperado 401, obtido {resp.status_code}"

    # ------------------------------------------------------------------ #
    #  TC-UO-007: Ocupação exatamente no máximo (valor de borda)
    # ------------------------------------------------------------------ #
    def test_update_occupancy_exactly_at_max(self, base_url, headers, create_center):
        """TC-UO-007 - Ocupação igual ao máximo deve ser permitida (204)."""
        cid = create_center(
            _make_payload("UO-AtMax", max_people=100, current=50, resources={"volunteer": 1})
        )
        resp = requests.put(
            f"{base_url}/communityCenter/{cid}/currentNumberOfPeople",
            json={"currentNumberOfPeople": 100},
            headers=headers,
        )
        assert resp.status_code == 204, (
            f"Esperado 204 (exatamente no maximo), obtido {resp.status_code}"
        )

    # ------------------------------------------------------------------ #
    #  TC-UO-008: Payload sem o campo obrigatório -> 400
    # ------------------------------------------------------------------ #
    def test_update_occupancy_missing_field(self, base_url, headers, create_center):
        """TC-UO-008 - Payload sem 'currentNumberOfPeople' deve retornar 400."""
        cid = create_center(
            _make_payload("UO-Missing", max_people=100, current=50, resources={"volunteer": 1})
        )
        resp = requests.put(
            f"{base_url}/communityCenter/{cid}/currentNumberOfPeople",
            json={},
            headers=headers,
        )
        assert resp.status_code == 400, (
            f"Esperado 400 (campo ausente), obtido {resp.status_code}"
        )


# =========================================================================
# Remoção de Centros
# =========================================================================
class TestDeleteCommunityCenter:
    """Cenários de teste para DELETE /communityCenter/{id}."""

    # ------------------------------------------------------------------ #
    #  TC-DC-001: Remoção bem-sucedida
    # ------------------------------------------------------------------ #
    def test_delete_center_success(self, base_url, headers):
        """TC-DC-001 - Remoção de centro existente deve retornar 204."""
        payload = {
            "name": f"Centro Delete {uuid.uuid4().hex[:6]}",
            "address": "Rua Deletar, 1",
            "maxNumberOfPeople": 50,
            "currentNumberOfPeople": 0,
            "resources": {"volunteer": 1},
        }
        create_resp = requests.post(
            f"{base_url}/communityCenter", json=payload, headers=headers
        )
        assert create_resp.status_code == 201
        cid = create_resp.json()["communityCenterId"]

        del_resp = requests.delete(f"{base_url}/communityCenter/{cid}", headers=headers)
        assert del_resp.status_code == 204, (
            f"Esperado 204, obtido {del_resp.status_code}"
        )

    # ------------------------------------------------------------------ #
    #  TC-DC-002: Centro inexistente -> 404
    # ------------------------------------------------------------------ #
    def test_delete_nonexistent_center(self, base_url, headers):
        """TC-DC-002 - Remoção de centro inexistente deve retornar 404."""
        fake_id = str(uuid.uuid4())
        resp = requests.delete(f"{base_url}/communityCenter/{fake_id}", headers=headers)
        assert resp.status_code == 404, f"Esperado 404, obtido {resp.status_code}"

    # ------------------------------------------------------------------ #
    #  TC-DC-003: Sem apiKey -> 401
    # ------------------------------------------------------------------ #
    def test_delete_without_api_key(self, base_url):
        """TC-DC-003 - Deleção sem apiKey deve retornar 401."""
        fake_id = str(uuid.uuid4())
        resp = requests.delete(f"{base_url}/communityCenter/{fake_id}")
        assert resp.status_code == 401, f"Esperado 401, obtido {resp.status_code}"

    # ------------------------------------------------------------------ #
    #  TC-DC-004: Após deleção, segunda tentativa deve retornar 404
    # ------------------------------------------------------------------ #
    def test_delete_center_idempotency(self, base_url, headers):
        """TC-DC-004 - Após deleção, segunda tentativa de deletar deve retornar 404."""
        payload = {
            "name": f"Centro Ghost {uuid.uuid4().hex[:6]}",
            "address": "Rua Fantasma, 1",
            "maxNumberOfPeople": 50,
            "currentNumberOfPeople": 0,
            "resources": {"volunteer": 1},
        }
        create_resp = requests.post(
            f"{base_url}/communityCenter", json=payload, headers=headers
        )
        assert create_resp.status_code == 201
        cid = create_resp.json()["communityCenterId"]

        # Primeira deleção: deve ser 204
        first = requests.delete(f"{base_url}/communityCenter/{cid}", headers=headers)
        assert first.status_code == 204

        # Segunda deleção: deve ser 404 (centro nao existe mais)
        second = requests.delete(f"{base_url}/communityCenter/{cid}", headers=headers)
        assert second.status_code == 404, (
            "Apos delecao, uma segunda tentativa deve retornar 404"
        )


# =========================================================================
# Listagem de Centros
# =========================================================================
class TestListCommunityCenters:
    """Cenários de teste para GET /communityCenter."""

    # ------------------------------------------------------------------ #
    #  TC-LC-001: Listagem retorna 200
    # ------------------------------------------------------------------ #
    def test_list_returns_200(self, base_url, headers):
        """TC-LC-001 - Listagem deve retornar 200."""
        resp = requests.get(f"{base_url}/communityCenter", headers=headers)
        assert resp.status_code == 200, f"Esperado 200, obtido {resp.status_code}"

    # ------------------------------------------------------------------ #
    #  TC-LC-002: Resposta tem estrutura de paginação
    # ------------------------------------------------------------------ #
    def test_list_pagination_structure(self, base_url, headers):
        """TC-LC-002 - Listagem deve conter campos de paginação obrigatórios."""
        resp = requests.get(f"{base_url}/communityCenter", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        for field in ("page", "size", "totalElements", "totalPages", "content"):
            assert field in body, f"Campo '{field}' ausente na resposta"

    # ------------------------------------------------------------------ #
    #  TC-LC-003: pageSize personalizado é respeitado
    # ------------------------------------------------------------------ #
    def test_list_custom_page_size(self, base_url, headers):
        """TC-LC-003 - Listagem com pageSize=1 deve ter no máximo 1 item."""
        resp = requests.get(
            f"{base_url}/communityCenter",
            params={"page": 0, "pageSize": 1},
            headers=headers,
        )
        assert resp.status_code == 200
        assert len(resp.json().get("content", [])) <= 1, (
            "Content nao deve ter mais itens do que o pageSize solicitado"
        )

    # ------------------------------------------------------------------ #
    #  TC-LC-004: Sem apiKey -> 401
    # ------------------------------------------------------------------ #
    def test_list_without_api_key(self, base_url):
        """TC-LC-004 - Listagem sem apiKey deve retornar 401."""
        resp = requests.get(f"{base_url}/communityCenter")
        assert resp.status_code == 401, f"Esperado 401, obtido {resp.status_code}"

    # ------------------------------------------------------------------ #
    #  TC-LC-005: Centro criado aparece na listagem
    # ------------------------------------------------------------------ #
    def test_list_includes_created_center(self, base_url, headers, create_center):
        """TC-LC-005 - Centro recém-criado deve aparecer na listagem."""
        cid = create_center(
            _make_payload("List-Check", max_people=100, current=10, resources={"volunteer": 2})
        )
        # Busca todas as páginas até encontrar o ID (ou esgota as páginas)
        page = 0
        found = False
        while True:
            resp = requests.get(
                f"{base_url}/communityCenter",
                params={"page": page, "pageSize": 50},
                headers=headers,
            )
            assert resp.status_code == 200
            body = resp.json()
            ids = [c["communityCenterId"] for c in body.get("content", [])]
            if cid in ids:
                found = True
                break
            if page >= body.get("totalPages", 1) - 1:
                break
            page += 1

        assert found, f"Centro {cid} nao foi encontrado na listagem"

    # ------------------------------------------------------------------ #
    #  TC-LC-006: Ordenação por campo funciona
    # ------------------------------------------------------------------ #
    def test_list_sort_by_name_desc(self, base_url, headers):
        """TC-LC-006 - Ordenação descendente por nome deve retornar 200 sem erros."""
        resp = requests.get(
            f"{base_url}/communityCenter",
            params={"sort": "-name"},
            headers=headers,
        )
        assert resp.status_code == 200, (
            f"Ordenacao por '-name' falhou com status {resp.status_code}"
        )
