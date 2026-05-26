"""
CosmoLearn Backend — Python / Flask
─────────────────────────────────────────────────────────────────────────────
Stack : Flask · Flask-CORS · Flask-SocketIO · slowapi (rate-limiter) · Anthropic SDK

Routes
  GET  /api/planets            → all planet data
  GET  /api/planets/<id>       → single planet
  GET  /api/sun                → Sun data
  POST /api/ai/ask             → AI space assistant (Anthropic SDK)
  GET  /api/quiz               → random quiz questions
  POST /api/quiz/score         → submit score & get badge
  GET  /api/achievements       → all achievement definitions
  POST /api/favorites          → save favourite planet (in-memory demo)
  GET  /api/favorites/<userId> → get favourites
  GET  /api/compare            → compare two planets ?a=earth&b=mars
  GET  /api/soundtrack         → list space soundtracks
  WS   /                       → Socket.io real-time meteor events

Install:
  pip install flask flask-cors flask-socketio slowapi anthropic python-dotenv

Run:
  ANTHROPIC_API_KEY=sk-... python app.py
"""

import os
import random
import threading
import time
from datetime import datetime, timezone
from uuid import uuid4

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

load_dotenv()

# ─── Constants ────────────────────────────────────────────────────────────────
PORT = int(os.environ.get("PORT", 4000))
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ─── Planet Data ─────────────────────────────────────────────────────────────
PLANETS = [
    {
        "id": "mercury",
        "name": "Mercury",
        "color": "#b5b5b5",
        "radius_km": 2439.7,
        "mass_kg": "3.30×10²³",
        "gravity_ms2": 3.7,
        "distance_from_sun_AU": 0.39,
        "distance_from_sun_km": 57_900_000,
        "orbital_period_days": 87.97,
        "rotation_period_hours": 1407.6,
        "surface_temp_min_C": -180,
        "surface_temp_max_C": 430,
        "atmosphere": "Extremely thin (oxygen, sodium, hydrogen, helium)",
        "moons": 0,
        "has_water": False,
        "has_oxygen": False,
        "survival_chance_percent": 0,
        "habitability_score": 2,
        "texture_hint": "rocky grey cratered surface",
        "fun_facts": [
            "A year on Mercury lasts only 88 Earth days.",
            "Despite being closest to the Sun, Venus is hotter.",
            "Mercury has ice in permanently shadowed craters at its poles.",
            "Its iron core makes up about 85 % of its radius.",
        ],
        "composition": {"iron": 70, "rock": 30},
        "magnetic_field": "Yes (weak — 1 % of Earth)",
        "rings": False,
        "type": "Terrestrial",
    },
    {
        "id": "venus",
        "name": "Venus",
        "color": "#e8cda0",
        "radius_km": 6051.8,
        "mass_kg": "4.87×10²⁴",
        "gravity_ms2": 8.87,
        "distance_from_sun_AU": 0.72,
        "distance_from_sun_km": 108_200_000,
        "orbital_period_days": 224.7,
        "rotation_period_hours": 5832.5,
        "surface_temp_min_C": 437,
        "surface_temp_max_C": 482,
        "atmosphere": "Dense CO₂ with sulfuric acid clouds (96.5% CO₂)",
        "moons": 0,
        "has_water": False,
        "has_oxygen": False,
        "survival_chance_percent": 0,
        "habitability_score": 3,
        "texture_hint": "thick yellowish atmosphere swirling clouds",
        "fun_facts": [
            "Venus rotates backwards compared to most planets.",
            "A day on Venus is longer than its year.",
            "Surface pressure is 92× that of Earth's sea level.",
            "It's the hottest planet despite not being closest to the Sun.",
        ],
        "composition": {"rock": 95, "iron": 5},
        "magnetic_field": "No",
        "rings": False,
        "type": "Terrestrial",
    },
    {
        "id": "earth",
        "name": "Earth",
        "color": "#1a7fd4",
        "radius_km": 6371,
        "mass_kg": "5.97×10²⁴",
        "gravity_ms2": 9.81,
        "distance_from_sun_AU": 1.0,
        "distance_from_sun_km": 149_600_000,
        "orbital_period_days": 365.25,
        "rotation_period_hours": 23.93,
        "surface_temp_min_C": -89,
        "surface_temp_max_C": 58,
        "atmosphere": "Nitrogen (78 %), Oxygen (21 %), Argon (0.9 %)",
        "moons": 1,
        "has_water": True,
        "has_oxygen": True,
        "survival_chance_percent": 100,
        "habitability_score": 100,
        "texture_hint": "blue oceans green continents white clouds",
        "fun_facts": [
            "Earth is the only known planet harboring life.",
            "71 % of the surface is covered in water.",
            "The Moon stabilises Earth's axial tilt.",
            "Earth's inner core is solid iron, hotter than the Sun's surface.",
        ],
        "composition": {"iron": 32, "oxygen": 30, "silicon": 15, "other": 23},
        "magnetic_field": "Yes (strong)",
        "rings": False,
        "type": "Terrestrial",
    },
    {
        "id": "mars",
        "name": "Mars",
        "color": "#c1440e",
        "radius_km": 3389.5,
        "mass_kg": "6.42×10²³",
        "gravity_ms2": 3.72,
        "distance_from_sun_AU": 1.52,
        "distance_from_sun_km": 227_900_000,
        "orbital_period_days": 686.97,
        "rotation_period_hours": 24.62,
        "surface_temp_min_C": -125,
        "surface_temp_max_C": 20,
        "atmosphere": "Thin CO₂ (95 %), Nitrogen (2.6 %), Argon (1.9 %)",
        "moons": 2,
        "has_water": "Subsurface ice",
        "has_oxygen": False,
        "survival_chance_percent": 1,
        "habitability_score": 18,
        "texture_hint": "red rocky dusty surface with canyons",
        "fun_facts": [
            "Olympus Mons is the tallest volcano in the solar system.",
            "Valles Marineris is as wide as the United States.",
            "Mars has two small moons: Phobos and Deimos.",
            "A dust storm on Mars can last months and cover the whole planet.",
        ],
        "composition": {"iron_oxide": 20, "rock": 75, "other": 5},
        "magnetic_field": "No (remnant patches)",
        "rings": False,
        "type": "Terrestrial",
    },
    {
        "id": "jupiter",
        "name": "Jupiter",
        "color": "#c88b3a",
        "radius_km": 69911,
        "mass_kg": "1.90×10²⁷",
        "gravity_ms2": 24.79,
        "distance_from_sun_AU": 5.2,
        "distance_from_sun_km": 778_500_000,
        "orbital_period_days": 4332.59,
        "rotation_period_hours": 9.92,
        "surface_temp_min_C": -145,
        "surface_temp_max_C": -108,
        "atmosphere": "Hydrogen (89 %), Helium (10 %), methane, ammonia",
        "moons": 95,
        "has_water": "Possible in cloud layers",
        "has_oxygen": False,
        "survival_chance_percent": 0,
        "habitability_score": 5,
        "texture_hint": "orange brown bands great red spot gas giant",
        "fun_facts": [
            "Jupiter's Great Red Spot is a storm older than 350 years.",
            "Jupiter is 1,300× the volume of Earth.",
            "Its moon Europa may have a subsurface liquid ocean.",
            "Jupiter acts as a planetary shield deflecting asteroids.",
        ],
        "composition": {"hydrogen": 89, "helium": 10, "other": 1},
        "magnetic_field": "Yes (strongest in solar system)",
        "rings": True,
        "type": "Gas Giant",
    },
    {
        "id": "saturn",
        "name": "Saturn",
        "color": "#e4d191",
        "radius_km": 58232,
        "mass_kg": "5.68×10²⁶",
        "gravity_ms2": 10.44,
        "distance_from_sun_AU": 9.58,
        "distance_from_sun_km": 1_432_000_000,
        "orbital_period_days": 10759.22,
        "rotation_period_hours": 10.66,
        "surface_temp_min_C": -178,
        "surface_temp_max_C": -138,
        "atmosphere": "Hydrogen (96 %), Helium (3 %), trace methane",
        "moons": 146,
        "has_water": "Possibly as ice in rings",
        "has_oxygen": False,
        "survival_chance_percent": 0,
        "habitability_score": 4,
        "texture_hint": "golden planet with prominent ring system",
        "fun_facts": [
            "Saturn's rings are made of ice and rock particles.",
            "Saturn is less dense than water — it could float!",
            "Its moon Titan has a thick atmosphere and methane lakes.",
            "Saturn has the most moons of any planet (146 confirmed).",
        ],
        "composition": {"hydrogen": 96, "helium": 3, "other": 1},
        "magnetic_field": "Yes",
        "rings": True,
        "type": "Gas Giant",
    },
    {
        "id": "uranus",
        "name": "Uranus",
        "color": "#7de8e8",
        "radius_km": 25362,
        "mass_kg": "8.68×10²⁵",
        "gravity_ms2": 8.87,
        "distance_from_sun_AU": 19.22,
        "distance_from_sun_km": 2_867_000_000,
        "orbital_period_days": 30688.5,
        "rotation_period_hours": 17.24,
        "surface_temp_min_C": -224,
        "surface_temp_max_C": -197,
        "atmosphere": "Hydrogen (83 %), Helium (15 %), Methane (2 %)",
        "moons": 28,
        "has_water": "Possible icy mantle",
        "has_oxygen": False,
        "survival_chance_percent": 0,
        "habitability_score": 2,
        "texture_hint": "pale cyan ice giant smooth featureless",
        "fun_facts": [
            "Uranus rotates on its side — axial tilt of 98°.",
            "It's the coldest planetary atmosphere in the solar system.",
            "Uranus has 13 known rings.",
            "Its moons are named after Shakespeare characters.",
        ],
        "composition": {"water_ice": 65, "rock": 20, "hydrogen": 10, "helium": 5},
        "magnetic_field": "Yes (tilted 59° from axis)",
        "rings": True,
        "type": "Ice Giant",
    },
    {
        "id": "neptune",
        "name": "Neptune",
        "color": "#3f54ba",
        "radius_km": 24622,
        "mass_kg": "1.02×10²⁶",
        "gravity_ms2": 11.15,
        "distance_from_sun_AU": 30.05,
        "distance_from_sun_km": 4_495_000_000,
        "orbital_period_days": 60182,
        "rotation_period_hours": 16.11,
        "surface_temp_min_C": -218,
        "surface_temp_max_C": -200,
        "atmosphere": "Hydrogen (80 %), Helium (19 %), Methane (1 %)",
        "moons": 16,
        "has_water": "Deep icy mantle",
        "has_oxygen": False,
        "survival_chance_percent": 0,
        "habitability_score": 2,
        "texture_hint": "deep blue ice giant with dark storm spots",
        "fun_facts": [
            "Neptune has the fastest winds in the solar system (2,100 km/h).",
            "It was predicted mathematically before it was observed.",
            "Its moon Triton orbits backwards (retrograde).",
            "Neptune radiates 2.6× more heat than it receives from the Sun.",
        ],
        "composition": {"water_ice": 60, "rock": 25, "hydrogen": 10, "helium": 5},
        "magnetic_field": "Yes",
        "rings": True,
        "type": "Ice Giant",
    },
    {
        "id": "pluto",
        "name": "Pluto",
        "color": "#c5a98b",
        "radius_km": 1188.3,
        "mass_kg": "1.30×10²²",
        "gravity_ms2": 0.62,
        "distance_from_sun_AU": 39.48,
        "distance_from_sun_km": 5_906_000_000,
        "orbital_period_days": 90560,
        "rotation_period_hours": 153.3,
        "surface_temp_min_C": -240,
        "surface_temp_max_C": -218,
        "atmosphere": "Thin nitrogen, methane, carbon monoxide",
        "moons": 5,
        "has_water": "Possible subsurface ocean",
        "has_oxygen": False,
        "survival_chance_percent": 0,
        "habitability_score": 1,
        "texture_hint": "brown icy dwarf planet heart-shaped nitrogen plain",
        "fun_facts": [
            "Pluto has a heart-shaped nitrogen plain called Tombaugh Regio.",
            "Its moon Charon is half its size — they orbit each other.",
            "Pluto was reclassified as a dwarf planet in 2006.",
            "New Horizons flew by Pluto in July 2015.",
        ],
        "composition": {"rock": 70, "ice": 30},
        "magnetic_field": "Unknown",
        "rings": False,
        "type": "Dwarf Planet",
    },
]

