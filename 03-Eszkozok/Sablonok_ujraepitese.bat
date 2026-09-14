@echo off
REM A Word sablonok ujraepitese a stilusmesterbol.
REM Akkor futtasd, ha a szabvany (stilusok) valtozott.
REM
REM A mar letrehozott dokumentumokat NEM erinti. Egy meglevo dokumentum
REM stilusfrissiteset a "medtpl restyle" vegzi - az viszont nem nyul olyan
REM fajlhoz, amit nem ez az eszkoz keszitett.

chcp 65001 >nul
setlocal
cd /d "%~dp0.."

echo.
echo ============================================
echo   Sablonok ujraepitese
echo ============================================
echo.

python "_tool\medtpl.py" check
if errorlevel 1 goto :failed

echo.
python "_tool\medtpl.py" build
if errorlevel 1 goto :failed

echo.
echo Kesz. Az uj sablonok a 02-Sablonok mappaban vannak.
goto :end

:failed
echo.
echo A sablon ellenorzese vagy epitese elbukott - a sablonok NEM frissultek.
echo A fenti uzenet mondja meg, melyik ellenorzes bukott el.

:end
echo.
pause
