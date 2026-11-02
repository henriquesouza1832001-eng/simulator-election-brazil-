"""Simulated public-works portfolio with dated prices and deterministic incidents."""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

WORK_CATALOG: dict[str, dict[str, Any]] = {
    "br116_sul": {"name": "Corredor rodoviário Sul-Sudeste", "kind": "Rodovia", "route": "BR-116 · Sul e Sudeste", "regions": ["sul", "sudeste"], "base_cost_bi": 24.0, "duration_days": 1095, "risk": 0.10, "description": "Duplicação e adequação de trechos logísticos prioritários.", "effects": {"infrastructure": 2.0, "economic_activity": 1.2}},
    "fioleste": {"name": "Ferrovia de Integração Leste-Oeste", "kind": "Ferrovia", "route": "FIOL · Bahia e Centro-Oeste", "regions": ["nordeste", "centro_oeste"], "base_cost_bi": 48.0, "duration_days": 1825, "risk": 0.18, "description": "Implantação faseada de corredor ferroviário para carga e integração regional.", "effects": {"infrastructure": 3.0, "economic_activity": 1.8}},
    "hidrovia_tocantins": {"name": "Hidrovia Tocantins-Araguaia", "kind": "Hidrovia", "route": "Tocantins-Araguaia · Norte e Centro-Oeste", "regions": ["norte", "centro_oeste"], "base_cost_bi": 17.0, "duration_days": 1460, "risk": 0.16, "description": "Terminais, sinalização e navegabilidade, condicionados às licenças de cada trecho.", "effects": {"infrastructure": 1.8, "economic_activity": 1.4}},
    "hidrovia_paraguai": {"name": "Hidrovia do Paraguai", "kind": "Hidrovia", "route": "Pantanal · Centro-Oeste", "regions": ["centro_oeste"], "base_cost_bi": 11.0, "duration_days": 1095, "risk": 0.17, "description": "Modernização de terminais e segurança de navegação, com salvaguardas ambientais.", "effects": {"infrastructure": 1.4, "economic_activity": 1.0}},
    "porto_santos": {"name": "Acesso ferroviário e portuário de Santos", "kind": "Porto e ferrovia", "route": "Porto de Santos · Sudeste", "regions": ["sudeste"], "base_cost_bi": 19.0, "duration_days": 1095, "risk": 0.12, "description": "Acessos, pátios e integração de cargas para reduzir filas e gargalos.", "effects": {"infrastructure": 1.8, "economic_activity": 1.6}},
    "saneamento_norte": {"name": "Saneamento e drenagem de cidades do Norte", "kind": "Saneamento", "route": "Carteira regional · Norte", "regions": ["norte"], "base_cost_bi": 13.0, "duration_days": 1460, "risk": 0.12, "description": "Obras por lotes para água, esgoto e drenagem urbana resiliente.", "effects": {"infrastructure": 1.4, "economic_activity": 0.8}},
}

# All companies are invented game entities. Numbers represent gameplay tradeoffs.
CONTRACTORS: dict[str, dict[str, Any]] = {
    "consorcio_horizonte": {"name": "Consórcio Horizonte", "price_factor": 1.04, "financial_risk": 0.04, "integrity_risk": 0.04, "capacity": "Alta", "profile": "Mais caro; histórico simulado de entrega consistente."},
    "vias_do_centro": {"name": "Vias do Centro", "price_factor": 0.97, "financial_risk": 0.10, "integrity_risk": 0.09, "capacity": "Média", "profile": "Preço intermediário; risco moderado de atraso."},
    "consorcio_arco": {"name": "Consórcio Arco", "price_factor": 0.91, "financial_risk": 0.17, "integrity_risk": 0.18, "capacity": "Limitada", "profile": "Menor preço; maior risco de dificuldade financeira ou questionamento."},
}

