#!/usr/bin/env python3
"""Robô que cria a instância ARM gratuita (A1.Flex) na Oracle assim que houver vaga.

A cada rodada tenta 2 núcleos e 12 GB; se não houver vaga, tenta 1 núcleo e 6 GB.
Quando uma criação dá certo, espera a máquina ficar Running, grava o IP em instancia-oracle.txt e para.
Ele CRIA a instância (não só consulta). Para não criar duas, para se já existir uma A1.Flex ativa.

Uso:  python cacar_a1.py            (lê robo.local.json ao lado deste arquivo)
      python cacar_a1.py --uma-vez  (só uma rodada, para testar)
      python cacar_a1.py --status   (mostra como o robô está, lendo estado.json)

Como acompanhar de longe (tudo opcional, em robo.local.json):
  porta_status     porta da página de status na rede local (padrão 8765; 0 desliga).
                   No celular, no mesmo Wi-Fi: http://IP-DA-MAQUINA:8765
  status_token     se definido, a página só abre com ?t=SEU_TOKEN
  ntfy_topic       tópico do app ntfy (https://ntfy.sh) para receber aviso no celular, de qualquer lugar
  heartbeat_horas  de quantas em quantas horas avisar que continua rodando (padrão 12; 0 desliga)
"""
import json
import random
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime
from pathlib import Path

import oci

AQUI = Path(__file__).resolve().parent
SHAPE = "VM.Standard.A1.Flex"
TAMANHOS = [(2, 12), (1, 6)]  # (núcleos, GB), do melhor para o mínimo
ESPERA_PADRAO = 300  # segundos entre rodadas
MAX_ERROS_DESCONHECIDOS = 6
ESTADO_ARQUIVO = AQUI / "estado.json"
ESTADO = {"iniciado": None, "rodada": 0, "tentativas": 0, "sem_vaga": 0, "erros_rede": 0, "ultima_tentativa": None,
          "ultimo_resultado": "ainda não tentou", "encontrado": False, "ip": None, "parado": None,
          "sinal_ts": None, "proxima_ts": None, "ultima_ts": None,
          "tentativas_total": 0, "desde": None, "tentativas_anteriores": 0, "conferencia": None, "console_url": None}
CONTEXTO = {"compute": None, "config": None, "compartimento": None}
_TRAVA = threading.Lock()
PARAR = threading.Event()  # acionado pelo botão 'Desligar' da página de status
ARQUIVO_PARADO = AQUI / "PARADO"  # impede que o Termux:Boot religue um robô desligado de propósito


def log(texto):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {texto}"
    print(linha, flush=True)
    with open(AQUI / "robo.log", "a", encoding="utf-8") as arquivo:
        arquivo.write(linha + "\n")


def agora():
    return datetime.now().strftime("%d/%m %H:%M:%S")


def salvar_estado(**mudancas):
    with _TRAVA:
        ESTADO.update(mudancas)
        ESTADO_ARQUIVO.write_text(json.dumps(ESTADO, ensure_ascii=False, indent=2), encoding="utf-8")


def batimento():
    """Marca que o robô está vivo a cada 10 s (a página mostra 'sem sinal' se isso parar)."""
    while True:
        try:
            salvar_estado(sinal_ts=time.time())
        except Exception:  # noqa: BLE001
            pass
        time.sleep(10)


def duracao(segundos):
    segundos = int(max(0, segundos))
    if segundos < 90:
        return f"{segundos} s"
    return f"{segundos // 60} min {segundos % 60:02d} s" if segundos < 3600 else f"{segundos // 3600} h {(segundos % 3600) // 60:02d} min"


def vivo():
    ts = ESTADO.get("sinal_ts")
    return bool(ts) and time.time() - ts < 60


def texto_conferencia(c):
    if not c:
        return "Validação: ainda não conferida. Use o botão 'Conferir na Oracle agora'."
    if not c.get("ok"):
        return f"Validação ({c.get('conferido_em')}): NÃO consegui consultar a Oracle: {c.get('erro')}"
    if c["achou"]:
        linhas = [f"Validação ({c['conferido_em']}): ACHOU {len(c['instancias'])} máquina(s) A1 na sua conta:"]
        for i in c["instancias"]:
            linhas.append(f"  - {i['nome']}: {i['nucleos']} núcleo(s), {i['memoria_gb']} GB, {i['estado']}, IP {i['ip'] or 'ainda sem IP'}, criada em {i['criada_em']}")
        return "\n".join(linhas)
    return f"Validação ({c['conferido_em']}): NÃO ACHOU nenhuma máquina A1 na sua conta ({c.get('total_instancias_na_conta', 0)} outra(s) instância(s) existem)."


