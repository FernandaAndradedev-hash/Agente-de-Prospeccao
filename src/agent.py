import asyncio
import csv
import logging
from pathlib import Path

import config
from enricher import analyze_fit, enrich_with_hunter
from hubspot_client import push_to_hubspot
from models import EnrichedLead, Lead, LeadTemperature, ProspectionReport
from validators import validate_lead_row

logger = logging.getLogger(__name__)


def load_leads(csv_path: str) -> tuple[list[Lead], list[str]]:
    
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: '{csv_path}'")
    if path.suffix.lower() != ".csv":
        raise ValueError(f"Arquivo deve ser CSV, recebido: '{path.suffix}'")

    leads = []
    errors = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Verifica colunas obrigatórias
        required_cols = {
            "company_name", "website", "sector", "city", "state",
            "employees_estimate", "contact_name", "contact_role", "contact_email"
        }
        if not required_cols.issubset(set(reader.fieldnames or [])):
            missing = required_cols - set(reader.fieldnames or [])
            raise ValueError(f"Colunas faltando no CSV: {missing}")

        for i, row in enumerate(reader, start=2):  
            try:
                clean = validate_lead_row(row)
                leads.append(Lead(**clean))
            except ValueError as exc:
                error_msg = f"Linha {i}: {exc}"
                errors.append(error_msg)
                logger.warning(error_msg)

    logger.info(
        "CSV carregado: %d leads válidos, %d erros",
        len(leads),
        len(errors),
    )
    return leads, errors


async def process_lead(lead: Lead) -> EnrichedLead:
    
    try:
        # Enriquecimento opcional via Hunter.io
        domain = lead.website.replace("https://", "").replace("http://", "").split("/")[0]
        extra_data = await enrich_with_hunter(domain)

        # Análise de fit com Claude (síncrono — Claude SDK não tem async nativo)
        fit = await asyncio.to_thread(analyze_fit, lead, extra_data)

        return EnrichedLead(lead=lead, fit=fit)

    except Exception as exc:
        logger.error("Erro ao processar '%s': %s", lead.company_name, exc)
        from models import FitAnalysis
        return EnrichedLead(
            lead=lead,
            fit=FitAnalysis(
                score=0,
                temperature=LeadTemperature.COLD,
                justification="Erro de processamento.",
                strengths=[],
                objections=[],
                suggested_approach="",
            ),
            error=str(exc),
        )


async def run_prospection(
    csv_path: str,
    push_hubspot: bool = True,
) -> ProspectionReport:
   
    report = ProspectionReport()

    # Carrega leads
    leads, load_errors = load_leads(csv_path)
    report.total_leads = len(leads)
    report.errors = len(load_errors)

    if not leads:
        logger.warning("Nenhum lead válido encontrado no CSV.")
        return report

    # Processa em lotes para respeitar rate limits
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_LEADS)

    async def process_with_semaphore(lead: Lead) -> EnrichedLead:
        async with semaphore:
            return await process_lead(lead)

    logger.info("Iniciando análise de %d leads...", len(leads))
    enriched_leads = await asyncio.gather(
        *[process_with_semaphore(lead) for lead in leads]
    )

    # Contabiliza resultados
    for enriched in enriched_leads:
        if not enriched.error:
            temp = enriched.fit.temperature
            if temp == LeadTemperature.HOT:
                report.hot_leads += 1
            elif temp == LeadTemperature.WARM:
                report.warm_leads += 1
            else:
                report.cold_leads += 1

    # Envia para HubSpot
    if push_hubspot:
        logger.info("Enviando leads para o HubSpot...")
        for enriched in enriched_leads:
            if not enriched.error:
                enriched = push_to_hubspot(enriched)
                if enriched.hubspot_contact_id:
                    report.created_in_hubspot += 1
            else:
                report.errors += 1

    report.results = list(enriched_leads)
    return report


def save_report_csv(report: ProspectionReport, output_path: str) -> None:
    """
    Salva o relatório em CSV para análise posterior.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Empresa", "Setor", "Cidade", "Estado", "Funcionários",
            "Contato", "Cargo", "E-mail",
            "Score", "Temperatura",
            "Justificativa", "Abordagem Sugerida",
            "HubSpot Contato ID", "HubSpot Deal ID", "Erro"
        ])

        for enriched in report.results:
            lead = enriched.lead
            fit = enriched.fit
            writer.writerow([
                lead.company_name, lead.sector, lead.city, lead.state,
                lead.employees_estimate, lead.contact_name, lead.contact_role,
                lead.contact_email, fit.score, fit.temperature.value,
                fit.justification, fit.suggested_approach,
                enriched.hubspot_contact_id, enriched.hubspot_deal_id,
                enriched.error,
            ])

    logger.info("Relatório salvo em: %s", path)