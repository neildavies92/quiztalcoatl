# V-001 evidence register — research draft

Prepared by Codex on 2026-10-26. **No human verification or editorial approval has been recorded.**
This register supports inspection of exact draft facts and assets; it does not establish publication readiness.
M2b preparation is merged in [PR #4](https://github.com/neildavies92/quiztalcoatl/pull/4), while
editorial acceptance continues separately in M2c. The production snapshot remains draft; merged
code, source research and green CI are not human approval. Record genuine decisions in
[the M2c decision register](V-001-decisions.md) after following [the UAT steps](V-001-review.md).

## Editorial seed and scope

The connected [Quiz Channel MVP workbook](https://docs.google.com/spreadsheets/d/1cnquAHbJ2t3BEBOKgMBSNpmllpyiSSH3_ghrU-__460/edit)
was read on 2026-10-26: `Countries!A1:L25`, `Videos!A1:T4`,
`'Bespoke Questions'!A1:T5`, `Learnings!A1:L8` and `Learnings!A9:L25`.
All 20 seeded country IDs are retained; their source rows were marked Needs verification.
The workbook was not modified and is not factual evidence. Prototype SVG references and bespoke
questions were not copied as approved production data.

`data/countries.json` contains 20 sourced research records. `recipes/V-001.json` explicitly selects
19 candidates for 15 questions. Portugal is retained for review but **excluded** from the recipe
and flag eligibility because its particular source artwork carries an unresolved colour warning.
The other 19 candidates are proposed editorially easy, familiar flags; human difficulty review is pending.
All countries have capital and outline eligibility disabled for this flag-only pilot; no ambiguity is
silently resolved by the software. No outline asset is required.

The UN Statistics Division country profiles below supply country identity, capital and geographic
subregion. Continents are editorial groupings: Mexico is in North America with the UN subregion
Central America, Canada uses Northern America, and France is grouped with metropolitan Europe
rather than attempting an ontology of overseas territories. South Korea is the familiar display
name for the Republic of Korea. These labels are reviewable editorial choices.

## Exact proposed reveal text and sources

Each short sentence is drafted for approximately seven seconds; spoken pace and legibility need
human UAT. Status for every identity, capital, flag and learning-fact record remains
`needs_verification`, with no `verified_by` or `verified_on` invented. Sources were researched,
not treated as automatic approval. All accessed-on dates denote research access, not review dates.

### `france` — France

- Geography/capital: Europe / Western Europe; Paris. [UN profile](https://data.un.org/legacy/en/iso/fr.html).
- Proposed explanation: **The flag's blue-white-red order was fixed by decree in February 1794.**
- Explanation evidence: [La petite histoire du drapeau tricolore — French Government](https://www.info.gouv.fr/actualite/la-petite-histoire-du-drapeau-tricolore).
- Artwork: [`assets/flags/france.png`](../../assets/flags/france.png); 1920×1280 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_France.svg&oldid=1291253550).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Avoid colour-origin myth: this government account says the royal-white/Paris-colours explanation is a later legend, while Élysée presents the traditional account. Selected decree/history fact avoids disagreement. Overall ratio should be confirmed from source asset's original dimensions.

### `japan` — Japan

- Geography/capital: Asia / Eastern Asia; Tokyo. [UN profile](https://data.un.org/legacy/en/iso/jp.html).
- Proposed explanation: **The red sun's diameter is three-fifths of the flag's height.**
- Explanation evidence: [National Flag and Anthem — Government of Japan](https://www.japan.go.jp/japan/flagandanthem/index.html).
- Artwork: [`assets/flags/japan.png`](../../assets/flags/japan.png); 1920×1280 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Japan.svg&oldid=1276144940).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Official source calls the disc the rising sun and gives its diameter and 2:3 height/width ratio. Distinguish national Hinomaru from naval rising-sun ensign.

### `canada` — Canada

- Geography/capital: North America / Northern America; Ottawa. [UN profile](https://data.un.org/legacy/en/iso/ca.html).
- Proposed explanation: **The maple leaf has 11 points, reduced from 13 to stay clear at a distance.**
- Explanation evidence: [Description of the National Flag of Canada — Canadian Heritage](https://www.canada.ca/en/canadian-heritage/services/flag-canada-description.html).
- Artwork: [`assets/flags/canada.png`](../../assets/flags/canada.png); 1920×960 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Canada.svg&oldid=1254032112).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Source explicitly says flag and maple leaf are protected symbols under Trademarks Act; review source artwork terms and usage restrictions, not just copyright/public-domain label.

### `brazil` — Brazil

- Geography/capital: South America / South America; Brasília. [UN profile](https://data.un.org/legacy/en/iso/br.html).
- Proposed explanation: **Its 27 stars represent Brazil's 26 states and Federal District.**
- Explanation evidence: [As constelações da bandeira — Agência Espacial Brasileira](https://www.gov.br/aeb/pt-br/centrais-de-conteudo/publicacoes/instagram-do-periodo-de-defeso-eleitoral-2022/semana-espacial-100-anos-de-independencia-as-constelacoes-da-bandeira/).
- Explanation evidence: [Additional official support — Brazil](https://educa.ibge.gov.br/jovens/conheca-o-brasil/territorio/19637-divisao-territorial.html).
- Artwork: [`assets/flags/brazil.png`](../../assets/flags/brazil.png); 1920×1344 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Brazil.svg&oldid=1263985246).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Federal museum source states 27 stars, one for each federation unit; IBGE confirms 26 states plus Federal District. Do not use green=forest/yellow=gold as an unqualified origin claim. Law also regulates respectful use. Museum page returned 401 on direct fetch; chosen Space Agency source fetched successfully and explicitly confirms 27 stars.

### `germany` — Germany

- Geography/capital: Europe / Western Europe; Berlin. [UN profile](https://data.un.org/legacy/en/iso/de.html).
- Proposed explanation: **Black, red and gold symbolised unity and freedom during the 1848–49 revolution.**
- Explanation evidence: [The Federal Flag — German Bundestag](https://www.bundestag.de/en/parliament/symbols/flag/flag-199494).
- Artwork: [`assets/flags/germany.png`](../../assets/flags/germany.png); 1920×1152 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Germany.svg&oldid=1291253561).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Use plain federal tricolour, not restricted federal service flag with shield/eagle. Bundestag says colour origins cannot be identified with certainty, so avoid a definitive uniform-origin story.

### `italy` — Italy

- Geography/capital: Europe / Southern Europe; Rome. [UN profile](https://data.un.org/legacy/en/iso/it.html).
- Proposed explanation: **The Italian tricolour originated in Reggio Emilia in 1797.**
- Explanation evidence: [Italian Tricolour Flag — Presidency of the Italian Republic](https://www.quirinale.it/it/pagine/italian-tricolour-flag).
- Artwork: [`assets/flags/italy.png`](../../assets/flags/italy.png); 1920×1280 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Italy.svg&oldid=1291680852).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Historical 1797 Cispadane tricolour had different layout; fact claims origin, not that present vertical flag was fully adopted in that form then.

### `spain` — Spain

- Geography/capital: Europe / Southern Europe; Madrid. [UN profile](https://data.un.org/legacy/en/iso/es.html).
- Proposed explanation: **Spain's central yellow stripe is twice as wide as either red stripe.**
- Explanation evidence: [Symbols of the State — Spanish Public Administration](https://administracion.gob.es/en/espanaadmon/comoseorganizaestado/simbolosestado).
- Artwork: [`assets/flags/spain.png`](../../assets/flags/spain.png); 1920×1280 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Spain.svg&oldid=1291257240).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Official source quotes Constitution art.4.1; ratio set by flag regulations. State version with coat of arms is familiar; record exact asset chosen.

### `portugal` — Portugal — EXCLUDED

- Geography/capital: Europe / Southern Europe; Lisbon. [UN profile](https://data.un.org/legacy/en/iso/pt.html).
- Proposed explanation: **The golden armillary sphere depicts a historic navigation instrument.**
- Explanation evidence: [National flag drawing instructions — archived Portuguese Presidency](https://jorgesampaio.arquivo.presidencia.pt/pt/republica/simbolos/bandeiras/index.html).
- Explanation evidence: [Additional official support — Portugal](https://www.presidencia.pt/en-en/president-of-the-republic/the-presidency/national-symbols/).
- Artwork: [`assets/flags/portugal.png`](../../assets/flags/portugal.png); 1920×1280 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Portugal.svg&oldid=1254134722).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Official drawing instructions say green occupies two-fifths, red three-fifths, height is two-thirds of length; sphere described as stylised navigation instrument. Excluded from the candidate pool pending source artwork colour review.

### `ireland` — Ireland

- Geography/capital: Europe / Northern Europe; Dublin. [UN profile](https://data.un.org/legacy/en/iso/ie.html).
- Proposed explanation: **Its green, white and orange express hope of unity between Ireland's different traditions.**
- Explanation evidence: [The National Flag — Irish Defence Forces](https://www.military.ie/en/public-information/defence-forces-museums/defence-forces-history/the-national-flag/).
- Artwork: [`assets/flags/ireland.png`](../../assets/flags/ireland.png); 1920×960 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Ireland.svg&oldid=1291254861).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Official source describes inclusion/aspiration for unity and quotes white as a lasting truce. All three stripes equal; green at hoist. Department of Taoiseach source returned 403 on direct fetch, so chosen Defence Forces text is fetched and directly supports the general flag meaning.

### `sweden` — Sweden

- Geography/capital: Europe / Northern Europe; Stockholm. [UN profile](https://data.un.org/legacy/en/iso/se.html).
- Proposed explanation: **Swedish blue-and-yellow cross flags appear in a royal coat of arms from 1557.**
- Explanation evidence: [SOU 2021:74, page 114 — Swedish Parliament official inquiry](https://www.riksdagen.se/sv/dokument-och-lagar/dokument/statens-offentliga-utredningar/ett-modernt-beloningssystem-de-allmanna_h9b374/html/).
- Artwork: [`assets/flags/sweden.png`](../../assets/flags/sweden.png); 1920×1200 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Sweden.svg&oldid=1267168676).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Official inquiry says Gustav Vasa issued heraldic arms for Duke Johan in 1557; part shows two crossed blue/yellow cross flags resembling present flag. Avoid claiming precise modern flag date. Norden redirects temporarily and Riksarkivet direct fetch timed out; use Parliament inquiry.

### `norway` — Norway

- Geography/capital: Europe / Northern Europe; Oslo. [UN profile](https://data.un.org/legacy/en/iso/no.html).
- Proposed explanation: **Norway's parliament chose the red, white and blue cross design in 1821.**
- Explanation evidence: [The Norwegian flag — Stortinget](https://www.stortinget.no/no/english/About-the-Storting/the-norwegian-flag/).
- Artwork: [`assets/flags/norway.png`](../../assets/flags/norway.png); 1920×1397 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Norway.svg&oldid=1269120819).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Use the plain civil flag, without historic union mark.

### `finland` — Finland

- Geography/capital: Europe / Northern Europe; Helsinki. [UN profile](https://data.un.org/legacy/en/iso/fi.html).
- Proposed explanation: **Finland's blue-cross national flag became official in 1918, shortly after independence.**
- Explanation evidence: [The Finnish flag — ThisisFINLAND](https://finland.fi/facts-stats-and-info/the-finnish-flag/).
- Artwork: [`assets/flags/finland.png`](../../assets/flags/finland.png); 1920×1174 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Finland.svg&oldid=1254052092).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Civil national flag chosen, not the state flag bearing arms.

### `denmark` — Denmark

- Geography/capital: Europe / Northern Europe; Copenhagen. [UN profile](https://data.un.org/legacy/en/iso/dk.html).
- Proposed explanation: **Denmark's flag is called Dannebrog, meaning the cloth of the Danes.**
- Explanation evidence: [Danish national flag — Danish Ministry of Foreign Affairs](https://um.dk/estland/en/denmark-and-estonia/national-symbols/danish-national-flag).
- Artwork: [`assets/flags/denmark.png`](../../assets/flags/denmark.png); 1920×1453 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Denmark.svg&oldid=1282500602).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. The 1219 falling-from-sky story is a legend, not an established origin date. Rectangular stutflag selected.

### `poland` — Poland

- Geography/capital: Europe / Eastern Europe; Warsaw. [UN profile](https://data.un.org/legacy/en/iso/pl.html).
- Proposed explanation: **Poland's white-over-red colours come from heraldry, including its white eagle on a red shield.**
- Explanation evidence: [Poland’s Day of the Flag — Polish Ministry of Foreign Affairs](https://www.gov.pl/web/diplomacy/polands-day-of-the-flag).
- Artwork: [`assets/flags/poland.png`](../../assets/flags/poland.png); 1920×1200 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Poland.svg&oldid=842002303).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Plain civil flag selected, not the state/ensign variant bearing arms.

### `greece` — Greece

- Geography/capital: Europe / Southern Europe; Athens. [UN profile](https://data.un.org/legacy/en/iso/gr.html).
- Proposed explanation: **Greece's striped design began as a sea flag; its early land flag used a simple cross.**
- Explanation evidence: [The Flag — Presidency of the Hellenic Republic](https://www.presidency.gr/en/presidency/the-flag/).
- Artwork: [`assets/flags/greece.png`](../../assets/flags/greece.png); 1920×1280 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Greece.svg&oldid=1258159256).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Avoid unqualified historical claims about nine stripes representing motto syllables; selected fact uses documented flag types.

### `india` — India

- Geography/capital: Asia / Southern Asia; New Delhi. [UN profile](https://data.un.org/legacy/en/iso/in.html).
- Proposed explanation: **India's navy-blue Ashoka Chakra has 24 spokes, inspired by the wheel on Ashoka's lion capital.**
- Explanation evidence: [Nation Brief — High Commission of India, Mbabane](https://www.hcimbabane.gov.in/page/nation-brief/).
- Artwork: [`assets/flags/india.png`](../../assets/flags/india.png); 1920×1280 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_India.svg&oldid=1291257205).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Use flag geometry, not unqualified spoke-by-spoke symbolism. National-symbol usage restrictions require review.

### `south-korea` — South Korea

- Geography/capital: Asia / Eastern Asia; Seoul. [UN profile](https://data.un.org/legacy/en/iso/kr.html).
- Proposed explanation: **South Korea's four black trigrams represent sky, earth, water and fire.**
- Explanation evidence: [The National Flag — Ministry of the Interior and Safety, Republic of Korea](https://www.mois.go.kr/eng/sub/a03/nationalSymbol/screen.do).
- Artwork: [`assets/flags/south-korea.png`](../../assets/flags/south-korea.png); 1920×1280 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_South_Korea.svg&oldid=1271357108).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Display name South Korea corresponds to Republic of Korea; distinguish from Democratic People’s Republic of Korea.

### `mexico` — Mexico

- Geography/capital: North America / Central America; Mexico City. [UN profile](https://data.un.org/legacy/en/iso/mx.html).
- Proposed explanation: **Mexico's eagle, cactus and snake recall the traditional story of Tenochtitlan's founding.**
- Explanation evidence: [Nuestros símbolos patrios — Archivo General de la Nación](https://archivos.gob.mx/transparencia/pdf/SimbolosPatrios.pdf).
- Artwork: [`assets/flags/mexico.png`](../../assets/flags/mexico.png); 1920×1098 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Mexico.svg&oldid=1291254298).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Claim is explicitly about a traditional story, not archaeological proof. Review national-symbol use and obverse orientation.

### `argentina` — Argentina

- Geography/capital: South America / South America; Buenos Aires. [UN profile](https://data.un.org/legacy/en/iso/ar.html).
- Proposed explanation: **The sun on Argentina's flag has 32 rays, alternating straight and wavy.**
- Explanation evidence: [Bandera Nacional — Government of Argentina](https://www.argentina.gob.ar/pais/simbolos/bandera).
- Artwork: [`assets/flags/argentina.png`](../../assets/flags/argentina.png); 1920×1200 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_Argentina.svg&oldid=1274988508).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. Sun-bearing official national flag selected; avoid sky-colour origin myths.

### `south-africa` — South Africa

- Geography/capital: Africa / Southern Africa; Pretoria (administrative), Cape Town (legislative), Bloemfontein (judicial). [UN profile](https://data.un.org/legacy/en/iso/za.html).
- Proposed explanation: **South Africa's Y-shape is interpreted as diverse elements of society converging in unity.**
- Explanation evidence: [National flag — South African Government](https://www.gov.za/about-sa/national-flag-1).
- Capital-role evidence: [South African Government provinces overview](https://www.gov.za/about-sa/south-africas-provinces). Bloemfontein is the conventional judicial capital and seat of the Supreme Court of Appeal; the Constitutional Court is in Johannesburg.
- Artwork: [`assets/flags/south-africa.png`](../../assets/flags/south-africa.png); 1920×1280 PNG. [Exact source-page revision](https://commons.wikimedia.org/w/index.php?title=File%3AFlag_of_South_Africa.svg&oldid=1249969430).
- Review notes: Research draft; human UAT and publication approval pending. Capital/outline quizzes disabled for this flag-only pilot. No universal meaning assigned to individual colours. Three capitals retained; Bloemfontein houses Supreme Court of Appeal, Constitutional Court is in Johannesburg.

## Automated-agent preparation review

Pillow verified all 20 PNGs; local checksum/path/dimension checks and the M2a structural gate run
without network access. A Codex visual inspection of the labelled contact sheet found no obvious
wrong association, watermark, clipping or corruption. This is preparation QA, **not human UAT**;
fine emblem details, official hues and all licensing/use questions require the checklist review.

[Contact sheet](flag-contact-sheet.png) shows every source flag with proportions preserved and
Portugal visibly marked EXCLUDED. Compare the full-size files and source originals; the preview
is not production artwork or a quiz renderer. Tests check exact committed preview/asset hashes
and per-file dimensions via the local provenance register; they cannot prove legal rights or facts.

## Open concerns

- Portugal: source file revision is categorised `Flags with invalid colors`. Resolve against
  authoritative digital specifications or replace from a traceable source, then rerun checks
  and explicitly re-enable eligibility/add the candidate ID only after review.
- Canada: the source page directs business-use requests to Canadian Heritage; human review must
  resolve the proposed monetised educational use and any required permission.
- Sweden: source warns against use in commercial marks suggesting official endorsement.
- All artwork: public-domain copyright labels coexist with insignia/national-symbol restrictions;
  see [asset licences](asset-licences.md). No claim of unrestricted commercial use is made.
- France: official colour-origin accounts disagree; the selected 1794 order/decree fact avoids the
  royal-white/Paris-colours origin story. Germany's colour origins are uncertain; selected fact
  describes documented 1848–49 symbolism. South Africa uses qualified design interpretation,
  not invented universal meanings for each colour. Denmark's 1219 story is explicitly a legend,
  and is not the selected fact. Greece avoids unqualified motto-syllable origin claims.
- The proposed 355-second recipe and placeholder *identifier* `geography-pilot` need final
  timing and identifier acceptance. Accepting `geography-pilot` as a future configuration reference
  is distinct from visual-theme UAT; no theme configuration or rendering is provided.

Complete [the country-by-country review](V-001-review.md) before changing review metadata.
