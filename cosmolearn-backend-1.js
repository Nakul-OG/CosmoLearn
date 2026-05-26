/**
 * CosmoLearn Backend — Node.js / Express
 * ─────────────────────────────────────────────────────────────────────────────
 * Stack : Express · CORS · Helmet · Morgan · Rate-limiter · Socket.io
 *
 * Routes
 *   GET  /api/planets            → all planet data
 *   GET  /api/planets/:id        → single planet
 *   GET  /api/sun                → Sun data
 *   POST /api/ai/ask             → AI space assistant (Anthropic SDK)
 *   GET  /api/quiz               → random quiz questions
 *   POST /api/quiz/score         → submit score & get badge
 *   GET  /api/achievements       → all achievement definitions
 *   POST /api/favorites          → save favourite planet (in-memory demo)
 *   GET  /api/favorites/:userId  → get favourites
 *   GET  /api/compare            → compare two planets ?a=earth&b=mars
 *   GET  /api/soundtrack         → list space soundtracks
 *   WS   /                       → Socket.io real-time meteor events
 *
 * Install:
 *   npm i express cors helmet morgan express-rate-limit socket.io uuid @anthropic-ai/sdk dotenv
 *
 * Run:
 *   ANTHROPIC_API_KEY=sk-... node cosmolearn-backend.js
 */

"use strict";
require("dotenv").config();

const express = require("express");
const http = require("http");
const cors = require("cors");
const helmet = require("helmet");
const morgan = require("morgan");
const { RateLimiterMemory } = require("rate-limiter-flexible");
const { Server: SocketIO } = require("socket.io");
const { v4: uuidv4 } = require("uuid");
const Anthropic = require("@anthropic-ai/sdk");

