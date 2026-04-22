# Tareas programadas (formato)

Las tareas se guardan en BD (`scheduled_tasks`). Campos:

| Campo | Descripción |
|--------|---------------|
| `name` | Nombre legible |
| `cron` | Expresión cron estándar (min hora día mes dow) |
| `task_type` | `drain_scan` (por defecto) |
| `account_filter` | JSON lista de usuarios cPanel o `null` = todas las detectadas en staging |
| `max_concurrent` | Entero ≥1; el worker procesa **un archivo** por iteración de cola |
| `enabled` | boolean |

El **worker** evalúa cron con `croniter`; fuera de ventana puede permanecer en sleep largo vía `WORKER_POLL_IDLE_SECONDS`.

## Reintentos

Variables de entorno: `DRAIN_MAX_RETRIES`, `DRAIN_RETRY_BASE_SECONDS`.
