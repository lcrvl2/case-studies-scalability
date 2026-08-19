# Les études de cas Scalability, en version écrite

Les 9 témoignages clients existaient en vidéo, sans version écrite à côté. Les voici, rédigés à
partir des transcripts, un par client.

## Ce qu'il y a dans ce repo

| | |
|---|---|
| [`case-studies/`](case-studies/) | Les 9 études de cas rédigées |
| [`SKILL.md`](SKILL.md) | La méthode complète, rejouable sur d'autres clients |
| [`scripts/`](scripts/) | Les 5 scripts utilisés (extraction, transcription, vérification) |

## Les études de cas

| Client | Mots | Angle |
|---|---|---|
| [Karmen](case-studies/karmen.md) | 842 | Ils ont internalisé pendant deux ans avant de revenir |
| [Brevo](case-studies/brevo.md) *(en anglais)* | 652 | Ouvrir l'Espagne sans acheter dix licences de plus |
| [Ircam Amplify](case-studies/ircam-amplify.md) | 630 | « Ça prend du temps », et ce qu'il a fallu accepter |
| [Ubiq](case-studies/ubiq.md) | 597 | 500 entreprises rencontrées, 38 000 personnes contactées |
| [Hyperline](case-studies/hyperline.md) | 543 | Quatre constats, et la décision d'externaliser |
| [Angel Studio](case-studies/angel-studio.md) | 528 | 30 % du CA, après plusieurs prestataires décevants |
| [Banque Populaire](case-studies/banque-populaire.md) | 508 | L'acquisition digitale dans une banque de réseau |
| [Sopht](case-studies/sopht.md) | 492 | Des contrats pluriannuels, dont une entreprise du CAC 40 |
| [impact.com](case-studies/impact.md) | 458 | 70 % du volume d'affaires gagné sur le lancement France |

18 min 50 s de parole client, 4 010 mots de verbatim extraits, 5 250 mots rédigés.

Deux points de méthode rédactionnelle : les citations sont vérifiées mot à mot contre les
transcripts, et aucun chiffre ne vient d'ailleurs que des vidéos. Quand une formulation du site
diffère de ce que dit le client, c'est la version du client qui est retenue, avec une note en fin
de document. Trois intervenants ne se présentant que par leur prénom sont cités par leur fonction.

## La méthode d'extraction

Le détail est dans [`SKILL.md`](SKILL.md). Les quatre étapes qui comptent.

### 1. Sortir l'audio d'un Vimeo verrouillé au domaine

Les vidéos sont restreintes au domaine du site, ce qui bloque les outils habituels :

| Voie | Résultat |
|---|---|
| `yt-dlp` | 401 sur tous les clients (web, android, ios) |
| endpoint `/config` du player | 403 en direct, CORS depuis la page |
| pistes de sous-titres | absentes (`getTextTracks()` renvoie `[]`) |

Ce qui marche : laisser le navigateur lire la vidéo, récupérer l'URL signée `playlist.json` dans
le log réseau, puis réassembler les segments audio. Les URLs signées expirent en une heure.

```bash
python scripts/grab.py client "<url playlist.json>" "https://www.getscalability.io/"
```

### 2. Transcrire deux fois, avec deux modèles différents

```bash
python scripts/transcribe.py client.m4a transcripts/client fr
```

`nova-2` apporte la ponctuation et la diarisation (utile sur Ubiq, qui a deux intervenants),
`whisper-large` est nettement meilleur sur les noms propres.

### 3. Croiser les deux transcripts

```bash
python scripts/compare.py transcripts/client_nova.txt transcripts/client_whisper.txt diff.md
```

C'est le cœur de la méthode. Deux modèles ASR indépendants se trompent différemment : là où ils
écrivent la même chose le mot est fiable, là où ils divergent il faut aller regarder. La
divergence sert de détecteur d'erreurs.

Sur ces 9 vidéos : 207 divergences, 5 arbitrages réels. Un seul transcript aurait laissé passer
une proposition entière sautée par un modèle, celle qui contient « plus de 70 opportunités…
plusieurs centaines de milliers d'euros ».

Ce que la comparaison ne détecte pas : les cas où **les deux modèles se trompent pareil**. C'est
fréquent sur les noms propres, d'où une vérification externe des identités.

### 4. Vérifier chaque citation par script

```bash
python scripts/verify_quotes.py case-studies/client.md \
    transcripts/client_nova.txt transcripts/client_whisper.txt
```

L'étape la moins évidente et la plus utile. En rédigeant, on corrige machinalement la grammaire
orale d'un client : « j'ai eue » pour « j'ai eu », « à moindres frais » pour « à moindre frais ».
Aucune de ces retouches ne change le sens, donc aucune ne se voit à la relecture, et le texte
n'est plus verbatim.

Sur ces études de cas, le premier passage donnait 6 citations conformes sur 16. Les textes livrés
sont à 100 %.

Le script sort en code 1 si une citation échoue, ce qui permet de le brancher en CI.

## Installation

```bash
pip install -r requirements.txt
export DEEPGRAM_API_KEY=...
```

---

Lucas Carval
