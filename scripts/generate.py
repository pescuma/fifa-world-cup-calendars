#!/usr/bin/env python3
"""Generate FIFA World Cup 2026 .ics calendar files — all matches + per-team."""

import json
import hashlib
import os
import re
import unicodedata
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from icalendar import Alarm, Calendar, Event, vText

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
STATE_FILE = Path("data/state.json")
OUTPUT_DIR = Path("calendars")
MATCH_DURATION = timedelta(hours=2)
UID_DOMAIN = "worldcup-calendar"

# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------
LANGUAGES = {
    "en": {
        "calendar_name": "FIFA World Cup 2026",
        "calendar_desc": (
            "All matches of the FIFA World Cup 2026 — "
            "United States, Canada & Mexico"
        ),
        "countries": {
            "AR": "Argentina",
            "AT": "Austria",
            "AU": "Australia",
            "BA": "Bosnia & Herzegovina",
            "BE": "Belgium",
            "BR": "Brazil",
            "CA": "Canada",
            "CD": "DR Congo",
            "CH": "Switzerland",
            "CI": "Ivory Coast",
            "CO": "Colombia",
            "CV": "Cape Verde",
            "CW": "Curaçao",
            "CZ": "Czech Republic",
            "DE": "Germany",
            "DZ": "Algeria",
            "EC": "Ecuador",
            "EG": "Egypt",
            "ENG": "England",
            "ES": "Spain",
            "FR": "France",
            "GB": "United Kingdom",
            "GH": "Ghana",
            "HR": "Croatia",
            "HT": "Haiti",
            "IQ": "Iraq",
            "IR": "Iran",
            "JO": "Jordan",
            "JP": "Japan",
            "KR": "South Korea",
            "MA": "Morocco",
            "MX": "Mexico",
            "NL": "Netherlands",
            "NO": "Norway",
            "NZ": "New Zealand",
            "PA": "Panama",
            "PT": "Portugal",
            "PY": "Paraguay",
            "QA": "Qatar",
            "SA": "Saudi Arabia",
            "SCT": "Scotland",
            "SE": "Sweden",
            "SN": "Senegal",
            "TR": "Turkey",
            "US": "USA",
            "UY": "Uruguay",
            "UZ": "Uzbekistan",
            "WLS": "Wales",
            "ZA": "South Africa",
        },
        "phase": {
            "Matchday": "Matchday",
            "Round of 32": "Round of 32",
            "Round of 16": "Round of 16",
            "Quarter-final": "Quarter-final",
            "Semi-final": "Semi-final",
            "Match for third place": "Third Place Match",
            "Final": "Final",
        },
        "group": "Group",
        "venue": "Venue",
        "vs": "vs",
        "result": "Result",
        "reminder": "Match starts in 30 minutes",
    },
    "es": {
        "calendar_name": "Copa Mundial de la FIFA 2026",
        "calendar_desc": (
            "Todos los partidos de la Copa Mundial de la FIFA 2026 — "
            "Estados Unidos, Canadá y México"
        ),
        "countries": {
            "AR": "Argentina",
            "AT": "Austria",
            "AU": "Australia",
            "BA": "Bosnia y Herzegovina",
            "BE": "Bélgica",
            "BR": "Brasil",
            "CA": "Canadá",
            "CD": "RD Congo",
            "CH": "Suiza",
            "CI": "Costa de Marfil",
            "CO": "Colombia",
            "CV": "Cabo Verde",
            "CW": "Curazao",
            "CZ": "República Checa",
            "DE": "Alemania",
            "DZ": "Argelia",
            "EC": "Ecuador",
            "EG": "Egipto",
            "ENG": "Inglaterra",
            "ES": "España",
            "FR": "Francia",
            "GB": "Reino Unido",
            "GH": "Ghana",
            "HR": "Croacia",
            "HT": "Haití",
            "IQ": "Irak",
            "IR": "Irán",
            "JO": "Jordania",
            "JP": "Japón",
            "KR": "Corea del Sur",
            "MA": "Marruecos",
            "MX": "México",
            "NL": "Países Bajos",
            "NO": "Noruega",
            "NZ": "Nueva Zelanda",
            "PA": "Panamá",
            "PT": "Portugal",
            "PY": "Paraguay",
            "QA": "Catar",
            "SA": "Arabia Saudita",
            "SCT": "Escocia",
            "SE": "Suecia",
            "SN": "Senegal",
            "TR": "Turquía",
            "US": "Estados Unidos",
            "UY": "Uruguay",
            "UZ": "Uzbekistán",
            "WLS": "Gales",
            "ZA": "Sudáfrica",
        },
        "phase": {
            "Matchday": "Jornada",
            "Round of 32": "Dieciseisavos de Final",
            "Round of 16": "Octavos de Final",
            "Quarter-final": "Cuartos de Final",
            "Semi-final": "Semifinal",
            "Match for third place": "Partido por el Tercer Lugar",
            "Final": "Final",
        },
        "group": "Grupo",
        "venue": "Estadio",
        "vs": "vs",
        "result": "Resultado",
        "reminder": "El partido comienza en 30 minutos",
    },
    "pt": {
        "calendar_name": "Copa do Mundo FIFA 2026",
        "calendar_desc": (
            "Todas as partidas da Copa do Mundo FIFA 2026 — "
            "Estados Unidos, Canadá e México"
        ),
        "countries": {
            "AR": "Argentina",
            "AT": "Áustria",
            "AU": "Austrália",
            "BA": "Bósnia e Herzegovina",
            "BE": "Bélgica",
            "BR": "Brasil",
            "CA": "Canadá",
            "CD": "RD Congo",
            "CH": "Suíça",
            "CI": "Costa do Marfim",
            "CO": "Colômbia",
            "CV": "Cabo Verde",
            "CW": "Curaçao",
            "CZ": "República Tcheca",
            "DE": "Alemanha",
            "DZ": "Argélia",
            "EC": "Equador",
            "EG": "Egito",
            "ENG": "Inglaterra",
            "ES": "Espanha",
            "FR": "França",
            "GB": "Reino Unido",
            "GH": "Gana",
            "HR": "Croácia",
            "HT": "Haiti",
            "IQ": "Iraque",
            "IR": "Irã",
            "JO": "Jordânia",
            "JP": "Japão",
            "KR": "Coreia do Sul",
            "MA": "Marrocos",
            "MX": "México",
            "NL": "Países Baixos",
            "NO": "Noruega",
            "NZ": "Nova Zelândia",
            "PA": "Panamá",
            "PT": "Portugal",
            "PY": "Paraguai",
            "QA": "Catar",
            "SA": "Arábia Saudita",
            "SCT": "Escócia",
            "SE": "Suécia",
            "SN": "Senegal",
            "TR": "Turquia",
            "US": "Estados Unidos",
            "UY": "Uruguai",
            "UZ": "Uzbequistão",
            "WLS": "País de Gales",
            "ZA": "África do Sul",
        },
        "phase": {
            "Matchday": "Rodada",
            "Round of 32": "Dezesseis-avos de Final",
            "Round of 16": "Oitavas de Final",
            "Quarter-final": "Quartas de Final",
            "Semi-final": "Semifinal",
            "Match for third place": "Disputa pelo Terceiro Lugar",
            "Final": "Final",
        },
        "group": "Grupo",
        "venue": "Estádio",
        "vs": "x",
        "result": "Resultado",
        "reminder": "A partida começa em 30 minutos",
    },
    "fr": {
        "calendar_name": "Coupe du Monde FIFA 2026",
        "calendar_desc": (
            "Tous les matches de la Coupe du Monde FIFA 2026 — "
            "États-Unis, Canada et Mexique"
        ),
        "countries": {
            "AR": "Argentine",
            "AT": "Autriche",
            "AU": "Australie",
            "BA": "Bosnie-Herzégovine",
            "BE": "Belgique",
            "BR": "Brésil",
            "CA": "Canada",
            "CD": "RD Congo",
            "CH": "Suisse",
            "CI": "Côte d'Ivoire",
            "CO": "Colombie",
            "CV": "Cap-Vert",
            "CW": "Curaçao",
            "CZ": "République tchèque",
            "DE": "Allemagne",
            "DZ": "Algérie",
            "EC": "Équateur",
            "EG": "Égypte",
            "ENG": "Angleterre",
            "ES": "Espagne",
            "FR": "France",
            "GB": "Royaume-Uni",
            "GH": "Ghana",
            "HR": "Croatie",
            "HT": "Haïti",
            "IQ": "Irak",
            "IR": "Iran",
            "JO": "Jordanie",
            "JP": "Japon",
            "KR": "Corée du Sud",
            "MA": "Maroc",
            "MX": "Mexique",
            "NL": "Pays-Bas",
            "NO": "Norvège",
            "NZ": "Nouvelle-Zélande",
            "PA": "Panama",
            "PT": "Portugal",
            "PY": "Paraguay",
            "QA": "Qatar",
            "SA": "Arabie saoudite",
            "SCT": "Écosse",
            "SE": "Suède",
            "SN": "Sénégal",
            "TR": "Turquie",
            "US": "États-Unis",
            "UY": "Uruguay",
            "UZ": "Ouzbékistan",
            "WLS": "Pays de Galles",
            "ZA": "Afrique du Sud",
        },
        "phase": {
            "Matchday": "Jour de match",
            "Round of 32": "1/16ème de finale",
            "Round of 16": "1/8ème de finale",
            "Quarter-final": "1/4 de finale",
            "Semi-final": "Demie Finale",
            "Match for third place": "Match pour la 3ème place",
            "Final": "Finale",
        },
        "group": "Groupe",
        "venue": "Stade",
        "vs": "vs",
        "result": "Résultat",
        "reminder": "Match commence dans 30 minutes",
    },
}

