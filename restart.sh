#!/bin/bash
echo "Restarting Flask app..."
pkill -f "gunicorn.*app:app" || pkill -f "flask run" || pkill -f "python.*app.py"
sleep 1
echo "App restarted!"
