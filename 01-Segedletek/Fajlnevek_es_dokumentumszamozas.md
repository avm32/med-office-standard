# Fájlnevek és dokumentumszámozás

Ez a dokumentum önmagában érthető — nem kell hozzá sem Claude, sem a kód.

---

## A fájlnév felépítése

Minden kiadott dokumentum neve hét mezőből áll, kötőjellel elválasztva, majd
kiadáskor a státusz és a revízió:

```
26030 - MED - ZZ - ZZ - T - S - 0001 - S3 - P01 . docx
  │      │     │    │    │   │     │     │     │
  │      │     │    │    │   │     │     │     └─ revízió
  │      │     │    │    │   │     │     └─────── státusz
  │      │     │    │    │   │     └───────────── sorszám (4 jegy)
  │      │     │    │    │   └─────────────────── szakág
  │      │     │    │    └─────────────────────── forma
  │      │     │    └──────────────────────────── térbeli bontás
  │      │     └───────────────────────────────── funkcionális bontás
  │      └─────────────────────────────────────── készítő
  └────────────────────────────────────────────── munkaszám
```

**Három szabály, amit soha nem szegünk meg:**

1. A kötőjel az elválasztó — ezért **kötőjel egyetlen mezőben sem szerepelhet**.
2. Csak betű és szám. Nincs szóköz, nincs ékezet, nincs aláhúzás a mezőkben.
3. **A mezők száma állandó.** Ha egy mező nem értelmezhető, `ZZ` vagy `XX`
   kerül bele — soha nem hagyjuk ki. Egy hatmezős és egy hétmezős név egy
   listában nem rendezhető és nem értelmezhető együtt.

---

## A mezők

### 1. Munkaszám — `26030`

`ÉÉNNN`: kétjegyű év + háromjegyű sorszám. A `26030` a 2026-os év 30. munkája.
A projekt indulásakor rögzítjük, és soha nem változik.

### 2. Készítő — `MED`

Mindig `MED`. Ha más iroda ad ki dokumentumot ugyanabban a projektben, ő a saját
kódját használja.

### 3. Funkcionális bontás — `ZZ`

Melyik funkcionális részegységre vonatkozik.

| Kód | Jelentés |
|---|---|
| `ZZ` | több részegység / az egész épület |
| `XX` | nem értelmezhető |
| `SB` | alapozás (substructure) |
| `SS` | felépítmény |
| `EN` | burkolat, homlokzat |
| `EX` | külső munkák |

### 4. Térbeli bontás — `ZZ`

Melyik szintre vagy helyre vonatkozik.

| Kód | Jelentés |
|---|---|
| `ZZ` | több szint |
| `XX` | nem értelmezhető |
| `B1` | pince 1 |
| `00` | földszint |
| `01`, `02` … | 1., 2. emelet |
| `RF` | tető |

### 5. Forma — `T`

**Milyen formájú az információ** — nem a tartalma, hanem a formája.

| Kód | Jelentés |
|---|---|
| `D` | rajz (drawing) |
| `M` | modell |
| `T` | szöveges dokumentum — műleírás, jelentés, számítás |
| `L` | lista, táblázat, kimutatás |
| `G` | diagram, ábra |
| `I` | kép |
| `V` | videó, hang |

### 6. Szakág — `S`

| Kód | Szakág |
|---|---|
| `S` | tartószerkezet |
| `A` | építészet |
| `C` | mélyépítés |
| `G` | geotechnika |
| `M` | gépészet |
| `E` | elektromos |
| `K` | megbízó |
| `X` | nem szakági |
| `Z` | több szakág |

### 7. Sorszám — `0001`

Négy számjegy, vezető nullákkal. Rajzoknál a sorozat számít:

| Sorozat | Tartalom |
|---|---|
| `0000–` | meglévő állapot, felmérés |
| `1000–` | tervezett alaprajzok |
| `2000–` | metszetek, homlokzatok |
| `3000–` | részletek |
| `4000–` | bontás |
| `5000–` | vasalás |
| `6000–` | vízelvezetés |
| `7000–` | külső munkák |
| `8000–` | ideiglenes szerkezetek |

**A szintek tízesével lépnek**, hogy a földszint mindig `..00`-ra végződjön:

```
1090   alaplemez kiosztás
1100   földszinti alaprajz
1110   1. emeleti alaprajz
1120   2. emeleti alaprajz
3100   földszinti metszetek és részletek
```

---

## Státusz és revízió

Ezek **nem a dokumentum része** — a kiadás állapotát írják le. Ezért kerülnek a
név végére, és ezért változnak minden kiadáskor.

### Státusz

| Kód | Jelentés | Szerződéses? |
|---|---|---|
| `S0` | munkapéldány, nem adjuk ki | nem |
| `S2` | tájékoztatásra | **nem** |
| `S3` | véleményezésre | **nem** |
| `S4` | jóváhagyásra | **nem** |
| `A1`, `A2` … | jóváhagyva, elfogadva | **igen** |

> **Ez a legfontosabb megkülönböztetés az egész rendszerben.** Az `S` kódok
> kifejezetten **nem szerződéses** kiadások. Csak az `A` kód jelenti azt, hogy a
> dokumentumot jóváhagyták. `S2`-n kiadni valamit és jóváhagyottként kezelni a
> leggyakoribb és legdrágább félreértés.

