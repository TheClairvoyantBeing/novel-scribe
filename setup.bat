@echo off
echo [1/3] Creating virtual environment...
python -m venv venv

echo [2/3] Installing dependencies...
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r requirements.txt

echo [3/3] Setting up environment variables...
venv\Scripts\python main.py env

echo.
echo ===========================================
echo Setup complete! 
echo To start work, activate your environment with:
echo    venv\Scripts\activate
echo ===========================================
pause
