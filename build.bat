@echo off
REM Builds dist\ForzaController.exe (run from the project root on Windows)
python -m venv .venv || goto :err
call .venv\Scripts\activate || goto :err
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller || goto :err
pyinstaller --noconfirm --clean --onefile --noconsole --uac-admin --name ForzaController ^
  --paths . ^
  --add-data "web;web" ^
  --collect-all qrcode --collect-all vgamepad ^
  --hidden-import PIL.ImageTk ^
  app\main.py || goto :err
echo.
echo Done: dist\ForzaController.exe
exit /b 0
:err
echo Build failed.
exit /b 1
