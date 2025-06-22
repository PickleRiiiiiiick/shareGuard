cd C:\ShareGuard
.\venv\Scripts\activate
$env:PYTHONPATH = "C:\ShareGuard\src"
$env:PATH = "$env:PATH;C:\Program Files\nodejs\"

uvicorn app:app --reload