def conferir():
    """Consulta a Oracle agora (de verdade) e diz se existe alguma A1.Flex. Serve para ter certeza antes de desligar."""
    ctx = CONTEXTO
    if not ctx["compute"]:
        return {"ok": False, "erro": "o robô ainda está iniciando", "conferido_em": agora()}
    try:
        compute = ctx["compute"]
        lista = compute.list_instances(ctx["compartimento"]).data
        a1 = [i for i in lista if i.shape == SHAPE and i.lifecycle_state not in ("TERMINATED", "TERMINATING")]
        rede = oci.core.VirtualNetworkClient(ctx["config"])
        itens = []
        for inst in a1:
            ip = None
            try:
                for anexo in compute.list_vnic_attachments(inst.compartment_id, instance_id=inst.id).data:
                    vnic = rede.get_vnic(anexo.vnic_id).data
                    if vnic.public_ip:
                        ip = vnic.public_ip
                        break
            except Exception:  # noqa: BLE001
                pass
            forma = inst.shape_config
            itens.append({"nome": inst.display_name, "estado": inst.lifecycle_state, "nucleos": getattr(forma, "ocpus", None), "memoria_gb": getattr(forma, "memory_in_gbs", None),
                          "ip": ip, "criada_em": str(inst.time_created)[:19]})
        resultado = {"ok": True, "achou": bool(itens), "instancias": itens, "total_instancias_na_conta": len(lista) - len(a1), "conferido_em": agora()}
    except Exception as erro:  # noqa: BLE001
        resultado = {"ok": False, "erro": f"{type(erro).__name__}: {erro}"[:200], "conferido_em": agora()}
    salvar_estado(conferencia=resultado)
    return resultado


def ultimas_linhas(n=8):
    caminho = AQUI / "robo.log"
    if not caminho.exists():
        return []
    return caminho.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]


def texto_status():
    with _TRAVA:
        e = dict(ESTADO)
    agora_ts = time.time()
    if e["encontrado"]:
        situacao = f"ENCONTROU a máquina! IP {e['ip']}"
    elif e["parado"]:
        situacao = f"PARADO: {e['parado']}"
    elif not vivo():
        situacao = "SEM SINAL: o robô parou de responder (pode ter travado ou a TV box desligou)"
    else:
        situacao = "RODANDO, procurando vaga (ele espera cerca de 2 minutos entre as rodadas)"
    sinal = f"Sinal de vida: há {duracao(agora_ts - e['sinal_ts'])}" if e.get("sinal_ts") else "Sinal de vida: ainda não houve"
    ultima = f"Última tentativa: {e['ultima_tentativa']} (há {duracao(agora_ts - e['ultima_ts'])}) → {e['ultimo_resultado']}" if e.get("ultima_ts") else f"Última tentativa: {e['ultima_tentativa']} → {e['ultimo_resultado']}"
    proxima = f"Próxima tentativa em cerca de {duracao(e['proxima_ts'] - agora_ts)}" if (e.get("proxima_ts") and e["proxima_ts"] > agora_ts and not e["parado"] and not e["encontrado"]) else None
    antes = int(e.get("tentativas_anteriores") or 0)
    total = int(e.get("tentativas_total") or 0)
    contagem = f"Tentativas no total: {total + antes}" + (f" ({total} nesta TV box desde {e.get('desde')} + {antes} no PC antes)" if antes else f" desde {e.get('desde')}")
    linhas = [f"Robô da Oracle: {situacao}", sinal, f"Iniciado em: {e['iniciado']}", contagem,
              f"Nesta execução: rodadas {e['rodada']} · tentativas {e['tentativas']} · sem vaga {e['sem_vaga']} · falhas de rede {e['erros_rede']}",
              ultima, *([proxima] if proxima else []), "", texto_conferencia(e.get("conferencia")), "", "Últimas linhas do log:", *ultimas_linhas()]
    return "\n".join(linhas) + "\n"