COUNTRY_CODES = {
    "Algeria": "DZ",
    "Argentina": "AR",
    "Australia": "AU",
    "Austria": "AT",
    "Belgium": "BE",
    "Bosnia & Herzegovina": "BA",
    "Brazil": "BR",
    "Canada": "CA",
    "Cape Verde": "CV",
    "Colombia": "CO",
    "Croatia": "HR",
    "Curaçao": "CW",
    "Czech Republic": "CZ",
    "DR Congo": "CD",
    "Ecuador": "EC",
    "Egypt": "EG",
    "England": "ENG",
    "France": "FR",
    "Germany": "DE",
    "Ghana": "GH",
    "Haiti": "HT",
    "Iran": "IR",
    "Iraq": "IQ",
    "Ivory Coast": "CI",
    "Japan": "JP",
    "Jordan": "JO",
    "Mexico": "MX",
    "Morocco": "MA",
    "Netherlands": "NL",
    "New Zealand": "NZ",
    "Norway": "NO",
    "Panama": "PA",
    "Paraguay": "PY",
    "Portugal": "PT",
    "Qatar": "QA",
    "Saudi Arabia": "SA",
    "Scotland": "SCT",
    "Senegal": "SN",
    "South Africa": "ZA",
    "South Korea": "KR",
    "Spain": "ES",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Tunisia": "TN",
    "Turkey": "TR",
    "USA": "US",
    "Uruguay": "UY",
    "Uzbekistan": "UZ",
    "Wales": "WLS",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fetch_data(url: str) -> dict:
    """Fetch JSON data from a URL."""
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def slugify(name: str) -> str:
    """Convert a team name to a URL-safe slug."""
    s = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("ASCII")
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[-\s]+", "-", s)
    return s


def extract_teams(matches: list[dict]) -> dict[str, str]:
    """Extract real team names and return {name: slug} mapping."""
    teams = set()
    for m in matches:
        for key in ("team1", "team2"):
            t = m.get(key, "")
            if not t:
                continue
            # Skip placeholders like W74, L101, 1A, 2B, 3A/B/C, etc.
            if re.match(r"^[WL]\d+$", t):
                continue
            if re.match(r"^\d[A-Z]$", t):
                continue
            if "/" in t:
                continue
            teams.add(t)
    return {t: slugify(t) for t in sorted(teams)}


def filter_matches_for_team(matches: list[dict], team: str) -> list[dict]:
    """Return only matches where the given team plays."""
    return [m for m in matches if m.get("team1") == team or m.get("team2") == team]


def parse_utc_offset(tz_str: str):
    """Parse strings like 'UTC-6', 'UTC+5:30' into a timezone."""
    m = re.match(r"UTC([+-])(\d+)(?::(\d+))?", tz_str)
    if not m:
        return timezone.utc
    sign = 1 if m.group(1) == "+" else -1
    hours = int(m.group(2))
    minutes = int(m.group(3)) if m.group(3) else 0
    return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))


