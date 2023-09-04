Start-Process -FilePath ./app/pocketbase/pocketbase -ArgumentList serve -NoNewWindow
watchexec --restart --watch app --exts py,js,html,css -- python -m app.main