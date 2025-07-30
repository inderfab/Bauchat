from huggingface_hub import hf_hub_download
import os

REPO_ID = "TheBloke/phi-2-GGUF"
FILENAME = "phi-2.Q4_K_M.gguf"
LOCAL_DIR = "./models"

os.makedirs(LOCAL_DIR, exist_ok=True)

print("Modell wird heruntergeladen...")
path = hf_hub_download(
    repo_id=REPO_ID,
    filename=FILENAME,
    local_dir=LOCAL_DIR,
    local_dir_use_symlinks=False
)
print(f"Download abgeschlossen: {path}")