def parse_match_datetime(date_str: str, time_str: str) -> datetime:
    """Parse a match date/time into a UTC datetime."""
    parts = time_str.split()
    time_part = parts[0]
    tz = parse_utc_offset(parts[1]) if len(parts) > 1 else timezone.utc
    dt = datetime.strptime(f"{date_str} {time_part}", "%Y-%m-%d %H:%M")
    dt = dt.replace(tzinfo=tz)
    return dt.astimezone(timezone.utc)


def stable_uid(match: dict) -> str:
    """Generate a stable UID for a match based on immutable properties."""
    key = "|".join(
        str(match.get(k, "")) for k in ("date", "time", "round", "ground")
    )
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return f"fifa-wc-2026-{digest}@{UID_DOMAIN}"


def localize_phase(phase_key: str, lang: str) -> str:
    """Translate a round/phase name."""
    t = LANGUAGES[lang]["phase"]
    if phase_key.startswith("Matchday "):
        num = phase_key.split(" ", 1)[1]
        return f"{t['Matchday']} {num}"
    return t.get(phase_key, phase_key)


def localize_team(team: str, lang: str) -> str:
    """Translate a team name using its country code."""
    if team not in COUNTRY_CODES:
        return team

    code = COUNTRY_CODES[team]
    name = LANGUAGES[lang]["countries"].get(code, team)
    flag = country_code_to_flag(code)
    return f"{flag} {name}"


