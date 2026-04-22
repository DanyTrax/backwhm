# Cuentas mayores que el espacio libre en el nodo WHM

## Estrategias

1. **Volumen adicional montado** solo para staging de backups (recomendado).
2. **Destino adicional** en WHM (SFTP/S3 compatible) para que el motor escriba fuera del `/` lleno.
3. **Reubicación del homedir** de la cuenta gigante a otro disco mediante **herramientas WHM** (no mover carpetas a mano).

## Rol de esta app

El worker **asume** que WHM puede **completar** el archivo en el staging; si el disco es insuficiente, el evento quedará en **auditoría** como error y deberá actuarse en infraestructura WHM.