def ensure_works_state(state: dict[str, Any]) -> dict[str, Any]:
    works = state.setdefault("budget", {}).setdefault("works", {})
    works.setdefault("price_index", 1.0)
    works.setdefault("last_index_date", state.get("date", "2027-01-01"))
    works.setdefault("projects", [])
    works.setdefault("annual_overrun_bi", 0.0)
    works.setdefault("last_award_date", None)
    return works


def _active(project: dict[str, Any]) -> bool:
    return project.get("status") in {"active", "needs_decision"}


def _current_cost(project: dict[str, Any], price_index: float) -> float:
    award_index = max(.01, float(project.get("award_price_index", 1)))
    return float(project.get("contract_cost_bi", 0)) * price_index / award_index


def _refresh_project_schedule(project: dict[str, Any], today: date) -> None:
    duration = max(1, int(project.get("duration_days", 1)))
    worked = min(duration, max(0, int(project.get("worked_days", 0))))
    project["progress"] = round(worked / duration, 4)
    project["target_completion"] = (today + timedelta(days=max(1, duration - worked))).isoformat()


def refresh_work_finance(state: dict[str, Any]) -> dict[str, Any]:
    works = ensure_works_state(state)
    projects = [item for item in works["projects"] if _active(item)]
    index = float(works["price_index"])
    annual_commitment = sum(_current_cost(item, index) * 365 / max(1, int(item["duration_days"])) for item in projects)
    logistics_budget = float(state.get("budget", {}).get("allocations", {}).get("logistics", 0))
    works["annual_commitment_bi"] = round(annual_commitment, 3)
    works["annual_overrun_bi"] = round(max(0.0, annual_commitment - logistics_budget), 3)
    return works


def works_overview(state: dict[str, Any]) -> dict[str, Any]:
    works = refresh_work_finance(state)
    index = float(works["price_index"])
    committed = float(works.get("annual_commitment_bi", 0))
    allocation = float(state.get("budget", {}).get("allocations", {}).get("logistics", 0))
    today = date.fromisoformat(state["date"])
    options = []
    for key, item in WORK_CATALOG.items():
        quoted = float(item["base_cost_bi"]) * index
        options.append({"id": key, **item, "quoted_cost_bi": round(quoted, 2),
                        "annual_cost_bi": round(quoted * 365 / item["duration_days"], 2),
                        "expected_completion": (today + timedelta(days=int(item["duration_days"]))).isoformat(),
                        "affordable": committed + quoted * 365 / item["duration_days"] <= allocation + 1e-9})
    projects = []
    for project in works["projects"]:
        projects.append({**project, "current_cost_bi": round(_current_cost(project, index), 2),
                         "current_annual_cost_bi": round(_current_cost(project, index) * 365 / max(1, int(project["duration_days"])), 2)})
    last_award = works.get("last_award_date")
    award_wait = max(0, 30 - (date.fromisoformat(state["date"]) - date.fromisoformat(last_award)).days) if last_award else 0
    return {"price_index": round(index, 4), "price_index_date": works["last_index_date"],
            "annual_allocation_bi": round(allocation, 2), "annual_committed_bi": round(committed, 2),
            "annual_available_bi": round(max(0, allocation - committed), 2),
            "annual_overrun_bi": works["annual_overrun_bi"], "days_until_next_award": award_wait, "options": options,
            "contractors": [{"id": key, **value} for key, value in CONTRACTORS.items()],
            "projects": projects,
            "price_note": "Valores-base em R$ de 2027. A projeção dos contratos ativos é corrigida pelo índice simulado (inflação + 1,5 p.p. ao ano); reajustes previstos elevam o custo fiscal estimado, enquanto o valor original do leilão permanece no histórico."}


