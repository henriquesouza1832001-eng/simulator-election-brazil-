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

## Segurança

A chave de API dá acesso à sua conta Oracle. Ela fica só neste computador (nada disso vai para o Git: `robo.local.json`, `robo.log` e `instancia-oracle.txt` estão no `.gitignore`). Depois de conseguir a máquina, apague a chave em *My profile > API keys*.
