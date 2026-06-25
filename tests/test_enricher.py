import os
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-fake")
os.environ.setdefault("HUBSPOT_API_KEY", "test-key")

import json
from unittest.mock import MagicMock, patch

import pytest
from models import Lead, LeadTemperature


SAMPLE_LEAD = Lead(
    company_name="Distribuidora Rápida Ltda",
    website="distribuidorarapida.com.br",
    sector="Logística",
    city="São Paulo",
    state="SP",
    employees_estimate=120,
    contact_name="Carlos Mendes",
    contact_role="Diretor de Operações",
    contact_email="carlos@distribuidorarapida.com.br",
)


class TestAnalyzeFit:

    @patch("enricher._client")
    def test_analise_retorna_fit_analysis(self, mock_client):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "score": 85,
            "justification": "Empresa de logística com bom fit.",
            "strengths": ["Setor de alto fit", "Tamanho ideal"],
            "objections": ["Pode já ter sistema"],
            "suggested_approach": "Foco na integração com sistemas existentes."
        }))]
        mock_client.messages.create.return_value = mock_response

        from enricher import analyze_fit
        result = analyze_fit(SAMPLE_LEAD)

        assert result.score == 85
        assert result.temperature == LeadTemperature.HOT
        assert len(result.strengths) == 2
        assert len(result.objections) == 1

    @patch("enricher._client")
    def test_score_acima_threshold_e_hot(self, mock_client):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "score": 75,
            "justification": "Bom fit.",
            "strengths": ["Tamanho ideal"],
            "objections": [],
            "suggested_approach": "Abordagem direta."
        }))]
        mock_client.messages.create.return_value = mock_response

        from enricher import analyze_fit
        result = analyze_fit(SAMPLE_LEAD)
        assert result.temperature == LeadTemperature.HOT

    @patch("enricher._client")
    def test_json_invalido_retorna_fallback(self, mock_client):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="isso não é json")]
        mock_client.messages.create.return_value = mock_response

        from enricher import analyze_fit
        result = analyze_fit(SAMPLE_LEAD)

        assert result.score == 50
        assert result.temperature == LeadTemperature.WARM
        assert "erro" in result.justification.lower()