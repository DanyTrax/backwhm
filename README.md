# WHM Backup Panel

Orquestación **WHM → VPS (Docker/Dockge) → Google Drive** con panel web (login, roles, auditoría exportable, restauración), worker de drenaje y webhook opcional firmado (HMAC).

## Requisitos

- Docker y Docker Compose (o [Dockge](https://dockge.kuma.pet/) apuntando a este `docker-compose.yml`).
- En el VPS de backup: volumen `rclone_config` (resultado de `rclone config`) y clave SSH en `./secrets/whm_rsa`.

## Puesta en marcha

```bash
cp .env.example .env
# Editar al menos POSTGRES_PASSWORD, SESSION_SECRET, CSRF_SECRET.
# WHM/Drive pueden dejarse aquí como valores por defecto o configurarse después en el panel (admin → Integraciones).

mkdir -p secrets
# Copiar clave privada SSH a secrets/whm_rsa (chmod 600)

docker compose up -d --build
```

- API/UI: `http://IP:8000` (ponga TLS con Caddy/Traefik delante en producción).
- **Primer acceso:** abra `http://IP:8000/setup` y cree el **único** usuario inicial (administrador). El resto de usuarios del panel se crean en **Usuarios**.
- **Integraciones:** como admin, en `http://IP:8000/settings/integrations` defina host SSH WHM, rutas, remote `rclone` y prefijo de Drive (sustituyen al `.env` si no están vacíos).

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

Si en Dockge **solo pega** el `docker-compose.yml`, la carpeta del stack **no incluye** el `Dockerfile` y el build falla. Por defecto el compose usa **`BUILD_CONTEXT`** apuntando a **GitHub** (`https://github.com/DanyTrax/backwhm.git#main`) para construir `api` y `worker` sin clonar.

Alternativas:

1. **Recomendado (Dockge “solo YAML”)**: deje `BUILD_CONTEXT` sin definir; el servidor necesita salida a internet para clonar el repo al construir.
2. **Stack con repo completo**: clone el proyecto en la carpeta del stack y en `.env` ponga `BUILD_CONTEXT=.` (directorio actual con `Dockerfile`).
3. **Fork privado**: cambie la URL en `docker-compose.yml` o defina `BUILD_CONTEXT=https://github.com/SU_ORG/SU_REPO.git#main` (y token si hace falta para clone privado).
