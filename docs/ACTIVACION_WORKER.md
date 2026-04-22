# Activación del worker (sin polling agresivo)

- `WORKER_POLL_ACTIVE_SECONDS`: intervalo tras un ciclo donde hubo trabajo (p. ej. 120 s).
- `WORKER_POLL_IDLE_SECONDS`: intervalo cuando no hubo nada que hacer (p. ej. 900 s = 15 min).
- Opcional: combine con **hook** `postFinalize` que llama a `/webhooks/pkgacct` para registrar eventos y acudir a logs; el worker sigue haciendo polling pero puede acortar `WORKER_POLL_IDLE_SECONDS` si recibe señales externas (fase 2).
