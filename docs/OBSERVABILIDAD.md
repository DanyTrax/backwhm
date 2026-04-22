# Alertas

Configure `ALERT_WEBHOOK_URL` con un endpoint que acepte `POST` JSON `{ "title": "...", "body": { ... } }`.

Eventos que disparan alerta hoy:

- Fallo de `scp` en drenaje.
- Fallo de `rclone` en drenaje.

**Fase 2 sugerida:** alerta si el staging no vacía tras X horas, disco del VPS por encima de umbral, SSH inaccesible (healthcheck externo).
