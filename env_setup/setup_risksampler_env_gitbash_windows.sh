#!/usr/bin/env bash
# ------------------------------------------------------------------
# setup_risksampler_env_gitbash_windows.sh
# Target: Git Bash on Windows
# - Remove env anterior (risksampler-lock)
# - Cria venv com Python 3.13
# - Instala pip 23.3.2 + pip-tools 7.3.0
# - Gera env_setup/requirements.txt com versões fixadas
# ------------------------------------------------------------------
set -e

ENV_PATH="/c/Users/JM/envs/risksampler-lock"
PYTHON_EXEC="/c/Python313/python.exe"
PROJECT_DIR="/c/Users/JM/Documents/0_CienciaDados/1_Frameworks/RiskSampler"

echo "🧹 Removing previous env (if any)..."
rm -rf "$ENV_PATH"

echo "🐍 Creating new virtualenv with Python 3.13..."
"$PYTHON_EXEC" -m venv "$ENV_PATH"

echo "✅ Activating env..."
source "$ENV_PATH/Scripts/activate"

echo "🚀 Upgrading core build tools..."
"$ENV_PATH/Scripts/python.exe" -m pip install --upgrade pip setuptools wheel

echo "📦 Installing stable pip + pip-tools..."
"$ENV_PATH/Scripts/python.exe" -m pip install pip==23.3.2 pip-tools==7.3.0

echo "📂 Moving to project root ..."
cd "$PROJECT_DIR" || { echo '❌ Project dir not found'; exit 1; }

echo "📁 Ensuring env_setup folder exists ..."
mkdir -p env_setup

echo "📄 Generating env_setup/requirements.txt (no hashes)..."
pip-compile --output-file env_setup/requirements.txt pyproject.toml

echo "✅ Environment ready and requirements.txt generated!"
