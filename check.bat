@echo off
title OpenSea Multi-Terminal Orchestrator
cls

:: App setup configuration variables
set SCRIPT_NAME=check.py
set TOTAL_TERMINALS=3

echo ========================================================
echo  Spawning %TOTAL_TERMINALS% Dedicated Scraping Terminals...
echo ========================================================
echo.

:: Terminal Instance #1
start "OpenSea Scraper - Terminal 1" cmd /k "python %SCRIPT_NAME% --worker_id 0 --total_workers %TOTAL_TERMINALS%"

:: Terminal Instance #2
start "OpenSea Scraper - Terminal 2" cmd /k "python %SCRIPT_NAME% --worker_id 1 --total_workers %TOTAL_TERMINALS%"

:: Terminal Instance #3
start "OpenSea Scraper - Terminal 3" cmd /k "python %SCRIPT_NAME% --worker_id 2 --total_workers %TOTAL_TERMINALS%"

echo.
echo ========================================================
echo  All threads assigned and executing concurrently.
echo ========================================================
pause