# ─── Sun Data ─────────────────────────────────────────────────────────────────
SUN = {
    "id": "sun",
    "name": "The Sun",
    "type": "G-type main-sequence star (Yellow Dwarf)",
    "radius_km": 695_700,
    "mass_kg": "1.99×10³⁰",
    "surface_temp_K": 5778,
    "core_temp_K": 15_000_000,
    "age_billion_years": 4.6,
    "luminosity_watts": "3.83×10²⁶",
    "composition_percent": {"hydrogen": 73, "helium": 25, "other": 2},
    "distance_from_galactic_center_ly": 26000,
    "energy_output": "3.83×10²⁶ watts (3.83 yottawatts)",
    "survival_near_sun": {
        "survival_chance_percent": 0,
        "lethal_radius_km": 20_000_000,
        "note": "At 20 million km, radiation and heat would instantly vaporise any known material.",
    },
    "solar_flares": "Occur regularly; largest (X-class) can disrupt satellites and power grids on Earth.",
    "solar_wind_speed_kms": 400,
    "fun_facts": [
        "The Sun contains 99.86 % of the solar system's total mass.",
        "Light from the Sun takes 8 minutes 20 seconds to reach Earth.",
        "The Sun converts 600 million tonnes of hydrogen to helium every second.",
        "It has burned for 4.6 billion years and has ~5 billion more to go.",
        "The solar corona is hotter than the surface — a mystery not yet fully explained.",
    ],
}

