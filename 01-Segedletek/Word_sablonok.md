# MED Word sablon — referencia

> Generálva: `medtpl docs`, 2026-09-14. Minden érték a `templates/master/word/styles.xml`
> fájlból olvasva — **nem újraépítve, nem becsülve.** Kézzel ne szerkeszd:
> módosítsd a mastert, és futtasd újra.

## Oldalbeállítás

| | |
|---|---|
| Lapméret | A4 |
| Margók | fent 2.5 · lent 2.5 · **bal 3.0 (fűzés)** · jobb 2.0 cm |
| Szövegtükör | 16.0 cm |
| Betűtípus | Arial |
| Nyelv | hu-HU |

A bal oldali fűzőmargó szándékos: a magyar engedélyezési dokumentációt bal
oldalon lefűzve adják be. A WG sablon 5,5 cm-es *jobb* margója az ő
oldalsávjuk — azt nem vettük át.

## Bekezdésstílusok

| Stílus | styleId | Alapja | Következő | Térköz |
|---|---|---|---|---|
| 10 - Alap | `10-Alap` | Normal | — | — |
| 11 - Szöveg | `11-Szoveg` | 10-Alap | — | line 260 atLeast, before 100, after 0 |
| 12 - Infoszöveg | `12-Infoszoveg` | 10-Alap | 11-Szoveg | line 240 atLeast, before 80, after 0 |
| 13 - Megjegyzés | `13-Megjegyzes` | 12-Infoszoveg | 11-Szoveg | — |
| 14 - Ábra felirat | `14-Abra-felirat` | 10-Alap | 11-Szoveg | line 160 exact, before 0, after 0 |
| 15 - Ábra | `15-Abra` | 18-Tablazatszoveg | 14-Abra-felirat | line 240 auto, before 240, after 0 |
| 16 - Táblázatcím | `16-Tablazatcim` | 11-Szoveg | 11-Szoveg | line - -, before 40, after 40 |
| 17 - Táblázat felirat | `17-Tablazat-felirat` | 14-Abra-felirat | 11-Szoveg | — |
| 18 - Táblázatszöveg | `18-Tablazatszoveg` | 11-Szoveg | — | line - -, before 0, after 0 |
| 21 - Címsor 1 | `21-Cimsor1` | 10-Alap | 11-Szoveg | line 400 exact, before 0, after 240 |
| 22 - Címsor 2 | `22-Cimsor2` | 10-Alap | 11-Szoveg | line 320 exact, before 360, after 120 |
| 23 - Címsor 3 szám nélkül | `23-Cimsor3-szam-nelkul` | 10-Alap | 11-Szoveg | line - -, before 240, after 80 |
| 24 - Címsor 3 számozott | `24-Cimsor3-szamozott` | 23-Cimsor3-szam-nelkul | 11-Szoveg | — |
| 27 - Melléklet | `27-Melleklet` | 50-Szamozatlan-cimsor | 11-Szoveg | line - -, before 0, after 200 |
| 28 - Melléklet alcím | `28-Melleklet-alcim` | 22-Cimsor2 | 11-Szoveg | line 280 atLeast, before 240, after 120 |
| 31 - Felsorolás pont | `31-Felsorolas-pont` | 10-Alap | — | line 260 atLeast, before 100, after 0 |
| 32 - Felsorolás gondolatjel | `32-Felsorolas-gondolatjel` | 10-Alap | — | line 260 atLeast, before 100, after 0 |
| 33 - Felsorolás gondolatjel 2 | `33-Felsorolas-gondolatjel-2` | 32-Felsorolas-gondolatjel | — | line - -, before 0, after 0 |
| 34 - Felsorolás számozott | `34-Felsorolas-szamozott` | 31-Felsorolas-pont | — | — |
| 35 - Felsorolás táblázatban | `35-Felsorolas-tablazatban` | 18-Tablazatszoveg | — | line 240 atLeast, before 0, after 0 |
| 41 - Megbízó | `41-Megbizo` | 10-Alap | 42-Megbizas-neve | line 240 auto, before 0, after 0 |
| 42 - Megbízás neve | `42-Megbizas-neve` | 41-Megbizo | — | — |
| 43 - Cím | `43-Cim` | 41-Megbizo | 11-Szoveg | — |
| 45 - Dokumentum címe | `45-Dokumentum-cime` | 10-Alap | 11-Szoveg | line 240 auto, before 80, after 40 |
| 46 - Dokumentumszám | `46-Dokumentumszam` | 12-Infoszoveg | 45-Dokumentum-cime | line 240 auto, before 0, after 0 |
| 47 - Dátum | `47-Datum` | 45-Dokumentum-cime | 11-Szoveg | — |
| 48 - Aláírás | `48-Alairas` | 11-Szoveg | 11-Szoveg | line 260 atLeast, before 480, after 0 |
| 49 - Nyilatkozat | `49-Nyilatkozat` | 11-Szoveg | 49-Nyilatkozat | line 280 atLeast, before 120, after 0 |
| 50 - Számozatlan címsor | `50-Szamozatlan-cimsor` | 10-Alap | — | line - -, before 0, after 360 |
| 52 - Címlap info | `52-Cimlap-info` | 12-Infoszoveg | 41-Megbizo | — |

## Buktatók

### Kötött sorköz és a képek

A `w:lineRule="exact"` rögzíti a sormagasságot, ezért a Word **levágja** a
nála magasabb beillesztett képet. Az `atLeast` ezzel szemben megnöveli a sort —
ez a kettő közti teljes különbség. A WG referencia §5 ezt tévesen írja le
(mindkettőtől óv), és emiatt nem találták meg az olcsó megoldást.

Ebben a sablonban kötött sorköze **csak** ezeknek a stílusoknak van, ahol a
kötött sormagasság tipográfiai szándék és kép amúgy sem kerül bele:

- `21-Cimsor1`
- `22-Cimsor2`
- `14-Abra-felirat`
- `17-Tablazat-felirat`
- `Caption`
- `Heading1`
- `Heading2`

A `medtpl check` ezt a listát ellenőrzi: ha bárhol máshol megjelenik a kötött
sorköz, a build elbukik.

### Egyéb

- **Ne gépelj fejezetszámot** a címsor szövegébe. A számozást a
  `numbering.xml` visszahivatkozása adja; ha begépeled, „1 1. Bevezetés” lesz.
- **Ne tegyél képet táblázatcellába** — PDF exportnál eltűnhet. Külön
  bekezdésbe, `15 - Ábra` stílussal.
- A `15 - Ábra` után Enterrel automatikusan a feliratstílusba kerülsz.

## Tulajdonjog

A **tartalom** a tiéd (Wordben szerkeszted), a **formázás** a masteré.
Amit begépelsz, túléli az újraépítést; amit kézzel átstílozol, nem —
azt a masterben módosítsd, vagy `medtpl unpack`-kel olvasd vissza.