def start_work(state: dict[str, Any], work_id: str, contractor_id: str) -> dict[str, Any]:
    if work_id not in WORK_CATALOG:
        raise ValueError("Escolha uma obra disponível no catálogo.")
    if contractor_id not in CONTRACTORS:
        raise ValueError("Escolha uma empresa do catálogo fictício.")
    budget = state.setdefault("budget", {})
    works = refresh_work_finance(state)
    last_award = works.get("last_award_date")
    if last_award and (date.fromisoformat(state["date"]) - date.fromisoformat(last_award)).days < 30:
        wait = 30 - (date.fromisoformat(state["date"]) - date.fromisoformat(last_award)).days
        raise ValueError(f"O próximo leilão federal simulado pode ser aberto em {wait} dia(s).")
    template = WORK_CATALOG[work_id]
    contractor = CONTRACTORS[contractor_id]
    today = date.fromisoformat(state["date"])
    index = float(works["price_index"])
    total = float(template["base_cost_bi"]) * index * float(contractor["price_factor"])
    annual = total * 365 / int(template["duration_days"])
    available = max(0.0, float(budget.get("allocations", {}).get("logistics", 0)) - float(works.get("annual_commitment_bi", 0)))
    if annual > available + 1e-9:
        raise ValueError(f"A obra exige cerca de R$ {annual:.2f} bi/ano, mas restam R$ {available:.2f} bi/ano na carteira de Transportes e logística. Remaneje orçamento antes de abrir o leilão.")
    project_id = f"obra-{work_id}-{today.isoformat()}-{len(works['projects']) + 1}"
    expected = today + timedelta(days=int(template["duration_days"]))
    project = {"id": project_id, "work_id": work_id, "name": template["name"], "kind": template["kind"],
               "route": template["route"], "regions": template["regions"], "description": template["description"],
               "contractor_id": contractor_id, "contractor": contractor["name"],
               "contract_cost_bi": round(total, 3), "award_price_index": index,
               "duration_days": int(template["duration_days"]), "start_date": today.isoformat(),
               "target_completion": expected.isoformat(), "worked_days": 0, "progress": 0.0,
               "risk": float(template["risk"]), "financial_risk": float(contractor["financial_risk"]),
               "integrity_risk": float(contractor["integrity_risk"]), "incidents_checked": [],
               "status": "active", "issue": None, "simulated": True}
    works["projects"].append(project)
    works["last_award_date"] = today.isoformat()
    refresh_work_finance(state)
    return {"project": project, "annual_cost_bi": round(annual, 2), "target_completion": expected.isoformat()}


def _open_issue(state: dict[str, Any], project: dict[str, Any], kind: str) -> str:
    if kind == "financial_distress":
        issue = {"kind": kind, "title": "Contratada em dificuldade financeira", "description": f"A empresa fictícia {project['contractor']} perdeu liquidez durante a obra {project['name']}. O cronograma para até uma decisão do governo.",
                 "options": [{"id": "rebid", "label": "Refazer o leilão", "detail": "+15% no custo contratado · +180 dias · troca para uma empresa de menor risco."},
                             {"id": "renegotiate", "label": "Renegociar e manter a empresa", "detail": "+8% no custo contratado · +90 dias."},
                             {"id": "cancel", "label": "Cancelar a obra", "detail": "Evita novos compromissos; a região perde a entrega planejada."}]}
    else:
        issue = {"kind": "integrity_review", "title": "Questionamento de integridade na contratação", "description": f"Um alerta fictício questiona a documentação do contrato de {project['name']}. Não representa acusação contra empresa real.",
                 "options": [{"id": "audit", "label": "Auditar e substituir a contratada", "detail": "+5% no custo · +90 dias · integridade do governo melhora com a apuração pública."},
                             {"id": "monitor", "label": "Manter com fiscalização reforçada", "detail": "Sem custo extra imediato · +30 dias · a exposição institucional continua."},
                             {"id": "cancel", "label": "Cancelar a obra", "detail": "Evita novos compromissos; a região perde a entrega planejada."}]}
    project["status"] = "needs_decision"
    project["issue"] = issue
    project["issue"]["opened_date"] = state["date"]
    state.setdefault("simulated_news", []).insert(0, {"id": f"news-{project['id']}-{kind}", "date": state["date"],
        "title": issue["title"], "region": "Nacional", "description": issue["description"], "simulated": True})
    state["simulated_news"] = state["simulated_news"][:20]
    return f"A obra {project['name']} parou para uma decisão: {issue['title'].lower()}."


