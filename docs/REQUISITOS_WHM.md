# Requisitos y comprobaciones WHM/cPanel

## Versión

Documente en producción la salida de:

```bash
/usr/local/cpanel/cpanel -V
```

La API OpenAPI de WHM y los hooks **PkgAcct** (`postFinalize`) pueden variar entre versiones. Valide en su servidor antes de confiar en automatismos.

## API WHM

- Cree un **token de API** en WHM con permisos **mínimos** para las operaciones que use la app (listar cuentas, colas de restore si aplica).
- Para **restauración automatizada** suele requerirse un token **separado** con permisos elevados; no reutilice el token de solo lectura del drenaje.

## Espacio en disco

- Política recomendada: **staging dedicado** (p. ej. `/home/backup` o volumen montado) con espacio suficiente para el **artefacto más grande** en ventana de backup.
- Consulte espacio libre: `df -h` en el filesystem del staging.

## Concurrencia `pkgacct` / backups programados

En **WHM → Backup → Backup Configuration** revise si los backups de cuentas se ejecutan en **paralelo** o en **serie**. El worker de drenaje asume **1 archivo activo** a la vez por cola; si WHM genera varios `.tar` simultáneos, ajuste el paralelismo en WHM o dimensione el staging.

## Firewall

Restrinja **SSH (22)** y, si aplica, **WHM (2087)** al **IP fija del VPS de backup** y a sus IPs de administración.
