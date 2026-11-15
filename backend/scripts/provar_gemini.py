"""Prova real do Gemini: o que funciona, o que cai no texto local sem avisar e quanto custa um mandato inteiro.

Uso (na pasta backend, com a chave em GEMINI_API_KEY ou em backend/.env):
    .venv/Scripts/python.exe scripts/provar_gemini.py            # tudo
    .venv/Scripts/python.exe scripts/provar_gemini.py --so-offline   # só o que não precisa de chave

A chave nunca é impressa. Cada recurso do jogo (interpretar medida, narrar, mapear ação, perguntas de entrevista)
cai no texto local quando a chamada falha; por isso o jogo "funciona" mesmo com o Gemini quebrado. Este script
mostra a falha de verdade: status HTTP, mensagem do Google e se a saída passou nas travas do motor.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from pathlib import Path

import httpx

for _stream in (sys.stdout, sys.stderr):
    _stream.reconfigure(encoding="utf-8", errors="replace")  # console do Windows usa cp1252

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai import interpreter, mapper_ai, narrator, question_ai  # noqa: E402

API = "https://generativelanguage.googleapis.com/v1beta"
FACTS = {"title": "Reduzir o preço da energia elétrica", "status": "feito", "forecast": {"approval": 1.2, "inflation": -0.1},
         "result": {"approval": 0.9, "inflation": -0.08}, "cost": "R$ 1,2 bi"}
RESULTS: list[tuple[str, str, str]] = []  # (situação, teste, detalhe)


def load_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    env_file = ROOT / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if line.startswith("GEMINI_MODEL=") and not os.getenv("GEMINI_MODEL"):
                os.environ["GEMINI_MODEL"] = line.split("=", 1)[1].strip().strip('"').strip("'")
    if key:
        os.environ["GEMINI_API_KEY"] = key
    return key


def redact(text: str, key: str) -> str:
    return text.replace(key, "***") if key else text


def record(ok: bool | None, name: str, detail: str = "") -> None:
    RESULTS.append(("OK" if ok else "—" if ok is None else "FALHA", name, detail))
    print(f"{RESULTS[-1][0]:6} {name}" + (f"  → {detail}" if detail else ""), flush=True)


def raw_call(model: str, key: str, payload: dict) -> tuple[int, float, dict, str]:
    started = time.perf_counter()
    try:
        r = httpx.post(f"{API}/models/{model}:generateContent", headers={"x-goog-api-key": key}, json=payload, timeout=60)
    except httpx.HTTPError as exc:
        return 0, time.perf_counter() - started, {}, redact(f"{type(exc).__name__}: {exc}", key)
    elapsed = time.perf_counter() - started
    try:
        body = r.json()
    except ValueError:
        body = {}
    message = ""
    if r.is_error:
        message = redact(str((body.get("error") or {}).get("message", r.text))[:240], key)
    return r.status_code, elapsed, body, message


def text_of(body: dict) -> str:
    parts = (body.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    return next((p["text"] for p in parts if isinstance(p, dict) and isinstance(p.get("text"), str)), "")


def offline() -> None:
    print("\n== Travas do motor (não usam a internet)")
    good = "Na simulação, a redução do preço da energia teve custo de R$ 1,2 bi. O motor previu aprovação 1,2 e o realizado foi 0,9."
    bad_number = "Na simulação, a redução do preço da energia aumentou a aprovação em 7 pontos, acima do previsto pelo motor, segundo a decisão."
    bad_name = "Na simulação, o ministro Fernando Haddad anunciou a redução do preço da energia, com custo de 1,2 bi, conforme o motor previu."
    record(narrator._acceptable(good, FACTS), "narrador aceita texto fiel aos fatos")
    record(not narrator._acceptable(bad_number, FACTS), "narrador recusa número inventado")
    record(not narrator._acceptable(bad_name, FACTS), "narrador recusa nome próprio inventado")
    record(narrator._acceptable("x" * 5, FACTS) is False, "narrador recusa texto curto demais")
    inconsistent = {name for name, model in [("interpretador", interpreter.DEFAULT_MODEL), ("narrador", narrator.DEFAULT_MODEL), ("mapeador", mapper_ai.DEFAULT_MODEL)]}
    models = {interpreter.DEFAULT_MODEL, narrator.DEFAULT_MODEL, mapper_ai.DEFAULT_MODEL}
    record(len(models) == 1, "todos os recursos usam o mesmo modelo padrão", ", ".join(sorted(models)) if len(models) > 1 else next(iter(models)))
    del inconsistent


async def with_bogus_key() -> None:
    print("\n== Chave inválida: o jogo precisa seguir com as regras locais")
    saved = os.environ.get("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = "chave-invalida-de-teste"
    try:
        n = await narrator.narrate(FACTS)
        record(n["source"] == "local" and bool(n["text"]), "narrar com chave inválida cai no texto local", f"source={n['source']}")
        i = await interpreter.interpret("Reduzir o preço da energia com meta e prazo de 12 meses.", [])
        record(bool(i), "interpretar com chave inválida devolve resultado local", f"fonte={i.get('source') or i.get('mode') or 'local'}")
    finally:
        if saved is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = saved


def online(key: str) -> None:
    model = os.getenv("GEMINI_MODEL", "").strip()
    print(f"\n== Modelos disponíveis para esta chave")
    r = httpx.get(f"{API}/models?pageSize=200", headers={"x-goog-api-key": key}, timeout=30)
    if r.is_error:
        record(False, "listar modelos", f"HTTP {r.status_code}: {redact(r.text[:200], key)}")
        print("   A chave não funcionou. Confira se ela é de https://aistudio.google.com/apikey e se a API está ativa.")
        return
    models = [m["name"].split("/")[-1] for m in r.json().get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
    flash = sorted(m for m in models if "flash" in m and "image" not in m and "tts" not in m and "live" not in m)
    record(True, f"chave válida; {len(models)} modelos geram texto", "flash: " + ", ".join(flash[:12]))
    lite = sorted(m for m in flash if "lite" in m)
    candidates = [model] if model else lite[-1:]
    candidates += [m for m in (interpreter.DEFAULT_MODEL, narrator.DEFAULT_MODEL) if m not in candidates]
    chosen = next((m for m in candidates if m in models), None)
    for m in candidates:
        record(m in models, f"modelo '{m}' existe para esta chave")
    if not chosen:
        chosen = flash[-1] if flash else None
        print(f"   Nenhum modelo configurado existe. Sugestão: GEMINI_MODEL={chosen}")
    if not chosen:
        return
    os.environ["GEMINI_MODEL"] = chosen
    print(f"\n== Chamadas cruas ao modelo '{chosen}' (mostram o erro que o jogo esconde)")
    base = {"systemInstruction": {"parts": [{"text": narrator.INSTRUCTIONS}]},
            "contents": [{"role": "user", "parts": [{"text": "Fatos do motor (JSON):\n" + json.dumps(FACTS, ensure_ascii=False)}]}]}
    variants = {
        "como o jogo envia (thinkingLevel=low)": {"maxOutputTokens": 400, "thinkingConfig": {"thinkingLevel": "low"}},
        "sem thinkingConfig": {"maxOutputTokens": 400},
        "thinkingBudget=0": {"maxOutputTokens": 400, "thinkingConfig": {"thinkingBudget": 0}},
    }
    working = None
    for label, cfg in variants.items():
        status, secs, body, err = raw_call(chosen, key, {**base, "generationConfig": cfg})
        out = text_of(body)
        record(status == 200 and bool(out), f"narrar · {label}", f"HTTP {status} em {secs:.1f}s" + (f" · {err}" if err else f" · {out[:90]!r}"))
        if status == 200 and out and working is None:
            working = label
    schema = {"type": "OBJECT", "properties": {"topic": {"type": "STRING"}}, "required": ["topic"]}
    shapes = {
        "JSON como o jogo envia (responseFormat.text)": {"responseFormat": {"text": {"mimeType": "APPLICATION_JSON", "schema": schema}}, "thinkingConfig": {"thinkingLevel": "low"}, "maxOutputTokens": 200},
        "JSON padrão (responseMimeType + responseSchema)": {"responseMimeType": "application/json", "responseSchema": schema, "maxOutputTokens": 200},
    }
    prompt = {"contents": [{"role": "user", "parts": [{"text": "Diga o tema principal de: reduzir o preço da energia elétrica."}]}]}
    for label, cfg in shapes.items():
        status, secs, body, err = raw_call(chosen, key, {**prompt, "generationConfig": cfg})
        ok = False
        detail = f"HTTP {status} em {secs:.1f}s"
        if status == 200:
            try:
                ok = isinstance(json.loads(text_of(body)), dict)
                detail += " · JSON válido" if ok else " · resposta não é objeto"
            except ValueError:
                detail += " · resposta não é JSON"
        else:
            detail += f" · {err}"
        record(ok, f"saída estruturada · {label}", detail)


async def features(key: str) -> None:
    os.environ["GEMINI_RECURSOS"] = "interpretar,mapear,narrar,perguntar"  # a prova testa todos, mesmo os desligados no jogo
    print("\n== Recursos do jogo de ponta a ponta (fonte 'gemini' = funcionou; 'local' = caiu no reserva)")
    n = await narrator.narrate(FACTS)
    record(n["source"] == "gemini", "narrador", f"fonte={n['source']} · {n['text'][:110]!r}")
    i = await interpreter.interpret("Reduzir o preço da energia elétrica com um programa de eficiência energética, meta de 10% e prazo de 12 meses.", [])
    src = i.get("source") or i.get("interpreter") or i.get("mode") or "?"
    record(src not in ("local", "fallback", "?") and not i.get("fallback_reason"), "interpretador de medida", f"fonte={src} · motivo={i.get('fallback_reason') or i.get('reason') or '-'}")
    m = await mapper_ai.refine("quero baixar a conta de luz", [{"id": "energia", "title": "Reduzir tarifa de energia"}, {"id": "gas", "title": "Reduzir preço do gás"}], [])
    record(m.get("source") == "gemini" and bool(m.get("choice") or m.get("questions")), "mapeador de ação", f"fonte={m.get('source')} · escolha={m.get('choice')}")
    q = await question_ai.generate([{"text": "Inflação em 4,5% e desemprego em 7,8%.", "topic": "economia"}], ["economia"], "entrevista", "presidente", 2)
    record(q["source"] == "gemini", "perguntas de entrevista", f"fonte={q['source']} · {len(q['questions'])} perguntas válidas")
    print("\n== Latência e custo de um mandato inteiro (narrador, 6 chamadas)")
    times = []
    ok = 0
    for _ in range(6):
        t = time.perf_counter()
        r = await narrator.narrate(FACTS)
        times.append(time.perf_counter() - t)
        ok += r["source"] == "gemini"
    p50, worst = statistics.median(times), max(times)
    record(ok == 6, "6 narrações seguidas", f"{ok}/6 pelo Gemini · mediana {p50:.1f}s · pior {worst:.1f}s")
    print(f"   Estimativa: 48 meses × 1 narração por decisão importante ≈ {48 * p50 / 60:.1f} min de espera total se houver 1 por mês.")
    print("   Meta de produto: nenhuma tela esperar mais de ~15 s (limite de leitura do código) e sempre ter texto local de reserva.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--so-offline", action="store_true")
    args = parser.parse_args()
    key = load_key()
    offline()
    asyncio.run(with_bogus_key())
    if args.so_offline:
        pass
    elif not key:
        print("\nSem GEMINI_API_KEY (ambiente ou backend/.env): provas com a internet foram puladas.")
        print("Crie a chave em https://aistudio.google.com/apikey e coloque em backend/.env como GEMINI_API_KEY=... (esse arquivo não vai para o Git).")
    else:
        online(key)
        if os.getenv("GEMINI_MODEL"):
            asyncio.run(features(key))
    fails = [r for r in RESULTS if r[0] == "FALHA"]
    print(f"\n{len(RESULTS) - len(fails)} ok, {len(fails)} falhas")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
