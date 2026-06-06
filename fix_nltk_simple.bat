@echo off
echo ========================================
echo Fixing NLTK and Running App
echo ========================================

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Cleaning up NLTK data...
rmdir /s /q "%APPDATA%\nltk_data" 2>nul

echo.
echo Downloading NLTK punkt...
python -c "import nltk; nltk.download('punkt')"

echo.
echo Verifying NLTK installation...
python -c "from nltk.tokenize import sent_tokenize; print('NLTK working!')"

echo.
echo ========================================
echo Starting Nexus Scholar App...
echo ========================================
echo.