// ─── Constants ────────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 4000;
const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// ─── Planet Data ─────────────────────────────────────────────────────────────
const PLANETS = [
  {
    id: "mercury",
    name: "Mercury",
    color: "#b5b5b5",
    radius_km: 2439.7,
    mass_kg: "3.30×10²³",
    gravity_ms2: 3.7,
    distance_from_sun_AU: 0.39,
    distance_from_sun_km: 57_900_000,
    orbital_period_days: 87.97,
    rotation_period_hours: 1407.6,
    surface_temp_min_C: -180,
    surface_temp_max_C: 430,
    atmosphere: "Extremely thin (oxygen, sodium, hydrogen, helium)",
    moons: 0,
    has_water: false,
    has_oxygen: false,
    survival_chance_percent: 0,
    habitability_score: 2,
    texture_hint: "rocky grey cratered surface",
    fun_facts: [
      "A year on Mercury lasts only 88 Earth days.",
      "Despite being closest to the Sun, Venus is hotter.",
      "Mercury has ice in permanently shadowed craters at its poles.",
      "Its iron core makes up about 85 % of its radius.",
    ],
    composition: { iron: 70, rock: 30 },
    magnetic_field: "Yes (weak — 1 % of Earth)",
    rings: false,
    type: "Terrestrial",
  },
  {
    id: "venus",
    name: "Venus",
    color: "#e8cda0",
    radius_km: 6051.8,
    mass_kg: "4.87×10²⁴",
    gravity_ms2: 8.87,
    distance_from_sun_AU: 0.72,
    distance_from_sun_km: 108_200_000,
    orbital_period_days: 224.7,
    rotation_period_hours: 5832.5,
    surface_temp_min_C: 437,
    surface_temp_max_C: 482,
    atmosphere: "Dense CO₂ with sulfuric acid clouds (96.5% CO₂)",
    moons: 0,
    has_water: false,
    has_oxygen: false,
    survival_chance_percent: 0,
    habitability_score: 3,
    texture_hint: "thick yellowish atmosphere swirling clouds",
    fun_facts: [
      "Venus rotates backwards compared to most planets.",
      "A day on Venus is longer than its year.",
      "Surface pressure is 92× that of Earth's sea level.",
      "It's the hottest planet despite not being closest to the Sun.",
    ],
    composition: { rock: 95, iron: 5 },
    magnetic_field: "No",
    rings: false,
    type: "Terrestrial",
  },
  {
    id: "earth",
    name: "Earth",
    color: "#1a7fd4",
    radius_km: 6371,
    mass_kg: "5.97×10²⁴",
    gravity_ms2: 9.81,
    distance_from_sun_AU: 1.0,
    distance_from_sun_km: 149_600_000,
    orbital_period_days: 365.25,
    rotation_period_hours: 23.93,
    surface_temp_min_C: -89,
    surface_temp_max_C: 58,
    atmosphere: "Nitrogen (78 %), Oxygen (21 %), Argon (0.9 %)",
    moons: 1,
    has_water: true,
    has_oxygen: true,
    survival_chance_percent: 100,
    habitability_score: 100,
    texture_hint: "blue oceans green continents white clouds",
    fun_facts: [
      "Earth is the only known planet harboring life.",
      "71 % of the surface is covered in water.",
      "The Moon stabilises Earth's axial tilt.",
      "Earth's inner core is solid iron, hotter than the Sun's surface.",
    ],
    composition: { iron: 32, oxygen: 30, silicon: 15, other: 23 },
    magnetic_field: "Yes (strong)",
    rings: false,
    type: "Terrestrial",
  },
  {
    id: "mars",
    name: "Mars",
    color: "#c1440e",
    radius_km: 3389.5,
    mass_kg: "6.42×10²³",
    gravity_ms2: 3.72,
    distance_from_sun_AU: 1.52,
    distance_from_sun_km: 227_900_000,
    orbital_period_days: 686.97,
    rotation_period_hours: 24.62,
    surface_temp_min_C: -125,
    surface_temp_max_C: 20,
    atmosphere: "Thin CO₂ (95 %), Nitrogen (2.6 %), Argon (1.9 %)",
    moons: 2,
    has_water: "Subsurface ice",
    has_oxygen: false,
    survival_chance_percent: 1,
    habitability_score: 18,
    texture_hint: "red rocky dusty surface with canyons",
    fun_facts: [
      "Olympus Mons is the tallest volcano in the solar system.",
      "Valles Marineris is as wide as the United States.",
      "Mars has two small moons: Phobos and Deimos.",
      "A dust storm on Mars can last months and cover the whole planet.",
    ],
    composition: { iron_oxide: 20, rock: 75, other: 5 },
    magnetic_field: "No (remnant patches)",
    rings: false,
    type: "Terrestrial",
  },
  {
    id: "jupiter",
    name: "Jupiter",
    color: "#c88b3a",
    radius_km: 69911,
    mass_kg: "1.90×10²⁷",
    gravity_ms2: 24.79,
    distance_from_sun_AU: 5.2,
    distance_from_sun_km: 778_500_000,
    orbital_period_days: 4332.59,
    rotation_period_hours: 9.92,
    surface_temp_min_C: -145,
    surface_temp_max_C: -108,
    atmosphere: "Hydrogen (89 %), Helium (10 %), methane, ammonia",
    moons: 95,
    has_water: "Possible in cloud layers",
    has_oxygen: false,
    survival_chance_percent: 0,
    habitability_score: 5,
    texture_hint: "orange brown bands great red spot gas giant",
    fun_facts: [
      "Jupiter's Great Red Spot is a storm older than 350 years.",
      "Jupiter is 1,300× the volume of Earth.",
      "Its moon Europa may have a subsurface liquid ocean.",
      "Jupiter acts as a planetary shield deflecting asteroids.",
    ],
    composition: { hydrogen: 89, helium: 10, other: 1 },
    magnetic_field: "Yes (strongest in solar system)",
    rings: true,
    type: "Gas Giant",
  },
  {
    id: "saturn",
    name: "Saturn",
    color: "#e4d191",
    radius_km: 58232,
    mass_kg: "5.68×10²⁶",
    gravity_ms2: 10.44,
    distance_from_sun_AU: 9.58,
    distance_from_sun_km: 1_432_000_000,
    orbital_period_days: 10759.22,
    rotation_period_hours: 10.66,
    surface_temp_min_C: -178,
    surface_temp_max_C: -138,
    atmosphere: "Hydrogen (96 %), Helium (3 %), trace methane",
    moons: 146,
    has_water: "Possibly as ice in rings",
    has_oxygen: false,
    survival_chance_percent: 0,
    habitability_score: 4,
    texture_hint: "golden planet with prominent ring system",
    fun_facts: [
      "Saturn's rings are made of ice and rock particles.",
      "Saturn is less dense than water — it could float!",
      "Its moon Titan has a thick atmosphere and methane lakes.",
      "Saturn has the most moons of any planet (146 confirmed).",
    ],
    composition: { hydrogen: 96, helium: 3, other: 1 },
    magnetic_field: "Yes",
    rings: true,
    type: "Gas Giant",
  },
  {
    id: "uranus",
    name: "Uranus",
    color: "#7de8e8",
    radius_km: 25362,
    mass_kg: "8.68×10²⁵",
    gravity_ms2: 8.87,
    distance_from_sun_AU: 19.22,
    distance_from_sun_km: 2_867_000_000,
    orbital_period_days: 30688.5,
    rotation_period_hours: 17.24,
    surface_temp_min_C: -224,
    surface_temp_max_C: -197,
    atmosphere: "Hydrogen (83 %), Helium (15 %), Methane (2 %)",
    moons: 28,
    has_water: "Possible icy mantle",
    has_oxygen: false,
    survival_chance_percent: 0,
    habitability_score: 2,
    texture_hint: "pale cyan ice giant smooth featureless",
    fun_facts: [
      "Uranus rotates on its side — axial tilt of 98°.",
      "It's the coldest planetary atmosphere in the solar system.",
      "Uranus has 13 known rings.",
      "Its moons are named after Shakespeare characters.",
    ],
    composition: { water_ice: 65, rock: 20, hydrogen: 10, helium: 5 },
    magnetic_field: "Yes (tilted 59° from axis)",
    rings: true,
    type: "Ice Giant",
  },
  {
    id: "neptune",
    name: "Neptune",
    color: "#3f54ba",
    radius_km: 24622,
    mass_kg: "1.02×10²⁶",
    gravity_ms2: 11.15,
    distance_from_sun_AU: 30.05,
    distance_from_sun_km: 4_495_000_000,
    orbital_period_days: 60182,
    rotation_period_hours: 16.11,
    surface_temp_min_C: -218,
    surface_temp_max_C: -200,
    atmosphere: "Hydrogen (80 %), Helium (19 %), Methane (1 %)",
    moons: 16,
    has_water: "Deep icy mantle",
    has_oxygen: false,
    survival_chance_percent: 0,
    habitability_score: 2,
    texture_hint: "deep blue ice giant with dark storm spots",
    fun_facts: [
      "Neptune has the fastest winds in the solar system (2,100 km/h).",
      "It was predicted mathematically before it was observed.",
      "Its moon Triton orbits backwards (retrograde).",
      "Neptune radiates 2.6× more heat than it receives from the Sun.",
    ],
    composition: { water_ice: 60, rock: 25, hydrogen: 10, helium: 5 },
    magnetic_field: "Yes",
    rings: true,
    type: "Ice Giant",
  },
  {
    id: "pluto",
    name: "Pluto",
    color: "#c5a98b",
    radius_km: 1188.3,
    mass_kg: "1.30×10²²",
    gravity_ms2: 0.62,
    distance_from_sun_AU: 39.48,
    distance_from_sun_km: 5_906_000_000,
    orbital_period_days: 90560,
    rotation_period_hours: 153.3,
    surface_temp_min_C: -240,
    surface_temp_max_C: -218,
    atmosphere: "Thin nitrogen, methane, carbon monoxide",
    moons: 5,
    has_water: "Possible subsurface ocean",
    has_oxygen: false,
    survival_chance_percent: 0,
    habitability_score: 1,
    texture_hint: "brown icy dwarf planet heart-shaped nitrogen plain",
    fun_facts: [
      "Pluto has a heart-shaped nitrogen plain called Tombaugh Regio.",
      "Its moon Charon is half its size — they orbit each other.",
      "Pluto was reclassified as a dwarf planet in 2006.",
      "New Horizons flew by Pluto in July 2015.",
    ],
    composition: { rock: 70, ice: 30 },
    magnetic_field: "Unknown",
    rings: false,
    type: "Dwarf Planet",
  },
];

