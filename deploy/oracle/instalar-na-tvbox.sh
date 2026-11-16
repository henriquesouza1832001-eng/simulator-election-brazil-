#!/usr/bin/env bash
# Roda NA TV box (Linux). Instala o robo da Oracle como servico que volta sozinho se reiniciar.
# Precisa da pasta "pacote" ao lado deste arquivo (gerada no PC, nunca vai para o git).
set -euo pipefail
DEST="$HOME/robo-oracle"
mkdir -p "$DEST"
cp -r "$(dirname "$0")/pacote/." "$DEST/"
sed -i "s/__USER__/$USER/" "$DEST/config"
chmod 600 "$DEST"/*.pem "$DEST"/config "$DEST"/oracle 2>/dev/null || true
sudo apt-get install -y python3 python3-venv >/dev/null
python3 -m venv "$DEST/venv"
"$DEST/venv/bin/pip" install -q oci
sudo tee /etc/systemd/system/robo-oracle.service >/dev/null <<UNIT
[Unit]
Description=Robo que cria a maquina A1 da Oracle
After=network-online.target
Wants=network-online.target
[Service]
User=$USER
WorkingDirectory=$DEST
ExecStart=$DEST/venv/bin/python $DEST/cacar_a1.py
Restart=always
RestartSec=60
[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now robo-oracle
echo "Pronto. Acompanhe com: tail -f $DEST/robo.log"
echo "Status no celular: http://$(hostname -I | cut -d' ' -f1):8765/?t=SEU_TOKEN (token em robo.local.json)"
echo "Estado resumido: $DEST/venv/bin/python $DEST/cacar_a1.py --status"
