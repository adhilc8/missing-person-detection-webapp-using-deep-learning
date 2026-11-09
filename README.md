# Missing Person Detection Webapp using Deep Learning

PersonTrack AI is a Flask web application for registering missing-person reports and matching uploaded photos against a face-recognition pipeline. The project includes the web app, presentation, and system architecture diagrams.

## Project files

- `webapp/` — Flask application, HTML templates, and static assets
- `Missing Person Detection Webapp using Deep Learning.pptx` — project presentation
- `Face Recognition Pipeline.drawio` and `.png` — recognition pipeline diagram
- `System Architecture.drawio` and `.png` — system architecture diagram

## Configuration

Set `FLASK_SECRET_KEY` before deployment. Email alerts require `SMTP_SENDER` and `SMTP_APP_PASSWORD`; without them, email alerts are disabled. Do not commit credentials, databases, or uploaded/detected images.

Run the Flask app from the `webapp` directory after installing its Python dependencies:

```powershell
cd webapp
python app.py
```