// ─── Sun Data ─────────────────────────────────────────────────────────────────
const SUN = {
  id: "sun",
  name: "The Sun",
  type: "G-type main-sequence star (Yellow Dwarf)",
  radius_km: 695_700,
  mass_kg: "1.99×10³⁰",
  surface_temp_K: 5778,
  core_temp_K: 15_000_000,
  age_billion_years: 4.6,
  luminosity_watts: "3.83×10²⁶",
  composition_percent: { hydrogen: 73, helium: 25, other: 2 },
  distance_from_galactic_center_ly: 26000,
  energy_output: "3.83×10²⁶ watts (3.83 yottawatts)",
  survival_near_sun: {
    survival_chance_percent: 0,
    lethal_radius_km: 20_000_000,
    note: "At 20 million km, radiation and heat would instantly vaporise any known material.",
  },
  solar_flares: "Occur regularly; largest (X-class) can disrupt satellites and power grids on Earth.",
  solar_wind_speed_kms: 400,
  fun_facts: [
    "The Sun contains 99.86 % of the solar system's total mass.",
    "Light from the Sun takes 8 minutes 20 seconds to reach Earth.",
    "The Sun converts 600 million tonnes of hydrogen to helium every second.",
    "It has burned for 4.6 billion years and has ~5 billion more to go.",
    "The solar corona is hotter than the surface — a mystery not yet fully explained.",
  ],
};

