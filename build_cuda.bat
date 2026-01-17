call .venv_cuda/Scripts/activate
set PYTHONWARNINGS=ignore
pyinstaller backend_cuda.spec --distpath src-tauri/bin --clean --noconfirm --log-level ERROR