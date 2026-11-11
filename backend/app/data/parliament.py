"""Importa a composição atual do Congresso a partir de dados abertos oficiais.

Fontes: API de Dados Abertos da Câmara dos Deputados e do Senado Federal.
Guardamos apenas nome parlamentar, partido, UF e identificador público; e-mails
e outros contatos não são copiados. Uso: python -m app.data.parliament
"""
from __future__ import annotations

import json
import urllib.request
from datetime import date
from pathlib import Path

CAMARA = "https://dadosabertos.camara.leg.br/api/v2/deputados?itens=100&pagina={page}&ordem=ASC&ordenarPor=nome"
SENADO = "https://legis.senado.leg.br/dadosabertos/senador/lista/atual"
OUT = Path(__file__).resolve().parents[2] / "data" / "parliament.json"


def _get(url: str) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "civiciclo-importador"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def collect() -> dict:
    deputies, page = [], 1
    while True:
        rows = _get(CAMARA.format(page=page)).get("dados", [])
        if not rows:
            break
        deputies += [{"id": r["id"], "name": r["nome"], "party": r["siglaPartido"], "state": r["siglaUf"]} for r in rows]
        page += 1
    senators = []
    for item in _get(SENADO)["ListaParlamentarEmExercicio"]["Parlamentares"]["Parlamentar"]:
        ident = item["IdentificacaoParlamentar"]
        senators.append({"id": int(ident["CodigoParlamentar"]), "name": ident["NomeParlamentar"],
                         "party": ident.get("SiglaPartidoParlamentar", ""), "state": ident.get("UfParlamentar", "")})
    return {
        "collected_on": date.today().isoformat(),
        "sources": [CAMARA.split("?")[0], SENADO],
        "license_note": "Dados abertos oficiais do Poder Legislativo; verifique os termos de uso nos portais de origem.",
        "camara": deputies, "senado": senators,
    }


if __name__ == "__main__":
    data = collect()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(data["camara"]), "deputados;", len(data["senado"]), "senadores ->", OUT)
