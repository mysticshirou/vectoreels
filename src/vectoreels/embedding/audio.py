from pathlib import Path
from typing import Protocol

import numpy as np

from vectoreels.download.audio import download_reel_audio
from vectoreels.embedding.decode import decode_audio_to_waveform

EMBEDDING_DIM = 512

_CHECKPOINT_FILENAME = "630k-audioset-best.pt"
_CHECKPOINT_URL = f"https://huggingface.co/lukewys/laion_clap/resolve/main/{_CHECKPOINT_FILENAME}"


class AudioEmbedder(Protocol):
    def embed(self, waveform: np.ndarray) -> list[float]: ...


def _resolve_checkpoint(checkpoint_cache_dir: str | Path | None) -> str | None:
    """Downloads the CLAP checkpoint into a cache dir if given, so it survives
    container recreation instead of redownloading (~1.8GB) every time. Returns
    None to fall back to laion_clap's own default (downloads into its package
    directory, not persisted across container rebuilds).
    """
    if checkpoint_cache_dir is None:
        return None

    import wget

    cache_dir = Path(checkpoint_cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = cache_dir / _CHECKPOINT_FILENAME
    if not ckpt_path.exists():
        wget.download(_CHECKPOINT_URL, str(cache_dir))
    return str(ckpt_path)


class ClapAudioEmbedder:
    """Wraps a loaded LAION-CLAP model, projecting mono 48kHz waveforms into
    its 512-dim joint audio/text embedding space. Loading the checkpoint is
    expensive (downloads ~1.8GB on first use), so construct one instance per
    process and reuse it.
    """

    def __init__(self, checkpoint_cache_dir: str | Path | None = None) -> None:
        import laion_clap  # heavy import; deferred so importing this module stays cheap

        self._model = laion_clap.CLAP_Module(enable_fusion=False)
        self._model.load_ckpt(ckpt=_resolve_checkpoint(checkpoint_cache_dir), verbose=False)

    def embed(self, waveform: np.ndarray) -> list[float]:
        embedding = self._model.get_audio_embedding_from_data(x=[waveform], use_tensor=False)
        return embedding[0].tolist()


def embed_reel_audio(
    url: str, embedder: AudioEmbedder, cookiefile: str | Path | None = None
) -> list[float] | None:
    audio_bytes = download_reel_audio(url, cookiefile=cookiefile)
    if audio_bytes is None:
        return None
    waveform = decode_audio_to_waveform(audio_bytes)
    return embedder.embed(waveform)
