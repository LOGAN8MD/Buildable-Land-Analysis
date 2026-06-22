# Buildable Land Analysis Backend

FastAPI, GeoPandas, and Shapely backend for parcel constraint analysis. Complete setup, architecture, data-source, and tradeoff documentation is in the [project README](../README.md).

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Run `pytest` for the backend suite. The API is served at `http://localhost:8000`, with Swagger documentation at `/docs`.