def iniciar_painel(cfg):
    porta = int(cfg.get("porta_status", 8765))
    if not porta:
        return
    token = cfg.get("status_token")

    class Painel(BaseHTTPRequestHandler):
        def _autorizado(self):
            return bool(token) and f"t={token}" in self.path

        def _responder(self, codigo, corpo, tipo="text/plain; charset=utf-8"):
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.end_headers()
            self.wfile.write(corpo.encode("utf-8"))

        def do_GET(self):  # noqa: N802
            if token and not self._autorizado():
                return self._responder(403, "Acesso negado.\n")
            if self.path.startswith("/conferir"):
                return self._responder(200, texto_conferencia(conferir()))
            if self.path.startswith("/json"):
                return self._responder(200, json.dumps(ESTADO, ensure_ascii=False), "application/json; charset=utf-8")
            if "text/html" in self.headers.get("Accept", ""):
                acao = f"/parar?t={token}" if token else "/parar"
                sem_sinal = not (ESTADO["encontrado"] or ESTADO["parado"] or vivo())
                cor = "#1f7a4a" if ESTADO["encontrado"] else "#c0392b" if (ESTADO["parado"] or sem_sinal) else "#2a6fa8"
                html = ("<!doctype html><html lang=pt-BR><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
                        "<meta http-equiv=refresh content=30><title>Robô da Oracle</title>"
                        f"<body style='font-family:system-ui;margin:0;background:#0e1319;color:#eef1f5'><div style='background:{cor};padding:14px 16px;font-size:20px;font-weight:700'>"
                        + ("Máquina criada!" if ESTADO["encontrado"] else "Parado" if ESTADO["parado"] else "Sem sinal" if sem_sinal else "Rodando: procurando vaga…") + "</div>"
                        f"<pre style='white-space:pre-wrap;padding:14px 16px;font-size:15px;line-height:1.5'>{texto_status()}</pre>"
                        f"<div style='padding:0 16px 8px;display:flex;flex-wrap:wrap;gap:10px'>"
                        "<button id=bv style='font-size:17px;padding:12px 16px;border-radius:8px;border:0;background:#2a6fa8;color:#fff'>Conferir na Oracle agora</button>"
                        f"<a href='{ESTADO.get('console_url') or 'https://cloud.oracle.com/compute/instances'}' target=_blank rel=noopener style='font-size:17px;padding:12px 16px;border-radius:8px;background:#161d26;color:#d9b44a;text-decoration:none;border:1px solid #d9b44a'>Abrir o console da Oracle ↗</a></div>"
                        "<pre id=rv style='white-space:pre-wrap;padding:6px 16px;font-size:15px;color:#d9b44a'></pre>"
                        f"<script>document.getElementById('bv').onclick=async function(){{var r=document.getElementById('rv');r.textContent='Consultando a Oracle…';try{{var x=await fetch('/conferir?t={token}');r.textContent=await x.text()}}catch(e){{r.textContent='Falhou: '+e}}}}</script>"
                        f"<form method=post action='{acao}' style='padding:8px 16px 28px' onsubmit=\"return confirm('Desligar o robô? Se ele disse que achou, confira antes no botão azul ou no console da Oracle.')\">"
                        "<button style='font-size:18px;padding:12px 18px;border-radius:8px;border:0;background:#e2554a;color:#fff'>Desligar o robô</button></form></body></html>")
                return self._responder(200, html, "text/html; charset=utf-8")
            return self._responder(200, texto_status())

        def do_POST(self):  # noqa: N802
            if not self.path.startswith("/parar"):
                return self._responder(404, "Não encontrado.\n")
            if not self._autorizado():
                return self._responder(403, "Para desligar é preciso definir status_token e usar ?t=SEU_TOKEN.\n")
            ARQUIVO_PARADO.write_text(f"desligado pelo celular em {agora()}\n", encoding="utf-8")
            salvar_estado(parado="desligado pelo celular")
            log("Desligado pelo botão da página de status.")
            self._responder(200, "Robô desligado. Para ligar de novo, apague o arquivo PARADO e inicie o robô.\n")
            PARAR.set()

        def log_message(self, *args):  # sem ruído no log
            pass

    try:
        servidor = ThreadingHTTPServer(("0.0.0.0", porta), Painel)
    except OSError as erro:
        log(f"Não consegui abrir a página de status na porta {porta}: {erro}")
        return
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    log(f"Página de status em http://IP-DESTA-MAQUINA:{porta}" + ("/?t=SEU_TOKEN" if token else ""))


