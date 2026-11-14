#!/usr/bin/env bash
# Eval-gate pre-commit.
# Bloquea el commit SOLO si hay codigo staged y el chequeo de sintaxis o los tests fallan.
# Commits solo-docs NO disparan el gate.
#
# Dificil de saltear por diseno:
#   - --no-verify NO tiene efecto: este es un hook de Claude Code (PreToolUse), no un git
#     hook. --no-verify salta los git hooks de .git/hooks, no los de CC.
#   - Path absoluto via $CLAUDE_PROJECT_DIR: con path relativo + cwd != raiz el hook
#     fallaria 127 y CC lo trataria como no-bloqueante (fail-open) -> el commit pasaria
#     sin gate. Por eso forzamos el cwd a la raiz del proyecto.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-}" 2>/dev/null || true

PY=".venv/Scripts/python.exe"

# 1) Es un commit? El payload del hook llega por stdin (tool_input.command).
input="$(cat)"
case "$input" in
  *"git commit"*) ;;       # es un commit -> seguir
  *) exit 0 ;;             # cualquier otro comando -> no-op
esac

# 2) Hay codigo staged? Si no, no gate (docs-only / otros).
staged="$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep -E '\.py$' || true)"
[ -z "$staged" ] && exit 0

echo "Eval-gate: hay codigo staged -> corriendo chequeo de sintaxis + tests..." >&2

# 3) Chequeo de sintaxis (Python no tiene typecheck configurado en este repo)
if ! tc_out="$("$PY" -m compileall -q main.py config.py src tests 2>&1)"; then
  echo "FALLO chequeo de sintaxis -- commit bloqueado. Ultimas lineas:" >&2
  echo "$tc_out" | tail -30 >&2
  exit 2
fi

# 4) Tests
#    Ya hay suite (tests/): el codigo 5 de pytest ("no hay tests") tambien bloquea, porque
#    quiere decir que la suite desaparecio o dejo de recolectarse.
test_out="$("$PY" -m pytest -q 2>&1)"
test_rc=$?
if [ "$test_rc" -ne 0 ]; then
  echo "FALLO tests -- commit bloqueado. Ultimas lineas:" >&2
  echo "$test_out" | tail -30 >&2
  exit 2
fi

echo "OK: sintaxis + tests verdes -- commit permitido." >&2
exit 0
