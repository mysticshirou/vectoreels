import functools
import logging
import os
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from elasticsearch import Elasticsearch
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from vectoreels.download.cookies import is_valid_cookiefile, write_cookiefile
from vectoreels.download.music import get_music_title
from vectoreels.embedding.audio import ClapAudioEmbedder, embed_reel_audio
from vectoreels.embedding.decode import decode_audio_to_waveform
from vectoreels.ingestion.ingest import parse_liked_posts
from vectoreels.processing.process import (
    AudioEmbeddingLookup,
    MusicTitleLookup,
    process_and_index_posts,
)
from vectoreels.search.query import to_search_filters
from vectoreels.search.search import ElasticsearchStageIndex, ensure_index, search_posts

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger("vectoreels.upload")

PACKAGE_DIR = Path(__file__).parent
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
INSTAGRAM_COOKIES_PATH = os.environ.get("INSTAGRAM_COOKIES_PATH")
CLAP_CHECKPOINT_CACHE_DIR = os.environ.get("CLAP_CHECKPOINT_CACHE_DIR")


def _build_music_title_lookup() -> MusicTitleLookup | None:
    if INSTAGRAM_COOKIES_PATH is None:
        return None
    return functools.partial(get_music_title, cookiefile=INSTAGRAM_COOKIES_PATH)


def _build_audio_embedding_lookup(embedder: ClapAudioEmbedder) -> AudioEmbeddingLookup:
    return functools.partial(embed_reel_audio, embedder=embedder, cookiefile=INSTAGRAM_COOKIES_PATH)


class UploadStatus:
    def __init__(self) -> None:
        self.stage: str | None = None
        self.count: int | None = None
        self.error: str | None = None


def _report_stage(status: UploadStatus, stage: str) -> None:
    status.stage = stage
    logger.info(stage)


def _run_upload(app: FastAPI, raw: bytes) -> None:
    status: UploadStatus = app.state.upload_status
    try:
        _report_stage(status, "Parsing liked_posts.json")
        posts = parse_liked_posts(raw)
        process_and_index_posts(
            posts,
            ElasticsearchStageIndex(app.state.es_client),
            music_title_lookup=_build_music_title_lookup(),
            audio_embedding_lookup=_build_audio_embedding_lookup(app.state.audio_embedder),
            on_stage=functools.partial(_report_stage, status),
        )
        status.count = len(posts)
        logger.info("Indexed %d posts", status.count)
    except Exception as exc:
        # Recorded so the polling UI can surface the failure instead of
        # spinning forever; still re-raised so it crashes and prints to the
        # logs exactly as an uncaught thread exception normally would.
        status.error = str(exc)
        raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client = Elasticsearch(ELASTICSEARCH_URL)
    ensure_index(client)
    app.state.es_client = client
    app.state.audio_embedder = ClapAudioEmbedder(checkpoint_cache_dir=CLAP_CHECKPOINT_CACHE_DIR)
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
    request.app.state.upload_status = UploadStatus()
    threading.Thread(target=_run_upload, args=(request.app, raw), daemon=True).start()
    return templates.TemplateResponse(
        request, "_upload_status.html", {"stage": "Starting…", "done": False}
    )


@app.get("/upload/status", response_class=HTMLResponse)
async def upload_status(request: Request) -> HTMLResponse:
    status: UploadStatus = request.app.state.upload_status
    if status.error is not None:
        return templates.TemplateResponse(
            request, "_upload_status.html", {"error": status.error, "done": True}
        )
    if status.count is not None:
        return templates.TemplateResponse(
            request, "_upload_status.html", {"count": status.count, "done": True}
        )
    return templates.TemplateResponse(
        request, "_upload_status.html", {"stage": status.stage, "done": False}
    )


@app.post("/cookies", response_class=HTMLResponse)
async def upload_cookies(request: Request, file: UploadFile) -> HTMLResponse:
    content = await file.read()
    if not is_valid_cookiefile(content):
        return templates.TemplateResponse(
            request, "_cookies_status.html", {"error": "That doesn't look like a Netscape cookies.txt file"}
        )
    if INSTAGRAM_COOKIES_PATH is None:
        return templates.TemplateResponse(
            request, "_cookies_status.html", {"error": "INSTAGRAM_COOKIES_PATH is not configured"}
        )
    write_cookiefile(Path(INSTAGRAM_COOKIES_PATH), content)
    return templates.TemplateResponse(request, "_cookies_status.html", {"success": True})


@app.post("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    keywords: list[str] = Form(default=[]),
    description: str = Form(default=""),
    song: str = Form(default=""),
    date_from: str = Form(default=""),
    date_to: str = Form(default=""),
    audio_file: UploadFile | None = File(default=None),
) -> HTMLResponse:
    audio_embedding = None
    if audio_file is not None and audio_file.filename:
        audio_bytes = await audio_file.read()
        waveform = decode_audio_to_waveform(audio_bytes)
        audio_embedding = request.app.state.audio_embedder.embed(waveform)

    filters = to_search_filters(
        keywords=[k for k in keywords if k],
        description=description,
        song=song,
        date_from=date_from,
        date_to=date_to,
        audio_embedding=audio_embedding,
    )
    posts = search_posts(request.app.state.es_client, filters)
    return templates.TemplateResponse(request, "_results.html", {"posts": posts})
