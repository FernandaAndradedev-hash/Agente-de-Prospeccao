import logging

import httpx

import config
from models import EnrichedLead, LeadTemperature

logger = logging.getLogger(__name__)

# URL base da API HubSpot v3
_BASE_URL = "https://api.hubapi.com/crm/v3"


def _headers() -> dict:
    
    return {
        "Authorization": f"Bearer {config.HUBSPOT_API_KEY}",
        "Content-Type": "application/json",
    }


def _get_deal_stage(temperature: LeadTemperature) -> str:
    
    mapping = {
        LeadTemperature.HOT: config.HUBSPOT_DEAL_STAGE_HOT,
        LeadTemperature.WARM: config.HUBSPOT_DEAL_STAGE_WARM,
        LeadTemperature.COLD: config.HUBSPOT_DEAL_STAGE_COLD,
    }
    return mapping.get(temperature, config.HUBSPOT_DEAL_STAGE_COLD)


def contact_exists(email: str) -> str | None:
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{_BASE_URL}/objects/contacts/search",
                headers=_headers(),
                json={
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "email",
                                    "operator": "EQ",
                                    "value": email,
                                }
                            ]
                        }
                    ],
                    "limit": 1,
                },
            )

            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    return results[0]["id"]

    except Exception as exc:
        logger.error("Erro ao verificar contato '%s': %s", email, exc)

    return None


def create_contact(enriched: EnrichedLead) -> str:
    
    lead = enriched.lead
    fit = enriched.fit

    # Monta nota com análise de fit
    fit_note = (
        f"Score de fit: {fit.score}/100 ({fit.temperature.value.upper()})\n"
        f"Análise: {fit.justification}\n"
        f"Pontos fortes: {', '.join(fit.strengths)}\n"
        f"Objeções prováveis: {', '.join(fit.objections)}\n"
        f"Abordagem sugerida: {fit.suggested_approach}"
    )

    contact_data = {
        "properties": {
            "firstname": lead.contact_name.split()[0],
            "lastname": " ".join(lead.contact_name.split()[1:]) or "-",
            "email": lead.contact_email,
            "jobtitle": lead.contact_role,
            "company": lead.company_name,
            "website": f"https://{lead.website}" if not lead.website.startswith("http") else lead.website,
            "city": lead.city,
            "state": lead.state,
            "numemployees": str(lead.employees_estimate),
            "industry": lead.sector,
            "hs_lead_status": "NEW",
            # Campo personalizado para o score — aparece no perfil do contato
            "description": fit_note,
        }
    }

    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            f"{_BASE_URL}/objects/contacts",
            headers=_headers(),
            json=contact_data,
        )
        response.raise_for_status()

    contact_id = response.json()["id"]
    logger.info(
        "Contato criado: '%s' (ID: %s | Score: %d)",
        lead.company_name,
        contact_id,
        fit.score,
    )
    return contact_id


def create_deal(enriched: EnrichedLead, contact_id: str) -> str:
    
    lead = enriched.lead
    fit = enriched.fit

    # Estimativa de valor baseada no tamanho da empresa
    # Lógica simples: base de R$800/mês × funcionários / 50 (proporção)
    estimated_value = min(
        max(800, (lead.employees_estimate // 50) * 800),
        5000
    ) * 12  # valor anual

    deal_name = (
        f"[{fit.temperature.value.upper()} | {fit.score}/100] "
        f"{lead.company_name} — NovaTech"
    )

    deal_data = {
        "properties": {
            "dealname": deal_name,
            "dealstage": _get_deal_stage(fit.temperature),
            "pipeline": config.HUBSPOT_PIPELINE_ID,
            "amount": str(estimated_value),
            "closedate": "",   # preenchido pelo time de vendas
            "description": fit.suggested_approach,
        }
    }

    with httpx.Client(timeout=10.0) as client:
        # Cria o deal
        response = client.post(
            f"{_BASE_URL}/objects/deals",
            headers=_headers(),
            json=deal_data,
        )
        response.raise_for_status()
        deal_id = response.json()["id"]

        # Associa deal ao contato
        client.put(
            f"{_BASE_URL}/objects/deals/{deal_id}/associations/contacts/{contact_id}/deal_to_contact",
            headers=_headers(),
        )

    logger.info(
        "Deal criado: '%s' (ID: %s | Valor estimado: R$ %s)",
        deal_name,
        deal_id,
        f"{estimated_value:,.0f}",
    )
    return deal_id


def push_to_hubspot(enriched: EnrichedLead) -> EnrichedLead:
    
    try:
        # Verifica duplicata
        existing_id = contact_exists(enriched.lead.contact_email)

        if existing_id:
            logger.info(
                "Contato já existe no HubSpot: '%s' (ID: %s). Pulando.",
                enriched.lead.company_name,
                existing_id,
            )
            enriched.hubspot_contact_id = existing_id
            return enriched

        # Cria contato
        contact_id = create_contact(enriched)
        enriched.hubspot_contact_id = contact_id

        # Cria deal apenas para leads quentes e mornos
        if enriched.fit.temperature != LeadTemperature.COLD:
            deal_id = create_deal(enriched, contact_id)
            enriched.hubspot_deal_id = deal_id

    except httpx.HTTPStatusError as exc:
        error_msg = f"HubSpot API error {exc.response.status_code}: {exc.response.text[:200]}"
        logger.error("Erro ao criar '%s' no HubSpot: %s", enriched.lead.company_name, error_msg)
        enriched.error = error_msg

    except Exception as exc:
        logger.error("Erro inesperado para '%s': %s", enriched.lead.company_name, exc)
        enriched.error = str(exc)

    return enriched