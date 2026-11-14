#!/usr/bin/env python3
"""Robô que cria a instância ARM gratuita (A1.Flex) na Oracle assim que houver vaga.

A cada rodada tenta 2 núcleos e 12 GB; se não houver vaga, tenta 1 núcleo e 6 GB.
Quando uma criação dá certo, espera a máquina ficar Running, grava o IP em instancia-oracle.txt e para.
Ele CRIA a instância (não só consulta). Para não criar duas, para se já existir uma A1.Flex ativa.

Uso:  python cacar_a1.py            (lê robo.local.json ao lado deste arquivo)
      python cacar_a1.py --uma-vez  (só uma rodada, para testar)
"""
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import oci

AQUI = Path(__file__).resolve().parent
SHAPE = "VM.Standard.A1.Flex"
TAMANHOS = [(2, 12), (1, 6)]  # (núcleos, GB), do melhor para o mínimo
ESPERA_PADRAO = 300  # segundos entre rodadas
MAX_ERROS_DESCONHECIDOS = 6


def log(texto):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {texto}"
    print(linha, flush=True)
    with open(AQUI / "robo.log", "a", encoding="utf-8") as arquivo:
        arquivo.write(linha + "\n")


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
    for numero in range(1, tentativas + 1):
        try:
            return funcao()
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
    manter_acordado()
    uma_vez = "--uma-vez" in sys.argv
    cfg = carregar_config()
    config = oci.config.from_file(cfg["oci_config"], cfg["perfil"])
    oci.config.validate_config(config)
    compartimento = cfg.get("compartimento") or config["tenancy"]
    compute = oci.core.ComputeClient(config)
    identidade = oci.identity.IdentityClient(config)
    chave_ssh = Path(cfg["ssh_public_key_path"]).expanduser().read_text(encoding="utf-8").strip()
    imagem = cfg.get("image_ocid") or achar_imagem(compute, compartimento)
    dominios = [d.name for d in com_retentativa(lambda: identidade.list_availability_domains(compartimento)).data]
    log(f"Pronto. Regiao {config['region']}, dominios {dominios}. Meta: {TAMANHOS[0]} nucleos/GB, minimo {TAMANHOS[-1]}.")

    erros_desconhecidos = 0
    rodada = 0
    while True:
        rodada += 1
        existente = ja_existe_a1(compute, compartimento)
        if existente:
            log(f"Ja existe uma A1.Flex ({existente.display_name}, {existente.lifecycle_state}). Nada a fazer.")
            return
        criada = None
        for dominio in dominios:
            for nucleos, gb in TAMANHOS:
                try:
                    criada = tentar_criar(compute, cfg, compartimento, dominio, imagem, chave_ssh, nucleos, gb)
                    log(f"CRIADA com {nucleos} nucleo(s) e {gb} GB em {dominio}. OCID {criada.id}")
                    break
                except oci.exceptions.ServiceError as erro:
                    texto = f"{erro.status} {erro.code}: {erro.message}"
                    if "capacity" in texto.lower() or erro.status == 500:
                        log(f"Rodada {rodada}: sem vaga ({nucleos}/{gb} GB, {dominio}).")
                        erros_desconhecidos = 0
                    elif erro.status == 401:
                        log("401 ao criar (chave ainda propagando). Espero 1 minuto.")
                        time.sleep(60)
                    elif erro.status == 429:
                        log("Muitas requisicoes (429). Esperando 10 minutos.")
                        time.sleep(600)
                    elif erro.code == "LimitExceeded":
                        log(f"Limite excedido para {nucleos}/{gb} GB; tentando o proximo tamanho. {erro.message}")
                    else:
                        erros_desconhecidos += 1
                        log(f"Erro inesperado ({erros_desconhecidos}/{MAX_ERROS_DESCONHECIDOS}): {texto}")
                        if erros_desconhecidos >= MAX_ERROS_DESCONHECIDOS:
                            log("Muitos erros inesperados seguidos. Parando para voce olhar.")
                            return
                except Exception as erro:  # rede caiu etc.
                    log(f"Falha de rede/outro: {erro}")
                    time.sleep(60)
            if criada:
                break
        if criada:
            ip = esperar_ip(config, compute, criada)
            texto = f"IP publico: {ip}\nOCID: {criada.id}\nNucleos/GB: {nucleos}/{gb}\nUsuario: ubuntu\n"
            (AQUI / "instancia-oracle.txt").write_text(texto, encoding="utf-8")
            log("PRONTO!\n" + texto)
            return
        if uma_vez:
            log("Rodada unica concluida sem vaga.")
            return
        espera = cfg["espera_segundos"] + random.randint(0, 30)
        time.sleep(espera)


if __name__ == "__main__":
    main()
