# Cleanup-Roadmap

Dieses Dokument sammelt alle bisher gefundenen Aufräum-Kandidaten aus einem Audit-Durchgang
(Stand 2026-08-09) — dead code, Kommentar-/Docstring-Bloat, Datei-Duplikate und
Struktur-Themen. Nichts hiervon wurde bereits umgesetzt; das ist bewusst eine Backlog-Liste
zum späteren, gezielten Abarbeiten, kein Änderungsprotokoll.

Risiko-Tags:
- 🟢 mechanisch/risikoarm — kann ohne große Diskussion umgesetzt werden
- 🟡 Judgment-Call — vertretbar so oder so, kurz abwägen
- 🔴 invasiv — berührt dynamische Erkennung (`loader.py`), git-Historie oder rechtliche Texte; bewusste Einzelentscheidung nötig

---

## 1. Toter Code 🟢 ✅ Erledigt

Alle unten aufgeführten Punkte wurden entfernt. Jede betroffene Datei danach mit
`py_compile` + `ast.parse` geprüft (keine Syntaxfehler), zusätzlich per grep verifiziert,
dass keine der entfernten Symbole noch irgendwo referenziert wird. `graphify update .`
danach gelaufen, um den Graphen aktuell zu halten.

- ~~`utils_ui.py:103-146`~~ — `Edited_DB_Banner`, `Banner_Editor_View`: komplettes Duplikat,
  gelöscht. Die echte, aktive Implementierung liegt weiter in `utils_dev/banner_editor/`.
- ~~`utils_ui.py:173-353`~~ — `Banner_Editor_Select`, `Banner_Modal`, `Banner_Color_Input`,
  `Banner_Blur_Input`, `Save_Banner_Button`, `Reset_Banner_Button`, `Cancel_Banner_Button`:
  ebenfalls gelöscht. `banner_file_handler()` und `BANNER_FIELD_LABEL_KEYS`/
  `banner_field_label()` (lagen mitten im toten Bereich) blieben erhalten, werden weiter von
  `utils_dev/banner_editor/ui/*.py` importiert.
  - Nebeneffekt: dadurch wurden auch `import re`, `import modules.banner_creator as BC` und
    `Select`/`Modal`/`TextInput` aus dem `discord.ui`-Import in `utils_ui.py` ungenutzt —
    mit entfernt. `utils_ui.py` ist von 358 auf 305 Zeilen geschrumpft.
- ~~`utils.py:129-137`~~ — `author_check()`: gelöscht (0 Referenzen bestätigt).
- **`utils.py:140-148`** — `guild_check()`: wie empfohlen **behalten** (dokumentiertes Muster,
  nur im Template referenziert).
- ~~`AMP.py:12`~~ — ungenutzter `Literal`-Import entfernt.
- ~~Auskommentierte Code-Leichen~~ entfernt in `discordBot.py` (toter `bot_utils_steamid`-Stub
  + TODO), `AMP.py` (6 Stellen: tote Handler-Referenz, alter Modul-Importname, doppelte
  Result-Prüfung samt Debug-Prints, drei tote `logger.dev`-Kommentare), `loader.py`
  (auskommentierte `except`-Handler, abgelöst durch den generischen `except Exception`),
  `AMP_Console.py` (tote Prefix-Logik samt TODO, toter `console_events()`-Aufruf, komplett
  auskommentierte `console_events()`-Methode), `DB.py` (6 Stellen: toter
  `_InitializeDefaultData()`-Aufruf auf eine nicht mehr existierende Methode, drei nie
  aktivierte `_AddConfig(...)`-Entwürfe, ein toter `super().__setattr__` und ein
  redundanter Kommentar-Rest).

