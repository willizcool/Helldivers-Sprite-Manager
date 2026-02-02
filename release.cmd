echo === Cleaning previous dist ===
rmdir /s /q "dist"

echo.
echo === Building with PyInstaller ===
pyinstaller -F --noconsole --icon=./icons/UIManagerLogo.ico --add-data "icons;icons" .\SpriteSheetManager.py
if errorlevel 1 (
    echo PyInstaller failed. Aborting.
    goto :end
)
xcopy ".\originals" ".\dist\originals" /E /I /H /C /Y
echo Copy complete!