// ─── Quiz Questions ────────────────────────────────────────────────────────────
const QUIZ_QUESTIONS = [
  { q: "Which planet has the most moons?", options: ["Jupiter", "Saturn", "Uranus", "Neptune"], answer: 1 },
  { q: "What is the hottest planet?", options: ["Mercury", "Venus", "Mars", "Jupiter"], answer: 1 },
  { q: "How long does sunlight take to reach Earth?", options: ["1 min", "4 min", "8 min 20 sec", "15 min"], answer: 2 },
  { q: "Which planet has a day longer than its year?", options: ["Mars", "Venus", "Mercury", "Pluto"], answer: 1 },
  { q: "What causes seasons on Earth?", options: ["Distance from Sun", "Axial tilt", "Orbital speed", "Moon phases"], answer: 1 },
  { q: "Which planet has the tallest volcano?", options: ["Earth", "Venus", "Mars", "Jupiter"], answer: 2 },
  { q: "Saturn's density compared to water?", options: ["10× denser", "Same", "Less — it would float", "Twice"], answer: 2 },
  { q: "Which moon might harbour life?", options: ["Titan", "Io", "Europa", "Ganymede"], answer: 2 },
  { q: "What is Pluto classified as?", options: ["Planet", "Asteroid", "Dwarf Planet", "Moon"], answer: 2 },
  { q: "Who first observed Jupiter's moons?", options: ["Copernicus", "Kepler", "Galileo", "Newton"], answer: 2 },
  { q: "Neptune's winds reach up to?", options: ["500 km/h", "1200 km/h", "2100 km/h", "3000 km/h"], answer: 2 },
  { q: "The Great Red Spot is a storm on?", options: ["Saturn", "Jupiter", "Neptune", "Uranus"], answer: 1 },
  { q: "Which planet rotates on its side?", options: ["Uranus", "Neptune", "Saturn", "Mercury"], answer: 0 },
  { q: "What % of solar system mass does the Sun hold?", options: ["50%", "80%", "95%", "99.86%"], answer: 3 },
  { q: "Valles Marineris is a canyon on?", options: ["Earth", "Mars", "Venus", "Mercury"], answer: 1 },
];

