# Runbook operativo

## El drenaje no borra en WHM

1. Revise auditoría (`/audit`) por `drain_rclone_fail` o `drain_scp_fail`.
2. Compruebe `rclone` y token Drive en el volumen de configuración.
3. Compruebe espacio en el VPS de staging (`/data/staging`).

## El panel no responde

1. `docker compose ps`
2. `docker compose logs api --tail 200`
3. Restaure BD desde metabackup si la base está corrupta.

## Pausar borrados en origen

- Detenga el servicio `worker`: `docker compose stop worker`.
- Los backups seguirán generándose en WHM hasta llenar disco — coordinar con ventana WHM.

## MVP vs fase 2

- **MVP:** drenaje, Drive, auditoría, usuarios, restore asistido/API, webhooks firmados, documentación in-app.
- **Fase 2:** 2FA, métricas Prometheus, alertas por “staging no vacío”, cola Redis.
