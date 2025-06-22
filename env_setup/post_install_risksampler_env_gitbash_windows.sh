#!/usr/bin/env bash
# ------------------------------------------------------------------
# post_install_risksampler_env_gitbash_windows.sh
# - Ativa env e instala dependências do requirements.txt
# - Instala RiskSampler com `pip install -e .`
# ------------------------------------------------------------------
set -e

ENV_PATH="/c/Users/JM/envs/risksampler-lock"
PROJECT_DIR="/c/Users/JM/Documents/0_CienciaDados/1_Frameworks/RiskSampler"

# Ativar venv se necessário
if [[ -z "$VIRTUAL_ENV" || "$VIRTUAL_ENV" != *"risksampler-lock"* ]]; then
echo "✅ Activating virtualenv risksampler-lock..."
source "$ENV_PATH/Scripts/activate"
fi

# Instalar dependências do requirements.txt
echo "📥 Installing dependencies from requirements.txt..."
pip install -r "$PROJECT_DIR/env_setup/requirements.txt"

# Instalar projeto em modo editável (com ou sem extras)
echo "📦 Installing RiskSampler (editable)..."
WIN_PROJECT_DIR=$(cygpath -w "$PROJECT_DIR")
pip install -e "$WIN_PROJECT_DIR"

echo "🔍 Smoke-test: import risk_sampler"
python - <<'PY'
import risk_sampler, sys
print("RiskSampler import OK – version:", getattr(risk_sampler, "__version__", "unknown"))
PY

echo "🚀 Post-setup completed. Happy sampling!"
