"""
Configurações globais do pytest e fixtures compartilhadas.
"""

import os
import uuid
import pytest
import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")


@pytest.fixture(scope="session")
def base_url():
    if not BASE_URL:
        pytest.fail(
            "Variável de ambiente BASE_URL não definida. Configure no arquivo .env ou no sistema."
        )
    return BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def api_key():
    if not API_KEY:
        pytest.fail(
            "Variável de ambiente API_KEY não definida. Configure no arquivo .env ou no sistema."
        )
    return API_KEY


@pytest.fixture(scope="session")
def headers(api_key):
    return {"apiKey": api_key, "Content-Type": "application/json"}


@pytest.fixture
def valid_center_payload():
    """Retorna um payload válido para criação de centro comunitário."""
    return {
        "name": f"Centro Teste {uuid.uuid4().hex[:6]}",
        "address": "Rua Automação, 100",
        "maxNumberOfPeople": 200,
        "currentNumberOfPeople": 50,
        "resources": {
            "doctor": 3,
            "volunteer": 10,
            "medicalSuppliesKit": 5,
            "transportVehicle": 2,
            "basicFoodBasket": 20,
        },
    }


@pytest.fixture
def create_center(base_url, headers, valid_center_payload):
    """
    Factory fixture: cria um centro comunitário via API e retorna o ID.
    Ao final do teste exclui o centro para manter o ambiente limpo.
    """
    created_ids = []

    def _create(payload=None):
        body = payload if payload is not None else valid_center_payload
        resp = requests.post(f"{base_url}/communityCenter", json=body, headers=headers)
        assert resp.status_code == 201, f"Falha ao criar centro: {resp.text}"
        center_id = resp.json()["communityCenterId"]
        created_ids.append(center_id)
        return center_id

    yield _create

    # Teardown: remove todos os centros criados durante o teste
    for cid in created_ids:
        requests.delete(f"{base_url}/communityCenter/{cid}", headers=headers)

