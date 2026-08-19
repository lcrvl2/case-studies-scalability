---
name: video-testimonial-to-case-study
description: Transforme des témoignages clients en vidéo en études de cas écrites, sans déformer les mots du client. Extrait l'audio (y compris depuis un Vimeo verrouillé au domaine), transcrit avec deux modèles ASR indépendants, croise les deux pour détecter les erreurs, vérifie chaque citation mot à mot contre le transcript. Use when a company has customer testimonials on video but no written case studies, when converting an interview into a publishable case study, or when you need verbatim-safe quotes from a recording.
---

# Témoignage vidéo → étude de cas écrite

Dans la plupart des cas, une étude de cas naît d'une interview filmée. La vidéo est la matière
brute, le texte en est tiré. Beaucoup s'arrêtent à la vidéo et la version écrite ne sort jamais,
parce que l'étape est manuelle.

Ce skill automatise l'extraction et la vérification. La rédaction reste un travail d'écriture,
mais elle s'appuie sur une matière dont chaque mot est traçable.

## Règle non négociable

**Les mots du client, pas les tiens.** Un témoignage réécrit en prose marketing perd exactement
ce qui le rend crédible. On garde les formulations orales, on coupe les hésitations, on
n'améliore rien. Aucun chiffre ni fait qui ne soit pas dans le transcript. Si une information
manque, on la signale, on ne la comble pas.

## Étape 1 — Inventorier

Recenser les vidéos, leur durée, et ce qui existe déjà en version écrite. Sans avant/après, le
livrable n'a pas de mesure.

Attention aux pages où les vidéos se chargent au clic : le DOM initial n'en montre qu'une. Il
faut cliquer chaque bloc et relever la source à chaque fois. Recouper les durées avec l'API
oEmbed publique de l'hébergeur (`https://vimeo.com/api/oembed.json?url=...`).

## Étape 2 — Extraire l'audio

Si les vidéos sont sur YouTube, `yt-dlp` suffit.

Si elles sont sur Vimeo et verrouillées au domaine du site, ces routes échouent :

| Voie | Résultat |
|---|---|
| `yt-dlp` | 401 sur tous les clients (web, android, ios) |
| endpoint `/config` du player | 403 en direct, CORS depuis la page |
| pistes de sous-titres | souvent absentes (`getTextTracks()` renvoie `[]`) |

**Ce qui marche** : laisser le navigateur lire la vidéo, récupérer l'URL signée `playlist.json`
dans le log réseau, puis réassembler les segments audio.

```bash
python scripts/grab.py <slug> "<url playlist.json signée>" "https://site-du-client.com/"
```

Les URLs signées expirent en une heure environ.

## Étape 3 — Transcrire deux fois

```bash
python scripts/transcribe.py audio.m4a transcripts/client fr
```

Deux modèles, parce qu'ils se trompent différemment. `nova-2` apporte la ponctuation et la
diarisation, `whisper-large` est nettement meilleur sur les noms propres.

Si la langue n'est pas certaine, passer `auto`. Forcer la mauvaise langue renvoie un transcript
quasi vide, ce qui ressemble à une erreur technique alors que c'est un problème de paramètre.

## Étape 4 — Croiser

```bash
python scripts/compare.py transcripts/client_nova.txt transcripts/client_whisper.txt out.md
```

Là où les deux modèles écrivent la même chose, le mot est fiable. Là où ils divergent, il faut
trancher. La divergence est un détecteur d'erreurs.

Sur le corpus d'origine : 18 min 50 s d'audio, 207 divergences, 5 arbitrages réels.

Ce que ça attrape et ce que ça rate :

- **attrape** : un nom déformé par un seul modèle, une proposition entière sautée par un modèle,
  un chiffre entendu différemment
- **rate** : les deux modèles qui se trompent **pareil**. C'est fréquent sur les noms propres.

Le JSON de `nova-2` contient un score de confiance par mot. Sur un passage douteux, le mot le
plus faible est souvent exactement celui où les modèles divergent. Deux signaux indépendants qui
pointent le même endroit.

## Étape 5 — Vérifier les identités à l'extérieur

Aucun modèle n'est fiable sur les noms. Sur le corpus d'origine, trois noms étaient faux **dans
les deux transcrits à la fois** : « Steb » pour Steib, « Giverdier » pour Duverdier, « Romain »
et « Robin » pour Roman.

Vérifier chaque intervenant sur LinkedIn ou dans la presse. Sans confirmation, citer par la
fonction seule (« le directeur commercial »). Ne jamais publier un nom non vérifié.

## Étape 6 — Rédiger

Quatre à cinq sections, une par temps du récit. Titres qui disent ce qui s'est passé, pas ce
qu'on en pense.

**La technique qui fait la différence** : ne pas citer un long bloc puis le commenter. Découper
la matière du client en deux, une partie devient l'explication, l'autre reste en citation. La
liaison vient alors de lui et ne fait pas doublon avec ce qui suit.

Avant :

> Il explique que la stack est plus complète et qu'elle leur dégage du temps.
>
> « Ils ont une stack beaucoup plus complète que ce qu'on pourrait mettre en interne, ça sert à
> enrichir, identifier les bonnes entreprises, et on a dégagé du temps pour se concentrer sur
> des tâches plus stratégiques. »

Après :

> Sur la stack, il la décrit comme beaucoup plus complète que ce qu'il serait possible de mettre
> en interne. Elle sert à enrichir les données et à identifier les entreprises les plus
> pertinentes pour eux.
>
> « On a aussi dégagé du temps pour pouvoir se concentrer sur des tâches beaucoup plus
> stratégiques, à plus forte valeur ajoutée de notre côté. »

Les mots du client peuvent vivre hors des guillemets. Ce qui est interdit, c'est d'inventer un
vocabulaire de consultant pour les liaisons.

Ce qu'il ne faut pas écrire dans les commentaires :

- les généralités inventées (« l'objection classique est… », « ce que personne ne documente »)
- les phrases qui plaident (« plus solide qu'un argumentaire commercial »)
- les commentaires de structure (« il revient au point de départ »)
- les phrases qui annoncent la citation suivante : le lecteur lit tout en double

## Étape 7 — Vérifier chaque citation

```bash
python scripts/verify_quotes.py case-studies/client.md \
    transcripts/client_nova.txt transcripts/client_whisper.txt
```

**C'est l'étape qui rattrape ce que la relecture ne voit pas.** En écrivant, on corrige
machinalement la grammaire du client. « j'ai eue » pour « j'ai eu ». Aucune ne change le sens,
donc aucune ne se remarque à la relecture, et le texte n'est plus verbatim.

Sur le corpus d'origine, le premier passage donnait **6 citations conformes sur 16**.

Quand une citation échoue, deux issues seulement : soit on rétablit les mots exacts, soit on
sort la phrase des guillemets et on la passe en commentaire. Jamais corriger le client.

## Résultat sur le corpus d'origine

9 témoignages, 18 min 50 s, 4 010 mots de verbatim, 9 études de cas, 5 250 mots.
100 % des citations vérifiées mot à mot.
