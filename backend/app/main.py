import os
from datetime import date, timedelta
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi import Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .ai.interpreter import interpret
from .db import add_correction, connect, correction_count, initialize, load_state, recent_actions, record_action, save_state, useful_corrections
from .engine.rules import apply_effects, forecast
from .engine.state import advance_state, new_game, refresh_calendar_fields
from .engine.events import ensure_event_state, respond_to_event
from .engine.politics import rupture_preview, attempt_rupture
from .engine.ministries import ministry_catalog, INVESTMENT_AREAS
from .engine.difficulty import DIFFICULTIES
from .engine.fiscal import fiscal_overview, refresh_fiscal_metrics
from .engine.diplomacy import diplomacy_overview, visit_country, attend_international_event
from .bot.agent import choose_action

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

FISCAL_REFERENCE_GDP_BI = 15000.0
app = FastAPI(title="Mandato Game API", version="0.1.0")
origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(CORSMiddleware, allow_origins=[origin, "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


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


class OperatingBudgetRequest(BaseModel):
    travel_cut_pct: int = Field(ge=0, le=75)
    residence_cut_pct: int = Field(ge=0, le=50)


class DiplomaticVisitRequest(BaseModel):
    country_code: str = Field(min_length=3, max_length=3)
    agenda: str = Field(pattern="^(trade|climate|science|security)$")


class DiplomaticEventRequest(BaseModel):
    event_id: str = Field(min_length=1, max_length=80)


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
            "simulated_news": state.get("simulated_news", []), "recent_actions": recent_actions(10),
            "learning": {"corrections_saved": correction_count()}}


@app.on_event("startup")
def startup() -> None:
    initialize()
    game_state()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "ai": "gemini" if os.getenv("GEMINI_API_KEY") else "local-fallback"}


@app.get("/api/bot/recommendation")
def bot_recommendation() -> dict[str, str]:
    decision = choose_action(game_state())
    return {"action": decision.action, "rationale": decision.rationale}


@app.get("/api/game/options")
def game_options() -> dict[str, Any]:
    return {"difficulties": DIFFICULTIES, "dashboard_cards": ["gdp_growth", "inflation", "unemployment", "debt_gdp", "primary_balance", "nominal_result", "country_risk", "fiscal_credibility", "approval", "governability", "integrity", "regional_infrastructure"]}


@app.get("/api/government/ministries")
def government_ministries() -> dict[str, Any]:
    return {"source": "SIORG", "as_of": "2026-11-01", "items": ministry_catalog()}


@app.get("/api/budget")
def budget_overview() -> dict[str, Any]:
    state = game_state()
    budget = state["budget"]
    return {"annual_investment_bi": budget["annual_investment_bi"], "allocations": budget["allocations"],
            "areas": INVESTMENT_AREAS, "pipeline": budget["pipeline"], "outcomes": budget["outcomes"],
            "last_reallocation": budget.get("last_reallocation"), "days_until_reallocation": max(0, 30 - ((date.fromisoformat(state["date"]) - date.fromisoformat(budget["last_reallocation"])).days if budget.get("last_reallocation") else 30)),
            "operating": operating_budget_summary(state), "fiscal": fiscal_overview(state)}


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


@app.patch("/api/game/difficulty")
def set_difficulty(request: DifficultyRequest) -> dict[str, Any]:
    state = game_state()
    state["difficulty"] = request.difficulty
    save_state(state)
    return public_state(state)


@app.patch("/api/game/dashboard")
def set_dashboard(request: DashboardRequest) -> dict[str, Any]:
    allowed = {"gdp_growth", "inflation", "unemployment", "debt_gdp", "primary_balance", "nominal_result", "country_risk", "fiscal_credibility", "approval", "governability", "integrity", "regional_infrastructure"}
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
    return rupture_preview(game_state())


@app.post("/api/regime/rupture/attempt")
def rupture_attempt() -> dict[str, Any]:
    state = game_state()
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
        raise HTTPException(status_code=502, detail=f"A interpretação não respondeu. Verifique a chave e o crédito Gemini. Detalhe: {str(exc)[:180]}") from exc
    instrument = interpretation.get("instrument", "")
    legal_timing = instrument in {"Projeto de Lei", "Projeto de Lei Complementar", "PEC"}
    timing = ("Envio ao Congresso; votação simulada após 90 a 150 dias. Os efeitos dependem de aprovação." if legal_timing
              else "Ato executivo sujeito ao intervalo da agenda; os efeitos começam quando aplicado.")
    return {"interpretation": interpretation, "forecast": forecast(game_state(), interpretation), "examples_used": len(examples), "timing": timing}


@app.post("/api/measures/apply")
def apply(request: ApplyRequest) -> dict[str, Any]:
    state = game_state()
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
