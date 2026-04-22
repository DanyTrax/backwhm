#!/usr/bin/env bash
# Volcado lógico de la BD del panel (ejecutar desde host con docker compose)
set -euo pipefail
OUT_DIR="${1:-./metabackup_out}"
mkdir -p "$OUT_DIR"
TS=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U backupwhm backupwhm \
  | gzip > "$OUT_DIR/backupwhm_${TS}.sql.gz"
echo "Guardado en $OUT_DIR/backupwhm_${TS}.sql.gz"
