import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from elasticsearch import Elasticsearch
from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from vectoreels.ingestion.ingest import parse_liked_posts
from vectoreels.processing.process import process_posts
from vectoreels.search.query import to_search_filters
from vectoreels.search.search import ensure_index, index_posts, search_posts

PACKAGE_DIR = Path(__file__).parent
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client = Elasticsearch(ELASTICSEARCH_URL)
    ensure_index(client)
    app.state.es_client = client
    yield
    client.close()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"posts": None})


@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile) -> HTMLResponse:
    raw = await file.read()
    posts = parse_liked_posts(raw)
    processed = process_posts(posts)
    index_posts(request.app.state.es_client, processed)
    return templates.TemplateResponse(
        request, "_upload_status.html", {"count": len(processed)}
    )


@app.post("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    keywords: list[str] = Form(default=[]),
    description: str = Form(default=""),
    date_from: str = Form(default=""),
    date_to: str = Form(default=""),
) -> HTMLResponse:
    filters = to_search_filters(
        keywords=[k for k in keywords if k], description=description, date_from=date_from, date_to=date_to
    )
    posts = search_posts(request.app.state.es_client, filters)
    return templates.TemplateResponse(request, "_results.html", {"posts": posts})