// ─── Achievements ─────────────────────────────────────────────────────────────
const ACHIEVEMENTS = [
  { id: "first_click", name: "First Contact", desc: "Click your first planet", icon: "🪐", xp: 10 },
  { id: "all_planets", name: "Solar Explorer", desc: "Visit all 9 planets", icon: "🚀", xp: 100 },
  { id: "sun_mode", name: "Icarus", desc: "Enter Sun exploration mode", icon: "☀️", xp: 25 },
  { id: "quiz_pass", name: "Cosmonaut", desc: "Score 80%+ on the quiz", icon: "🎓", xp: 50 },
  { id: "quiz_perfect", name: "Einstein", desc: "Perfect quiz score", icon: "🧠", xp: 150 },
  { id: "favorites_5", name: "Stargazer", desc: "Save 5 favourite planets", icon: "⭐", xp: 30 },
  { id: "compare", name: "Analyst", desc: "Compare two planets", icon: "⚖️", xp: 20 },
  { id: "ai_3", name: "Inquisitor", desc: "Ask the AI 3 questions", icon: "🤖", xp: 20 },
  { id: "warp_speed", name: "Warp Drive", desc: "Trigger warp speed transition", icon: "💫", xp: 15 },
  { id: "night_owl", name: "Night Owl", desc: "Visit after midnight (local time)", icon: "🦉", xp: 10 },
];

// ─── Soundtracks ──────────────────────────────────────────────────────────────
const SOUNDTRACKS = [
  { id: 1, title: "Interstellar Main Theme", artist: "Hans Zimmer", mood: "epic", bpm: 60 },
  { id: 2, title: "Space Ambience", artist: "CosmoLearn AI", mood: "calm", bpm: 40 },
  { id: 3, title: "Cosmic Pulse", artist: "CosmoLearn AI", mood: "energetic", bpm: 120 },
  { id: 4, title: "Deep Space Journey", artist: "CosmoLearn AI", mood: "mysterious", bpm: 55 },
  { id: 5, title: "Nebula Dreams", artist: "CosmoLearn AI", mood: "dreamy", bpm: 70 },
];

// ─── In-memory stores ─────────────────────────────────────────────────────────
const favoritesStore = new Map(); // userId → Set<planetId>
const scoresStore = []; // { userId, score, timestamp }

// ─── App Setup ────────────────────────────────────────────────────────────────
const app = express();
const server = http.createServer(app);
const io = new SocketIO(server, {
  cors: { origin: "*", methods: ["GET", "POST"] },
});

app.use(helmet({ crossOriginEmbedderPolicy: false }));
app.use(cors({ origin: "*" }));
app.use(morgan("dev"));
app.use(express.json({ limit: "50kb" }));

// Rate limiter
const limiter = new RateLimiterMemory({ points: 60, duration: 60 });
app.use(async (req, res, next) => {
  try {
    await limiter.consume(req.ip);
    next();
  } catch {
    res.status(429).json({ error: "Too many requests" });
  }
});

// ─── Helpers ──────────────────────────────────────────────────────────────────
const ok = (res, data, meta = {}) =>
  res.json({ success: true, timestamp: new Date().toISOString(), ...meta, data });
const err = (res, msg, status = 400) =>
  res.status(status).json({ success: false, error: msg });

// ─── Routes ───────────────────────────────────────────────────────────────────

// Health check
app.get("/api/health", (_, res) =>
  ok(res, { status: "ok", service: "CosmoLearn API v1.0" })
);

// All planets
app.get("/api/planets", (_, res) =>
  ok(res, PLANETS, { count: PLANETS.length })
);