**Zwei Funde, die über reines "totes Kommentar entfernen" hinausgingen — untersucht und
behoben:**
- ~~**`AMP_Console.py` — `console_filter()` nie aufgerufen**~~ ✅ **Behoben (echter Bug,
  kein totes Feature)**. Per `git log -p -S` verifiziert: Commit `029d1f7` ("Removed console
  filtering.", 2. März 2024, Original-Autor k8thekat) hat den Aufruf ohne Begründung
  auskommentiert, die Methode selbst im selben Commit aber weiter gepflegt (fehlendes
  `return False` ergänzt) — spricht eher für "vorübergehend deaktiviert, nie reaktiviert" als
  für eine bewusste Feature-Streichung. Bis eben war das Feature nach außen voll sichtbar,
  aber komplett wirkungslos: `/server console filter` (`cogs/AMP_server_cog.py:393`)
  bestätigte Admins weiterhin erfolgreich, `REGEX.md`/`COMMANDS.md` dokumentieren es
  ausführlich mit Beispielen, und `cogs/AMP_tasks_cog.py`s
  `amp_server_console_event_messages_send()`-Loop wartete permanent auf Event-Nachrichten,
  die nur `console_filter()` hätte liefern können. Der 2-zeilige Aufruf in
  `AMP_Console.py:146` (`console_parse_loop()`) wurde wieder aktiviert. Abhängigkeiten
  verifiziert: `Console_Filtered`/`Console_Filtered_Type` sind reguläre `Servers`-Spalten
  (Default `0`/deaktiviert), `GetServerRegexPatterns()` existiert weiterhin — die Änderung
  ändert also nichts für Server, bei denen die Filterung nie aktiviert wurde, macht sie aber
  für Server mit `flag:True` erstmals wieder tatsächlich wirksam.
- ~~**`DB.py` — `ServerNicknames` nicht mitgelöscht**~~ ✅ **Geprüft: kein aktiver Bug,
  nur totes Kommentar — gelöscht.** Das komplette "Server Nicknames"-Feature (mehrere
  Spitznamen pro Server; nicht zu verwechseln mit dem weiterhin aktiven `DisplayName`/
  `/server displayname`) ist bereits vollständig aus dem Code entfernt: kein
  `create table ServerNicknames` mehr in `_InitializeDatabase()`, keine
  `AddNickname()`/`GetServerNicknames()`-Methoden mehr vorhanden, und sogar der zugehörige
  Migrationsschritt (`DB_Update.py:32`, `nicknames_unique()`) ist selbst auskommentiert und
  wird nie aufgerufen. Frische Datenbanken haben die Tabelle also gar nicht erst — nur bei
  sehr alten, durchgängig migrierten Installationen könnte physisch noch eine leere/veraltete
  Tabelle in der SQLite-Datei liegen, aber nichts liest mehr daraus. Die auskommentierte
  Zeile in `delServer()` war damit tatsächlich einfach totes Kommentar wie die anderen in
  diesem Abschnitt — entfernt.

Beide Dateien nach der Änderung mit `py_compile` geprüft, keine Fehler.

**Nicht betroffen / bereits sauber:**
- `resources/templates/cog_template.py` und `amp_template.py` sind bewusstes,
  dokumentiertes Boilerplate (von `README.md:45` und `changelog.md` referenziert), keine
  Code-Leichen.
- `@utils.role_check()` ist konsistent über ~90+ Call-Sites wiederverwendet, keine
  copy-paste-duplizierte Permission-Logik gefunden.
- Kein Cog/Modul liegt außerhalb von `loader.py`s Lade-Mustern (`cog_*.py` in `cogs/`,
  `cog_<game>.py` in `modules/<Game>/`).

---

## 2. Docstring-/Kommentar-Bloat 🟢 ✅ Erledigt

- ~~**Doppelzeilen-Formatierungsbug**~~ — mit einem AST-verankerten Skript repariert (fasst
  nur echte Docstring-Literale an, nie Laufzeit-Strings): 37 Docstrings über 7 Dateien
  gefixt (`utils.py` 17, `AMP.py` 8, `DB.py` 7, `AMP_Console.py` 2, `utils_ui.py` 1,
  `cogs/whitelist_sync_cog.py` 1, `modules/banner_creator.py` 1 — `modules/Minecraft/
  amp_minecraft.py` hatte bei genauerer Prüfung keine Vorkommen mehr, die ursprüngliche
  Zählung von "38" war um eins daneben). Komplett-Scan danach bestätigt: keine
  verbleibenden Vorkommen im ganzen Repo.
- ~~**Überlange Docstrings auf trivialen Helfern**~~ — gekürzt: `utils.py`s
  `userAddRole`/`userRemoveRole`/`delMessage`/`editMessage`/`sendMessage`/
  `whitelist_reply_handler` sowie `AMP.py`s `AMPInstance`-Klassendocstring (46 Zeilen
  Attributliste → 5 Zeilen, nur die Einträge mit echtem Erklärwert behalten) und
  `getMetrics()`. **Nebenfund dabei**: `getMetrics()`s Docstring listete die
  Rückgabereihenfolge als `Uptime, TPS, Users, Memory, CPU`, tatsächlich zurückgegeben wird
  aber `TPS, Users, CPU, Memory, Uptime` (per `cogs/AMP_server_cog.py:204`s Unpacking
  bestätigt) — beim Kürzen gleich korrigiert, echte Doku-Ungenauigkeit, nicht nur Bloat.
- ~~**Code-wiederholende Kommentare**~~ entfernt: `utils.py`s `# Bold`/`# Italic`/
  `# Underline` in `message_formatter()`, zwei (nicht drei — Nachzählung) `# Lets also
  delete the Messages in discord` in `cogs/banner_cog.py`, und zwei (nicht eine — die Zeile
  war fälschlich als `DB.py:173` notiert, tatsächlich zweimal in `AMP.py`) `# This gets all
  the dictionary values tied to AMP and makes them attributes of self.`-Kommentare direkt
  über `setattr`-Loops.

**Ausdrücklich nicht angefasst** — wertvoller, nicht-offensichtlicher Kontext, kein Bloat:
die AMP-API-Eigenheiten-Kommentare in `AMP.py` (u.a. rund um den Content-Type-Workaround
und die Bootstrap-Reihenfolge-Logik) — per Inhaltssuche nach dem Docstring-Pass bestätigt,
dass sie unverändert erhalten sind.

Alle betroffenen Dateien danach mit `py_compile` geprüft (keine Fehler), `graphify update .`
gelaufen.

---

## 3. Datei-Duplikate / veraltete Docs 🟡 ✅ Erledigt

- ~~**`LICENSE` vs. `COPYING`**~~ — inhaltsgleicher GPLv3-Text, nur unterschiedlich
  formatiert. Entscheidung: `LICENSE` behalten (GitHub-Standardkonvention), `COPYING`
  gelöscht.
- ~~**`discord-role-synced-whitelist.md`**~~ — ursprüngliches Feature-Proposal, größtenteils
  bereits umgesetzt (siehe `changelog.md` "Update 4.8.0", `WHITELIST.md`). Entscheidung:
  Datei komplett gelöscht, inklusive der einzigen nicht umgesetzten Idee ("Global Ban /
  Moderation", `/gban`) — bewusst nirgends weiter festgehalten.
- ~~**`.DS_Store`**~~ — war nicht von git getrackt, aber auch nicht in `.gitignore`
  gelistet. Ergänzt, um versehentliches Commiten künftig zu verhindern.

---

## 4. Backlog — bewusst zurückgestellt 🔴

- ~~**Copyright-Header**~~ ✅ **Erledigt**: der ~20-zeilige GPL-Header (identisch in 40
  Dateien) wurde auf einen kurzen SPDX-Header gekürzt:
  ```python
  # Copyright (C) 2021-2022 Katelynn Cadwallader
  # SPDX-License-Identifier: GPL-3.0-or-later
  ```
  Voller Lizenztext bleibt unverändert in `LICENSE`/`COPYING`. `AMP.py` hatte vorher gar
  keinen Header (nur den 3-zeiligen `# AMP API / by k8thekat // Lightning / 11/10/2021`-
  Kommentar, der erhalten blieb) — bekam den SPDX-Header der Konsistenz halber ergänzt.
  Alle 41 Dateien nach der Änderung mit `py_compile` auf Syntaxfehler geprüft, keine
  gefunden.
- ~~**docs/-Ordner-Umzug**~~ ✅ **Erledigt**: alle 10 Root-Markdown-Docs (bis auf `README.md`/
  `LICENSE`, die per GitHub-Konvention im Root bleiben) nach `docs/` verschoben. Die zuvor als
  Blocker genannten root-relativen Links (`](/WHITELIST.md)` etc.) wurden mechanisch auf
  `](/docs/WHITELIST.md)` etc. umgeschrieben — 36 Links über 8 Dateien, verifiziert per
  Repo-weitem Grep, keine verbleibenden kaputten Links (die Backtick-Beispiele hier oben
  bleiben unverändert als historische Notiz stehen).
- ~~**Namenskonventionen**~~ ✅ **Erledigt**:
  - `modules/Counter-Strike_Go` → `modules/CounterStrikeGo` umbenannt. Verifiziert vor der
    Umbenennung: `loader.py`s `module_auto_loader()`/`AMP_Handler.py`s `moduleHandler()`
    matchen Module ausschließlich über `DisplayImageSources`, nie über den Ordnernamen — der
    Name fließt nur in den `load_extension()`-Dotted-Path ein, den `importlib` auch mit
    Bindestrichen korrekt auflöst (kein `__init__.py`/Identifier-Zwang unter `modules/`).
  - `cogs/AMP_server_cog.py`/`AMP_tasks_cog.py`/`DB_server_cog.py`/`DB_user_cog.py`/
    `Permissions_cog.py` → durchgehend kleingeschrieben (PEP8-Konvention, angeglichen an
    `banner_cog.py`/`regex_cog.py`/`whitelist_cog.py`/`whitelist_sync_cog.py`). `Dependencies`-
    Listen in `whitelist_cog.py`/`whitelist_sync_cog.py`/`banner_cog.py`/`permissions_cog.py`
    sowie 3 hardcodierte `'cogs.Permissions_cog'`-Stellen in `discordBot.py` (case-sensitiv auf
    Linux, im Gegensatz zu `loader.py`s eigenem, bereits lowercase-tolerantem Abhängigkeits-
    Check) entsprechend mitgezogen. `py_compile` + Repo-weiter Grep danach sauber.
- ~~**CLAUDE.md-Umbau**~~ ✅ **Erledigt**: der Abschnitt "Production deployment log (Hetzner,
  fullsendhub.de)" (~130 Zeilen, ca. 40% der Datei) wurde 1:1 nach `DEPLOYMENT_LOG.md`
  verschoben. `CLAUDE.md` behält nur einen kurzen Verweis-Absatz mit Link. Datei schrumpft
  von 192 auf 75 Zeilen; kein Inhalt verloren, nur räumlich getrennt.
- ~~**README.md-Straffung**~~ ✅ **Erledigt**: alle Setup-Abschnitte (Requirements, Python-
  Setup, Discord-Bot-Account, Installation Methods, Interacting with the Bot, Launch Args,
  Using Gatekeeperv2 as a Service) nach `INSTALL.md` verschoben. `README.md` behält nur
  Intro, "Why use this fork?" (Unterschiede/Verbesserungen ggü. Original), Features, Credits
  und Support — schrumpft von 238 auf 67 Zeilen. Zwei interne Anker-Links in "Features", die
  auf verschobene Abschnitte zeigten (`#amp-instance-instructions`,
  `#using-gatekeeperv2-as-a-service`), auf `/INSTALL.md#...` umgebogen; keine externen
  Cross-Doc-Links auf README-Anker gefunden (nur ein plain `](/README.md)` in
  `COMMANDS.md`), also nichts sonst zu reparieren.

---

## Vorschlag für die Reihenfolge, wenn's losgeht

1. ~~Abschnitt 1~~ ✅ erledigt.
2. ~~Abschnitt 2~~ ✅ erledigt.
3. ~~Abschnitt 3~~ ✅ erledigt.
4. ~~Abschnitt 4~~ ✅ erledigt.

Zusätzlich zur ursprünglichen Roadmap: die losen Root-Python-Module wurden ebenfalls in ein
`core/`-Package verschoben (nicht Teil dieses Dokuments, da erst nachträglich angefragt — siehe
`CLAUDE.md`s Architecture-Sektion für die aktuellen Pfade).
