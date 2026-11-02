"""Political career graph and unlock checks. Real law-specific rules belong in data/legal_rules."""

CAREER_STAGES = {
    "community": {"label": "Liderança comunitária", "elected": False, "next": ["vereador"]},
    "vereador": {"label": "Vereador(a)", "elected": True, "next": ["prefeito", "deputado_estadual", "deputado_federal"]},
    "prefeito": {"label": "Prefeito(a)", "elected": True, "next": ["deputado_estadual", "deputado_federal", "governador", "senador"]},
    "deputado_estadual": {"label": "Deputado(a) estadual", "elected": True, "next": ["prefeito", "deputado_federal", "governador", "senador"]},
    "deputado_federal": {"label": "Deputado(a) federal", "elected": True, "next": ["prefeito", "governador", "senador", "presidente"]},
    "senador": {"label": "Senador(a)", "elected": True, "next": ["governador", "presidente"]},
    "governador": {"label": "Governador(a)", "elected": True, "next": ["senador", "presidente"]},
    "ministro": {"label": "Ministro(a)", "elected": False, "next": ["deputado_federal", "senador", "governador", "presidente"]},
    "presidente": {"label": "Presidente(a)", "elected": True, "next": []},
    "stf_indicado": {"label": "Indicado(a) ao STF", "elected": False, "next": []},
}


def can_run_for(current_stage: str, target_stage: str, popularity: float, eligibility: dict) -> tuple[bool, str]:
    if target_stage not in CAREER_STAGES.get(current_stage, {}).get("next", []):
        return False, "Esse caminho ainda não está disponível a partir do cargo atual."
    if target_stage in {"governador", "senador", "presidente"} and popularity < 35:
        return False, "A popularidade ainda não sustenta uma candidatura competitiva nesse nível."
    if not eligibility.get(target_stage, True):
        return False, "O perfil ainda não cumpre os requisitos configurados para essa candidatura."
    return True, "Candidatura disponível."


def appointment_pool(role: str, known_profiles: list[dict], count: int = 5) -> list[dict]:
    """Select from qualified public profiles when possible; otherwise create fictional people."""
    qualified = [p for p in known_profiles if role in p.get("eligible_roles", [])]
    return qualified[:count]
