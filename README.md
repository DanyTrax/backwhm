# WHM Backup Panel

Orquestación **WHM → VPS (Docker/Dockge) → Google Drive** con panel web (login, roles, auditoría exportable, restauración), worker de drenaje y webhook opcional firmado (HMAC).

## Requisitos

- Docker y Docker Compose (o [Dockge](https://dockge.kuma.pet/) apuntando a este `docker-compose.yml`).
- En el VPS de backup: volumen `rclone_config` (resultado de `rclone config`) y clave SSH en `./secrets/whm_rsa`.

## Puesta en marcha

```bash
cp .env.example .env
# Editar POSTGRES_PASSWORD, SESSION_SECRET, CSRF_SECRET, WHM_*, RCLONE_REMOTE, DRIVE_REMOTE_PREFIX, WEBHOOK_HMAC_SECRET (opcional)

mkdir -p secrets
# Copiar clave privada SSH a secrets/whm_rsa (chmod 600)

docker compose up -d --build
```

- API/UI: `http://IP:8000` (ponga TLS con Caddy/Traefik delante en producción).
- Usuario inicial: variables `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD` (cámbielas de inmediato).

## Documentación

- [docs/RUNBOOK.md](docs/RUNBOOK.md)
- [docs/REQUISITOS_WHM.md](docs/REQUISITOS_WHM.md)
- [docs/DRENAJE_WHM.md](docs/DRENAJE_WHM.md)
- [docs/DRIVE_SEGURIDAD.md](docs/DRIVE_SEGURIDAD.md)
- Metabackup BD: [scripts/metabackup.sh](scripts/metabackup.sh)

## Pruebas

```bash
pip install -r requirements.txt
pytest -q
```

## Dockge

Cree un stack nuevo y pegue el contenido de `docker-compose.yml`, o use “Compose path” al directorio de este proyecto.
