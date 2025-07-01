cd C:\ShareGuard
.\venv\Scripts\activate
$env:PYTHONPATH = "C:\ShareGuard\src"
$env:PATH = "$env:PATH;C:\Program Files\nodejs\"
$env:USE_SQLITE = "true"
$env:SQLITE_PATH = "shareguard.db"

uvicorn app:app --reload