# ─── Quiz Questions ────────────────────────────────────────────────────────────
QUIZ_QUESTIONS = [
    {"q": "Which planet has the most moons?", "options": ["Jupiter", "Saturn", "Uranus", "Neptune"], "answer": 1},
    {"q": "What is the hottest planet?", "options": ["Mercury", "Venus", "Mars", "Jupiter"], "answer": 1},
    {"q": "How long does sunlight take to reach Earth?", "options": ["1 min", "4 min", "8 min 20 sec", "15 min"], "answer": 2},
    {"q": "Which planet has a day longer than its year?", "options": ["Mars", "Venus", "Mercury", "Pluto"], "answer": 1},
    {"q": "What causes seasons on Earth?", "options": ["Distance from Sun", "Axial tilt", "Orbital speed", "Moon phases"], "answer": 1},
    {"q": "Which planet has the tallest volcano?", "options": ["Earth", "Venus", "Mars", "Jupiter"], "answer": 2},
    {"q": "Saturn's density compared to water?", "options": ["10× denser", "Same", "Less — it would float", "Twice"], "answer": 2},
    {"q": "Which moon might harbour life?", "options": ["Titan", "Io", "Europa", "Ganymede"], "answer": 2},
    {"q": "What is Pluto classified as?", "options": ["Planet", "Asteroid", "Dwarf Planet", "Moon"], "answer": 2},
    {"q": "Who first observed Jupiter's moons?", "options": ["Copernicus", "Kepler", "Galileo", "Newton"], "answer": 2},
    {"q": "Neptune's winds reach up to?", "options": ["500 km/h", "1200 km/h", "2100 km/h", "3000 km/h"], "answer": 2},
    {"q": "The Great Red Spot is a storm on?", "options": ["Saturn", "Jupiter", "Neptune", "Uranus"], "answer": 1},
    {"q": "Which planet rotates on its side?", "options": ["Uranus", "Neptune", "Saturn", "Mercury"], "answer": 0},
    {"q": "What % of solar system mass does the Sun hold?", "options": ["50%", "80%", "95%", "99.86%"], "answer": 3},
    {"q": "Valles Marineris is a canyon on?", "options": ["Earth", "Mars", "Venus", "Mercury"], "answer": 1},
]

