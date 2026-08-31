"""
Testes automatizados - Recurso 1: Cadastro de Centros Comunitários
POST /communityCenter
"""

import pytest
import requests
import uuid


class TestCreateCommunityCenter:
    """Cenários de teste para criação de centros comunitários."""

    # ------------------------------------------------------------------ #
    #  TC-CC-001: Criação bem-sucedida com todos os campos válidos
    # ------------------------------------------------------------------ #
    def test_create_center_success(self, base_url, headers, create_center):
        """TC-CC-001 - Cria um centro comunitário com dados válidos e verifica 201 + ID."""
        payload = {
            "name": f"Centro Valido {uuid.uuid4().hex[:6]}",
            "address": "Av. Central, 500",
            "maxNumberOfPeople": 300,
            "currentNumberOfPeople": 80,
            "resources": {
                "doctor": 5,
                "volunteer": 15,
                "medicalSuppliesKit": 10,
                "transportVehicle": 3,
                "basicFoodBasket": 30,
            },
        }
        center_id = create_center(payload)
        assert isinstance(center_id, str) and len(center_id) > 0, (
            "O campo 'communityCenterId' deve ser uma string nao-vazia"
        )

    # ------------------------------------------------------------------ #
    #  TC-CC-002: Campo obrigatório ausente (name)
    # ------------------------------------------------------------------ #
    def test_create_center_missing_name(self, base_url, headers):
        """TC-CC-002 - Omitir 'name' deve retornar 400 Bad Request."""
        payload = {
            "address": "Rua Sem Nome, 0",
            "maxNumberOfPeople": 100,
            "currentNumberOfPeople": 10,
            "resources": {"volunteer": 5},
        }
        resp = requests.post(f"{base_url}/communityCenter", json=payload, headers=headers)
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-CC-003: Campo obrigatório ausente (address)
    # ------------------------------------------------------------------ #
    def test_create_center_missing_address(self, base_url, headers):
        """TC-CC-003 - Omitir 'address' deve retornar 400 Bad Request."""
        payload = {
            "name": "Centro Sem Endereco",
            "maxNumberOfPeople": 100,
            "currentNumberOfPeople": 10,
            "resources": {"volunteer": 5},
        }
        resp = requests.post(f"{base_url}/communityCenter", json=payload, headers=headers)
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-CC-004: Campo obrigatório ausente (maxNumberOfPeople)
    # ------------------------------------------------------------------ #
    def test_create_center_missing_max_people(self, base_url, headers):
        """TC-CC-004 - Omitir 'maxNumberOfPeople' deve retornar 400."""
        payload = {
            "name": "Centro Sem Max",
            "address": "Rua Teste, 1",
            "currentNumberOfPeople": 10,
            "resources": {"volunteer": 5},
        }
        resp = requests.post(f"{base_url}/communityCenter", json=payload, headers=headers)
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-CC-005: Campo obrigatório ausente (resources)
    # ------------------------------------------------------------------ #
    def test_create_center_missing_resources(self, base_url, headers):
        """TC-CC-005 - Omitir 'resources' deve retornar 400."""
        payload = {
            "name": "Centro Sem Recursos",
            "address": "Rua Vazia, 0",
            "maxNumberOfPeople": 100,
            "currentNumberOfPeople": 0,
        }
        resp = requests.post(f"{base_url}/communityCenter", json=payload, headers=headers)
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-CC-006: Ocupação inicial excede capacidade máxima
    # ------------------------------------------------------------------ #
    def test_create_center_occupancy_exceeds_max(self, base_url, headers):
        """TC-CC-006 - currentNumberOfPeople > maxNumberOfPeople deve retornar 400."""
        payload = {
            "name": "Centro Lotado",
            "address": "Rua Cheia, 999",
            "maxNumberOfPeople": 100,
            "currentNumberOfPeople": 150,
            "resources": {"volunteer": 2},
        }
        resp = requests.post(f"{base_url}/communityCenter", json=payload, headers=headers)
        assert resp.status_code == 400, (
            f"Esperado 400 (ocupacao excede maximo), obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-CC-007: Recurso com valor negativo
    # ------------------------------------------------------------------ #
    def test_create_center_negative_resource(self, base_url, headers):
        """TC-CC-007 - Recurso com quantidade negativa deve retornar 400."""
        payload = {
            "name": "Centro Recurso Negativo",
            "address": "Rua Invalida, 1",
            "maxNumberOfPeople": 100,
            "currentNumberOfPeople": 0,
            "resources": {"doctor": -1},
        }
        resp = requests.post(f"{base_url}/communityCenter", json=payload, headers=headers)
        assert resp.status_code == 400, (
            f"Esperado 400 (recurso negativo), obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-CC-008: maxNumberOfPeople = 0 (inválido, mínimo é 1)
    # ------------------------------------------------------------------ #
    def test_create_center_zero_max_people(self, base_url, headers):
        """TC-CC-008 - maxNumberOfPeople = 0 deve ser rejeitado (mínimo é 1)."""
        payload = {
            "name": "Centro Zero Capacidade",
            "address": "Rua Nenhuma, 0",
            "maxNumberOfPeople": 0,
            "currentNumberOfPeople": 0,
            "resources": {"volunteer": 1},
        }
        resp = requests.post(f"{base_url}/communityCenter", json=payload, headers=headers)
        assert resp.status_code == 400, (
            f"Esperado 400 (maxNumberOfPeople=0), obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-CC-009: Sem apiKey no header
    # ------------------------------------------------------------------ #
    def test_create_center_without_api_key(self, base_url, valid_center_payload):
        """TC-CC-009 - Requisição sem apiKey deve retornar 401 Unauthorized."""
        resp = requests.post(
            f"{base_url}/communityCenter",
            json=valid_center_payload,
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 401, (
            f"Esperado 401, obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-CC-010: apiKey inválida/desconhecida
    # ------------------------------------------------------------------ #
    def test_create_center_invalid_api_key(self, base_url, valid_center_payload):
        """TC-CC-010 - apiKey inválida deve retornar 401."""
        resp = requests.post(
            f"{base_url}/communityCenter",
            json=valid_center_payload,
            headers={"apiKey": "chave-invalida-xyz", "Content-Type": "application/json"},
        )
        assert resp.status_code == 401, (
            f"Esperado 401, obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-CC-011: Corpo vazio
    # ------------------------------------------------------------------ #
    def test_create_center_empty_body(self, base_url, headers):
        """TC-CC-011 - Corpo vazio deve retornar 400."""
        resp = requests.post(f"{base_url}/communityCenter", json={}, headers=headers)
        assert resp.status_code == 400, (
            f"Esperado 400, obtido {resp.status_code}. Corpo: {resp.text}"
        )

    # ------------------------------------------------------------------ #
    #  TC-CC-012: Resposta contém communityCenterId
    # ------------------------------------------------------------------ #
    def test_create_center_response_schema(self, base_url, headers, create_center):
        """TC-CC-012 - A resposta 201 deve conter o campo 'communityCenterId' como string."""
        payload = {
            "name": f"Centro Schema {uuid.uuid4().hex[:6]}",
            "address": "Rua Schema, 1",
            "maxNumberOfPeople": 50,
            "currentNumberOfPeople": 0,
            "resources": {"basicFoodBasket": 5},
        }
        center_id = create_center(payload)
        assert isinstance(center_id, str) and len(center_id) > 0, (
            "communityCenterId deve ser uma string nao-vazia"
        )