def resolve_work_issue(state: dict[str, Any], project_id: str, choice: str) -> dict[str, Any]:
    works = ensure_works_state(state)
    project = next((item for item in works["projects"] if item["id"] == project_id), None)
    if not project or project.get("status") != "needs_decision" or not project.get("issue"):
        raise ValueError("Esta obra não tem uma decisão pendente.")
    issue = project["issue"]
    valid = {option["id"] for option in issue["options"]}
    if choice not in valid:
        raise ValueError("Escolha uma das respostas disponíveis para esta obra.")
    today = date.fromisoformat(state["date"])
    message = ""
    if choice == "cancel":
        project["status"] = "cancelled"
        project["cancelled_date"] = today.isoformat()
        for region in project["regions"]:
            state.setdefault("regional_metrics", {}).setdefault(region, {"support": 50, "infrastructure": 85, "economic_activity": 100})
            state["regional_metrics"][region]["support"] = max(0, float(state["regional_metrics"][region].get("support", 50)) - 2)
        message = f"Obra cancelada. Não haverá novos compromissos; o registro e os gastos já realizados permanecem na simulação."
    elif choice == "rebid":
        project["contract_cost_bi"] = round(float(project["contract_cost_bi"]) * 1.15, 3)
        safer = min(CONTRACTORS.items(), key=lambda entry: (entry[1]["financial_risk"] + entry[1]["integrity_risk"], entry[0]))
        project["contractor_id"], contractor = safer
        project["contractor"] = contractor["name"]
        project["financial_risk"] = contractor["financial_risk"]
        project["integrity_risk"] = contractor["integrity_risk"]
        project["duration_days"] += 180
        _refresh_project_schedule(project, today)
        project["status"] = "active"
        message = "Novo leilão simulado concluído: a obra continua com custo e prazo maiores."
    elif choice == "renegotiate":
        project["contract_cost_bi"] = round(float(project["contract_cost_bi"]) * 1.08, 3)
        project["duration_days"] += 90
        _refresh_project_schedule(project, today)
        project["status"] = "active"
        message = "Contrato renegociado na simulação; a execução continua com custo e prazo maiores."
    elif choice == "audit":
        project["contract_cost_bi"] = round(float(project["contract_cost_bi"]) * 1.05, 3)
        safer = min(CONTRACTORS.items(), key=lambda entry: (entry[1]["integrity_risk"], entry[0]))
        project["contractor_id"], contractor = safer
        project["contractor"] = contractor["name"]
        project["integrity_risk"] = contractor["integrity_risk"]
        project["duration_days"] += 90
        _refresh_project_schedule(project, today)
        project["status"] = "active"
        state["metrics"]["integrity"] = min(100, float(state["metrics"].get("integrity", 50)) + 2)
        state["metrics"]["institutional_trust"] = min(100, float(state["metrics"].get("institutional_trust", 50)) + 1)
        message = "A apuração e a troca de contratada foram registradas; a obra continua com atraso e custo adicionais."
    elif choice == "monitor":
        project["duration_days"] += 30
        _refresh_project_schedule(project, today)
        project["status"] = "active"
        state["metrics"]["integrity"] = max(0, float(state["metrics"].get("integrity", 50)) - 2)
        message = "A obra continua sob fiscalização reforçada; o alerta fica registrado e o prazo aumenta."
    project["issue"] = None
    project.setdefault("resolved_issues", []).append({"kind": issue["kind"], "choice": choice, "date": today.isoformat()})
    refresh_work_finance(state)
    return {"message": message, "project": project, "annual_overrun_bi": works["annual_overrun_bi"]}


