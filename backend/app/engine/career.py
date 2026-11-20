"""Reusable political-career and election loop for all simulated offices.

All candidates, polls, votes and people generated here belong to the fictional
simulation. The rules are deliberately explicit so the UI can explain outcomes.
"""

# Fachada: o ciclo de carreira foi dividido por responsabilidade (career_*.py). Todos os nomes continuam importáveis daqui.
from __future__ import annotations

from . import seats as seats_for, tv_time

import random
import re
import unicodedata
import json
from math import sqrt
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .communications import ensure_communications_state
from .electoral_integrity import campaign_conduct_preview, resolve_campaign_conduct, settle_campaign_conduct
from .geography import get_municipality, get_state_population, resolve_municipality
from .issues import ISSUE_LABELS

from .career_base import (  # noqa: F401
    ACTIVITIES,
    APPOINTED_PATHS,
    CUSTOM_PARTY_BLOCKLIST,
    DEBATE_QUESTIONS,
    DEBATE_REPLIES,
    EXECUTIVE_BUDGET_BASELINES,
    EXECUTIVE_SERVICE_ACCESS,
    EXECUTIVE_SERVICE_BASE_COSTS,
    FAMILY_GROUP_EFFECTS,
    GROUPS,
    IDEOLOGY_SPECTRUM,
    ISSUES,
    LEGISLATIVE_ACTIONS,
    LEGISLATIVE_ACTIONS_BY_OFFICE,
    LEGISLATIVE_OFFICES,
    MAX_PRE_CAMPAIGN_ORGANIZATION,
    OFFICES,
    OPPONENT_CANDIDATE_POOL,
    PARTY_CATALOG_PATH,
    PRE_CAMPAIGN_ACTIONS,
    PROMISE_LANGUAGE_PATTERNS,
    PROMISE_LIMIT,
    PROMISE_MINIMUM_CHANGE,
    PROMISE_OUTCOMES,
    PROMISE_REVIEW_DAYS,
    SERVICE_AREAS,
    SPECTRUM_GROUP_EFFECTS,
    SPECTRUM_ORDER,
    STATES,
    STATE_CAPITALS,
    STATE_NAMES,
    STATE_REGIONS,
    TRAVEL_ACTIVITIES,
    _clamp,
    _inauguration_date,
    _norm,
    _regular_election_day,
    _term_end_date,
)
from .career_access import (  # noqa: F401
    _campaign,
    _campaign_team_location_id,
    _speech_score,
    is_career_governing,
)
from .career_setup import (  # noqa: F401
    career_options,
    validate_party_name,
)
from .career_polls import (  # noqa: F401
    _campaign_poll_schedule,
    _ensure_opponents,
    _opponent_supports,
    _projected_public_poll_support,
    _public_poll_sample_size,
    _record_public_poll,
    _requires_second_round,
    _runoff_vote_results,
    _spectrum_index,
)
from .career_promises import (  # noqa: F401
    _activate_campaign_promises,
    _is_explicit_promise,
    _promise_baseline,
    _promise_evidence,
    _promise_rule,
    _record_campaign_promise,
    _review_campaign_promises,
)
from .career_governance import (  # noqa: F401
    _ensure_scaled_governance_budget,
    _executive_annual_budget_mi,
    _executive_population_basis,
    _format_population_count,
    _historical_compare,
    _presidential_investment_cap_mi,
    _presidential_investment_commitment_mi,
    _publish_governance_report,
    _reference_election,
    career_debate_prompt,
    governance_actions_for,
    governance_territory_for,
    perform_governance_action,
)
from .career_overview import (  # noqa: F401
    _goals,
    career_overview,
)
from .career_action import (  # noqa: F401
    _forecast,
    perform_career_action,
    perform_career_preparation,
)
from .career_start import (  # noqa: F401
    start_career,
)
from .career_election import (  # noqa: F401
    LEGEND_VOTE_SHARE,
    LIST_MATE_MEAN,
    LIST_MATE_SD,
    TURNOUT_VALID,
    _list_mate_names,
    _proportional_electorate,
    _proportional_result,
    resolve_career_election,
)
from .career_calendar import advance_career  # noqa: F401
