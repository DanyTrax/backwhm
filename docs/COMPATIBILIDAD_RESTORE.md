# Compatibilidad restore

| Origen / destino | Notas |
|------------------|--------|
| Misma major cPanel | Menor fricción |
| Origen más antiguo → destino nuevo | Suele funcionar; revise notas de versión cPanel |
| Origen más nuevo → destino antiguo | **Evitar** |

Post-restore: DNS, SSL, IP, paquetes PHP, límites MySQL — checklist en la UI `/restore`.