// Single planet
app.get("/api/planets/:id", (req, res) => {
  const planet = PLANETS.find((p) => p.id === req.params.id.toLowerCase());
  if (!planet) return err(res, "Planet not found", 404);
  ok(res, planet);
});

// Sun
app.get("/api/sun", (_, res) => ok(res, SUN));

// Compare two planets
app.get("/api/compare", (req, res) => {
  const { a, b } = req.query;
  if (!a || !b) return err(res, "Provide ?a=<planet>&b=<planet>");
  const pA = PLANETS.find((p) => p.id === a.toLowerCase());
  const pB = PLANETS.find((p) => p.id === b.toLowerCase());
  if (!pA) return err(res, `Planet '${a}' not found`);
  if (!pB) return err(res, `Planet '${b}' not found`);
  const comparison = {
    planets: [pA.name, pB.name],
    larger: pA.radius_km > pB.radius_km ? pA.name : pB.name,
    heavier: parseFloat(pA.mass_kg) > parseFloat(pB.mass_kg) ? pA.name : pB.name,
    warmer: pA.surface_temp_max_C > pB.surface_temp_max_C ? pA.name : pB.name,
    more_habitable:
      pA.habitability_score > pB.habitability_score ? pA.name : pB.name,
    radius_ratio: (pA.radius_km / pB.radius_km).toFixed(2),
    distance_ratio: (
      pA.distance_from_sun_AU / pB.distance_from_sun_AU
    ).toFixed(2),
    planet_a: pA,
    planet_b: pB,
  };
  ok(res, comparison);
});

// Quiz — return random 10 questions
app.get("/api/quiz", (_, res) => {
  const shuffled = [...QUIZ_QUESTIONS].sort(() => Math.random() - 0.5);
  ok(res, shuffled.slice(0, 10));
});

// Submit quiz score
app.post("/api/quiz/score", (req, res) => {
  const { userId = uuidv4(), correctAnswers, totalQuestions } = req.body;
  if (correctAnswers === undefined || totalQuestions === undefined)
    return err(res, "Provide correctAnswers and totalQuestions");
  const pct = (correctAnswers / totalQuestions) * 100;
  const badge =
    pct === 100
      ? ACHIEVEMENTS.find((a) => a.id === "quiz_perfect")
      : pct >= 80
      ? ACHIEVEMENTS.find((a) => a.id === "quiz_pass")
      : null;
  const record = { userId, correctAnswers, totalQuestions, pct, timestamp: Date.now() };
  scoresStore.push(record);
  ok(res, { ...record, badge, rank: scoresStore.length });
});

// Achievements
app.get("/api/achievements", (_, res) =>
  ok(res, ACHIEVEMENTS, { count: ACHIEVEMENTS.length })
);

// Save favourite
app.post("/api/favorites", (req, res) => {
  const { userId, planetId } = req.body;
  if (!userId || !planetId) return err(res, "Provide userId and planetId");
  if (!PLANETS.find((p) => p.id === planetId))
    return err(res, "Planet not found");
  if (!favoritesStore.has(userId)) favoritesStore.set(userId, new Set());
  favoritesStore.get(userId).add(planetId);
  ok(res, { userId, favorites: [...favoritesStore.get(userId)] });
});

// Get favourites
app.get("/api/favorites/:userId", (req, res) => {
  const favSet = favoritesStore.get(req.params.userId) || new Set();
  const planets = PLANETS.filter((p) => favSet.has(p.id));
  ok(res, { userId: req.params.userId, count: planets.length, planets });
});

// Soundtracks
app.get("/api/soundtrack", (_, res) =>
  ok(res, SOUNDTRACKS, { count: SOUNDTRACKS.length })
);

