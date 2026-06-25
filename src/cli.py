import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich import box

from agent import run_prospection, save_report_csv
from models import LeadTemperature

# Configuração do logging — só mostra WARNING+ para não poluir o output do Rich
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold blue]NovaTech Solutions[/bold blue]\n"
        "[dim]Agente de Prospecção Automática[/dim]",
        border_style="blue",
    ))


def print_summary(report):
    """Exibe resumo colorido no terminal."""
    console.print("\n")
    console.print(Panel(
        f"[bold]Total de leads:[/bold] {report.total_leads}\n"
        f"[bold red]Leads quentes:[/bold red] {report.hot_leads} 🔥\n"
        f"[bold yellow]Leads mornos:[/bold yellow] {report.warm_leads} ☀️\n"
        f"[bold blue]Leads frios:[/bold blue] {report.cold_leads} ❄️\n"
        f"[bold green]Criados no HubSpot:[/bold green] {report.created_in_hubspot}\n"
        f"[bold red]Erros:[/bold red] {report.errors}",
        title="📊 Resumo da Prospecção",
        border_style="green",
    ))


def print_results_table(report):
    """Exibe tabela detalhada de resultados."""
    table = Table(
        title="Resultados por Lead",
        box=box.ROUNDED,
        show_lines=True,
    )

    table.add_column("Empresa", style="bold")
    table.add_column("Setor", style="dim")
    table.add_column("Score", justify="center")
    table.add_column("Temperatura", justify="center")
    table.add_column("HubSpot", justify="center")

    for enriched in report.results:
        lead = enriched.lead
        fit = enriched.fit

        # Cor baseada na temperatura
        temp_colors = {
            LeadTemperature.HOT: "[bold red]🔥 HOT[/bold red]",
            LeadTemperature.WARM: "[bold yellow]☀️ WARM[/bold yellow]",
            LeadTemperature.COLD: "[bold blue]❄️ COLD[/bold blue]",
        }

        score_color = "red" if fit.score >= 70 else "yellow" if fit.score >= 40 else "blue"
        hubspot_status = "✅" if enriched.hubspot_contact_id else ("❌" if enriched.error else "—")

        table.add_row(
            lead.company_name,
            lead.sector,
            f"[{score_color}]{fit.score}/100[/{score_color}]",
            temp_colors.get(fit.temperature, str(fit.temperature)),
            hubspot_status,
        )

    console.print(table)


def main():
    print_banner()

    # Parâmetros — pode expandir com argparse no futuro
    csv_path = "data/leads.csv"
    no_hubspot = "--no-hubspot" in sys.argv

    if not Path(csv_path).exists():
        console.print(f"[bold red]Erro:[/bold red] Arquivo '{csv_path}' não encontrado.")
        console.print("Crie o arquivo com a lista de leads antes de executar.")
        sys.exit(1)

    push = not no_hubspot
    if not push:
        console.print("[yellow]Modo simulação — HubSpot desativado[/yellow]")

    console.print(f"\nProcessando leads de [bold]{csv_path}[/bold]...\n")

    # Executa o pipeline
    report = asyncio.run(run_prospection(csv_path, push_hubspot=push))

    # Exibe resultados
    print_results_table(report)
    print_summary(report)

    # Salva relatório CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/results/prospection_{timestamp}.csv"
    save_report_csv(report, output_path)
    console.print(f"\n[dim]Relatório salvo em: {output_path}[/dim]")


if __name__ == "__main__":
    main()