# Google Drive con rclone

## Configuración

1. En el host o contenedor: `rclone config` y cree un remote (p. ej. `gdrive`) tipo **Google Drive**.
2. Monte el fichero generado en el volumen `rclone_config` del compose (solo lectura en worker salvo `token` refresh).

## OAuth

Use cuenta de Google con espacio suficiente (Workspace recomendado para volúmenes grandes).

## Retención en Drive

La retención la define **usted** en Drive (políticas de vida útil) o scripts externos; esta app **sube** y opcionalmente puede borrar en origen WHM, no sustituye políticas de archivo en Drive.

## Cifrado cliente (opcional)

Para cifrado antes de subir, evalúe `rclone crypt` remote encima de `gdrive`; no está habilitado por defecto en el MVP.
