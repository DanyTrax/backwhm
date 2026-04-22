# Worker de drenaje (WHM → VPS → Drive)

1. Lista por SSH los ficheros bajo `WHM_STAGING_PATH` con extensiones `.tar`, `.tar.gz` y metadatos `.master.meta`.
2. Para cada candidato, comprueba **estabilidad** (`stat` dos veces separadas por `FILE_STABLE_SECONDS`).
3. Respeta `account_filter` de la primera tarea programada habilitada que defina filtro.
4. `scp` del WHM al volumen `staging` local manteniendo ruta relativa.
5. `rclone copyto` hacia `{RCLONE_REMOTE}:{DRIVE_REMOTE_PREFIX}/<relativo>`.
6. `rm` en el WHM tras subida correcta; borra copia local temporal.

Errores disparan `ALERT_WEBHOOK_URL` si está definido.