def fim(cfg, uma_vez):
    """Terminou (máquina criada, já existia ou parou por erro): mantém a página no ar até alguém desligar pelo celular."""
    if uma_vez or not int(cfg.get("porta_status", 8765)):
        return
    log("Concluído. A página de status continua no ar; use o botão 'Desligar o robô' quando quiser encerrar.")
    PARAR.wait()
    time.sleep(1)


def avisar(cfg, titulo, texto, prioridade="default"):
    """Aviso no celular pelo ntfy (opcional). Qualquer falha é ignorada: aviso nunca derruba o robô."""
    topico = cfg.get("ntfy_topic")
    if not topico:
        return
    try:
        pedido = urllib.request.Request(f"https://ntfy.sh/{topico}", data=texto.encode("utf-8"), method="POST",
                                        headers={"Title": titulo.encode("ascii", "ignore").decode("ascii") or "Robo da Oracle", "Priority": prioridade})
        urllib.request.urlopen(pedido, timeout=15).close()
    except Exception as erro:  # noqa: BLE001
        log(f"Aviso no celular falhou ({type(erro).__name__}); sigo sem ele.")


def carregar_config():
    caminho = AQUI / "robo.local.json"
    if not caminho.exists():
        sys.exit(f"Falta {caminho.name}. Copie robo.exemplo.json para robo.local.json e preencha (veja o LEIA-ME).")
    cfg = json.loads(caminho.read_text(encoding="utf-8"))
    for chave in ("subnet_ocid", "ssh_public_key_path"):
        if not cfg.get(chave):
            sys.exit(f"Preencha '{chave}' em robo.local.json")
    cfg.setdefault("nome", "quatroanos-a1")
    cfg.setdefault("boot_gb", 100)
    cfg.setdefault("espera_segundos", ESPERA_PADRAO)
    cfg.setdefault("oci_config", str(Path.home() / ".oci" / "config"))
    cfg.setdefault("perfil", "DEFAULT")
    return cfg


def com_retentativa(funcao, tentativas=20, espera=30):
    """A chave de API recem-criada demora alguns minutos para valer em todos os servidores da Oracle: 401 no inicio e normal."""
    numero = 0
    while True:
        numero += 1
        try:
            return funcao()
        except (oci.exceptions.ConnectTimeout, oci.exceptions.RequestException) as erro:
            # Sem internet (PC dormiu, Wi-Fi caiu): espera e tenta de novo, nunca derruba o robo.
            log(f"Sem conexao com a Oracle ({type(erro).__name__}); espero 60s e tento de novo.")
            numero -= 1  # queda de rede nao conta como tentativa de 401
            time.sleep(60)
        except oci.exceptions.ServiceError as erro:
            if erro.status != 401 or numero == tentativas:
                raise
            log(f"401 (chave ainda propagando), tentativa {numero}/{tentativas}; espero {espera}s.")
            time.sleep(espera)


def achar_imagem(compute, compartimento):
    imagens = com_retentativa(lambda: compute.list_images(
        compartimento, operating_system="Canonical Ubuntu", operating_system_version="22.04",
        shape=SHAPE, sort_by="TIMECREATED", sort_order="DESC", limit=5,
    )).data
    if not imagens:
        sys.exit("Não achei imagem Ubuntu 22.04 compatível com ARM nesta região.")
    return imagens[0].id


def ja_existe_a1(compute, compartimento):
    ativos = ("PROVISIONING", "RUNNING", "STARTING", "STOPPING", "STOPPED")
    for inst in com_retentativa(lambda: compute.list_instances(compartimento)).data:
        if inst.shape == SHAPE and inst.lifecycle_state in ativos:
            return inst
    return None


