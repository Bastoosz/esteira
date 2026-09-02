# Deploy — serviços systemd da esteira

Serviços de **usuário** (`systemctl --user`). Credencial dos CLIs mora
em `~/.esteira-auth/` e pertence ao usuário — serviço de sistema não
alcançaria.

## Sobre o espaço no caminho

O repo mora em `/home/nicolas/Área de trabalho/esteira` — com espaço e
acento. O `ExecStart` aponta direto para o Python do venv, **entre aspas**.
Não é preciso *symlink*: o systemd aceita caminho citado. Provado:

```bash
systemd-run --user --wait --collect --unit=teste \
  --property=WorkingDirectory="/home/nicolas/Área de trabalho/esteira" \
  -- "/home/nicolas/Área de trabalho/esteira/.venv/bin/python" -c "print('ok')"
# journalctl mostra: ok
```

## Instalar

```bash
cd /home/nicolas/Área de trabalho/esteira
cp -n .env.example .env   # ajuste valores
systemctl --user daemon-reload
systemctl --user enable --now esteira-worker.service esteira-vigia.service esteira-smoke.timer
systemctl --user status esteira-worker.service
```

## Verificar

```bash
systemctl --user list-timers   # confira esteira-smoke.timer
journalctl --user -u esteira-worker.service -f
```
