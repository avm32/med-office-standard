@echo off
REM Uj projektmappa letrehozasa az irodai dokumentumrend szerint.
REM Dupla kattintassal inditsd. Kerdez, amit kell.
REM
REM .bat es nem .exe: nincs build lepes, olvashato marad, es ha valami elromlik
REM latszik benne, hogy mit hivott meg. Python ugyis telepitve van a gepen.

chcp 65001 >nul
setlocal
cd /d "%~dp0.."

echo.
echo ============================================
echo   Uj projekt letrehozasa
echo ============================================
echo.

set /p CODE=Munkaszam (pl. 26031):
if "%CODE%"=="" goto :cancel

set /p NAME=Projekt neve (pl. Hamvas utca 6):
if "%NAME%"=="" goto :cancel

echo.
echo Mappanevek nyelve:
echo   1 = magyar  (01-Adminisztracio, 02-Bejovo, ...)
echo   2 = angol   (01-Admin, 02-Incoming, ...)
set /p LANGSEL=Valassz [1]:
if "%LANGSEL%"=="2" (set LANG=en) else (set LANG=hu)

set /p CLIENT=Megbizo (Enterrel kihagyhato):

echo.
echo Hova kerulyon a projekt?
echo   Alapertelmezett: C:\Users\PC\Documents\Projects\Medek_kft
set /p DEST=Utvonal (Enterrel az alapertelmezett):
if "%DEST%"=="" set DEST=C:\Users\PC\Documents\Projects\Medek_kft

echo.
echo --------------------------------------------
echo   Munkaszam : %CODE%
echo   Nev       : %NAME%
echo   Nyelv     : %LANG%
echo   Helye     : %DEST%
echo --------------------------------------------
echo.
set /p OK=Letrehozzam? [i/n]:
if /i not "%OK%"=="i" goto :cancel

echo.
python "_tool\medstd.py" new "%CODE%" "%NAME%" --lang %LANG% --dest "%DEST%" --client "%CLIENT%"
if errorlevel 1 goto :failed

echo.
echo Kesz. A projektjegyzetek az Obsidian vaultba kerultek,
echo a projektmappaban a 00-Notes hivatkozas mutat rajuk.
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
