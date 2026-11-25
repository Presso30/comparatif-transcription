# Transcrire une réunion avec interprète : ce que valent vraiment les modèles

J'avais à transcrire l'enregistrement d'une visioconférence de 1 h 20, pour en tirer un compte rendu. L'intervenant principal parlait anglais et une interprète traduisait en français par-dessus. Sur le canal français, on entend donc les deux langues en même temps : la voix de l'interprète au premier plan et l'anglais d'origine plus bas.

Mon premier réflexe était un site en ligne (TurboScribe), mais l'offre gratuite limite chaque fichier à 30 minutes et il aurait fallu découper l'audio. J'ai préféré tester plusieurs modèles, en local sur mon portable puis en ligne, pour savoir lequel donnait le texte le plus fidèle.

Ce dépôt contient les scripts et le résultat des tests. Il ne contient aucune donnée de la réunion.

## Le matériel

- Portable HP ZBook Fury G8, carte NVIDIA RTX A4000 Laptop (8 Go de mémoire vidéo), 14 Go de RAM, Ubuntu 26.04.
- Premier obstacle sans rapport avec la transcription : après une mise à jour du noyau Linux, le pilote NVIDIA ne se chargeait plus et la carte était invisible. Il manquait le module du pilote pour le nouveau noyau (`linux-modules-nvidia-595-open-generic-hwe-26.04`). Sans le GPU, la transcription aurait tourné sur le processeur, beaucoup plus lentement.

## La méthode

1. Extraire l'audio de la vidéo avec ffmpeg (16 kHz, mono). Les 6 Go de vidéo deviennent 148 Mo de WAV, ou 37 Mo en MP3.
2. Choisir un extrait de 5 minutes et le faire transcrire par chaque modèle.
3. Comparer les textes à l'écoute, puis lancer le gagnant sur la réunion entière.

Pour choisir les candidats, j'ai consulté le classement public [Open ASR Leaderboard](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard) de Hugging Face, colonne français (taux d'erreur sur les mots, relevé le 25 novembre 2026).

## Résultats sur l'extrait de 5 minutes

| Modèle | Rang FR au classement | Erreur FR au classement | Où | Temps | Ce que j'ai observé |
|---|---|---|---|---|---|
| Whisper large-v3 (OpenAI, via faster-whisper) | 29ᵉ sur 53 | 6,24 % | local | 16 s | Texte propre et fidèle, quelques mots faux, saute parfois une phrase |
| Cohere Transcribe 03-2026 (2 milliards de paramètres) | 11ᵉ | 4,03 % | local | plus de 10 min, téléchargement du modèle compris | Mélange l'anglais de fond et le français, puis part en boucle (« de l'income » répété plus de cent fois) |
| TheStage thewhisper-large-v3-turbo | 15ᵉ | 4,53 % | local | environ 9 min, téléchargement compris | Répétitions et passages entiers transcrits en anglais |
| ElevenLabs Scribe v2 | 2ᵉ | 3,28 % | API en ligne | 7 s | Le plus complet et le plus fidèle (garde les hésitations), quelques mots isolés faux |

Le modèle de TheStage a tourné avec la bibliothèque Transformers et un découpage en morceaux de 30 secondes, et non avec le kit de son éditeur, qui demande une carte plus récente que la mienne. Ce découpage a pu aggraver les répétitions.

Deux autres candidats ont été écartés sans test. Hojo-ASR-Multi-V1 (3ᵉ au classement) pèse 12 Go, plus que ma carte. Voxtral Mini 3B de Mistral est 27ᵉ en français, à peine devant Whisper large-v3.

Sur la réunion entière, Whisper large-v3 a pris 4 minutes et ElevenLabs une minute (l'offre gratuite de l'API couvrait cette durée).

## Ce que j'en retiens

**Le classement ne prédit pas le résultat sur un audio difficile.** Les deux modèles locaux les mieux classés ont été les pires sur mon enregistrement. Les scores sont mesurés sur des enregistrements propres, dans une seule langue. Une interprétation simultanée par-dessus l'anglais n'a rien à voir. Cohere Transcribe et les modèles du même type écrivent le texte avec un modèle de langage, et c'est ce rédacteur qui s'est emballé quand l'audio mélangeait deux langues. Le test sur un extrait de 5 minutes m'a coûté une demi-heure et m'a évité de bâtir le compte rendu sur un mauvais texte.

**Le défaut d'un modèle peut servir.** En voyant TheStage transcrire l'anglais de fond, j'ai lancé Whisper en mode anglais sur le même audio. Il a récupéré le discours d'origine, plus complet que la traduction : l'interprète résumait et avait sauté des phrases entières. Cette seconde transcription a aussi corrigé des chiffres mal traduits. Par exemple, un objectif de « 50-50 » était devenu « 55 » en français, et une date limite en 2027 était devenue 2025.

**La version finale combine trois sources** :
- ElevenLabs pour le texte de base ;
- Whisper en français pour corriger les mots mal reconnus ;
- Whisper en anglais pour vérifier les chiffres, les dates et les noms, et pour signaler en note ce que l'interprète avait omis.

Les passages douteux sont marqués et minutés pour une vérification à l'oreille. Aucun outil ne donne une transcription exacte à 100 %. Les noms propres et les sigles restent le point faible de tous.

**En local ou en ligne ?** Pour un enregistrement confidentiel, Whisper large-v3 en local donne un résultat très correct en quelques minutes sur une carte de 8 Go, et rien ne sort de la machine. Quand la confidentialité n'est pas un problème, ElevenLabs Scribe v2 était le plus précis sur mon audio.

## Utiliser les scripts

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 1. Extraire l'audio
ffmpeg -i video.mp4 -vn -ac 1 -ar 16000 audio.wav
ffmpeg -ss 600 -t 300 -i audio.wav extrait.wav   # extrait de 5 min pour les tests

# 2. Comparer les modèles locaux (GPU NVIDIA)
.venv/bin/python scripts/test_comparatif.py extrait.wav whisper     # Whisper large-v3, français
.venv/bin/python scripts/test_comparatif.py extrait.wav whisper_en  # même audio, en anglais
.venv/bin/python scripts/test_comparatif.py extrait.wav cohere      # compte Hugging Face et accord de licence requis
.venv/bin/python scripts/test_comparatif.py extrait.wav thestage

# 3. ElevenLabs Scribe v2 (clé dans la variable ELEVENLABS_API_KEY ou un fichier .env)
.venv/bin/python scripts/elevenlabs_stt.py extrait.mp3 fr

# 4. Markdown vers HTML imprimable (puis « Imprimer en PDF » dans Chrome)
.venv/bin/python scripts/md2pdf.py compte_rendu.md "Titre"
```

Chaque script écrit sa transcription à côté du fichier audio, avec un horodatage par phrase. Le script ElevenLabs regroupe aussi le texte par voix détectée.
