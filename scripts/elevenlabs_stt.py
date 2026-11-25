"""Transcription ElevenLabs Scribe v2 (fichier entier, intervenants, horodatage).
Usage : .venv/bin/python elevenlabs_stt.py <audio> [langue|auto]
La clé est lue dans la variable ELEVENLABS_API_KEY ou dans ./.env, jamais affichée.
Sorties : <audio>_elevenlabs.json (brut) et <audio>_elevenlabs.txt (lisible).
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

audio = Path(sys.argv[1])
langue = sys.argv[2] if len(sys.argv) > 2 else "fr"
cle = os.environ.get("ELEVENLABS_API_KEY")
if not cle and Path(".env").exists():  # sinon : fichier .env dans le dossier courant
    cle = next((l.split("=", 1)[1].strip() for l in Path(".env").read_text().splitlines()
                if l.startswith("ELEVENLABS_API_KEY=")), None)
if not cle:
    sys.exit("Clé absente : définir ELEVENLABS_API_KEY ou créer un fichier .env")

data = {"model_id": "scribe_v2", "diarize": "true", "timestamps_granularity": "word",
        "tag_audio_events": "false"}
if langue != "auto":
    data["language_code"] = langue

t = time.time()
with audio.open("rb") as f:
    r = requests.post(
        "https://api.elevenlabs.io/v1/speech-to-text",
        headers={"xi-api-key": cle},
        data=data,
        files={"file": (audio.name, f)},
        timeout=3600,
    )
if r.status_code != 200:
    sys.exit(f"Erreur {r.status_code} : {r.text[:500]}")
res = r.json()
base = audio.with_name(audio.stem + "_elevenlabs")
base.with_suffix(".json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

# Regroupe les mots en paragraphes par intervenant (nouveau paragraphe si changement
# d'intervenant ou pause > 2 s).
lignes, cur, debut, spk, fin_prec = [], [], 0.0, None, 0.0
for w in res.get("words", []):
    if w.get("type") == "spacing":
        if cur:
            cur.append(w["text"])
        continue
    s = w.get("speaker_id")
    if cur and (s != spk or w["start"] - fin_prec > 2):
        m, sec = divmod(int(debut), 60)
        lignes.append(f"[{m:02d}:{sec:02d}] ({spk}) {''.join(cur).strip()}")
        cur = []
    if not cur:
        debut, spk = w["start"], s
    cur.append(w["text"])
    fin_prec = w["end"]
if cur:
    m, sec = divmod(int(debut), 60)
    lignes.append(f"[{m:02d}:{sec:02d}] ({spk}) {''.join(cur).strip()}")
base.with_suffix(".txt").write_text("\n".join(lignes) + "\n", encoding="utf-8")
print(f"ElevenLabs : {time.time() - t:.0f}s, langue détectée {res.get('language_code')} "
      f"({res.get('language_probability')}) -> {base}.txt")
