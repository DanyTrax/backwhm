# Pruebas en staging

1. Despliegue el stack en un VPS de prueba con `.env` apuntando a un **WHM de laboratorio** o a un subconjunto de cuentas.
2. Coloque un `.tar` pequeño artificial bajo `WHM_STAGING_PATH` y verifique que el worker lo **suba** y lo **borre** del origen.
3. **Restore:** cree un job en modo `assisted`, compruebe el fichero en `WHM_RESTORE_INCOMING` y ejecute restore manual; repita con `api` solo si conoce el impacto.
4. Valide el hook `postFinalize` con un backup real de una cuenta de prueba.
