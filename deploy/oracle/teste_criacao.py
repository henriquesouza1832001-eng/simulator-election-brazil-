"""Teste do caminho de criacao do robo com uma maquina PAGA (A2.Flex 1 OCPU/6 GB), apagada logo em seguida.
Usa as mesmas funcoes do robo. Custo: centavos (alguns minutos de uso)."""
import oci, time, cacar_a1 as r
from pathlib import Path

r.SHAPE = "VM.Standard.A2.Flex"
cfg = r.carregar_config(); cfg["nome"] = "teste-robo-apagar"; cfg["boot_gb"] = 50
config = oci.config.from_file(cfg["oci_config"], cfg["perfil"])
comp = cfg.get("compartimento") or config["tenancy"]
compute = oci.core.ComputeClient(config)
dominio = r.com_retentativa(lambda: oci.identity.IdentityClient(config).list_availability_domains(comp)).data[0].name
imagem = r.achar_imagem(compute, comp)
chave = Path(cfg["ssh_public_key_path"]).expanduser().read_text(encoding="utf-8").strip()
inst = None
try:
    inst = r.tentar_criar(compute, cfg, comp, dominio, imagem, chave, 1, 6)
    r.log(f"TESTE: criada {inst.id}")
    ip = r.esperar_ip(config, compute, inst)
    r.log(f"TESTE: IP publico lido = {ip}")
    (r.AQUI / "teste-instancia.txt").write_text(f"IP: {ip}\nOCID: {inst.id}\n", encoding="utf-8")
finally:
    if inst:
        compute.terminate_instance(inst.id, preserve_boot_volume=False)
        r.log("TESTE: apagando a maquina de teste.")
        for _ in range(60):
            est = compute.get_instance(inst.id).data.lifecycle_state
            if est == "TERMINATED": break
            time.sleep(10)
        r.log(f"TESTE: estado final = {est}")
