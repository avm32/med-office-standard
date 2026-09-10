# Medek Mernoki Iroda kft - Office Standard

> Generated from `standard.json` by `medstd.py docs`. Do not edit by hand -
> edit `standard.json` and regenerate.

Originator code: **MED**  ·  Project code pattern: **YYNNN**

## Container ID

```
project - originator - functional - spatial - form - discipline - number
```

Delimiter `-`, characters `A-Za-z0-9`. Status and revision are always suffixed:

```
26014-MED-ZZ-02-D-S-0104-S3-P04.pdf
```

## Folder structure (en)

```
01-Admin/
    01-Appointment/
    02-Fee_Invoicing/
    03-Programme/
    04-Correspondence/
    05-Meetings/
    06-Health_Safety/
    07-Authority/
02-Incoming/
    01-Client/
    02-Architect/
    03-Mechanical/
    04-Electrical/
    05-Geotechnical/
    06-Surveyor/
    07-Contractor/
    08-Other/
03-Site_Information/
    01-Survey/
    02-Ground_Investigation/
    03-Existing_Drawings/
    04-Photos/
04-Calculations/
    01-Loading/
    02-Foundations/
    03-Vertical_Structure/
    04-Horizontal_Structure/
    05-Stability/
    06-Connections/
05-Models/
    01-Analysis/
    02-Geometry/
    03-BIM/
    04-Exports/
06-Drawings/
    01-Working/
    02-Sketches/
07-Documents/
    01-Reports/
    02-Specifications/
    03-Schedules/
08-Outgoing/
    01-Client/
    02-Architect/
    03-Mechanical/
    04-Electrical/
    05-Contractor/
    06-Subcontractor/
    07-Authority/
    08-Other/
XX-Superseded/
```

## Folder structure (hu)

```
01-Adminisztracio/
    01-Megbizas/
    02-Dij_Szamlazas/
    03-Utemterv/
    04-Levelezes/
    05-Egyeztetesek/
    06-Munkavedelem/
    07-Hatosagi/
02-Bejovo/
    01-Megbizo/
    02-Epitesz/
    03-Gepesz/
    04-Elektromos/
    05-Geotechnika/
    06-Geodezia/
    07-Kivitelezo/
    08-Egyeb/
03-Helyszini_Adatok/
    01-Felmeres/
    02-Talajvizsgalat/
    03-Meglevo_Tervek/
    04-Fotok/
04-Szamitasok/
    01-Terhek/
    02-Alapozas/
    03-Fuggoleges_Szerkezet/
    04-Vizszintes_Szerkezet/
    05-Stabilitas/
    06-Csomopontok/
05-Modellek/
    01-Statikai_Modell/
    02-Geometria/
    03-BIM/
    04-Exportok/
06-Tervek/
    01-Munka/
    02-Vazlatok/
07-Dokumentumok/
    01-Jelentesek/
    02-Muszaki_Leiras/
    03-Kimutatasok/
08-Kimeno/
    01-Megbizo/
    02-Epitesz/
    03-Gepesz/
    04-Elektromos/
    05-Kivitelezo/
    06-Alvallalkozo/
    07-Hatosag/
    08-Egyeb/
XX-Elavult/
```

## Codes

**Form (NA.3.6)**

| Code | Meaning |
|------|---------|
| `D` | Drawing |
| `G` | Diagram |
| `I` | Image |
| `L` | List / table / schedule |
| `M` | Model |
| `T` | Textual (report, spec, note) |
| `V` | Video / audio |

**Discipline (NA.3.7)**

| Code | Meaning |
|------|---------|
| `S` | Structural engineering |
| `C` | Civil engineering |
| `A` | Architecture |
| `G` | Ground engineering |
| `M` | Mechanical engineering |
| `E` | Electrical engineering |
| `K` | Client |
| `X` | Non-discipline specific |
| `Z` | Multiple disciplines |

**Status (NA.4.2)**

| Code | Meaning |
|------|---------|
| `S0` | Work in progress |
| `S2` | Suitable for information |
| `S3` | Suitable for review and comment |
| `S4` | Suitable for review and authorization |
| `A1` | Authorized and accepted |

**Spatial breakdown - practice defaults**

| Code | Meaning |
|------|---------|
| `ZZ` | Multiple levels |
| `XX` | No level applicable |
| `B1` | Basement 1 |
| `00` | Ground floor |
| `01` | Level 1 |
| `02` | Level 2 |
| `RF` | Roof |

**Functional breakdown - practice defaults**

| Code | Meaning |
|------|---------|
| `ZZ` | Multiple subdivisions |
| `XX` | No subdivision applicable |
| `SB` | Substructure |
| `SS` | Superstructure |
| `EN` | Envelope |
| `EX` | External works |

**Drawing number series**

| Code | Meaning |
|------|---------|
| `0000` | Existing / survey |
| `1000` | Proposed general arrangements |
| `2000` | Sections and elevations |
| `3000` | Details |
| `4000` | Demolition |
| `5000` | Reinforcement |
| `6000` | Drainage |
| `7000` | External works |
| `8000` | Temporary works |
