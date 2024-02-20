#!/bin/bash

./app/pocketbase/pocketbase serve &
watchexec --restart --watch app --exts py,js,html,jinja,css -- python -m app.main &
watchexec --restart --watch app --exts py,js,html,jinja,css -- uvicorn app.main:app --host=0.0.0.0 --port=8000 &
./tailwindcss -i ./app/static/input.css -o ./app/static/output.css --watch