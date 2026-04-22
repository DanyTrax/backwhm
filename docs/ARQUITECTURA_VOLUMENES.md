# NVMe + volumen adicional (ej. ~300 GB)

## NVMe principal

- Contiene el sistema y, típicamente, `/home` con cuentas pequeñas/medianas.
- Carpeta de staging de backups (ej. `/home/backup`) debe tener **filesystem con espacio suficiente** para la corrida.

## Volumen grande (~300 GB)

- Use **WHM → Modify an Account** (o equivalente) para **cambiar partición de home** de cuentas muy grandes al mount del volumen extra.
- Monte el volumen con `fstab` persistente y permisos adecuados.

## Verificación

```bash
df -h /home/backup
lsblk
```
