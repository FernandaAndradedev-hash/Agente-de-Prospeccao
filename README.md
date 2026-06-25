# Agente de Prospecção e CRM Automático — NovaTech Solutions
 
> Agente autônomo que pesquisa leads, analisa fit com IA, enriquece dados e cria contatos e deals automaticamente no HubSpot.
 
---
 
## Sobre o projeto
 
Agente de prospecção B2B para a **NovaTech Solutions**, empresa fictícia de SaaS. O agente recebe uma lista de empresas-alvo, pesquisa informações publicamente disponíveis, analisa o perfil de cada lead com Claude, pontua o fit com o produto e cria automaticamente contatos e deals no HubSpot.
 
---
 
## Funcionalidades
 
- Lê lista de empresas-alvo de um arquivo CSV
- Enriquece dados via web search (Hunter.io opcional)
- Analisa fit e pontua cada lead com Claude
- Cria contatos e deals no HubSpot automaticamente
- Gera relatório final em CSV com scores e status
- Rate limiting, validação de dados e proteção de API keys
---
 
## Stack
 
| Camada | Tecnologia | Função |
|--------|-----------|--------|
| Orquestração | Python async | Processa leads em paralelo |
| Análise de fit | Anthropic Claude Haiku | Pontua e analisa cada lead |
| Enriquecimento | Hunter.io API (opcional) | Busca e-mails corporativos |
| CRM | HubSpot API v3 | Cria contatos e deals |
| Relatório | CSV + Rich | Saída formatada no terminal |

---

## Licença
 
Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.