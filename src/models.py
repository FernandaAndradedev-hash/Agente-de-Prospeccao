from dataclasses import dataclass, field
from enum import Enum


class LeadTemperature(str, Enum):
    
    HOT = "hot"       # score >= 70 — alta prioridade
    WARM = "warm"     # score 40-69 — média prioridade
    COLD = "cold"     # score < 40 — baixa prioridade


@dataclass
class Lead:
   
    company_name: str
    website: str
    sector: str
    city: str
    state: str
    employees_estimate: int
    contact_name: str
    contact_role: str
    contact_email: str


@dataclass
class FitAnalysis:
    
    score: int                    # 0 a 100
    temperature: LeadTemperature  # hot / warm / cold
    justification: str            # por que esse score
    strengths: list[str]          # pontos positivos
    objections: list[str]         # objeções prováveis
    suggested_approach: str       # como abordar esse lead


@dataclass
class EnrichedLead:
 
    lead: Lead
    fit: FitAnalysis
    hubspot_contact_id: str = ""   # preenchido após criar no HubSpot
    hubspot_deal_id: str = ""      # preenchido após criar no HubSpot
    error: str = ""                # mensagem de erro se algo falhou


@dataclass
class ProspectionReport:
    
    total_leads: int = 0
    hot_leads: int = 0
    warm_leads: int = 0
    cold_leads: int = 0
    created_in_hubspot: int = 0
    errors: int = 0
    results: list[EnrichedLead] = field(default_factory=list)