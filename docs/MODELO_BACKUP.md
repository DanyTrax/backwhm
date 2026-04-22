# Modelo de backup adoptado por esta aplicación

## Decisión

- **Origen**: artefactos generados por el **motor nativo de backups de WHM/cPanel** bajo el directorio de staging configurado (p. ej. `/home/backup`), con subcarpetas `weekly/YYYY-MM-DD/accounts|system` y `YYYY-MM-DD/accounts|system`.
- **Transporte**: el **worker** drena archivos **estables** (tamaño sin cambios durante ventana configurable), los copia al VPS de trabajo y los sube a **Google Drive** vía **rclone**, preservando la jerarquía relativa bajo `DRIVE_REMOTE_PREFIX` (p. ej. `WHM03_BACKUP`).
- **No** se implementa en MVP un sustituto de `pkgacct` por rsync de `/home` solo: el plan prioriza **restauración tipo cPanel** desde `.tar` oficiales.

## Impacto en disco WHM

- El pico de disco ocurre **mientras WHM escribe** el artefacto; el drenaje reduce **retención acumulada** al borrar en origen tras verificación en Drive.
- Cuentas mayores que el espacio libre requieren **volumen extra** o **destino remoto WHM**; ver `CUENTAS_GIGANTES.md`.

## Incrementales

- Los incrementales son los que **genere WHM** en esos `.tar`/artefactos; el worker **no recalcula** incrementalidad, solo transporta y borra.
