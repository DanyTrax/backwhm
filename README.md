# WHM Backup Panel

Orquestación **WHM → VPS (Docker/Dockge) → Google Drive** con panel web (login, roles, auditoría exportable, restauración), worker de drenaje y webhook opcional firmado (HMAC).

## Requisitos

- Docker y Docker Compose (o [Dockge](https://dockge.kuma.pet/) con este `docker-compose.yml`).
- En el VPS de backup: volumen `rclone_config` (resultado de `rclone config`) y clave SSH en `./secrets/whm_rsa`.

## Puesta en marcha (Dockge “completo”)

1. Cree el stack y pegue el `docker-compose.yml` del repositorio (el build usa GitHub por defecto si no clonó el código).
2. En **Variables / .env** del stack defina al menos **`POSTGRES_PASSWORD`** (contraseña fuerte). Opcional: `API_PORT` (por defecto 8000).
3. En la carpeta del stack cree **`secrets/`** y coloque la clave privada SSH como **`whm_rsa`** (permisos restrictivos en el host).
4. Despliegue. Espere a que Postgres esté sano y la API arranque.
5. Abra **`http://IP:PUERTO/install`**: asistente paso a paso — claves de sesión ya generadas en la BD, opción de generar secreto HMAC para el webhook, creación del **primer administrador**.
6. En **`/install/complete`** siga el enlace al login; luego como admin abra **`/settings/integrations`** para conectar **WHM** y **Drive** (sustituyen valores por defecto del `.env` si los rellena en el panel).

No es obligatorio rellenar `SESSION_SECRET` ni `CSRF_SECRET` en `.env`: la sesión firma con un secreto almacenado en la tabla `app_secrets`. Puede definir `SESSION_SECRET` en entorno solo como respaldo si la base de datos no está disponible en el arranque.

## Puesta en marcha (local con repo clonado)

```bash
cp .env.example .env
# Ajuste POSTGRES_PASSWORD y, si construye en local, BUILD_CONTEXT=.

mkdir -p secrets
# Copiar clave privada SSH a secrets/whm_rsa

docker compose up -d --build
```

- API/UI: `http://IP:8000` (TLS con Caddy/Traefik delante en producción).
- **Instalación:** `http://IP:8000/install` (redirige el login si aún no hay usuarios).

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

## Dockge y build desde Git

Si en Dockge **solo pega** el `docker-compose.yml`, la carpeta del stack **no incluye** el `Dockerfile`. Por defecto el compose usa **`BUILD_CONTEXT`** apuntando a **GitHub** (`https://github.com/DanyTrax/backwhm.git#main`) para construir `api` y `worker` sin clonar.

Alternativas:

1. **Recomendado (Dockge “solo YAML”)**: deje `BUILD_CONTEXT` sin definir; el servidor necesita salida a internet para clonar el repo al construir.
2. **Stack con repo completo**: clone el proyecto en la carpeta del stack y en `.env` ponga `BUILD_CONTEXT=.` (directorio actual con `Dockerfile`).
3. **Fork privado**: cambie la URL en `docker-compose.yml` o defina `BUILD_CONTEXT=https://github.com/SU_ORG/SU_REPO.git#main` (y credenciales si el clone es privado).