# ─── Achievements ─────────────────────────────────────────────────────────────
ACHIEVEMENTS = [
    {"id": "first_click", "name": "First Contact", "desc": "Click your first planet", "icon": "🪐", "xp": 10},
    {"id": "all_planets", "name": "Solar Explorer", "desc": "Visit all 9 planets", "icon": "🚀", "xp": 100},
    {"id": "sun_mode", "name": "Icarus", "desc": "Enter Sun exploration mode", "icon": "☀️", "xp": 25},
    {"id": "quiz_pass", "name": "Cosmonaut", "desc": "Score 80%+ on the quiz", "icon": "🎓", "xp": 50},
    {"id": "quiz_perfect", "name": "Einstein", "desc": "Perfect quiz score", "icon": "🧠", "xp": 150},
    {"id": "favorites_5", "name": "Stargazer", "desc": "Save 5 favourite planets", "icon": "⭐", "xp": 30},
    {"id": "compare", "name": "Analyst", "desc": "Compare two planets", "icon": "⚖️", "xp": 20},
    {"id": "ai_3", "name": "Inquisitor", "desc": "Ask the AI 3 questions", "icon": "🤖", "xp": 20},
    {"id": "warp_speed", "name": "Warp Drive", "desc": "Trigger warp speed transition", "icon": "💫", "xp": 15},
    {"id": "night_owl", "name": "Night Owl", "desc": "Visit after midnight (local time)", "icon": "🦉", "xp": 10},
]