def tentar_criar(compute, cfg, compartimento, dominio, imagem, chave_ssh, nucleos, gb):
    detalhes = oci.core.models.LaunchInstanceDetails(
        availability_domain=dominio,
        compartment_id=compartimento,
        display_name=cfg["nome"],
        shape=SHAPE,
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(ocpus=nucleos, memory_in_gbs=gb),
        source_details=oci.core.models.InstanceSourceViaImageDetails(
            image_id=imagem, boot_volume_size_in_gbs=cfg["boot_gb"]),
        create_vnic_details=oci.core.models.CreateVnicDetails(subnet_id=cfg["subnet_ocid"], assign_public_ip=True),
        metadata={"ssh_authorized_keys": chave_ssh},
    )
    return compute.launch_instance(detalhes).data


def esperar_ip(config, compute, inst):
    rede = oci.core.VirtualNetworkClient(config)
    for _ in range(60):
        atual = compute.get_instance(inst.id).data
        if atual.lifecycle_state == "RUNNING":
            for anexo in compute.list_vnic_attachments(atual.compartment_id, instance_id=atual.id).data:
                vnic = rede.get_vnic(anexo.vnic_id).data
                if vnic.public_ip:
                    return vnic.public_ip
        time.sleep(10)
    return None


def manter_acordado():
    """No Windows, pede para o sistema nao suspender enquanto o robo roda (nao muda nenhuma configuracao)."""
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # CONTINUOUS | SYSTEM_REQUIRED
    except Exception:
        pass


