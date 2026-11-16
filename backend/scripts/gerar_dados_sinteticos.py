"""Dados sintéticos para treinar os modelos pequenos do jogo, usando o GPT-6 Luna como professor, fora do jogo.

Uso (na pasta backend):
    .venv/Scripts/python.exe scripts/gerar_dados_sinteticos.py                       # estimativa de custo, sem rede
    .venv/Scripts/python.exe scripts/gerar_dados_sinteticos.py --conjunto propostas --total 2000
    .venv/Scripts/python.exe scripts/gerar_dados_sinteticos.py --conjunto propostas --total 200 --executar --limite-usd 2

ESTADO: a estimativa e a montagem dos pedidos estão testadas. A chamada real à API (--executar) NÃO foi testada,
porque exige uma chave da OpenAI (OPENAI_API_KEY no ambiente ou em backend/.env, que o Git ignora; nunca no chat).
Teste primeiro com --total 20 e confira os arquivos antes de gerar em escala.

Regras: os exemplos saem com review="pendente" e proveniência (modelo, data, versão do pedido). Nada entra no jogo sem
revisão humana por amostragem e sem passar nas mesmas travas do motor (números e nomes só dos fatos fornecidos).
Não envie dados pessoais nem dados de jogadores. Confira os termos de uso da OpenAI sobre uso das saídas para treino.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-6-luna"
# Preço por milhão de tokens divulgado por agregadores (entrada, saída). CONFIRA na página oficial antes de gastar.
PRICE_IN_USD, PRICE_OUT_USD = 0.10, 0.50
PROMPT_VERSION = "2026-11-15.1"
OFFICES = ["vereador", "prefeito", "deputado estadual", "deputado federal", "senador", "governador", "presidente"]
THEMES = ["saúde", "educação", "segurança", "economia", "meio ambiente", "transporte", "habitação", "energia", "agricultura", "assistência social", "ciência e espaço", "tributos"]
STYLES = ["objetivo e técnico", "emocional e popular", "vago e cheio de promessas", "com custo e prazo explícitos", "com erro de português e gírias", "longo e burocrático"]
KINDS = {
    "propostas": {"per_request": 10, "in_tokens": 450, "out_per_item": 90,
                  "ask": "Escreva {n} propostas de políticas públicas que um(a) {cargo} do Brasil poderia digitar em um simulador, sobre {tema}, em estilo {estilo}. "
                         "Para cada uma, dê o rótulo correto: category (fiscal_efficiency, public_investment, social_policy, tax_change, security, economico, other), "
                         "instrument (Decreto, Projeto de Lei, Projeto de Lei Complementar, PEC, Medida provisória) e policy_area. Só JSON: lista de objetos {text, category, instrument, policy_area}.",
                  "axes": [OFFICES, THEMES, STYLES]},
    "manchetes": {"per_request": 8, "in_tokens": 300, "out_per_item": 40,
                  "ask": "Escreva {n} manchetes curtas e neutras sobre o fato: {tema}, no tom {estilo}, para um simulador político fictício. Não cite pessoas reais. Só JSON: lista de strings.",
                  "axes": [["decisão aprovada pelo Congresso", "crise de enchente", "alta da inflação", "queda de aprovação", "resultado de eleição", "veto presidencial"], ["neutro", "irônico", "dramático"]]},
    "perguntas": {"per_request": 6, "in_tokens": 300, "out_per_item": 60,
                  "ask": "Escreva {n} perguntas de entrevista para um(a) {cargo} sobre {tema}, em tom {estilo}, terminando em '?', com até 280 caracteres. Só JSON: lista de strings.",
                  "axes": [OFFICES, THEMES, ["duro", "técnico", "amistoso"]]},
}


def jobs(kind: str, total: int):
    spec = KINDS[kind]
    combos = list(itertools.product(*spec["axes"]))
    n = max(1, round(total / spec["per_request"]))
    for i in range(n):
        yield combos[i % len(combos)]


def estimate(kind: str, total: int) -> dict:
    spec = KINDS[kind]
    requests = max(1, round(total / spec["per_request"]))
    tokens_in = requests * spec["in_tokens"]
    tokens_out = requests * spec["per_request"] * spec["out_per_item"]
    usd = tokens_in / 1e6 * PRICE_IN_USD + tokens_out / 1e6 * PRICE_OUT_USD
    return {"conjunto": kind, "exemplos": requests * spec["per_request"], "pedidos": requests, "tokens_entrada": tokens_in, "tokens_saida": tokens_out, "custo_usd": round(usd, 2)}


def build_prompt(kind: str, combo: tuple) -> str:
    spec = KINDS[kind]
    names = {"propostas": ("cargo", "tema", "estilo"), "manchetes": ("tema", "estilo"), "perguntas": ("cargo", "tema", "estilo")}[kind]
    return spec["ask"].format(n=spec["per_request"], **dict(zip(names, combo)))


def load_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    env = ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENAI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return key


def call(key: str, prompt: str):
    import httpx
    r = httpx.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, timeout=90,
                   json={"model": MODEL, "messages": [{"role": "system", "content": "Você gera dados de treino em português do Brasil para um simulador político fictício. Responda só com JSON válido."},
                                                      {"role": "user", "content": prompt}]})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"], r.json().get("usage", {})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conjunto", choices=list(KINDS), default=None)
    ap.add_argument("--total", type=int, default=2000)
    ap.add_argument("--executar", action="store_true")
    ap.add_argument("--limite-usd", type=float, default=2.0)
    args = ap.parse_args()
    kinds = [args.conjunto] if args.conjunto else list(KINDS)
    print("== Estimativa (preços de agregadores; confira na página oficial)")
    for k in kinds:
        print(" ", json.dumps(estimate(k, args.total), ensure_ascii=False))
    if not args.executar:
        print("\nNada foi enviado. Para gerar de verdade: --executar (exige OPENAI_API_KEY).")
        return 0
    key = load_key()
    if not key:
        print("Sem OPENAI_API_KEY (ambiente ou backend/.env). Nada foi enviado.")
        return 2
    out_dir = ROOT / "data" / "sintetico"
    out_dir.mkdir(parents=True, exist_ok=True)
    spent = 0.0
    for k in kinds:
        path = out_dir / f"{k}-{date.today().isoformat()}.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            for combo in jobs(k, args.total):
                content, usage = call(key, build_prompt(k, combo))
                spent += usage.get("prompt_tokens", 0) / 1e6 * PRICE_IN_USD + usage.get("completion_tokens", 0) / 1e6 * PRICE_OUT_USD
                try:
                    items = json.loads(content)
                except json.JSONDecodeError:
                    continue
                for item in items if isinstance(items, list) else []:
                    fh.write(json.dumps({"conjunto": k, "item": item, "combo": list(combo), "review": "pendente",
                                         "origem": {"modelo": MODEL, "data": date.today().isoformat(), "pedido": PROMPT_VERSION}}, ensure_ascii=False) + "\n")
                if spent >= args.limite_usd:
                    print(f"Limite de US$ {args.limite_usd} atingido; parando.")
                    return 0
                time.sleep(0.5)
        print(f"{k}: gravado em {path}")
    print(f"Gasto estimado: US$ {spent:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
