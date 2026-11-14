"""Backup enxuto do banco: copia o SQLite com a API de backup e tira as tabelas do TSE (tse_*).

As tabelas do TSE têm mais de 1 GB, mas são dados públicos que os importadores recriam
(python -m app.data.tse_candidacies / tse_votes). O que importa guardar são as partidas.
Uso, dentro do container da API:  python - /tmp/saida.sqlite3 < slim_backup.py
"""
import sqlite3
import sys

target_path = sys.argv[1]
source = sqlite3.connect("file:/data/game.sqlite3?mode=ro", uri=True)
target = sqlite3.connect(target_path)
source.backup(target)
source.close()
tables = [row[0] for row in target.execute("select name from sqlite_master where type='table' and name like 'tse\\_%' escape '\\'")]
for name in tables:
    target.execute(f'drop table "{name}"')
target.commit()
target.execute("vacuum")
target.close()
print(f"backup enxuto em {target_path}; tabelas do TSE removidas: {len(tables)}")