def country_code_to_flag(country_code: str) -> str:
    """Convert a 2-letter country code into a Unicode flag emoji."""
    country_code = country_code.upper()

    special = {
        "SCT": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
        "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "WLS": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    }

    if country_code in special:
        return special[country_code]

    if len(country_code) != 2 or not country_code.isalpha():
        raise ValueError("Country code must be two letters")

    return ''.join(chr(ord(char) + 127397) for char in country_code)


def format_score(match: dict) -> str | None:
    """Extract full-time score if available."""
    score = match.get("score")
    if not score:
        return None
    ft = score.get("ft")
    if ft and len(ft) == 2:
        return f"{ft[0]}-{ft[1]}"
    return None


def event_content_hash(
        summary: str,
        description: str,
        location: str,
        dtstart: datetime,
        dtend: datetime,
        score: str | None,
) -> str:
    """Create a hash of event content to detect changes."""
    payload = "|".join(
        [
            summary,
            description,
            location,
            dtstart.isoformat(),
            dtend.isoformat(),
            score or "",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# ICS Generation
# ---------------------------------------------------------------------------


def create_event(match: dict, lang: str, state: dict, now: datetime) -> Event:
    """Create an icalendar Event for a single match."""
    t = LANGUAGES[lang]

    uid = stable_uid(match)
    dt_start = parse_match_datetime(match["date"], match["time"])
    dt_end = dt_start + MATCH_DURATION

    team1 = match.get("team1", "TBD")
    team1 = localize_team(team1, lang)
    team2 = match.get("team2", "TBD")
    team2 = localize_team(team2, lang)
    phase_key = match.get("round", "")
    phase_localized = localize_phase(phase_key, lang)
    group = match.get("group")
    venue = match.get("ground", "TBD")
    score = format_score(match)

    if score:
        summary = f"{team1} {score} {team2}"
    else:
        summary = f"{team1} {t['vs']} {team2}"

    desc_lines = [phase_localized]
    if group:
        desc_lines.append(f"{t['group']}: {group}")
    desc_lines.append(f"{t['venue']}: {venue}")
    if score:
        desc_lines.append(f"{t['result']}: {score}")
    description = "\n".join(desc_lines)

    content_hash = event_content_hash(
        summary, description, venue, dt_start, dt_end, score
    )

    prev = state.get(uid, {})
    if prev.get("hash") != content_hash:
        sequence = prev.get("sequence", -1) + 1
        dtstamp = now
        state[uid] = {"hash": content_hash, "sequence": sequence, "dtstamp": dtstamp.isoformat()}
    else:
        sequence = prev.get("sequence", 0)
        dtstamp = datetime.fromisoformat(prev.get("dtstamp", ""))

    event = Event()
    event.add("uid", uid)
    event.add("dtstamp", dtstamp)
    event.add("dtstart", dt_start)
    event.add("dtend", dt_end)
    event.add("summary", summary)
    event.add("description", description)
    event.add("location", vText(venue))
    event.add("sequence", sequence)
    event.add("status", "CONFIRMED")
    event.add("transp", "OPAQUE")
    event.add("categories", ["FIFA World Cup 2026", "Football"])

    alarm = Alarm()
    alarm.add("action", "DISPLAY")
    alarm.add("description", t["reminder"])
    alarm.add("trigger", timedelta(minutes=-30))
    event.add_component(alarm)

    return event


def generate_calendar(
        matches: list[dict],
        lang: str,
        state: dict,
        now: datetime,
        calendar_name: str | None = None,
        calendar_desc: str | None = None
) -> Calendar:
    """Generate a complete Calendar for a given language."""
    t = LANGUAGES[lang]

    cal = Calendar()
    cal.add("prodid", f"-//worldcup-calendar//FIFA WC 2026 {lang.upper()}//EN")
    cal.add("version", "2.0")
    cal.add("method", "PUBLISH")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", calendar_name or t["calendar_name"])
    cal.add("x-wr-caldesc", calendar_desc or t["calendar_desc"])
    cal.add("x-wr-timezone", "UTC")

    for match in matches:
        event = create_event(match, lang, state, now)
        cal.add_component(event)

    return cal


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------


def load_state() -> dict:
    """Load persistent state from disk.

    Returns a dict with keys 'all' and 'teams'.
    Migrates legacy format (flat per-language) automatically.
    """
    if not STATE_FILE.exists():
        return {"all": {}, "teams": {}}

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

    # Migrate legacy format (pre-per-team)
    if "all" not in state and any(lang in state for lang in LANGUAGES):
        state = {"all": state, "teams": {}}

    state.setdefault("all", {})
    state.setdefault("teams", {})
    return state


def save_state(state: dict) -> None:
    """Save persistent state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(f"Fetching data from {DATA_URL} ...")
    data = fetch_data(DATA_URL)
    matches = data.get("matches", [])
    print(f"Loaded {len(matches)} total matches.")

    teams = extract_teams(matches)
    print(f"Found {len(teams)} teams.")

    state = load_state()

    now = datetime.now(timezone.utc)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Generate "all matches" calendars ---
    for lang in LANGUAGES:
        print(f"Generating {lang}.ics ...")
        lang_state = state["all"].get(lang, {})
        cal = generate_calendar(matches, lang, lang_state, now)
        state["all"][lang] = lang_state
        with open(OUTPUT_DIR / f"{lang}.ics", "wb") as f:
            f.write(cal.to_ical())

    # --- Generate per-team calendars ---
    teams_dir = OUTPUT_DIR / "teams"
    teams_dir.mkdir(parents=True, exist_ok=True)

    # Clean up old team directories to prevent stale files
    existing_teams = {d.name for d in teams_dir.iterdir() if d.is_dir()}
    current_slugs = set(teams.values())
    for stale in existing_teams - current_slugs:
        import shutil
        shutil.rmtree(teams_dir / stale)
        print(f"  Removed stale directory: {stale}")

    for team_name, team_slug in teams.items():
        team_matches = filter_matches_for_team(matches, team_name)
        if not team_matches:
            continue

        team_dir = teams_dir / team_slug
        team_dir.mkdir(parents=True, exist_ok=True)

        for lang in LANGUAGES:
            t = LANGUAGES[lang]
            cal_name = f"{team_name} — {t['calendar_name']}"
            cal_desc = f"{t['calendar_desc']} — {team_name} matches only"

            lang_state = state["teams"].setdefault(team_slug, {}).get(lang, {})
            cal = generate_calendar(team_matches, lang, lang_state, now, cal_name, cal_desc)
            state["teams"].setdefault(team_slug, {})[lang] = lang_state

            with open(team_dir / f"{lang}.ics", "wb") as f:
                f.write(cal.to_ical())

    save_state(state)
    print("Done.")


if __name__ == "__main__":
    main()
