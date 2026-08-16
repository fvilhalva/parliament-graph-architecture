#!/usr/bin/env bash
#
# run.sh - orquestra a análise de redes parlamentares (parliament-graph-architecture)
#
# Uso:
#   ./run.sh setup            # cria .env (do .env.example) e builda a imagem Docker
#   ./run.sh test             # roda a suíte de testes (pytest via Docker)
#   ./run.sh pipeline         # roda o pipeline completo 2022-2025 (gera data/)
#   ./run.sh compare          # análise comparativa entre anos (gera PNGs em data/plots)
#   ./run.sh all              # setup + pipeline + compare + test (faz tudo, na ordem certa)
#   ./run.sh status           # mostra o que já foi gerado e o estado do Docker
#   ./run.sh clean [-y]       # APAGA data/ gerado (destrutivo)
#   ./run.sh help
#
# O comando 'all' roda os testes POR ÚLTIMO, de propósito: com os dados já
# gerados pelo pipeline, os 64 testes de integridade de dataset deixam de ser
# pulados e a suíte completa (210) valida os resultados reais.
#
set -euo pipefail

# --------------------------------------------------------------------------
# Configuração
# --------------------------------------------------------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# --------------------------------------------------------------------------
# Helpers de log
# --------------------------------------------------------------------------
log()  { printf '\033[1;34m>>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32mOK\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mXX\033[0m %s\n' "$*" >&2; exit 1; }

# --------------------------------------------------------------------------
# Pré-requisitos
# --------------------------------------------------------------------------
need_docker() {
  command -v docker >/dev/null 2>&1 || die "docker não encontrado no PATH."
  docker info >/dev/null 2>&1 || die "Docker não está rodando (ligue o Docker Desktop e tente de novo)."
}

ensure_env() {
  if [ ! -f .env ]; then
    [ -f .env.example ] || die ".env.example não encontrado — não dá pra gerar o .env."
    cp .env.example .env
    ok ".env criado a partir de .env.example"
  else
    ok ".env já existe"
  fi
}

ensure_image() {
  if ! docker compose images tests 2>/dev/null | grep -q .; then
    log "Imagem ainda não existe — buildando..."
    docker compose build
  fi
}

# --------------------------------------------------------------------------
# Comandos
# --------------------------------------------------------------------------
cmd_setup() {
  need_docker
  ensure_env
  log "Buildando a imagem Docker..."
  docker compose build
  ok "Setup concluído."
}

cmd_test() {
  need_docker; ensure_env; ensure_image
  log "Rodando a suíte de testes (pytest)..."
  docker compose run --rm tests
  ok "Testes finalizados."
}

cmd_pipeline() {
  need_docker; ensure_env; ensure_image
  log "Rodando o pipeline completo (2022-2025) — pode levar ~15-25 min..."
  docker compose run --rm pipeline_chamber
  ok "Pipeline concluído — resultados em data/analysis/ e data/metricas/."
}

cmd_compare() {
  need_docker; ensure_env; ensure_image
  if ! ls data/analysis/analysis_*.json >/dev/null 2>&1; then
    die "Nenhum data/analysis/analysis_*.json encontrado. Rode './run.sh pipeline' antes."
  fi
  log "Gerando análise comparativa entre anos..."
  docker compose run --rm compare
  ok "Comparação concluída — PNGs em data/plots/."
}

cmd_all() {
  need_docker; ensure_env
  log "== Passo 1/4: build =="
  docker compose build
  log "== Passo 2/4: pipeline (2022-2025) =="
  docker compose run --rm pipeline_chamber
  log "== Passo 3/4: comparação entre anos =="
  docker compose run --rm compare
  log "== Passo 4/4: testes (agora com dados -> suíte completa) =="
  docker compose run --rm tests
  echo; ok "Tudo pronto. Resultados em data/analysis/, data/metricas/ e data/plots/."
}

cmd_status() {
  echo "== Containers do projeto =="
  docker compose ps 2>/dev/null || warn "docker compose indisponível"
  echo
  echo "== Artefatos gerados (data/) =="
  if [ -d data ]; then
    for sub in analysis metricas gexf plots; do
      if [ -d "data/$sub" ]; then
        n=$(find "data/$sub" -type f | wc -l | tr -d ' ')
        printf '  %-10s %s arquivo(s)\n' "$sub/" "$n"
      else
        printf '  %-10s (não gerado)\n' "$sub/"
      fi
    done
  else
    warn "data/ ainda não existe — rode './run.sh pipeline'."
  fi
}

cmd_clean() {
  local yes=0
  case "${1:-}" in -y|--yes) yes=1 ;; esac
  warn "Isto vai APAGAR toda a pasta data/ (dados gerados: cache, análises, métricas, gexf, plots)."
  if [ "$yes" -ne 1 ]; then
    printf '\033[1;33m!!\033[0m Confirma? digite "sim" para continuar: '
    local ans; read -r ans
    [ "$ans" = "sim" ] || { log "cancelado (nada foi apagado)"; return 0; }
  fi
  rm -rf data/
  ok "data/ removido. (O pipeline recria tudo do zero.)"
}

# --------------------------------------------------------------------------
# Dispatch
# --------------------------------------------------------------------------
usage() { sed -n '3,17p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

case "${1:-help}" in
  setup)    cmd_setup ;;
  test)     cmd_test ;;
  pipeline) cmd_pipeline ;;
  compare)  cmd_compare ;;
  all)      cmd_all ;;
  status)   cmd_status ;;
  clean)    shift; cmd_clean "${1:-}" ;;
  help|-h|--help) usage ;;
  *) die "comando desconhecido: ${1:-} (use: setup|test|pipeline|compare|all|status|clean|help)" ;;
esac