# ─── Soundtracks ──────────────────────────────────────────────────────────────
SOUNDTRACKS = [
    {"id": 1, "title": "Interstellar Main Theme", "artist": "Hans Zimmer", "mood": "epic", "bpm": 60},
    {"id": 2, "title": "Space Ambience", "artist": "CosmoLearn AI", "mood": "calm", "bpm": 40},
    {"id": 3, "title": "Cosmic Pulse", "artist": "CosmoLearn AI", "mood": "energetic", "bpm": 120},
    {"id": 4, "title": "Deep Space Journey", "artist": "CosmoLearn AI", "mood": "mysterious", "bpm": 55},
    {"id": 5, "title": "Nebula Dreams", "artist": "CosmoLearn AI", "mood": "dreamy", "bpm": 70},
]

# ─── In-memory stores ─────────────────────────────────────────────────────────
favorites_store = {}   # userId → set of planetIds
scores_store = []      # list of { userId, score, timestamp }

# ─── Rate limiter (simple in-memory) ─────────────────────────────────────────
rate_limit_store = {}  # ip → {"points": int, "reset_at": float}
RATE_LIMIT_POINTS = 60
RATE_LIMIT_DURATION = 60  # seconds

def check_rate_limit(ip):
    now = time.time()
    entry = rate_limit_store.get(ip)
    if not entry or now > entry["reset_at"]:
        rate_limit_store[ip] = {"points": RATE_LIMIT_POINTS - 1, "reset_at": now + RATE_LIMIT_DURATION}
        return True
    if entry["points"] > 0:
        entry["points"] -= 1
        return True
    return False

# ─── App Setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*")

# ─── Helpers ──────────────────────────────────────────────────────────────────
def ok(data, meta=None):
    payload = {"success": True, "timestamp": datetime.now(timezone.utc).isoformat()}
    if meta:
        payload.update(meta)
    payload["data"] = data
    return jsonify(payload)

def err(msg, status=400):
    return jsonify({"success": False, "error": msg}), status

# ─── Rate-limit middleware ────────────────────────────────────────────────────
@app.before_request
def rate_limiter():
    ip = request.remote_addr or "unknown"
    if not check_rate_limit(ip):
        return jsonify({"error": "Too many requests"}), 429

# ─── Routes ───────────────────────────────────────────────────────────────────

# Health check
@app.get("/api/health")
def health():
    return ok({"status": "ok", "service": "CosmoLearn API v1.0"})

# All planets
@app.get("/api/planets")
def get_planets():
    return ok(PLANETS, {"count": len(PLANETS)})

