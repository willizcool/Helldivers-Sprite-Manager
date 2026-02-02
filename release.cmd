echo === Cleaning previous dist ===
rmdir /s /q "dist"

echo.
echo === Building with PyInstaller ===
pyinstaller -F --noconsole --icon=./icons/UIManagerLogo.ico .\SpriteSheetManager.py
if errorlevel 1 (
    echo PyInstaller failed. Aborting.
    goto :end
)

echo.
echo === Copying files into dist ===
xcopy /i /s /e /y "icons" "dist\icons"