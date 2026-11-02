import os
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi import Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .ai.interpreter import interpret
from .db import add_correction, archive_state, connect, correction_count, initialize, list_archives, load_state, recent_actions, record_action, restore_archive, save_state, useful_corrections, set_player_id, reset_player_id
from .engine.rules import apply_effects, forecast
from .engine.state import advance_state, new_game, refresh_calendar_fields
from .engine.events import ensure_event_state, respond_to_event
from .engine.politics import rupture_preview, attempt_rupture
from .engine.campaign import campaign_overview, perform_campaign_action
from .engine.career import career_options, career_overview, perform_career_action, perform_governance_action, start_career
from .engine.appointments import appointments_overview, appoint_minister, nominate_judge
from .engine.communications import require_inaugural_address, submit_inaugural_address
from .engine.ministries import ministry_catalog, INVESTMENT_AREAS
from .engine.difficulty import DIFFICULTIES
from .engine.fiscal import fiscal_overview, refresh_fiscal_metrics
from .engine.diplomacy import diplomacy_overview, visit_country, attend_international_event
from .engine.works import start_work, resolve_work_issue, refresh_work_finance, works_overview
from .bot.agent import choose_action

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

FISCAL_REFERENCE_GDP_BI = 15000.0
app = FastAPI(title="Mandato Game API", version="0.1.0")
origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
_jwks_clients: dict[str, Any] = {}
app.add_middleware(CORSMiddleware, allow_origins=[origin, "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def player_authentication(request: Request, call_next):
    """Use Cognito's immutable subject as the database owner; local mode stays single-player."""
    if not request.url.path.startswith("/api/") or request.url.path in {"/api/health", "/api/auth/config"} or request.method == "OPTIONS":
        return await call_next(request)
    region = os.getenv("COGNITO_REGION", "")
    pool_id = os.getenv("COGNITO_USER_POOL_ID", "")
    client_id = os.getenv("COGNITO_CLIENT_ID", "")
    if not any((region, pool_id, client_id)):
        token = set_player_id("local")
        try:
            blocked = _inauguration_gate(request)
            if blocked:
                return blocked
            return await call_next(request)
        finally:
            reset_player_id(token)
    if not all((region, pool_id, client_id)):
        return JSONResponse(status_code=503, content={"detail": "Autenticação Cognito incompleta na configuração do servidor."})
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return JSONResponse(status_code=401, content={"detail": "Entre na sua conta para continuar."})
    try:
        import jwt
        from jwt import PyJWKClient
        issuer = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
        jwks = f"{issuer}/.well-known/jwks.json"
        client = _jwks_clients.get(issuer)
        if client is None:
            client = _jwks_clients[issuer] = PyJWKClient(jwks)
        signing_key = client.get_signing_key_from_jwt(authorization[7:].strip()).key
        claims = jwt.decode(authorization[7:].strip(), signing_key, algorithms=["RS256"], issuer=issuer,
                            options={"verify_aud": False, "require": ["iss", "sub", "exp", "token_use", "client_id"]})
        if claims.get("token_use") != "access" or claims.get("client_id") != client_id:
            raise ValueError("JWT de acesso não corresponde ao cliente configurado")
        player_id = str(claims["sub"])
    except Exception:
        return JSONResponse(status_code=401, content={"detail": "Sessão inválida ou expirada. Entre novamente."})
    token = set_player_id(player_id)
    try:
        blocked = _inauguration_gate(request)
        if blocked:
            return blocked
        return await call_next(request)
    finally:
        reset_player_id(token)


class AdvanceRequest(BaseModel):
    days: int = Field(default=1, ge=1, le=90)


class MeasureRequest(BaseModel):
    text: str = Field(min_length=5, max_length=3000)


class ApplyRequest(MeasureRequest):
    interpretation: dict[str, Any]


class CorrectionRequest(BaseModel):
    original_text: str = Field(min_length=5, max_length=3000)
    corrected_interpretation: str = Field(min_length=3, max_length=5000)


class DifficultyRequest(BaseModel):
    difficulty: str = Field(pattern="^(tranquilo|normal|dificil|complicado|realismo_puro)$")


class DashboardRequest(BaseModel):
    cards: list[str] = Field(min_length=1, max_length=8)


class EventResponseRequest(BaseModel):
    choice: str = Field(min_length=1, max_length=40)


class BudgetTransferRequest(BaseModel):
    source: str
    target: str
    amount_bi: float = Field(gt=0, le=10)


class WorkStartRequest(BaseModel):
    work_id: str = Field(min_length=2, max_length=60)
    contractor_id: str = Field(min_length=2, max_length=60)


class WorkIssueRequest(BaseModel):
    project_id: str = Field(min_length=2, max_length=120)
    choice: str = Field(min_length=2, max_length=30)


class OperatingBudgetRequest(BaseModel):
    travel_cut_pct: int = Field(ge=0, le=75)
    residence_cut_pct: int = Field(ge=0, le=50)


class DiplomaticVisitRequest(BaseModel):
    country_code: str = Field(min_length=3, max_length=3)
    agenda: str = Field(pattern="^(trade|climate|science|security)$")


class DiplomaticEventRequest(BaseModel):
    event_id: str = Field(min_length=1, max_length=80)


class CampaignActionRequest(BaseModel):
    activity_type: str = Field(pattern="^(comicio|entrevista|debate|encontro)$")
    region: str = Field(pattern="^(norte|nordeste|centro_oeste|sudeste|sul)$")
    issue: str = Field(pattern="^(economia|seguranca|servicos|trabalho|integridade)$")
    message: str = Field(min_length=12, max_length=600)
    conduct: str = Field(default="regular", pattern="^(regular|irregular)$")


class CareerStartRequest(BaseModel):
    office: str = Field(min_length=3, max_length=40)
    state_code: str = Field(min_length=2, max_length=2)
    municipality: str = Field(min_length=2, max_length=80)
    party: str = Field(min_length=2, max_length=80)
    ideology: str = Field(min_length=2, max_length=40)
    candidate_name: str = Field(default="", max_length=80)


class CareerActionRequest(BaseModel):
    activity_type: str = Field(min_length=3, max_length=30)
    issue: str = Field(min_length=3, max_length=30)
    message: str = Field(min_length=12, max_length=600)
    conduct: str = Field(default="regular", pattern="^(regular|irregular)$")


class CareerGovernanceRequest(BaseModel):
    action: str = Field(min_length=3, max_length=40)
    issue: str = Field(default="", max_length=160)


class MinisterAppointmentRequest(BaseModel):
    ministry_id: str = Field(min_length=2, max_length=100)
    candidate_id: str = Field(min_length=2, max_length=100)


class SupremeCourtNominationRequest(BaseModel):
    candidate_id: str = Field(min_length=2, max_length=100)


class InauguralAddressRequest(BaseModel):
    text: str = Field(min_length=80, max_length=1200)


def _inauguration_gate(request: Request) -> JSONResponse | None:
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None
    if request.url.path in {
        "/api/game/inaugural-address",
        "/api/measures/preview",
        "/api/career/start",
        "/api/game/difficulty",
    }:
        return None
    state = load_state()
    if state is not None and require_inaugural_address(state):
        return JSONResponse(status_code=409, content={
            "detail": "Registre o pronunciamento obrigatório de posse antes de avançar o governo.",
            "action": "inaugural_address",
        })
    return None


def game_state() -> dict[str, Any]:
    state = load_state()
    if state is None:
        state = refresh_calendar_fields(new_game())
        save_state(state)
    state.setdefault("difficulty", "normal")
    state.setdefault("dashboard_cards", ["gdp_growth", "inflation", "unemployment", "debt_gdp", "primary_balance", "approval"])
    state.setdefault("term_start", "2027-01-01")
    state.setdefault("institutions", {"military_loyalty": 60, "constitutional_order": 65, "civilian_legitimacy": 55, "institutional_resistance": 50})
    state.setdefault("metrics", {}).setdefault("regional_infrastructure", 85)
    ensure_event_state(state)
    refresh_calendar_fields(state)
    return state


def require_presidential_authority(state: dict[str, Any], action: str) -> None:
    career = state.get("career") or {}
    if career.get("mode") and (career.get("office") != "presidente" or career.get("phase") != "office"):
        raise HTTPException(status_code=403, detail=f"{action} exige estar no exercício da Presidência nesta partida.")


def public_state(state: dict[str, Any]) -> dict[str, Any]:
    now = date.fromisoformat(state["date"])
    events = [{**event, "simulated": True, "days_until": (date.fromisoformat(event["date"]) - now).days}
              for event in state.get("events", [])
              if date.fromisoformat(event["date"]) >= now]
    executive_last = state.get("executive_calendar", {}).get("last_action")
    legislative_last = state.get("legislative_calendar", {}).get("last_submission")
    exec_cooldown = int(state.get("executive_calendar", {}).get("cooldown_days", 7))
    executive_wait = max(0, exec_cooldown - (now - date.fromisoformat(executive_last)).days) if executive_last else 0
    legislative_cooldown = int(state.get("legislative_calendar", {}).get("cooldown_days", 60))
    legislative_wait = max(0, legislative_cooldown - (now - date.fromisoformat(legislative_last)).days) if legislative_last else 0
    return {**state, "events": events, "active_crises": [c for c in state.get("active_crises", []) if c.get("status") == "active"],
            "action_limits": {"executive_days": executive_wait, "legislative_days": legislative_wait,
                              "pending_bills": len(state.get("legislative_calendar", {}).get("pending_bills", [])),
                              "laws_enacted": state.get("legislative_calendar", {}).get("laws_enacted", 0)},
            "simulated_news": state.get("simulated_news", []), "recent_actions": recent_actions(10, state.get("action_log_start_id"), state.get("action_log_end_id")),
            "campaign_overview": campaign_overview(state),
            "career_overview": career_overview(state),
            "learning": {"corrections_saved": correction_count()}}


@app.on_event("startup")
def startup() -> None:
    initialize()
    game_state()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "ai": "gemini" if os.getenv("GEMINI_API_KEY") else "local-fallback"}


@app.get("/api/auth/config")
def auth_config() -> dict[str, Any]:
    region = os.getenv("COGNITO_REGION", "")
    pool_id = os.getenv("COGNITO_USER_POOL_ID", "")
    client_id = os.getenv("COGNITO_CLIENT_ID", "")
    domain = os.getenv("COGNITO_DOMAIN", "")
    return {"enabled": bool(region and pool_id and client_id and domain), "region": region,
            "user_pool_id": pool_id, "client_id": client_id,
            "domain": domain}


@app.get("/api/bot/recommendation")
def bot_recommendation() -> dict[str, str]:
    decision = choose_action(game_state())
    return {"action": decision.action, "rationale": decision.rationale}


@app.get("/api/game/options")
def game_options() -> dict[str, Any]:
    return {"difficulties": DIFFICULTIES, "dashboard_cards": ["gdp_growth", "inflation", "unemployment", "debt_gdp", "primary_balance", "nominal_result", "country_risk", "fiscal_credibility", "approval", "governability", "integrity", "regional_infrastructure", "nominal_gdp_bi", "annual_revenue_bi", "annual_primary_spending_bi", "annual_interest_bi", "interest_rate_pct", "population_millions", "human_development_index", "gini_index", "poverty_rate_pct", "life_expectancy_years", "infant_mortality_per_1000", "homicide_rate_per_100k", "sanitation_coverage_pct", "school_completion_pct"]}


@app.get("/api/career/options")
def political_career_options() -> dict[str, Any]:
    return career_options(date.fromisoformat(game_state()["date"]))


@app.get("/api/game/archives")
def game_archives() -> dict[str, Any]:
    return {"items": list_archives()}


@app.post("/api/game/archives/{archive_id}/restore")
def restore_game_archive(archive_id: int) -> dict[str, Any]:
    snapshot = restore_archive(archive_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Esta partida arquivada não está disponível para sua conta.")
    current = game_state()
    archive_state(current, f"Partida anterior · {current.get('date', 'sem data')}")
    snapshot = refresh_calendar_fields(snapshot)
    save_state(snapshot)
    return {"state": public_state(snapshot), "archives": list_archives()}


@app.post("/api/career/start")
def begin_political_career(request: CareerStartRequest) -> dict[str, Any]:
    state = game_state()
    title = f"{state.get('career', {}).get('office_label', 'Presidência')} · {state.get('date', '')}"
    snapshot = deepcopy(state)
    continuing_career = bool((state.get("career") or {}).get("mode"))
    try:
        start_career(state, request.office, request.state_code.upper(), request.municipality,
                     request.party, request.ideology, request.candidate_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    archive_id = None if continuing_career else archive_state(snapshot, title)
    state.pop("action_log_end_id", None)
    refresh_calendar_fields(state)
    save_state(state)
    start_action_id = record_action(state["date"], "carreira", f"Início de carreira para {state['career']['office_label']}", "",
                                    request.model_dump(), [{"phase": state["career"]["phase"], "campaign_start": state["career"]["campaign_start"], "election_date": state["career"]["election_date"], "archived_game_id": archive_id, "continuing_character": continuing_career}])
    if not continuing_career:
        state["action_log_start_id"] = start_action_id
    save_state(state)
    return {"state": public_state(state), "archived_game_id": archive_id}


@app.get("/api/government/ministries")
def government_ministries() -> dict[str, Any]:
    return {"source": "SIORG", "as_of": "2026-11-01", "items": ministry_catalog()}


@app.get("/api/government/appointments")
def government_appointments() -> dict[str, Any]:
    state = game_state()
    data = appointments_overview(state)
    save_state(state)
    return data


@app.post("/api/government/appointments/minister")
def appoint_government_minister(request: MinisterAppointmentRequest) -> dict[str, Any]:
    state = game_state()
    require_presidential_authority(state, "Nomear ministros")
    try:
        result = appoint_minister(state, request.ministry_id, request.candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    action_date = state["date"]
    state, calendar_message = advance_state(state, 1)
    save_state(state)
    record_action(action_date, "nomeação", f"Ministro(a) de {result['ministry']}", result["appointed"]["name"],
                  request.model_dump(), [{"candidate": result["appointed"], "summary": result["summary"]}])
    return {"state": public_state(state), "result": result, "calendar_message": calendar_message,
            "appointments": appointments_overview(state)}


@app.post("/api/government/appointments/stf")
def nominate_supreme_court_judge(request: SupremeCourtNominationRequest) -> dict[str, Any]:
    state = game_state()
    require_presidential_authority(state, "Indicar ministro ao STF")
    try:
        result = nominate_judge(state, request.candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    action_date = state["date"]
    state, calendar_message = advance_state(state, 1)
    save_state(state)
    record_action(action_date, "nomeação", "Indicação simulada ao STF", result["nomination"]["name"],
                  request.model_dump(), [{"nomination": result["nomination"], "summary": result["summary"]}])
    return {"state": public_state(state), "result": result, "calendar_message": calendar_message,
            "appointments": appointments_overview(state)}


@app.get("/api/budget")
def budget_overview() -> dict[str, Any]:
    state = game_state()
    budget = state["budget"]
    works = works_overview(state)
    refresh_fiscal_metrics(state)
    return {"annual_investment_bi": budget["annual_investment_bi"], "allocations": budget["allocations"],
            "areas": INVESTMENT_AREAS, "pipeline": budget["pipeline"], "outcomes": budget["outcomes"],
            "last_reallocation": budget.get("last_reallocation"), "days_until_reallocation": max(0, 30 - ((date.fromisoformat(state["date"]) - date.fromisoformat(budget["last_reallocation"])).days if budget.get("last_reallocation") else 30)),
            "operating": operating_budget_summary(state), "fiscal": fiscal_overview(state), "works": works}


@app.post("/api/budget/works/start")
def award_public_work(request: WorkStartRequest) -> dict[str, Any]:
    state = game_state()
    require_presidential_authority(state, "Abrir leilão federal")
    if state.get("office_status") in {"former_president", "detained_after_failed_rupture"}:
        raise HTTPException(status_code=409, detail="Você não está no Executivo para abrir um leilão federal.")
    try:
        result = start_work(state, request.work_id, request.contractor_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    refresh_fiscal_metrics(state)
    save_state(state)
    record_action(state["date"], "obras", f"Leilão: {result['project']['name']}", "",
                  request.model_dump(), [{"contract_cost_bi": result["project"]["contract_cost_bi"],
                                          "annual_cost_bi": result["annual_cost_bi"],
                                          "target_completion": result["target_completion"]}])
    return {"state": public_state(state), "budget": budget_overview(), "result": result}


@app.post("/api/budget/works/resolve")
def decide_public_work_issue(request: WorkIssueRequest) -> dict[str, Any]:
    state = game_state()
    require_presidential_authority(state, "Administrar obras federais")
    try:
        result = resolve_work_issue(state, request.project_id, request.choice)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    refresh_fiscal_metrics(state)
    save_state(state)
    record_action(state["date"], "obras", "Resposta a ocorrência em obra", "",
                  request.model_dump(), [{"message": result["message"], "annual_overrun_bi": result["annual_overrun_bi"]}])
    return {"state": public_state(state), "budget": budget_overview(), "result": result}


def operating_budget_summary(state: dict[str, Any]) -> dict[str, Any]:
    budget = state["budget"].setdefault("operating", {})
    today = date.fromisoformat(state["date"])
    last = budget.get("last_review")
    wait = max(0, 30 - (today - date.fromisoformat(last)).days) if last else 0
    lines = budget.get("lines", {})
    travel = lines.get("official_travel", {})
    residence = lines.get("official_residence", {})
    travel_cut = int(budget.get("travel_cut_pct", 0))
    residence_cut = int(budget.get("residence_cut_pct", 0))
    travel_saving = round(float(travel.get("annual_cost_bi", 0)) * travel_cut / 100, 3)
    residence_saving = round(float(residence.get("annual_cost_bi", 0)) * residence_cut / 100, 3)
    travel_spent = float(budget.get("spent_by_year", {}).get(str(today.year), 0))
    travel_available = float(travel.get("annual_cost_bi", 0)) * (1 - travel_cut / 100)
    return {"lines": lines, "travel_cut_pct": travel_cut, "residence_cut_pct": residence_cut,
            "annual_savings_bi": round(travel_saving + residence_saving, 3), "days_until_review": wait,
            "last_review": last, "nominal_gdp_bi": FISCAL_REFERENCE_GDP_BI,
            "travel_spent_bi": round(travel_spent, 4), "travel_remaining_bi": round(max(0.0, travel_available - travel_spent), 4),
            "note": "Estimativas ficticias do simulador; cortes reduzem a despesa primaria anual e desaceleram a trajetoria da divida."}


@app.post("/api/budget/operating")
def adjust_operating_budget(request: OperatingBudgetRequest) -> dict[str, Any]:
    state = game_state()
    require_presidential_authority(state, "Revisar despesas da Presidência")
    if state.get("office_status") in {"former_president", "detained_after_failed_rupture"}:
        raise HTTPException(status_code=409, detail="Você não está no Executivo.")
    budget = state["budget"].setdefault("operating", {})
    today = date.fromisoformat(state["date"])
    last = budget.get("last_review")
    if last and (today - date.fromisoformat(last)).days < 30:
        wait = 30 - (today - date.fromisoformat(last)).days
        raise HTTPException(status_code=409, detail=f"As despesas de funcionamento foram revistas recentemente. Aguarde {wait} dia(s).")

    before_balance = float(state["metrics"].get("primary_balance", 0))
    before = operating_budget_summary(state)["annual_savings_bi"]
    budget["travel_cut_pct"] = request.travel_cut_pct
    budget["residence_cut_pct"] = request.residence_cut_pct
    after = operating_budget_summary(state)["annual_savings_bi"]
    budget["last_review"] = today.isoformat()
    delta_savings = after - before
    refresh_fiscal_metrics(state)
    balance_delta = float(state["metrics"]["primary_balance"]) - before_balance
    effects = [{"label": "Economia anual recorrente", "value_bi": round(delta_savings, 3)},
               {"label": "Resultado primário", "value_pct_gdp": round(balance_delta, 4)}]
    save_state(state)
    record_action(state["date"], "orçamento", "Revisão de viagens e residência oficial", "",
                  {"travel_cut_pct": request.travel_cut_pct, "residence_cut_pct": request.residence_cut_pct}, effects)
    return {"state": public_state(state), "budget": budget_overview(), "effects": effects}


@app.post("/api/budget/reallocate")
def reallocate_budget(request: BudgetTransferRequest) -> dict[str, Any]:
    state = game_state()
    require_presidential_authority(state, "Remanejar orçamento federal")
    if state.get("office_status") in {"former_president", "detained_after_failed_rupture"}:
        raise HTTPException(status_code=409, detail="Você não está no Executivo.")
    if request.source not in INVESTMENT_AREAS or request.target not in INVESTMENT_AREAS or request.source == request.target:
        raise HTTPException(status_code=422, detail="Escolha duas áreas de investimento existentes e diferentes.")
    budget = state["budget"]
    today = date.fromisoformat(state["date"])
    last = budget.get("last_reallocation")
    if last and (today - date.fromisoformat(last)).days < 30:
        wait = 30 - (today - date.fromisoformat(last)).days
        raise HTTPException(status_code=409, detail=f"O orçamento de investimento foi revisto recentemente. Aguarde {wait} dia(s).")
    amount = round(float(request.amount_bi), 1)
    available = float(budget["allocations"].get(request.source, 0))
    if amount > available * .2:
        raise HTTPException(status_code=422, detail="O remanejamento não pode retirar mais de 20% da dotação anual da área de origem.")
    budget["allocations"][request.source] = round(available - amount, 1)
    budget["allocations"][request.target] = round(float(budget["allocations"].get(request.target, 0)) + amount, 1)
    refresh_work_finance(state)
    refresh_fiscal_metrics(state)
    area = INVESTMENT_AREAS[request.target]
    completion = today + timedelta(days=area["lag_days"])
    project = {"id": f"invest-{today.isoformat()}-{request.target}", "area": request.target, "source_area": request.source,
               "annual_increase_bi": amount, "start_date": today.isoformat(), "completion_date": completion.isoformat(), "status": "em execução", "simulated": True}
    budget["pipeline"].append(project)
    budget["last_reallocation"] = today.isoformat()
    save_state(state)
    record_action(state["date"], "orçamento", f"Remanejamento para {area['label']}", "",
                  {"source": request.source, "target": request.target, "amount_bi": amount}, [project])
    return {"state": public_state(state), "project": project, "budget": budget_overview()}


@app.get("/api/diplomacy")
def get_diplomacy() -> dict[str, Any]:
    state = game_state()
    return diplomacy_overview(state)


@app.post("/api/diplomacy/visit")
def diplomatic_visit(request: DiplomaticVisitRequest) -> dict[str, Any]:
    state = game_state()
    require_presidential_authority(state, "Realizar visita diplomática")
    if state.get("office_status") in {"former_president", "detained_after_failed_rupture"}:
        raise HTTPException(status_code=409, detail="Voce nao esta no Executivo para realizar uma visita oficial.")
    try:
        result = visit_country(state, request.country_code, request.agenda)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    save_state(state)
    record_action(state["date"], "diplomacia", f"Visita oficial a {result['country']}", "", request.model_dump(), [result])
    return {"state": public_state(state), "diplomacy": diplomacy_overview(state), "result": result}


@app.post("/api/diplomacy/events/attend")
def attend_diplomatic_event(request: DiplomaticEventRequest) -> dict[str, Any]:
    state = game_state()
    require_presidential_authority(state, "Participar de evento diplomático")
    if state.get("office_status") in {"former_president", "detained_after_failed_rupture"}:
        raise HTTPException(status_code=409, detail="Voce nao esta no Executivo para representar o pais.")
    try:
        result = attend_international_event(state, request.event_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    save_state(state)
    record_action(state["date"], "diplomacia", f"Participação em {result['event']}", "", request.model_dump(), [result])
    return {"state": public_state(state), "diplomacy": diplomacy_overview(state), "result": result}


@app.get("/api/data/tse/candidates")
def find_tse_candidates(year: int | None = None, state_code: str | None = None,
                        office: str | None = None, search: str | None = None,
                        limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0)) -> dict[str, Any]:
    clauses, values = [], []
    if year is not None:
        clauses.append("election_year = ?"); values.append(year)
    if state_code:
        clauses.append("state = ?"); values.append(state_code.upper()[:2])
    if office:
        clauses.append("office LIKE ?"); values.append(f"%{office[:80]}%")
    if search:
        clauses.append("display_name LIKE ?"); values.append(f"%{search[:80]}%")
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with connect() as db:
        exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='tse_candidates'").fetchone()
        if not exists:
            return {"total": 0, "items": []}
        total = db.execute("SELECT COUNT(*) FROM tse_candidates" + where, values).fetchone()[0]
        rows = db.execute("SELECT election_year,candidate_id,display_name,party,office,state,municipality,result_status,profile_json,source_url,license_name,imported_at FROM tse_candidates" + where + " ORDER BY election_year DESC, display_name LIMIT ? OFFSET ?", (*values, limit, offset)).fetchall()
    return {"total": total, "items": [{**dict(row), "profile": json.loads(row["profile_json"])} for row in rows]}


@app.get("/api/data/tse/status")
def tse_data_status() -> dict[str, Any]:
    with connect() as db:
        exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='tse_candidates'").fetchone()
        if not exists:
            return {"ready": False, "years": [], "source": "TSE/AGEL", "source_url": "https://dadosabertos.tse.jus.br/group/candidatos"}
        years = db.execute("SELECT election_year,COUNT(*) AS candidate_count,MAX(imported_at) AS imported_at FROM tse_candidates GROUP BY election_year ORDER BY election_year DESC").fetchall()
    return {"ready": bool(years), "years": [dict(row) for row in years], "source": "TSE/AGEL",
            "source_url": "https://dadosabertos.tse.jus.br/group/candidatos"}


@app.patch("/api/game/difficulty")
def set_difficulty(request: DifficultyRequest) -> dict[str, Any]:
    state = game_state()
    state["difficulty"] = request.difficulty
    save_state(state)
    return public_state(state)


@app.patch("/api/game/dashboard")
def set_dashboard(request: DashboardRequest) -> dict[str, Any]:
    allowed = {"gdp_growth", "inflation", "unemployment", "debt_gdp", "primary_balance", "nominal_result", "country_risk", "fiscal_credibility", "approval", "governability", "integrity", "regional_infrastructure", "nominal_gdp_bi", "annual_revenue_bi", "annual_primary_spending_bi", "annual_interest_bi", "interest_rate_pct", "population_millions", "human_development_index", "gini_index", "poverty_rate_pct", "life_expectancy_years", "infant_mortality_per_1000", "homicide_rate_per_100k", "sanitation_coverage_pct", "school_completion_pct"}
    cards = list(dict.fromkeys(card for card in request.cards if card in allowed))
    if not cards:
        raise HTTPException(status_code=422, detail="Mantenha ao menos um indicador no painel.")
    state = game_state()
    state["dashboard_cards"] = cards
    save_state(state)
    return public_state(state)


@app.get("/api/game")
def get_game() -> dict[str, Any]:
    return public_state(game_state())


@app.post("/api/game/advance")
def advance(request: AdvanceRequest) -> dict[str, Any]:
    state, message = advance_state(game_state(), request.days)
    save_state(state)
    return {"state": public_state(state), "message": message}


@app.post("/api/game/inaugural-address")
def inaugural_address(request: InauguralAddressRequest) -> dict[str, Any]:
    state = game_state()
    action_date = state["date"]
    try:
        result = submit_inaugural_address(state, request.text)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    save_state(state)
    record_action(action_date, "pronunciamento", "Primeiro pronunciamento de posse", request.text,
                  {"required": True}, [result])
    return {"state": public_state(state), "result": result}


@app.post("/api/campaign/action")
def campaign_action(request: CampaignActionRequest) -> dict[str, Any]:
    state = game_state()
    if (state.get("career") or {}).get("mode"):
        raise HTTPException(status_code=409, detail="Use a campanha do cargo atual na aba Carreira.")
    action_date = state["date"]
    try:
        result = perform_campaign_action(state, request.activity_type, request.region, request.issue, request.message, request.conduct)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    state, calendar_message = advance_state(state, result["days_cost"])
    save_state(state)
    record_action(action_date, "campanha", result["activity"]["label"], request.message,
                  {"activity_type": request.activity_type, "region": request.region, "issue": request.issue},
                  [{"score": result["score"], "rubric": result["rubric"], "national_support": result["national_support"],
                    "regional_support": result["regional_support"], "cost_bi": result["cost_bi"], "days_cost": result["days_cost"]}])
    return {"state": public_state(state), "result": result, "calendar_message": calendar_message}


@app.post("/api/career/action")
def political_career_action(request: CareerActionRequest) -> dict[str, Any]:
    state = game_state()
    action_date = state["date"]
    try:
        result = perform_career_action(state, request.activity_type, request.issue, request.message, request.conduct)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    state, calendar_message = advance_state(state, result["days_cost"] or 1)
    save_state(state)
    record_action(action_date, "carreira", result["activity"]["label"], request.message,
                  {"activity_type": request.activity_type, "issue": request.issue},
                  [{"score": result["score"], "rubric": result["rubric"], "poll_support": result["poll_support"],
                    "local_support": result["local_support"], "state_support": result["state_support"],
                    "cost_mi": result["activity"]["cost_mi"], "days_cost": result["days_cost"]}])
    return {"state": public_state(state), "result": result, "calendar_message": calendar_message}


@app.post("/api/career/govern")
def political_governance_action(request: CareerGovernanceRequest) -> dict[str, Any]:
    state = game_state()
    action_date = state["date"]
    try:
        result = perform_governance_action(state, request.action, request.issue)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    save_state(state)
    record_action(action_date, "mandato", result["action"]["title"], request.issue,
                  {"action": request.action}, [{"summary": result["summary"], "cost_mi": result["action"]["cost_mi"], "status": result["action"]["status"]}])
    return {"state": public_state(state), "result": result}


@app.post("/api/events/{event_id}/respond")
def event_response(event_id: str, request: EventResponseRequest) -> dict[str, Any]:
    state = game_state()
    try:
        result = respond_to_event(state, event_id, request.choice)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    save_state(state)
    record_action(state["date"], "evento", "Resposta a crise simulada", request.choice,
                  {"event_id": event_id, "choice": request.choice}, [result])
    return {"state": public_state(state), "result": result}


@app.get("/api/regime/rupture/preview")
def get_rupture_preview() -> dict[str, Any]:
    state = game_state()
    require_presidential_authority(state, "Ação institucional da Presidência")
    return rupture_preview(state)


@app.post("/api/regime/rupture/attempt")
def rupture_attempt() -> dict[str, Any]:
    state = game_state()
    require_presidential_authority(state, "Ação institucional da Presidência")
    if state.get("office_status") in {"former_president", "detained_after_failed_rupture", "de_facto_ruler"}:
        raise HTTPException(status_code=409, detail="Esta rota não está disponível na situação atual do personagem.")
    result = attempt_rupture(state)
    save_state(state)
    record_action(state["date"], "instituições", "Tentativa de ruptura simulada", "", result, [])
    return {"state": public_state(state), "result": result}


@app.post("/api/measures/preview")
async def preview(request: MeasureRequest) -> dict[str, Any]:
    examples = useful_corrections(request.text)
    try:
        interpretation = await interpret(request.text, examples)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="A interpretação não pôde ser gerada. Tente novamente.") from exc
    instrument = interpretation.get("instrument", "")
    legal_timing = instrument in {"Projeto de Lei", "Projeto de Lei Complementar", "PEC"}
    timing = ("Envio ao Congresso; votação simulada após 90 a 150 dias. Os efeitos dependem de aprovação." if legal_timing
              else "Ato executivo sujeito ao intervalo da agenda; os efeitos começam quando aplicado.")
    return {"interpretation": interpretation, "forecast": forecast(game_state(), interpretation), "examples_used": len(examples), "timing": timing}


@app.post("/api/measures/apply")
def apply(request: ApplyRequest) -> dict[str, Any]:
    state = game_state()
    require_presidential_authority(state, "Assinar medida federal")
    if state.get("office_status") in {"former_president", "detained_after_failed_rupture"}:
        raise HTTPException(status_code=409, detail="Você não está mais no Executivo. Continue a carreira pelo módulo político quando ele estiver disponível.")
    interpretation = request.interpretation
    # Never accept model-supplied numerical forecasts from the browser.
    category = interpretation.get("category", "other")
    if category not in {"fiscal_efficiency", "business_formalization", "public_investment", "tax_change", "social_policy", "security", "communication", "other"}:
        category = "other"
    interpretation = {"title": str(interpretation.get("title", "Medida"))[:100], "category": category,
                      "instrument": str(interpretation.get("instrument", "Indefinido"))[:40],
                      "duration_days": min(1461, max(0, int(interpretation.get("duration_days", 0)))),
                      "fiscal_cost_bi": min(1000.0, max(0.0, float(interpretation.get("fiscal_cost_bi", 0))))}
    instrument = interpretation["instrument"].strip().lower()
    today = date.fromisoformat(state["date"])
    if instrument in {"projeto de lei", "projeto de lei complementar", "pec"}:
        calendar = state["legislative_calendar"]
        last = calendar.get("last_submission")
        interval = 180 if instrument == "pec" else 60
        if last and (today - date.fromisoformat(last)).days < interval:
            wait = interval - (today - date.fromisoformat(last)).days
            raise HTTPException(status_code=409, detail=f"A pauta legislativa já tem proposta recente. Aguarde {wait} dia(s) para enviar outro projeto.")
        bill_number = int(calendar.get("laws_enacted", 0)) + int(calendar.get("laws_failed", 0)) + len(calendar.get("pending_bills", [])) + 1
        bill = {"id": f"bill-{today.isoformat()}-{bill_number}", "title": interpretation["title"],
                "instrument": interpretation["instrument"], "submitted_date": today.isoformat(),
                "decision_date": (today + timedelta(days=150 if instrument in {"pec", "projeto de lei complementar"} else 90)).isoformat(), "status": "em tramitação",
                "interpretation": interpretation, "simulated": True}
        calendar["last_submission"] = today.isoformat()
        calendar["cooldown_days"] = interval
        calendar["pending_bills"].append(bill)
        save_state(state)
        record_action(state["date"], "projeto", interpretation["title"], request.text, interpretation, [bill])
        return {"state": public_state(state), "effects": [{"label": "Enviado ao Congresso", "status": "em tramitação", "decision_date": bill["decision_date"]}], "status": "pending_legislation"}
    else:
        executive_calendar = state["executive_calendar"]
        last_action = executive_calendar.get("last_action")
        cooldown = 30 if instrument == "medida provisória" else 7
        if last_action and (today - date.fromisoformat(last_action)).days < cooldown:
            wait = cooldown - (today - date.fromisoformat(last_action)).days
            raise HTTPException(status_code=409, detail=f"A agenda administrativa já foi usada recentemente. Aguarde {wait} dia(s).")
        executive_calendar["last_action"] = today.isoformat()
        executive_calendar["cooldown_days"] = cooldown
        effects = apply_effects(state, interpretation)
    save_state(state)
    record_action(state["date"], "medida", interpretation["title"], request.text, interpretation, effects)
    return {"state": public_state(state), "effects": effects, "status": "implemented"}


@app.post("/api/learning/corrections")
def save_correction(request: CorrectionRequest) -> dict[str, str]:
    add_correction(request.original_text, request.corrected_interpretation)
    return {"status": "saved"}
