# ai-powered real time system for missing person Identification & alert

PersonTrack AI is a Flask web application for registering missing-person reports and matching uploaded photos against a face-recognition pipeline. The project includes the web app, presentation, and system architecture diagrams.

## Project files

- `webapp/` — Flask application, HTML templates, and static assets
- `ai-powered real time system for missing person Identification & alert.pptx` — project presentation
- `Face Recognition Pipeline.drawio` and `.png` — recognition pipeline diagram
- `System Architecture.drawio` and `.png` — system architecture diagram

## Configuration

Set `FLASK_SECRET_KEY` before deployment. Email alerts use `adhilc8848@gmail.com` by default; set `SMTP_SENDER` to override it and provide `SMTP_APP_PASSWORD` to enable sending. Do not commit credentials, databases, or uploaded/detected images.

The face-recognition dependencies require Python 3.10. On Windows, install Python 3.10, then create a virtual environment and install the pinned compatible packages from the project root:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the Flask app from the `webapp` directory:

```powershell
cd .\webapp
..\.venv\Scripts\python.exe app.py
```

