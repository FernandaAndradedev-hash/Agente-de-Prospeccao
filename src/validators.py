import re
import logging

logger = logging.getLogger(__name__)

# Regex para validação de e-mail (padrão RFC 5322 simplificado)
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

# Regex para website (com ou sem https://)
_WEBSITE_RE = re.compile(
    r"^(https?://)?"
    r"([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+"
    r"[a-zA-Z]{2,}$"
)

# Injeção de prompt via CSV — alguém pode colocar instruções nos dados
_INJECTION_RE = re.compile(
    r"ignore\s+.*instructions?|"
    r"you\s+are\s+now|"
    r"forget\s+everything|"
    r"new\s+instructions?:|"
    r"system\s+prompt",
    re.IGNORECASE,
)

# Estados brasileiros válidos
_VALID_STATES = {
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
    "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
    "RS","RO","RR","SC","SP","SE","TO"
}


def validate_lead_row(row: dict) -> dict:
  
    errors = []

    # company_name
    company = str(row.get("company_name", "")).strip()
    if not company or len(company) < 2:
        errors.append("company_name inválido")
    if _INJECTION_RE.search(company):
        errors.append("company_name contém conteúdo inválido")

    # website
    website = str(row.get("website", "")).strip().lower()
    if not website or not _WEBSITE_RE.match(website):
        errors.append(f"website inválido: '{website}'")

    # sector
    sector = str(row.get("sector", "")).strip()
    if not sector or len(sector) < 2:
        errors.append("sector inválido")

    # city e state
    city = str(row.get("city", "")).strip()
    if not city:
        errors.append("city inválido")

    state = str(row.get("state", "")).strip().upper()
    if state not in _VALID_STATES:
        errors.append(f"state inválido: '{state}'")

    # employees_estimate
    try:
        employees = int(row.get("employees_estimate", 0))
        if employees < 1 or employees > 100000:
            errors.append(f"employees_estimate fora do range: {employees}")
    except (ValueError, TypeError):
        errors.append("employees_estimate deve ser um número")
        employees = 0

    # contact_name
    contact_name = str(row.get("contact_name", "")).strip()
    if not contact_name or len(contact_name) < 3:
        errors.append("contact_name inválido")

    # contact_role
    contact_role = str(row.get("contact_role", "")).strip()
    if not contact_role:
        errors.append("contact_role inválido")

    # contact_email
    contact_email = str(row.get("contact_email", "")).strip().lower()
    if not contact_email or not _EMAIL_RE.match(contact_email):
        errors.append(f"contact_email inválido: '{contact_email}'")

    if errors:
        raise ValueError(
            f"Lead '{company}' tem {len(errors)} erro(s): {'; '.join(errors)}"
        )

    return {
        "company_name": company,
        "website": website,
        "sector": sector,
        "city": city,
        "state": state,
        "employees_estimate": employees,
        "contact_name": contact_name,
        "contact_role": contact_role,
        "contact_email": contact_email,
    }


def sanitize_for_llm(text: str, max_length: int = 500) -> str:
  
    if not isinstance(text, str):
        text = str(text)

    # Remove possíveis injeções
    if _INJECTION_RE.search(text):
        logger.warning("Possível injeção detectada em dados do lead: %r", text[:50])
        return "[conteúdo removido por segurança]"

    # Trunca se necessário
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text.strip()