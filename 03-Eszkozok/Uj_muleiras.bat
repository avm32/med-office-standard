@echo off
REM Uj statikai muleiras inditasa egy meglevo projektben.
REM Az adatokat a projekt PROJECT.md fajljabol olvassa ki.

chcp 65001 >nul
setlocal
cd /d "%~dp0.."

echo.
echo ============================================
echo   Uj statikai muleiras
echo ============================================
echo.
echo Huzd ide a projektmappat, vagy ird be az utvonalat.
set /p PROJ=Projektmappa: 
if "%PROJ%"=="" goto :cancel
set PROJ=%PROJ:"=%

set /p DESIGNER=Tervezo neve (Enterrel a PROJECT.md szerint): 
set /p REV=Revizio [S3-P01]: 
if "%REV%"=="" set REV=S3-P01

echo.
if "%DESIGNER%"=="" (
  python "_tool\medtpl.py" new "%PROJ%" --revision "%REV%"
) else (
  python "_tool\medtpl.py" new "%PROJ%" --designer "%DESIGNER%" --revision "%REV%"
)
if errorlevel 1 goto :failed

echo.
echo Kesz. Amit a program TBC-kent jelzett, azt a PROJECT.md-be ird be,
echo ne a dokumentumba - onnan minden dokumentumba automatikusan bekerul.
goto :end

:failed
echo.
echo HIBA tortent. A fenti uzenet mondja meg, mi.
goto :end

:cancel
echo.
echo Megszakitva, semmi nem tortent.

:end
echo.
pause
