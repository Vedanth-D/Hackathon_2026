@echo off
REM Run the evidence review pipeline (requires Python 3.10+)
where python3 2>nul && python3 main.py %* && goto :done
where python 2>nul && python main.py %* && goto :done
echo Python 3 not found. Install Python 3.10+ and run: pip install -r requirements.txt
:done