// ─── AI Assistant ─────────────────────────────────────────────────────────────
app.post("/api/ai/ask", async (req, res) => {
  const { question, context = "" } = req.body;
  if (!question || question.trim().length < 2)
    return err(res, "Provide a question");

  const systemPrompt = `You are ARIA — Advanced Research Intelligence Assistant for CosmoLearn, a futuristic space education platform.
You are a holographic AI guide with deep knowledge of astronomy, planetary science, space exploration, and cosmology.
Respond in an engaging, cinematic tone — knowledgeable yet accessible.
Keep answers concise (3–5 sentences) unless the topic demands depth.
Use metric units. When mentioning numbers, make them vivid and relatable.
${context ? `Current context: ${context}` : ""}`;

  try {
    const message = await anthropic.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 500,
      system: systemPrompt,
      messages: [{ role: "user", content: question }],
    });
    const answer = message.content
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join("");
    ok(res, { question, answer, model: message.model, usage: message.usage });
  } catch (e) {
    console.error("Anthropic error:", e.message);
    // Fallback static answers
    const fallbacks = {
      mars: "Mars is a cold desert world with the largest volcano in the solar system — Olympus Mons. Its thin atmosphere makes it inhospitable, but it remains humanity's top candidate for future colonisation.",
      earth: "Earth is our pale blue dot — the only world in the known universe confirmed to harbour life. Its liquid water, oxygen-rich atmosphere, and magnetic field make it uniquely habitable.",
      sun: "Our Sun is a G-type main-sequence star converting 600 million tonnes of hydrogen to helium every second. It has powered Earth's biosphere for 4.6 billion years and has roughly 5 billion more to go.",
    };
    const lower = question.toLowerCase();
    const fallback = Object.entries(fallbacks).find(([k]) => lower.includes(k));
    ok(res, {
      question,
      answer: fallback
        ? fallback[1]
        : "The cosmos holds endless mysteries. Every planet in our solar system tells a unique story forged over billions of years of cosmic evolution. What specific aspect would you like to explore?",
      model: "fallback",
    });
  }
});

// ─── Socket.io — real-time meteor events ──────────────────────────────────────
io.on("connection", (socket) => {
  console.log(`🌌 Client connected: ${socket.id}`);

  // Send a welcome pulse
  socket.emit("cosmos_event", {
    type: "welcome",
    message: "ARIA online. Solar system monitoring active.",
    timestamp: Date.now(),
  });

  // Broadcast random meteor events every 5–15 seconds
  const meteorInterval = setInterval(() => {
    io.emit("cosmos_event", {
      type: "meteor",
      x: Math.random(),
      y: Math.random(),
      speed: 0.5 + Math.random() * 2,
      size: 0.1 + Math.random() * 0.5,
      timestamp: Date.now(),
    });
  }, 5000 + Math.random() * 10000);

  // Solar flare events every 30–60 seconds
  const flareInterval = setInterval(() => {
    io.emit("cosmos_event", {
      type: "solar_flare",
      intensity: ["minor", "moderate", "strong"][Math.floor(Math.random() * 3)],
      timestamp: Date.now(),
    });
  }, 30000 + Math.random() * 30000);

  socket.on("disconnect", () => {
    clearInterval(meteorInterval);
    clearInterval(flareInterval);
    console.log(`🌌 Client disconnected: ${socket.id}`);
  });
});

// ─── 404 + Error handlers ─────────────────────────────────────────────────────
app.use((req, res) => res.status(404).json({ error: "Not found", path: req.path }));
app.use((error, req, res, _next) => {
  console.error(error);
  res.status(500).json({ error: "Internal server error" });
});

// ─── Start ────────────────────────────────────────────────────────────────────
server.listen(PORT, () => {
  console.log(`
╔══════════════════════════════════════════════════╗
║          🚀  CosmoLearn API  v1.0  🚀           ║
║  Server : http://localhost:${PORT}                   ║
║  Socket : ws://localhost:${PORT}                     ║
║  Health : http://localhost:${PORT}/api/health        ║
╚══════════════════════════════════════════════════╝
  `);
});

module.exports = { app, server };
