# Irodai dokumentumrend — mi ez a mappa?

**Ez a mappa tartja a Medek Mérnöki Iroda Kft. dokumentumrendjét:** hogyan
nevezünk el fájlokat, hogyan épül fel egy projektmappa, és milyen Word
sablonokkal dolgozunk.

Két különböző módon lehet ide belépni, és érdemes tudni, melyikben vagy:

| | |
|---|---|
| **Használat** — sablont nyitok, elolvasom a leírásokat, új projektet indítok | `01-Segedletek/`, `02-Sablonok/`, `03-Eszkozok/` |
| **Karbantartás** — magát a dokumentumrendet módosítom | `_tool/`, és általában Claude-dal együtt |

A kettő szándékosan van szétválasztva. A `_tool/` mappa nem titkos és nem
tiltott — csak nem oda kell nyúlni ahhoz, hogy valaki *használja* a rendszert.

---

## 01-Segedletek — ezt olvasd

| Fájl | Mi van benne |
|---|---|
| `Fajlnevek_es_dokumentumszamozas.md` | **A fájlnév-konvenció.** Mit jelent a `26030-MED-ZZ-ZZ-T-S-0001-S3-P01` és hogyan képezd. |
| `Mappaszerkezet.md` | A projektmappa felépítése, magyarul és angolul. |
| `Word_sablonok.md` | Milyen stílusok vannak, mit mire használj, mire figyelj. |
| `Projekt_migracio.md` | Hogyan viszel át egy már elindult projektet erre a rendre. |

## 02-Sablonok — ezt nyisd meg

A kész `.dotx` sablonok. Dupla kattintás **új dokumentumot** hoz létre belőlük;
magát a sablont nem írja felül.

- `MED-Statikai_muleiras.dotx` — engedélyezési terv statikai műleírás
- `MED-Stiluskatalogus.docx` — stíluskatalógus: minden stílus egy lapon,
  ellenőrzéshez

## 03-Eszkozok — ezt futtasd

Dupla kattintható indítók. Megkérdezik, amit kell, és elvégzik a munkát.

- `Uj_projekt.bat` — új projektmappa létrehozása a dokumentumrend szerint
- `Uj_muleiras.bat` — új műleírás indítása egy meglévő projektben
- `Sablonok_ujraepitese.bat` — a sablonok újraépítése, ha a dokumentumrend változott

---

## `_tool/` — a gépezet

Itt lakik a Python kód, a stílusmester (`master/`, nyers XML), és a git
előzmény. **Ide akkor nyúlj, ha magát a dokumentumrendet akarod módosítani** — és
akkor is inkább Claude-dal együtt, mert a `master/` egy Word-csomag szétszedett
XML-je, amit kézzel szerkeszteni könnyű elrontani.

Amit **nem** érdemes csinálni:

- `master/` fájljait kézzel átírni — helyette: módosítsd a sablont Wordben, és
  futtasd a `medtpl.py unpack` parancsot, ami visszaolvassa
- a `.git` mappát törölni vagy mozgatni
- a `build/` mappa tartalmát szerkeszteni — az kimenet, minden újraépítéskor
  felülíródik

Amit nyugodtan lehet: bármit elolvasni, bárhova belenézni, bármit lemásolni.

---

## Ha valami elromlik

A teljes dokumentumrend verziókövetett és fel van töltve ide:
`github.com/avm32/med-office-standard` (privát). Bármelyik korábbi állapot
visszaállítható, tehát nincs olyan hiba, amit ne lehetne visszacsinálni.
