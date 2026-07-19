@echo off
rem Sunday 08:00 feed for the weekly social review lane: competitor screen, then report.
set PY=C:\Users\MSI\Documents\tradercockpit\OpenMontage\.venv\Scripts\python.exe
"%PY%" C:\Users\MSI\Documents\tradercockpit\tools\social_analytics.py hotdog
"%PY%" C:\Users\MSI\Documents\tradercockpit\tools\social_analytics.py report