### Revízió

| Helyzet | Alak | Példa |
|---|---|---|
| első verzió | `P01.01` | |
| munka közben | `P##.##` | `P02.05` |
| kiadott, előzetes | `P##` | `P03` |
| szerződéses | `C##` | `C01` |

Munka közben a második számot léptetjük (`P01.01` → `P01.02`). Kiadáskor
elhagyjuk, és az elsőt léptetjük (`P02`). Szerződés után `C01`, `C02`…

---

## Példák

```
26030-MED-ZZ-ZZ-T-S-0001-S3-P01.docx
      statikai műleírás, egész épület, véleményezésre, 1. revízió

26030-MED-ZZ-02-D-S-1120-S4-P02.pdf
      2. emeleti alaprajz, jóváhagyásra, 2. revízió

26030-MED-SB-ZZ-D-S-5010-A1-C01.pdf
      alapozás vasalási terv, jóváhagyva, szerződéses 1. kiadás

26030-MED-ZZ-ZZ-T-S-0002-S3-P01.docx
      erőtani statikai számítás
```

---

## Hol látszik a tervfázis?

**Az azonosítóban nincs tervfázis-mező — szándékosan.** Az ISO 19650 hét mezője
azt írja le, *mi* a dokumentum, nem azt, *melyik fázisban* adjuk ki. A fázis a
kiadás tulajdonsága, nem a dokumentumé: ugyanaz a műleírás engedélyezési és
kiviteli fázisban is létezhet.

A fázis ezért két helyen látszik:

### 1. A mappa

```
07-Dokumentumok/
└── 02-Muszaki_Leiras/
    ├── 01-Engedelyezesi_terv/
    └── 02-Kiviteli_terv/
```

Ez a fő hely. A fájl a mappájában egyértelmű.

### 2. A leíró utótag

A kiadott fájl neve az azonosító után **aláhúzással** kaphat egy emberi
olvasásra szánt megnevezést:

```
26030-MED-ZZ-ZZ-T-S-0001-S3-P05_Engedelyezesi_terv_statikai_muleiras.docx
└──────── azonosító ─────────┘ └────────── megnevezés ──────────┘
```

Ez akkor számít, amikor a fájl **kikerül a mappájából** — e-mail melléklet,
letöltési mappa, pendrive. Ilyenkor a mappa már nem segít, a név viszont igen.

**Két szabály az utótagra:**

- **Aláhúzás választja el, nem kötőjel.** A kötőjel a mezőelválasztó; ha az
  utótagban is szerepelne, a nevet nem lehetne gépileg szétszedni.
- **Az utótag nem azonosító.** Nem szabad rá hivatkozni, nem szabad belőle
  következtetni. Ha eltér a mappa nevétől, a mappa és az azonosító a mérvadó.

> Régebbi BS 1192 gyakorlat ugyanezt engedte meg (`..._Doors`). Az ISO 19650
> nemzeti melléklete kimondja, hogy az azonosító *nem* tartalmaz megnevezést —
> és azt is, hogy a projekt információs szabványa írja le, milyen kiegészítő
> adat kerül a névbe a CDE-ből való kivitelkor. Ez itt pontosan az.

---

## Mappaszerkezet

```
26030-Hamvas_utca_6/
├── 01-Adminisztracio/     megbízás, díj, ütemterv, levelezés, egyeztetések
├── 02-Bejovo/             ami mástól érkezik — fél szerint almappákban
├── 03-Helyszini_Adatok/   felmérés, talajvizsgálat, meglévő tervek, fotók
├── 04-Szamitasok/         számítások, téma szerint (nem tervfázis szerint!)
├── 05-Modellek/           statikai modell, geometria, BIM
├── 06-Tervek/             élő rajzfájlok, vázlatok
├── 07-Dokumentumok/       jelentések, műszaki leírások, kimutatások
├── 08-Kimeno/             kiadott példányok — fél szerint, azon belül dátummal
├── XX-Elavult/            leváltott anyagok, dátum + ok szerint
└── 00-Notes/              → a jegyzetek az Obsidian vaultban (link)
```

**A `02-Bejovo` és a `08-Kimeno` azonos számozású**: a `02` mindkét irányban az
építész. Így a szám önmagában egyértelmű.

Két dolog, ami nem nyilvánvaló:

- **A számítások téma szerint állnak, nem tervfázis szerint.** Egy alapozási
  számítás végigkíséri a koncepciótól a kiviteli tervig — egy helyen marad, a
  revízió lép. A fázis lezárásakor a kiadott csomag a `08-Kimeno` alá fagy be.
- **A `08-Kimeno` dátumozott mappái a kiadási napló.** Ami egyszer kiment, azt
  nem szerkesztjük. Javítás = új kiadás.

---

## Amit soha nem csinálunk

- **Nem nevezünk át visszamenőleg** már kiadott fájlt. A címzettnél az a név van.
  A konvenció a következő kiadástól él.
- **Nem törlünk.** Ami leváltódik, az `XX-Elavult/ÉÉHHNN-Ok/` alá kerül, az
  eredeti nevén.
- **Nem írjuk felül a `08-Kimeno` dátumozott mappáinak tartalmát.**
- **Nem gépelünk fejezetszámot** a Word címsor szövegébe — a számozás automatikus.