def main():
    if "--status" in sys.argv:
        print(ESTADO_ARQUIVO.read_text(encoding="utf-8") if ESTADO_ARQUIVO.exists() else "Ainda não há estado.json: o robô não rodou aqui.")
        return
    if ARQUIVO_PARADO.exists():
        sys.exit(f"Robô desligado de propósito ({ARQUIVO_PARADO.read_text(encoding='utf-8').strip()}). Apague {ARQUIVO_PARADO.name} para ligar de novo.")
    manter_acordado()
    uma_vez = "--uma-vez" in sys.argv
    cfg = carregar_config()
    if ESTADO_ARQUIVO.exists():  # totais continuam de onde pararam, mesmo se o robô reiniciar
        try:
            anterior = json.loads(ESTADO_ARQUIVO.read_text(encoding="utf-8"))
            ESTADO["tentativas_total"] = int(anterior.get("tentativas_total") or anterior.get("tentativas") or 0)
            ESTADO["desde"] = anterior.get("desde") or anterior.get("iniciado")
        except (ValueError, OSError):
            pass
    salvar_estado(iniciado=agora(), desde=ESTADO["desde"] or agora(), tentativas_anteriores=int(cfg.get("tentativas_anteriores", 0)))
    iniciar_painel(cfg)
    threading.Thread(target=batimento, daemon=True).start()
    ultimo_aviso = time.time()
    avisar(cfg, "Robo da Oracle iniciado", f"Procurando vaga A1 desde {agora()}.")
    config = oci.config.from_file(cfg["oci_config"], cfg["perfil"])
    oci.config.validate_config(config)
    compartimento = cfg.get("compartimento") or config["tenancy"]
    compute = oci.core.ComputeClient(config)
    CONTEXTO.update(compute=compute, config=config, compartimento=compartimento)
    salvar_estado(console_url=f"https://cloud.oracle.com/compute/instances?region={config['region']}")
    identidade = oci.identity.IdentityClient(config)
    chave_ssh = Path(cfg["ssh_public_key_path"]).expanduser().read_text(encoding="utf-8").strip()
    imagem = cfg.get("image_ocid") or achar_imagem(compute, compartimento)
    dominios = [d.name for d in com_retentativa(lambda: identidade.list_availability_domains(compartimento)).data]
    log(f"Pronto. Regiao {config['region']}, dominios {dominios}. Meta: {TAMANHOS[0]} nucleos/GB, minimo {TAMANHOS[-1]}.")

    erros_desconhecidos = 0
    rodada = 0
    while True:
        if PARAR.is_set():
            log("Busca encerrada a pedido (botão Desligar).")
            return
        rodada += 1
        existente = ja_existe_a1(compute, compartimento)
        if existente:
            log(f"Ja existe uma A1.Flex ({existente.display_name}, {existente.lifecycle_state}). Nada a fazer.")
            salvar_estado(parado="já existe uma A1.Flex nesta conta")
            return fim(cfg, uma_vez)
        criada = None
        salvar_estado(rodada=rodada)
        for dominio in dominios:
            for nucleos, gb in TAMANHOS:
                if PARAR.is_set():
                    log("Busca encerrada a pedido (botão Desligar).")
                    return
                try:
                    salvar_estado(tentativas=ESTADO["tentativas"] + 1, tentativas_total=ESTADO["tentativas_total"] + 1, ultima_tentativa=agora(), ultima_ts=time.time())
                    criada = tentar_criar(compute, cfg, compartimento, dominio, imagem, chave_ssh, nucleos, gb)
                    log(f"CRIADA com {nucleos} nucleo(s) e {gb} GB em {dominio}. OCID {criada.id}")
                    break
                except oci.exceptions.ServiceError as erro:
                    texto = f"{erro.status} {erro.code}: {erro.message}"
                    if "capacity" in texto.lower() or erro.status == 500:
                        log(f"Rodada {rodada}: sem vaga ({nucleos}/{gb} GB, {dominio}).")
                        salvar_estado(sem_vaga=ESTADO["sem_vaga"] + 1, ultimo_resultado=f"sem vaga ({nucleos} núcleo(s), {gb} GB)")
                        erros_desconhecidos = 0
                    elif erro.status == 401:
                        log("401 ao criar (chave ainda propagando). Espero 1 minuto.")
                        time.sleep(60)
                    elif erro.status == 429:
                        log("Muitas requisicoes (429). Esperando 10 minutos.")
                        salvar_estado(ultimo_resultado="limite de requisições (429); esperando 10 min")
                        if PARAR.wait(600):
                            return
                    elif erro.code == "LimitExceeded":
                        log(f"Limite excedido para {nucleos}/{gb} GB; tentando o proximo tamanho. {erro.message}")
                    else:
                        erros_desconhecidos += 1
                        log(f"Erro inesperado ({erros_desconhecidos}/{MAX_ERROS_DESCONHECIDOS}): {texto}")
                        if erros_desconhecidos >= MAX_ERROS_DESCONHECIDOS:
                            log("Muitos erros inesperados seguidos. Parando para voce olhar.")
                            salvar_estado(parado=f"muitos erros inesperados: {texto[:120]}")
                            avisar(cfg, "Robo da Oracle PAROU", f"Muitos erros seguidos: {texto[:200]}", "high")
                            return fim(cfg, uma_vez)
                except Exception as erro:  # rede caiu etc.
                    log(f"Falha de rede/outro: {erro}")
                    salvar_estado(erros_rede=ESTADO["erros_rede"] + 1, ultimo_resultado=f"falha de rede ({type(erro).__name__})")
                    time.sleep(60)
            if criada:
                break
        if criada:
            ip = esperar_ip(config, compute, criada)
            texto = f"IP publico: {ip}\nOCID: {criada.id}\nNucleos/GB: {nucleos}/{gb}\nUsuario: ubuntu\n"
            (AQUI / "instancia-oracle.txt").write_text(texto, encoding="utf-8")
            log("PRONTO!\n" + texto)
            salvar_estado(encontrado=True, ip=ip, ultimo_resultado=f"CRIADA com {nucleos} núcleo(s) e {gb} GB")
            validacao = conferir()  # confirma na Oracle antes de avisar
            confirmada = "CONFIRMADA na Oracle" if validacao.get("ok") and validacao.get("achou") else "ainda nao confirmada, confira no console"
            avisar(cfg, "Maquina A1 criada!", f"IP {ip} - {nucleos} nucleo(s) e {gb} GB ({confirmada}). Console: {ESTADO['console_url']} - depois apague a chave de API.", "urgent")
            return fim(cfg, uma_vez)
        if uma_vez:
            log("Rodada unica concluida sem vaga.")
            return
        horas = float(cfg.get("heartbeat_horas", 12))
        if horas and time.time() - ultimo_aviso >= horas * 3600:
            ultimo_aviso = time.time()
            avisar(cfg, "Robo da Oracle continua rodando", f"Rodada {rodada}, {ESTADO['sem_vaga']} sem vaga ate agora. Ultima: {ESTADO['ultimo_resultado']}.")
        espera = cfg["espera_segundos"] + random.randint(0, 30)
        salvar_estado(proxima_ts=time.time() + espera)
        if PARAR.wait(espera):  # a espera acorda na hora se pedirem para desligar
            log("Busca encerrada a pedido (botão Desligar).")
            return


if __name__ == "__main__":
    main()
