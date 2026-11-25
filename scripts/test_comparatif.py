"""Test comparatif sur un extrait : Whisper large-v3 vs Cohere Transcribe.
Usage : .venv/bin/python test_comparatif.py extrait_5min.wav [whisper|cohere|tous]
Sorties : <extrait>_whisper.txt et <extrait>_cohere.txt
"""
import sys
import time
from pathlib import Path

audio = Path(sys.argv[1])
choix = sys.argv[2] if len(sys.argv) > 2 else "tous"


def whisper(langue="fr"):
    from faster_whisper import WhisperModel

    t = time.time()
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")
    import soundfile as sf

    wav, _ = sf.read(str(audio), dtype="float32")  # wav 16 kHz mono
    segments, info = model.transcribe(
        wav, language=langue, beam_size=5, vad_filter=True,
        condition_on_previous_text=False,
    )
    lignes = []
    for s in segments:
        m, sec = divmod(int(s.start), 60)
        lignes.append(f"[{m:02d}:{sec:02d}] {s.text.strip()}")
    out = audio.with_name(audio.stem + ("_whisper.txt" if langue == "fr" else f"_whisper_{langue}.txt"))
    out.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print(f"Whisper : {time.time() - t:.0f}s -> {out}")


def cohere():
    import torch
    from transformers import AutoProcessor, CohereAsrForConditionalGeneration
    from transformers.audio_utils import load_audio

    t = time.time()
    mid = "CohereLabs/cohere-transcribe-03-2026"
    processor = AutoProcessor.from_pretrained(mid)
    model = CohereAsrForConditionalGeneration.from_pretrained(
        mid, device_map="cuda", dtype=torch.bfloat16
    )
    wav = load_audio(str(audio), sampling_rate=16000)
    inputs = processor(audio=wav, sampling_rate=16000, return_tensors="pt", language="fr")
    idx = inputs.get("audio_chunk_index")
    inputs.to(model.device, dtype=model.dtype)
    with torch.inference_mode():
        outputs = model.generate(**inputs, max_new_tokens=448)
    texte = processor.decode(
        outputs, skip_special_tokens=True, audio_chunk_index=idx, language="fr"
    )
    if isinstance(texte, list):
        texte = texte[0]
    out = audio.with_name(audio.stem + "_cohere.txt")
    out.write_text(texte.strip() + "\n", encoding="utf-8")
    print(f"Cohere : {time.time() - t:.0f}s -> {out}")


def thestage():
    """TheStageAI/thewhisper-large-v3-turbo : poids HF standard, chargés via transformers."""
    import soundfile as sf
    import torch
    from transformers import pipeline

    t = time.time()
    asr = pipeline(
        "automatic-speech-recognition",
        model="TheStageAI/thewhisper-large-v3-turbo",
        dtype=torch.float16, device="cuda",
    )
    wav, _ = sf.read(str(audio), dtype="float32")
    res = asr(
        {"raw": wav, "sampling_rate": 16000},
        chunk_length_s=30, batch_size=8, return_timestamps=True,
        generate_kwargs={"language": "fr", "task": "transcribe", "num_beams": 5},
    )
    lignes = []
    for c in res["chunks"]:
        debut = c["timestamp"][0] or 0
        m, sec = divmod(int(debut), 60)
        lignes.append(f"[{m:02d}:{sec:02d}] {c['text'].strip()}")
    out = audio.with_name(audio.stem + "_thestage.txt")
    out.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print(f"TheStage : {time.time() - t:.0f}s -> {out}")


if choix == "whisper_en":
    whisper("en")
if choix == "thestage":
    thestage()
if choix in ("whisper", "tous"):
    whisper()
if choix in ("cohere", "tous"):
    cohere()
