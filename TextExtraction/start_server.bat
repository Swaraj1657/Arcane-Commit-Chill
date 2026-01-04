@echo off
REM Start the certificate verification API server

echo Starting Certificate Verification API Server...
echo Make sure you have:
echo 1. Installed all dependencies (pip install -r requirements.txt)
echo 2. Set up your API keys in text.py and beautifyText.py
echo 3. Installed Poppler and updated POPPLER_PATH in text.py
echo.
echo Server will start on http://localhost:8000
echo.

python api_server.py

pause

