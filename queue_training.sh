#!/bin/bash
# Queue SolidWorks Semantic Engine Axolotl training
# Waits for BCL training (PID 3588626) to finish, then starts SW training
# -------------------------------------------------------------------

set -euo pipefail

BCL_PID=3588626
AXOLOTL_VENV="/home/samuraibuddha/Documents/GitHub/axolotl/venv_axolotl"
SW_DIR="/home/samuraibuddha/Documents/GitHub/sw-semantic-engine"
CONFIG="axolotl_solidworks_config.yml"
LOG_FILE="${SW_DIR}/training_$(date +%Y%m%d_%H%M%S).log"

echo "=== SolidWorks Semantic Engine - Queued Training ==="
echo "Waiting for BCL training (PID ${BCL_PID}) to finish..."
echo "Log file: ${LOG_FILE}"
echo ""

# Wait for BCL process to finish
if kill -0 "${BCL_PID}" 2>/dev/null; then
    echo "[$(date '+%H:%M:%S')] BCL training still running. Polling every 30s..."
    while kill -0 "${BCL_PID}" 2>/dev/null; do
        sleep 30
    done
    echo "[$(date '+%H:%M:%S')] BCL training finished!"
else
    echo "[$(date '+%H:%M:%S')] BCL training already finished."
fi

# Brief cooldown to let GPU memory free up
echo "[$(date '+%H:%M:%S')] Waiting 15s for GPU memory to release..."
sleep 15

# Verify GPU is available
echo "[$(date '+%H:%M:%S')] GPU status:"
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader
echo ""

# Activate venv and start training
echo "[$(date '+%H:%M:%S')] Starting SolidWorks fine-tuning..."
echo "  Base model: Qwen/Qwen2.5-Coder-7B"
echo "  Adapter: QLoRA (r=16, alpha=32)"
echo "  Dataset: 2,793 SolidWorks training pairs"
echo "  Epochs: 3"
echo "  Output: ${SW_DIR}/solidworks_finetune/"
echo ""

source "${AXOLOTL_VENV}/bin/activate"
cd "${SW_DIR}"

python -m axolotl.cli.train "${CONFIG}" 2>&1 | tee "${LOG_FILE}"

echo ""
echo "[$(date '+%H:%M:%S')] Training complete! Output in: ${SW_DIR}/solidworks_finetune/"
