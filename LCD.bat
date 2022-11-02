@echo off

echo Activating conda environment...
call conda activate guienv
echo Loading LCD...
call python "%~dp0\LC_Dielectrics.py"

