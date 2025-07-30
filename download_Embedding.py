from huggingface_hub import snapshot_download
import os

local_path = "./huggingface_models/all-MiniLM-L6-v2"
model_id = "sentence-transformers/all-MiniLM-L6-v2"

snapshot_download(
    repo_id=model_id,
    local_dir=local_path,
    local_dir_use_symlinks=False
)