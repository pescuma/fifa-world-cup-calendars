#!/usr/bin/env python3
"""Generate FIFA World Cup .ics calendar files — all matches + per-team."""

import json
import hashlib
import re
from unittest import result

import unicodedata
import urllib.request
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from babel import Locale

from icalendar import Alarm, Calendar, Event, vText

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
YEARS = [1986, 1990, 1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022, 2026]
DATA_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/{year}/worldcup.json"
STATE_DIR = Path("state")
OUTPUT_DIR = Path("calendars")
MATCH_DURATION = timedelta(hours=2)
UID_DOMAIN = "worldcup-calendar"

# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------
LANGUAGES = {
    "en": {
        "calendar_name": "FIFA World Cup {year}",
        "calendar_desc": (
            "All matches of the FIFA World Cup {year}"
        ),
        "countries": {
            "CS": "Serbia and Montenegro",
            "ENG": "England",
            "NIR": "Northern Ireland",
            "SCT": "Scotland",
            "SU": "Soviet Union",
            "WG": "West Germany",
            "WLS": "Wales",
            "CSK": "Czechoslovakia",
            "YU": "Yugoslavia",
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
        "reminder": "Match starts in 30 minutes",
        "half_time": "Half-time",
        "full_time": "Full-time",
        "extra_time": "Extra time",
        "penalties": "Penalties",
    },
    "es": {
        "calendar_name": "Copa Mundial de la FIFA {year}",
        "calendar_desc": (
            "Todos los partidos de la Copa Mundial de la FIFA {year}"
        ),
        "countries": {
            "CS": "Serbia y Montenegro",
            "ENG": "Inglaterra",
            "NIR": "Irlanda del Norte",
            "SCT": "Escocia",
            "SU": "Unión Soviética",
            "WG": "Alemania Occidental",
            "WLS": "Gales",
            "CSK": "Checoslovaquia",
            "YU": "Yugoslavia",
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
        "reminder": "El partido comienza en 30 minutos",
        "half_time": "Descanso",
        "full_time": "Final",
        "extra_time": "Prórroga",
        "penalties": "Penaltis",
    },
    "pt": {
        "calendar_name": "Copa do Mundo FIFA {year}",
        "calendar_desc": (
            "Todas as partidas da Copa do Mundo FIFA {year}"
        ),
        "countries": {
            "CS": "Sérvia e Montenegro",
            "ENG": "Inglaterra",
            "NIR": "Irlanda do Norte",
            "NL": "Holanda",
            "SCT": "Escócia",
            "SU": "União Soviética",
            "WG": "Alemanha Ocidental",
            "WLS": "País de Gales",
            "CSK": "Tchecoslováquia",
            "YU": "Iugoslávia",
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
        "reminder": "A partida começa em 30 minutos",
        "half_time": "Intervalo",
        "full_time": "Final",
        "extra_time": "Prorrogação",
        "penalties": "Pênaltis",
    },
    "fr": {
        "calendar_name": "Coupe du Monde FIFA {year}",
        "calendar_desc": (
            "Tous les matches de la Coupe du Monde FIFA {year}"
        ),
        "countries": {
            "CS": "Serbie-et-Monténégro",
            "ENG": "Angleterre",
            "NIR": "Irlande du Nord",
            "SCT": "Écosse",
            "SU": "Union soviétique",
            "WG": "Allemagne de l'Ouest",
            "WLS": "Pays de Galles",
            "CSK": "Tchécoslovaquie",
            "YU": "Yougoslavie",
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
        "reminder": "Match commence dans 30 minutes",
        "half_time": "Mi-temps",
        "full_time": "Fin du match",
        "extra_time": "Prolongation",
        "penalties": "Tirs au but",
    },
}

COUNTRY_CODES = {
    "Afghanistan": "AF",
    "Albania": "AL",
    "Algeria": "DZ",
    "Andorra": "AD",
    "Angola": "AO",
    "Antigua and Barbuda": "AG",
    "Argentina": "AR",
    "Armenia": "AM",
    "Australia": "AU",
    "Austria": "AT",
    "Azerbaijan": "AZ",
    "Bahamas": "BS",
    "Bahrain": "BH",
    "Bangladesh": "BD",
    "Barbados": "BB",
    "Belarus": "BY",
    "Belgium": "BE",
    "Belize": "BZ",
    "Benin": "BJ",
    "Bhutan": "BT",
    "Bolivia": "BO",
    "Bosnia & Herzegovina": "BA",
    "Bosnia-Herzegovina": "BA",
    "Botswana": "BW",
    "Brazil": "BR",
    "Brunei": "BN",
    "Bulgaria": "BG",
    "Burkina Faso": "BF",
    "Burundi": "BI",
    "Cambodia": "KH",
    "Cameroon": "CM",
    "Canada": "CA",
    "Cape Verde": "CV",
    "Central African Republic": "CF",
    "Chad": "TD",
    "Chile": "CL",
    "China": "CN",
    "Colombia": "CO",
    "Comoros": "KM",
    "Congo": "CG",
    "Costa Rica": "CR",
    "Croatia": "HR",
    "Curaçao": "CW",
    "Cyprus": "CY",
    "Czech Republic": "CZ",
    "Czechoslovakia": "CSK",
    "Côte d'Ivoire": "CI",
    "DR Congo": "CD",
    "Denmark": "DK",
    "Djibouti": "DJ",
    "Dominica": "DM",
    "Dominican Republic": "DO",
    "Ecuador": "EC",
    "Egypt": "EG",
    "El Salvador": "SV",
    "England": "ENG",
    "Equatorial Guinea": "GQ",
    "Eritrea": "ER",
    "Estonia": "EE",
    "Eswatini": "SZ",
    "Ethiopia": "ET",
    "Fiji": "FJ",
    "Finland": "FI",
    "France": "FR",
    "Gabon": "GA",
    "Gambia": "GM",
    "Georgia": "GE",
    "Germany": "DE",
    "Ghana": "GH",
    "Greece": "GR",
    "Grenada": "GD",
    "Guatemala": "GT",
    "Guinea": "GN",
    "Guinea-Bissau": "GW",
    "Guyana": "GY",
    "Haiti": "HT",
    "Honduras": "HN",
    "Hungary": "HU",
    "Iceland": "IS",
    "India": "IN",
    "Indonesia": "ID",
    "Iran": "IR",
    "Iraq": "IQ",
    "Ireland": "IE",
    "Israel": "IL",
    "Italy": "IT",
    "Ivory Coast": "CI",
    "Jamaica": "JM",
    "Japan": "JP",
    "Jordan": "JO",
    "Kazakhstan": "KZ",
    "Kenya": "KE",
    "Kiribati": "KI",
    "Kosovo": "XK",
    "Kuwait": "KW",
    "Kyrgyzstan": "KG",
    "Laos": "LA",
    "Latvia": "LV",
    "Lebanon": "LB",
    "Lesotho": "LS",
    "Liberia": "LR",
    "Libya": "LY",
    "Liechtenstein": "LI",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Madagascar": "MG",
    "Malawi": "MW",
    "Malaysia": "MY",
    "Maldives": "MV",
    "Mali": "ML",
    "Malta": "MT",
    "Marshall Islands": "MH",
    "Mauritania": "MR",
    "Mauritius": "MU",
    "Mexico": "MX",
    "Micronesia": "FM",
    "Moldova": "MD",
    "Monaco": "MC",
    "Mongolia": "MN",
    "Montenegro": "ME",
    "Morocco": "MA",
    "Mozambique": "MZ",
    "Myanmar": "MM",
    "Namibia": "NA",
    "Nauru": "NR",
    "Nepal": "NP",
    "Netherlands": "NL",
    "New Zealand": "NZ",
    "Nicaragua": "NI",
    "Niger": "NE",
    "Nigeria": "NG",
    "North Korea": "KP",
    "North Macedonia": "MK",
    "Northern Ireland": "NIR",
    "Norway": "NO",
    "Oman": "OM",
    "Pakistan": "PK",
    "Palau": "PW",
    "Palestine": "PS",
    "Panama": "PA",
    "Papua New Guinea": "PG",
    "Paraguay": "PY",
    "Peru": "PE",
    "Philippines": "PH",
    "Poland": "PL",
    "Portugal": "PT",
    "Qatar": "QA",
    "Romania": "RO",
    "Russia": "RU",
    "Rwanda": "RW",
    "Saint Kitts and Nevis": "KN",
    "Saint Lucia": "LC",
    "Saint Vincent and the Grenadines": "VC",
    "Samoa": "WS",
    "San Marino": "SM",
    "Sao Tome and Principe": "ST",
    "Saudi Arabia": "SA",
    "Scotland": "SCT",
    "Senegal": "SN",
    "Serbia and Montenegro": "CS",
    "Serbia": "RS",
    "Seychelles": "SC",
    "Sierra Leone": "SL",
    "Singapore": "SG",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Solomon Islands": "SB",
    "Somalia": "SO",
    "South Africa": "ZA",
    "South Korea": "KR",
    "South Sudan": "SS",
    "Soviet Union": "SU",
    "Spain": "ES",
    "Sri Lanka": "LK",
    "Sudan": "SD",
    "Suriname": "SR",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Syria": "SY",
    "Tajikistan": "TJ",
    "Tanzania": "TZ",
    "Thailand": "TH",
    "Timor-Leste": "TL",
    "Togo": "TG",
    "Trinidad and Tobago": "TT",
    "Tunisia": "TN",
    "Turkey": "TR",
    "Turkmenistan": "TM",
    "Tuvalu": "TV",
    "USA": "US",
    "Uganda": "UG",
    "Ukraine": "UA",
    "United Arab Emirates": "AE",
    "United Kingdom": "GB",
    "United States": "US",
    "Uruguay": "UY",
    "Uzbekistan": "UZ",
    "Vanuatu": "VU",
    "Vatican City": "VA",
    "Venezuela": "VE",
    "Vietnam": "VN",
    "Wales": "WLS",
    "West Germany": "WG",
    "Yemen": "YE",
    "Yugoslavia": "YU",
    "Zambia": "ZM",
    "Zimbabwe": "ZW",
}

COUNTRY_FLAGS = {
    "AD": "🇦🇩",
    "AE": "🇦🇪",
    "AF": "🇦🇫",
    "AG": "🇦🇬",
    "AL": "🇦🇱",
    "AM": "🇦🇲",
    "AO": "🇦🇴",
    "AR": "🇦🇷",
    "AT": "🇦🇹",
    "AU": "🇦🇺",
    "AZ": "🇦🇿",
    "BA": "🇧🇦",
    "BB": "🇧🇧",
    "BD": "🇧🇩",
    "BE": "🇧🇪",
    "BF": "🇧🇫",
    "BG": "🇧🇬",
    "BH": "🇧🇭",
    "BI": "🇧🇮",
    "BJ": "🇧🇯",
    "BN": "🇧🇳",
    "BO": "🇧🇴",
    "BR": "🇧🇷",
    "BS": "🇧🇸",
    "BT": "🇧🇹",
    "BW": "🇧🇼",
    "BY": "🇧🇾",
    "BZ": "🇧🇿",
    "CA": "🇨🇦",
    "CD": "🇨🇩",
    "CF": "🇨🇫",
    "CG": "🇨🇬",
    "CH": "🇨🇭",
    "CI": "🇨🇮",
    "CL": "🇨🇱",
    "CM": "🇨🇲",
    "CN": "🇨🇳",
    "CO": "🇨🇴",
    "CR": "🇨🇷",
    "CS": "🇷🇸🇲🇪",
    "CSK": "🇨🇿🇸🇰",
    "CV": "🇨🇻",
    "CW": "🇨🇼",
    "CY": "🇨🇾",
    "CZ": "🇨🇿",
    "DE": "🇩🇪",
    "DJ": "🇩🇯",
    "DK": "🇩🇰",
    "DM": "🇩🇲",
    "DO": "🇩🇴",
    "DZ": "🇩🇿",
    "EC": "🇪🇨",
    "EE": "🇪🇪",
    "EG": "🇪🇬",
    "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "ER": "🇪🇷",
    "ES": "🇪🇸",
    "ET": "🇪🇹",
    "FI": "🇫🇮",
    "FJ": "🇫🇯",
    "FM": "🇫🇲",
    "FR": "🇫🇷",
    "GA": "🇬🇦",
    "GB": "🇬🇧",
    "GD": "🇬🇩",
    "GE": "🇬🇪",
    "GH": "🇬🇭",
    "GM": "🇬🇲",
    "GN": "🇬🇳",
    "GQ": "🇬🇶",
    "GR": "🇬🇷",
    "GT": "🇬🇹",
    "GW": "🇬🇼",
    "GY": "🇬🇾",
    "HN": "🇭🇳",
    "HR": "🇭🇷",
    "HT": "🇭🇹",
    "HU": "🇭🇺",
    "ID": "🇮🇩",
    "IE": "🇮🇪",
    "IL": "🇮🇱",
    "IN": "🇮🇳",
    "IQ": "🇮🇶",
    "IR": "🇮🇷",
    "IS": "🇮🇸",
    "IT": "🇮🇹",
    "JM": "🇯🇲",
    "JO": "🇯🇴",
    "JP": "🇯🇵",
    "KE": "🇰🇪",
    "KG": "🇰🇬",
    "KH": "🇰🇭",
    "KI": "🇰🇮",
    "KM": "🇰🇲",
    "KN": "🇰🇳",
    "KP": "🇰🇵",
    "KR": "🇰🇷",
    "KW": "🇰🇼",
    "KZ": "🇰🇿",
    "LA": "🇱🇦",
    "LB": "🇱🇧",
    "LC": "🇱🇨",
    "LI": "🇱🇮",
    "LK": "🇱🇰",
    "LR": "🇱🇷",
    "LS": "🇱🇸",
    "LT": "🇱🇹",
    "LU": "🇱🇺",
    "LV": "🇱🇻",
    "LY": "🇱🇾",
    "MA": "🇲🇦",
    "MC": "🇲🇨",
    "MD": "🇲🇩",
    "ME": "🇲🇪",
    "MG": "🇲🇬",
    "MH": "🇲🇭",
    "MK": "🇲🇰",
    "ML": "🇲🇱",
    "MM": "🇲🇲",
    "MN": "🇲🇳",
    "MR": "🇲🇷",
    "MT": "🇲🇹",
    "MU": "🇲🇺",
    "MV": "🇲🇻",
    "MW": "🇲🇼",
    "MX": "🇲🇽",
    "MY": "🇲🇾",
    "MZ": "🇲🇿",
    "NA": "🇳🇦",
    "NE": "🇳🇪",
    "NG": "🇳🇬",
    "NI": "🇳🇮",
    "NL": "🇳🇱",
    "NO": "🇳🇴",
    "NP": "🇳🇵",
    "NR": "🇳🇷",
    "NZ": "🇳🇿",
    "OM": "🇴🇲",
    "PA": "🇵🇦",
    "PE": "🇵🇪",
    "PG": "🇵🇬",
    "PH": "🇵🇭",
    "PK": "🇵🇰",
    "PL": "🇵🇱",
    "PS": "🇵🇸",
    "PT": "🇵🇹",
    "PW": "🇵🇼",
    "PY": "🇵🇾",
    "QA": "🇶🇦",
    "RO": "🇷🇴",
    "RS": "🇷🇸",
    "RU": "🇷🇺",
    "RW": "🇷🇼",
    "SA": "🇸🇦",
    "SB": "🇸🇧",
    "SC": "🇸🇨",
    "SCT": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "SD": "🇸🇩",
    "SE": "🇸🇪",
    "SG": "🇸🇬",
    "SI": "🇸🇮",
    "SK": "🇸🇰",
    "SL": "🇸🇱",
    "SM": "🇸🇲",
    "SN": "🇸🇳",
    "SO": "🇸🇴",
    "SR": "🇸🇷",
    "SS": "🇸🇸",
    "ST": "🇸🇹",
    "SU": "🇸🇺",
    "SV": "🇸🇻",
    "SY": "🇸🇾",
    "SZ": "🇸🇿",
    "TD": "🇹🇩",
    "TG": "🇹🇬",
    "TH": "🇹🇭",
    "TJ": "🇹🇯",
    "TL": "🇹🇱",
    "TM": "🇹🇲",
    "TN": "🇹🇳",
    "TR": "🇹🇷",
    "TT": "🇹🇹",
    "TV": "🇹🇻",
    "TZ": "🇹🇿",
    "UA": "🇺🇦",
    "UG": "🇺🇬",
    "US": "🇺🇸",
    "UY": "🇺🇾",
    "UZ": "🇺🇿",
    "VA": "🇻🇦",
    "VC": "🇻🇨",
    "VE": "🇻🇪",
    "VN": "🇻🇳",
    "VU": "🇻🇺",
    "WG": "🇩🇪",
    "WLS": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "WS": "🇼🇸",
    "XK": "🇽🇰",
    "YE": "🇾🇪",
    "YU": "🇷🇸🇲🇪",
    "ZA": "🇿🇦",
    "ZM": "🇿🇲",
    "ZW": "🇿🇼",
    "NIR": None,
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


def is_placeholder(name: str) -> bool:
    """Check if a team name is a placeholder like W74, L101, 1A, 2B, 3A/B/C, etc."""
    if re.match(r"^[WL]\d+$", name):
        return True
    if re.match(r"^\d[A-Z]$", name):
        return True
    if "/" in name:
        return True
    return False


def extract_teams(matches: list[dict]) -> dict[str, str]:
    """Extract real team names and return {name: slug} mapping."""
    teams = set()
    for m in matches:
        for key in ("team1", "team2"):
            t = m.get(key, "")
            if not t:
                continue
            if is_placeholder(t):
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


def parse_match_date(date_str: str) -> date:
    """Parse a match date into a UTC datetime."""
    return datetime.strptime(f"{date_str}", "%Y-%m-%d").date()


def stable_uid(year: int, match: dict) -> str:
    """Generate a stable UID for a match based on immutable properties."""
    key = "|".join(
        str(match.get(k, "")) for k in ("date", "time", "round", "ground")
    )
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return f"fifa-wc-{year}-{digest}@{UID_DOMAIN}"


def localize_phase(phase_key: str, lang: str) -> str:
    """Translate a round/phase name."""
    t = LANGUAGES[lang]["phase"]
    if phase_key.startswith("Matchday "):
        num = phase_key.split(" ", 1)[1]
        return f"{t['Matchday']} {num}"
    return t.get(phase_key, phase_key)


def localize_team(team: str, lang: str) -> str:
    """Translate a team name using its country code."""

    if is_placeholder(team):
        return team

    if team not in COUNTRY_CODES:
        print(f"[WARN] Unknown team: {team}")
        return team

    code = COUNTRY_CODES[team]

    name = LANGUAGES[lang]["countries"].get(code)
    if not name:
        locale = Locale.parse(lang)
        name = locale.territories.get(code)

    if not name:
        print(f"[WARN] Unknown translation: {code} in {lang}")
        return team

    if code not in COUNTRY_FLAGS:
        print(f"[WARN] Unknown flag: {code}")
        return name

    flag = COUNTRY_FLAGS[code]
    if flag:
        name = f"{COUNTRY_FLAGS[code]} {name}"

    return name


def format_score_summary(t, match: dict) -> str | None:
    """Extract full-time score if available."""
    score = match.get("score")
    if not score:
        return None

    l = ""
    r = ""

    ft = score.get("ft")
    if ft and len(ft) == 2:
        l = ft[0]
        r = ft[1]

    et = score.get("et")
    if et and len(et) == 2:
        l = f"{l}+{et[0]}"
        r = f"{et[1]}+{r}"

    p = score.get("p")
    if p and len(p) == 2:
        l = f"{l}[{p[0]}]"
        r = f"[{p[1]}]{r}"

    if l == "" and r == "":
        return None

    return f"{l}-{r}"


def format_score(t, match: dict) -> str | None:
    """Extract full-time score if available."""
    score = match.get("score")
    if not score:
        return None

    result = []

    ht = score.get("ht")
    if ht:
        result.append(f"{t['half_time']}: {ht[0]}-{ht[1]}")

    ft = score.get("ft")
    if ft:
        result.append(f"{t['full_time']}: {ft[0]}-{ft[1]}")

    et = score.get("et")
    if et:
        result.append(f"{t['extra_time']}: {et[0]}-{et[1]}")

    p = score.get("p")
    if p:
        result.append(f"{t['penalties']}: {p[0]}-{p[1]}")

    if len(result) == 0:
        return None

    return "\n".join(result)


def event_content_hash(
        summary: str,
        description: str,
        location: str,
        dtstart: datetime | date,
        dtend: datetime | date,
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


def create_event(year: int, match: dict, lang: str, state: dict, now: datetime) -> Event:
    """Create an icalendar Event for a single match."""
    t = LANGUAGES[lang]

    uid = stable_uid(year, match)
    if "time" in match:
        dt_start = parse_match_datetime(match["date"], match["time"])
        dt_end = dt_start + MATCH_DURATION
    else:
        dt_start = parse_match_date(match["date"])
        dt_end = dt_start + timedelta(days=1)

    team1 = match.get("team1", "TBD")
    team1 = localize_team(team1, lang)
    team2 = match.get("team2", "TBD")
    team2 = localize_team(team2, lang)
    phase_key = match.get("round", "")
    phase_localized = localize_phase(phase_key, lang)
    group = match.get("group")
    venue = match.get("ground", "TBD")
    vs = format_score_summary(t, match)
    if not vs:
        vs = t['vs']

    summary = f"{team1} {vs} {team2}"

    desc_lines = [phase_localized]
    if group:
        desc_lines.append(f"{t['group']}: {group}")
    desc_lines.append(f"{t['venue']}: {venue}")
    score = format_score(t, match)
    if score:
        desc_lines.append(score)
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
        year: int,
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
    cal.add("prodid", f"-//worldcup-calendar//FIFA WORLD CUP {year} {lang.upper()}//EN")
    cal.add("version", "2.0")
    cal.add("method", "PUBLISH")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", calendar_name or t["calendar_name"].format(year=year))
    cal.add("x-wr-caldesc", calendar_desc or t["calendar_desc"].format(year=year))
    cal.add("x-wr-timezone", "UTC")

    for match in matches:
        event = create_event(year, match, lang, state, now)
        cal.add_component(event)

    return cal


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------


def load_state(year: int) -> dict:
    """Load persistent state from disk.

    Returns a dict with keys 'all' and 'teams'.
    Migrates legacy format (flat per-language) automatically.
    """

    file = STATE_DIR / f"{year}-state.json"

    if not file.exists():
        return {"all": {}, "teams": {}}

    with open(file, "r", encoding="utf-8") as f:
        state = json.load(f)

    state.setdefault("all", {})
    state.setdefault("teams", {})
    return state


def save_state(year: int, state: dict) -> None:
    """Save persistent state to disk."""
    file = STATE_DIR / f"{year}-state.json"
    file.parent.mkdir(parents=True, exist_ok=True)

    with open(file, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    for year in YEARS:
        generate_year(year)


def generate_year(year: int) -> None:
    data_url = DATA_URL.format(year=year)

    print(f"{year}: Fetching data from {data_url} ...")
    data = fetch_data(data_url)
    matches = data.get("matches", [])
    print(f"{year}: Loaded {len(matches)} total matches.")

    teams = extract_teams(matches)
    print(f"{year}: Found {len(teams)} teams.")

    state = load_state(year)

    now = datetime.now(timezone.utc)

    year_dir = OUTPUT_DIR / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)

    # --- Generate "all matches" calendars ---
    for lang in LANGUAGES:
        print(f"Generating {lang}.ics ...")
        lang_state = state["all"].get(lang, {})
        cal = generate_calendar(year, matches, lang, lang_state, now)
        state["all"][lang] = lang_state
        with open(year_dir / f"{lang}.ics", "wb") as f:
            f.write(cal.to_ical())

    # --- Generate per-team calendars ---
    teams_dir = year_dir / "teams"
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
            team_name_localized = localize_team(team_name, lang)
            cal_name = f"{t['calendar_name'].format(year=year)} - {team_name_localized}"
            cal_desc = f"{t['calendar_desc'].format(year=year)} - {team_name_localized} matches only"

            lang_state = state["teams"].setdefault(team_slug, {}).get(lang, {})
            cal = generate_calendar(year, team_matches, lang, lang_state, now, cal_name, cal_desc)
            state["teams"].setdefault(team_slug, {})[lang] = lang_state

            with open(team_dir / f"{lang}.ics", "wb") as f:
                f.write(cal.to_ical())

    save_state(year, state)
    print(f"{year}: Done.")


if __name__ == "__main__":
    main()