def advance_works(state: dict[str, Any], before: date, after: date) -> list[str]:
    works = ensure_works_state(state)
    elapsed = max(0, (after - before).days)
    if elapsed:
        inflation = max(-2.0, float(state.get("metrics", {}).get("inflation", 4.5)))
        annual_price_growth = max(0.0, inflation + 1.5)
        works["price_index"] = float(works["price_index"]) * (1 + annual_price_growth / 100) ** (elapsed / 365)
        works["last_index_date"] = after.isoformat()
    messages: list[str] = []
    for project in works["projects"]:
        if project.get("status") != "active":
            continue
        duration = max(1, int(project["duration_days"]))
        previous_worked = min(duration, max(0, int(project.get("worked_days", 0))))
        target_worked = min(duration, previous_worked + elapsed)
        seed = str(state.get("campaign_seed", 203001))
        incidents = project.setdefault("incidents_checked", [])
        checkpoints = (("financial_distress", .35), ("integrity_review", .72))
        opened_issue = False
        for issue_kind, threshold in checkpoints:
            checkpoint_day = max(1, int(duration * threshold + .9999))
            if issue_kind in incidents or not (previous_worked < checkpoint_day <= target_worked):
                continue
            incidents.append(issue_kind)
            seed_kind = "financial" if issue_kind == "financial_distress" else "integrity"
            rng = random.Random(f"{seed}:{project['id']}:{seed_kind}")
            if issue_kind == "financial_distress":
                chance = min(.5, float(project["financial_risk"]) + float(project["risk"]) * .2)
            else:
                chance = min(.45, float(project["integrity_risk"]) + float(project["risk"]) * .2)
            if rng.random() < chance:
                project["worked_days"] = checkpoint_day
                _refresh_project_schedule(project, after)
                messages.append(_open_issue(state, project, issue_kind))
                opened_issue = True
                break
        if opened_issue:
            continue
        project["worked_days"] = target_worked
        _refresh_project_schedule(project, after)
        if project["progress"] >= 1:
            project["status"] = "delivered"
            completion_date = min(after, before + timedelta(days=max(1, duration - previous_worked)))
            project["delivery_date"] = completion_date.isoformat()
            project["target_completion"] = completion_date.isoformat()
            scale = min(2.0, float(project["contract_cost_bi"]) / 20)
            outcomes = state.setdefault("budget", {}).setdefault("outcomes", {})
            outcomes["infrastructure"] = min(100, float(outcomes.get("infrastructure", 50)) + float(WORK_CATALOG[project["work_id"]]["effects"]["infrastructure"]) * scale)
            state["metrics"]["gdp_growth"] = round(min(20, float(state["metrics"].get("gdp_growth", 2)) + .08 * scale), 2)
            state["metrics"]["regional_infrastructure"] = round(min(100, float(state["metrics"].get("regional_infrastructure", 85)) + .8 * scale), 1)
            for region in project["regions"]:
                region_state = state.setdefault("regional_metrics", {}).setdefault(region, {"support": 50, "infrastructure": 85, "economic_activity": 100})
                region_state["infrastructure"] = min(100, float(region_state.get("infrastructure", 85)) + float(WORK_CATALOG[project["work_id"]]["effects"]["infrastructure"]) * scale)
                region_state["economic_activity"] = min(150, float(region_state.get("economic_activity", 100)) + float(WORK_CATALOG[project["work_id"]]["effects"]["economic_activity"]) * scale)
            text = f"Obra simulada entregue: {project['name']} em {project['route']}."
            messages.append(text)
            state.setdefault("simulated_news", []).insert(0, {"id": f"news-{project['id']}-delivered", "date": completion_date.isoformat(), "title": f"Entrega: {project['name']}", "region": project["route"], "description": text, "simulated": True})
            state["simulated_news"] = state["simulated_news"][:20]
    refresh_work_finance(state)
    return messages
