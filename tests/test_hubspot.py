import os
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-fake")
os.environ.setdefault("HUBSPOT_API_KEY", "test-key")

import json
from unittest.mock import MagicMock, patch

from models import EnrichedLead, FitAnalysis, Lead, LeadTemperature


SAMPLE_ENRICHED = EnrichedLead(
    lead=Lead(
        company_name="Empresa Teste",
        website="empresateste.com.br",
        sector="Varejo",
        city="São Paulo",
        state="SP",
        employees_estimate=100,
        contact_name="João Silva",
        contact_role="CEO",
        contact_email="joao@empresateste.com.br",
    ),
    fit=FitAnalysis(
        score=80,
        temperature=LeadTemperature.HOT,
        justification="Ótimo fit.",
        strengths=["Tamanho ideal"],
        objections=[],
        suggested_approach="Abordagem direta.",
    ),
)


class TestHubSpotClient:

    @patch("hubspot_client.httpx.Client")
    def test_contact_exists_retorna_id(self, mock_client_class):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"id": "123"}]}
        mock_client_class.return_value.__enter__.return_value.post.return_value = mock_response

        from hubspot_client import contact_exists
        result = contact_exists("joao@empresateste.com.br")
        assert result == "123"

    @patch("hubspot_client.httpx.Client")
    def test_contact_not_exists_retorna_none(self, mock_client_class):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_client_class.return_value.__enter__.return_value.post.return_value = mock_response

        from hubspot_client import contact_exists
        result = contact_exists("naoexiste@teste.com")
        assert result is None

    @patch("hubspot_client.httpx.Client")
    def test_create_contact_retorna_id(self, mock_client_class):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "456"}
        mock_response.raise_for_status = MagicMock()
        mock_client_class.return_value.__enter__.return_value.post.return_value = mock_response

        from hubspot_client import create_contact
        result = create_contact(SAMPLE_ENRICHED)
        assert result == "456"