# Single planet
@app.get("/api/planets/<planet_id>")
def get_planet(planet_id):
    planet = next((p for p in PLANETS if p["id"] == planet_id.lower()), None)
    if not planet:
        return err("Planet not found", 404)
    return ok(planet)

# Sun
@app.get("/api/sun")
def get_sun():
    return ok(SUN)

# Compare two planets
@app.get("/api/compare")
def compare_planets():
    a = request.args.get("a")
    b = request.args.get("b")
    if not a or not b:
        return err("Provide ?a=<planet>&b=<planet>")
    p_a = next((p for p in PLANETS if p["id"] == a.lower()), None)
    p_b = next((p for p in PLANETS if p["id"] == b.lower()), None)
    if not p_a:
        return err(f"Planet '{a}' not found")
    if not p_b:
        return err(f"Planet '{b}' not found")
    comparison = {
        "planets": [p_a["name"], p_b["name"]],
        "larger": p_a["name"] if p_a["radius_km"] > p_b["radius_km"] else p_b["name"],
        "heavier": p_a["name"] if float(p_a["mass_kg"].split("×")[0]) > float(p_b["mass_kg"].split("×")[0]) else p_b["name"],
        "warmer": p_a["name"] if p_a["surface_temp_max_C"] > p_b["surface_temp_max_C"] else p_b["name"],
        "more_habitable": p_a["name"] if p_a["habitability_score"] > p_b["habitability_score"] else p_b["name"],
        "radius_ratio": round(p_a["radius_km"] / p_b["radius_km"], 2),
        "distance_ratio": round(p_a["distance_from_sun_AU"] / p_b["distance_from_sun_AU"], 2),
        "planet_a": p_a,
        "planet_b": p_b,
    }
    return ok(comparison)

# Quiz — return random 10 questions
@app.get("/api/quiz")
def get_quiz():
    shuffled = QUIZ_QUESTIONS.copy()
    random.shuffle(shuffled)
    return ok(shuffled[:10])

# Submit quiz score
@app.post("/api/quiz/score")
def submit_score():
    body = request.get_json(silent=True) or {}
    user_id = body.get("userId", str(uuid4()))
    correct_answers = body.get("correctAnswers")
    total_questions = body.get("totalQuestions")
    if correct_answers is None or total_questions is None:
        return err("Provide correctAnswers and totalQuestions")
    pct = (correct_answers / total_questions) * 100
    badge = None
    if pct == 100:
        badge = next((a for a in ACHIEVEMENTS if a["id"] == "quiz_perfect"), None)
    elif pct >= 80:
        badge = next((a for a in ACHIEVEMENTS if a["id"] == "quiz_pass"), None)
    record = {
        "userId": user_id,
        "correctAnswers": correct_answers,
        "totalQuestions": total_questions,
        "pct": pct,
        "timestamp": int(time.time() * 1000),
    }
    scores_store.append(record)
    return ok({**record, "badge": badge, "rank": len(scores_store)})

# Achievements
@app.get("/api/achievements")
def get_achievements():
    return ok(ACHIEVEMENTS, {"count": len(ACHIEVEMENTS)})

# Save favourite
@app.post("/api/favorites")
def save_favorite():
    body = request.get_json(silent=True) or {}
    user_id = body.get("userId")
    planet_id = body.get("planetId")
    if not user_id or not planet_id:
        return err("Provide userId and planetId")
    if not any(p["id"] == planet_id for p in PLANETS):
        return err("Planet not found")
    if user_id not in favorites_store:
        favorites_store[user_id] = set()
    favorites_store[user_id].add(planet_id)
    return ok({"userId": user_id, "favorites": list(favorites_store[user_id])})

# Get favourites
@app.get("/api/favorites/<user_id>")
def get_favorites(user_id):
    fav_set = favorites_store.get(user_id, set())
    planets = [p for p in PLANETS if p["id"] in fav_set]
    return ok({"userId": user_id, "count": len(planets), "planets": planets})

# Soundtracks
@app.get("/api/soundtrack")
def get_soundtrack():
    return ok(SOUNDTRACKS, {"count": len(SOUNDTRACKS)})

