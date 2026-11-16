"""Baixa as malhas municipais do IBGE (contorno de cada município) e as grava em backend/data/malhas/<UF>.json.

Uso (na pasta backend):
    .venv/Scripts/python.exe scripts/baixar_malhas_ibge.py            # todos os estados
    .venv/Scripts/python.exe scripts/baixar_malhas_ibge.py SP MG      # só alguns

Fonte: API de malhas do IBGE (qualidade mínima, já simplificada). Cada arquivo guarda o viewBox e os caminhos SVG por
código IBGE do município, em unidades de 0,0001 grau, prontos para desenhar com scale(0.0001, -0.0001). Só roda quando
as malhas mudam; os arquivos vão para o repositório para o jogo funcionar sem internet.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import httpx

UF_CODE = {"AC": 12, "AL": 27, "AP": 16, "AM": 13, "BA": 29, "CE": 23, "DF": 53, "ES": 32, "GO": 52, "MA": 21, "MT": 51, "MS": 50, "MG": 31, "PA": 15,
           "PB": 25, "PR": 41, "PE": 26, "PI": 22, "RJ": 33, "RN": 24, "RS": 43, "RO": 11, "RR": 14, "SC": 42, "SP": 35, "SE": 28, "TO": 17}
URL = "https://servicodados.ibge.gov.br/api/v3/malhas/estados/{code}?formato=image/svg%2Bxml&qualidade=minima&intrarregiao=municipio"
OUT = Path(__file__).resolve().parents[1] / "data" / "malhas"


def parse(svg: str) -> dict:
    view = re.search(r'viewBox="([^"]+)"', svg)
    items = [{"id": m.group(1), "d": m.group(2)} for m in re.finditer(r'<path id="(\d+)" d="([^"]+)"', svg)]
    if not view or not items:
        raise ValueError("SVG inesperado")
    return {"viewBox": view.group(1), "unit": 0.0001, "fonte": "IBGE, malhas municipais (qualidade mínima)", "items": items}


def main() -> int:
    ufs = [u.upper() for u in sys.argv[1:]] or list(UF_CODE)
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        for uf in ufs:
            r = client.get(URL.format(code=UF_CODE[uf]))
            r.raise_for_status()
            data = parse(r.text)
            (OUT / f"{uf}.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
            size = (OUT / f"{uf}.json").stat().st_size
            total += size
            print(f"{uf}: {len(data['items'])} municípios, {size / 1024:.0f} KB", flush=True)
    print(f"Total: {total / 1024 / 1024:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
