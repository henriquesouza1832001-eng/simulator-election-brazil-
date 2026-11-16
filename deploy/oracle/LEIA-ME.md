# Robô que cria a instância ARM gratuita da Oracle

A região de São Paulo costuma ficar sem vaga de ARM ("Out of host capacity"). Este robô pede a criação da máquina **A1.Flex** a cada ~5 minutos até conseguir:

1. tenta **2 núcleos e 12 GB**;
2. se não houver vaga, tenta **1 núcleo e 6 GB**;
3. quando uma dá certo, espera ficar *Running*, grava o IP em `instancia-oracle.txt` e para.

Ele **cria** a máquina (não só consulta). Para não criar duas, ele para se já existir uma A1.Flex ativa. A máquina A2 que você criou antes não conta (é outro modelo).

## O que preparar (uma vez)

1. **Chave de API** no console da Oracle: perfil (canto superior direito) > *My profile* > *API keys* > *Add API key* > *Generate API key pair*. Baixe a chave privada e copie o texto de configuração que aparece.
2. Salve esse texto em `C:\Users\Dell\.oci\config` e ajuste `key_file=` para o caminho da chave privada baixada (por exemplo `C:\Users\Dell\.oci\oci_api_key.pem`).
3. Copie a **chave pública SSH** da instância (a que começa com `ssh-rsa`) para um arquivo, por exemplo `C:\Users\Dell\.ssh\oracle.pub`. Se você usou "gerar par de chaves", baixe a *public key* de novo na tela de criação, ou gere uma com `ssh-keygen -t rsa -f C:\Users\Dell\.ssh\oracle`.
4. Copie `robo.exemplo.json` para `robo.local.json` e preencha:
   - `subnet_ocid`: Networking > Virtual cloud networks > henriquesouza > *public subnet-henriquesouza* > copiar OCID;
   - `ssh_public_key_path`: o caminho do arquivo `.pub`.

## Rodar

```
C:\Users\Dell\.oci-cli-venv\Scripts\python.exe deploy\oracle\cacar_a1.py --uma-vez   # teste de uma rodada
C:\Users\Dell\.oci-cli-venv\Scripts\python.exe deploy\oracle\cacar_a1.py             # fica tentando até conseguir
```

O que acontece fica em `robo.log`. O computador precisa ficar ligado, com internet e sem suspender (Configurações > Energia > nunca suspender enquanto conectado).

## Acompanhar do celular (sem deixar o PC ligado)

O robô pode rodar em outra máquina (a TV box, por exemplo) e você só consulta o estado dele:

- **Página de status (mesmo Wi-Fi):** abra no navegador do celular `http://IP-DA-TV-BOX:8765/?t=SUA_PALAVRA_SECRETA`. Mostra se está rodando, quantas rodadas e tentativas, a última tentativa e o final do log. Atualiza sozinha a cada 30 s. Versão para programas: `/json?t=...`.
- **Pelo terminal do celular (Termux):** `curl -s "http://IP-DA-TV-BOX:8765/?t=SUA_PALAVRA_SECRETA"`.
- **Aviso de qualquer lugar (ntfy):** instale o app **ntfy** no celular e assine o tópico que você pôs em `ntfy_topic` (use um nome longo e único, porque quem souber o nome lê os avisos). O robô avisa quando inicia, a cada 12 horas que continua rodando, se parar por erro e, com prioridade máxima, quando criar a máquina.
- **Na própria máquina:** `python cacar_a1.py --status` mostra o `estado.json`.
- **De fora de casa (link público):** com `"tunel": true` em `robo.local.json` e o `cloudflared` instalado (`pkg install cloudflared` no Termux), o robô abre um túnel da Cloudflare e envia o endereço, já com a palavra secreta, pelo ntfy. **O endereço muda** sempre que o túnel reinicia (a TV box reiniciar, a internet cair); o aviso mais recente do ntfy é o link válido. Como o endereço é público, use um `status_token` longo (24 caracteres ou mais): quem tiver o link e o token pode ver o status e desligar o robô.
- **Conferir e desligar:** a página tem o botão **Conferir na Oracle agora** (consulta a conta e diz achou/não achou, com o IP), o link para o console da Oracle e o botão **Desligar o robô**, que interrompe a busca.

As opções ficam em `robo.local.json` (`porta_status`, `status_token`, `ntfy_topic`, `heartbeat_horas`). Se a TV box usar firewall, libere a porta 8765 só para a rede local.

**Importante:** rode o robô em **um** lugar só. Dois robôs com a mesma chave aumentam o limite de requisições (erro 429). Quando ligar o da TV box, pare o do PC.

## Segurança

A chave de API dá acesso à sua conta Oracle. Ela fica só neste computador (nada disso vai para o Git: `robo.local.json`, `robo.log` e `instancia-oracle.txt` estão no `.gitignore`). Depois de conseguir a máquina, apague a chave em *My profile > API keys*.