# ─── AI Assistant ─────────────────────────────────────────────────────────────
@app.post("/api/ai/ask")
def ai_ask():
    body = request.get_json(silent=True) or {}
    question = body.get("question", "")
    context = body.get("context", "")
    if not question or len(question.strip()) < 2:
        return err("Provide a question")

    system_prompt = (
        "You are ARIA — Advanced Research Intelligence Assistant for CosmoLearn, "
        "a futuristic space education platform.\n"
        "You are a holographic AI guide with deep knowledge of astronomy, planetary science, "
        "space exploration, and cosmology.\n"
        "Respond in an engaging, cinematic tone — knowledgeable yet accessible.\n"
        "Keep answers concise (3–5 sentences) unless the topic demands depth.\n"
        "Use metric units. When mentioning numbers, make them vivid and relatable.\n"
        + (f"Current context: {context}" if context else "")
    )

    try:
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": question}],
        )
        answer = "".join(b.text for b in message.content if b.type == "text")
        return ok({
            "question": question,
            "answer": answer,
            "model": message.model,
            "usage": {
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            },
        })
    except Exception as e:
        print(f"Anthropic error: {e}")
        # Fallback static answers
        fallbacks = {
            "mars": (
                "Mars is a cold desert world with the largest volcano in the solar system — "
                "Olympus Mons. Its thin atmosphere makes it inhospitable, but it remains "
                "humanity's top candidate for future colonisation."
            ),
            "earth": (
                "Earth is our pale blue dot — the only world in the known universe confirmed "
                "to harbour life. Its liquid water, oxygen-rich atmosphere, and magnetic field "
                "make it uniquely habitable."
            ),
            "sun": (
                "Our Sun is a G-type main-sequence star converting 600 million tonnes of hydrogen "
                "to helium every second. It has powered Earth's biosphere for 4.6 billion years "
                "and has roughly 5 billion more to go."
            ),
        }
        lower = question.lower()
        fallback_answer = next(
            (v for k, v in fallbacks.items() if k in lower),
            "The cosmos holds endless mysteries. Every planet in our solar system tells a unique "
            "story forged over billions of years of cosmic evolution. What specific aspect would "
            "you like to explore?",
        )
        return ok({"question": question, "answer": fallback_answer, "model": "fallback"})

# ─── 404 + Error handlers ─────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found", "path": request.path}), 404

@app.errorhandler(500)
def server_error(e):
    print(e)
    return jsonify({"error": "Internal server error"}), 500

# ─── Socket.io — real-time meteor events ──────────────────────────────────────
@socketio.on("connect")
def on_connect():
    print(f"🌌 Client connected: {request.sid}")
    emit("cosmos_event", {
        "type": "welcome",
        "message": "ARIA online. Solar system monitoring active.",
        "timestamp": int(time.time() * 1000),
    })

    def meteor_loop(sid):
        while True:
            delay = 5 + random.random() * 10
            time.sleep(delay)
            socketio.emit("cosmos_event", {
                "type": "meteor",
                "x": random.random(),
                "y": random.random(),
                "speed": 0.5 + random.random() * 2,
                "size": 0.1 + random.random() * 0.5,
                "timestamp": int(time.time() * 1000),
            })

    def flare_loop(sid):
        while True:
            delay = 30 + random.random() * 30
            time.sleep(delay)
            socketio.emit("cosmos_event", {
                "type": "solar_flare",
                "intensity": random.choice(["minor", "moderate", "strong"]),
                "timestamp": int(time.time() * 1000),
            })

    threading.Thread(target=meteor_loop, args=(request.sid,), daemon=True).start()
    threading.Thread(target=flare_loop, args=(request.sid,), daemon=True).start()

@socketio.on("disconnect")
def on_disconnect():
    print(f"🌌 Client disconnected: {request.sid}")

# ─── Start ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════╗
║          🚀  CosmoLearn API  v1.0  🚀           ║
║  Server : http://localhost:{PORT}                   ║
║  Socket : ws://localhost:{PORT}                     ║
║  Health : http://localhost:{PORT}/api/health        ║
╚══════════════════════════════════════════════════╝
    """)
    socketio.run(app, host="0.0.0.0", port=PORT, debug=False)
