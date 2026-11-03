"""Canonical topic IDs shared by municipal geography and campaign systems."""

ISSUE_LABELS: dict[str, str] = {
    "economia": "Economia e custo de vida",
    "trabalho": "Emprego e renda",
    "saude": "Saúde",
    "educacao": "Educação",
    "seguranca": "Segurança pública",
    "mobilidade": "Transporte e mobilidade",
    "integridade": "Transparência e integridade",
}

# Legacy IDs remain valid when reading or advancing old presidential campaign saves.
ISSUE_ALIASES: dict[str, tuple[str, ...]] = {
    "servicos": ("saude", "educacao"),
}


def issue_label(issue_id: str) -> str:
    if issue_id in ISSUE_LABELS:
        return ISSUE_LABELS[issue_id]
    if issue_id == "servicos":
        return "Saúde e educação"
    return issue_id.replace("_", " ").capitalize()


def canonical_issue_ids(issue_id: str) -> tuple[str, ...]:
    """Resolve a canonical ID or a documented legacy alias to its topic IDs."""
    if issue_id in ISSUE_LABELS:
        return (issue_id,)
    return ISSUE_ALIASES.get(issue_id, ())
