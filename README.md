# Les études de cas Scalability, en version écrite

J'ai vu qu'il n'y avait pas de témoignage écrit sur le site de Scalability, et j'ai fait un
système pour transformer chaque vidéo en étude de cas écrite. J'espère que ça vous sera utile !

## Ce qu'il y a dans ce repo

| | |
|---|---|
| [`case-studies/`](case-studies/) | Les 9 études de cas |
| [`SKILL.md`](SKILL.md) | La méthode, si vous voulez la refaire tourner |
| [`scripts/`](scripts/) | Les scripts qui font le travail |

## Les 9 études de cas

| Client | | |
|---|---|---|
| [Karmen](case-studies/karmen.md) | 842 mots | Ils ont internalisé pendant deux ans, puis ils sont revenus |
| [Brevo](case-studies/brevo.md) | 652 mots | Ouvrir l'Espagne sans acheter dix licences de plus *(en anglais)* |
| [Ircam Amplify](case-studies/ircam-amplify.md) | 630 mots | Les creux entre deux campagnes, et pourquoi il a fallu tenir |
| [Ubiq](case-studies/ubiq.md) | 597 mots | 500 entreprises rencontrées, 38 000 personnes contactées |
| [Hyperline](case-studies/hyperline.md) | 543 mots | Quatre constats à l'arrivée du Head of Sales |
| [Angel Studio](case-studies/angel-studio.md) | 528 mots | 30 % du CA, après plusieurs prestataires décevants |
| [Banque Populaire](case-studies/banque-populaire.md) | 508 mots | Pourquoi ils n'ont pas pris de consultants |
| [Sopht](case-studies/sopht.md) | 492 mots | Le scoring leur a fait découvrir qui achète vraiment |
| [impact.com](case-studies/impact.md) | 458 mots | 70 % du volume d'affaires gagné sur le lancement France |

## Comment ça marche

### 1. Récupérer l'audio des vidéos

Les vidéos Vimeo du site sont restreintes au domaine. Donc je laisse le navigateur lire la vidéo,
je récupère l'URL signée `playlist.json` dans le log réseau, et je réassemble les segments audio.

```bash
python scripts/grab.py client "<url playlist.json>" "https://www.getscalability.io/"
```

Les URLs signées expirent au bout d'une heure environ.

### 2. Transcrire deux fois, avec deux modèles différents

```bash
python scripts/transcribe.py client.m4a transcripts/client fr
```

`nova-2` pour la ponctuation et la séparation des intervenants, ce qui sert sur Ubiq où il y en a
deux. `whisper-large` pour les noms propres, où il est bien meilleur.

### 3. Croiser les deux transcripts

```bash
python scripts/compare.py transcripts/client_nova.txt transcripts/client_whisper.txt diff.md
```

Deux modèles se trompent rarement au même endroit. Là où ils écrivent la même chose, le mot est
bon. Là où ils divergent, le script le signale et je vais réécouter le passage.

### 4. Vérifier chaque citation

```bash
python scripts/verify_quotes.py case-studies/client.md \
    transcripts/client_nova.txt transcripts/client_whisper.txt
```

Le script reprend chaque citation du texte final et la compare aux transcripts, mot à mot. S'il
trouve un mot qui n'y est pas, il le signale.

## Pour le refaire tourner

```bash
pip install -r requirements.txt
export DEEPGRAM_API_KEY=...
```

Le système marche sur n'importe quelle vidéo de témoignage, pas seulement les vôtres. Si vous en
tournez d'autres, vous pouvez le relancer dessus.

Et si vous voulez creuser ou adapter le système à autre chose, écrivez-moi.

---

Lucas Carval
