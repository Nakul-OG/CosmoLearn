from flask import Flask, jsonify, request
from flask_cors import CORS
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

PLANETS = [
    {
        "id": "mercury",
        "name": "Mercury",
        "type": "Terrestrial",
        "radius_km": 2439.7,
        "distance_from_sun_km": 57900000,
        "gravity_ms2": 3.7,
        "survival_chance_percent": 0
    },
    {
        "id": "venus",
        "name": "Venus",
        "type": "Terrestrial",
        "radius_km": 6051.8,
        "distance_from_sun_km": 108200000,
        "gravity_ms2": 8.87,
        "survival_chance_percent": 0
    },
    {
        "id": "earth",
        "name": "Earth",
        "type": "Terrestrial",
        "radius_km": 6371,
        "distance_from_sun_km": 149600000,
        "gravity_ms2": 9.81,
        "survival_chance_percent": 100
    },
    {
        "id": "mars",
        "name": "Mars",
        "type": "Terrestrial",
        "radius_km": 3389.5,
        "distance_from_sun_km": 227900000,
        "gravity_ms2": 3.72,
        "survival_chance_percent": 1
    },
    {
        "id": "jupiter",
        "name": "Jupiter",
        "type": "Gas Giant",
        "radius_km": 69911,
        "distance_from_sun_km": 778500000,
        "gravity_ms2": 24.79,
        "survival_chance_percent": 0
    },
    {
        "id": "saturn",
        "name": "Saturn",
        "type": "Gas Giant",
        "radius_km": 58232,
        "distance_from_sun_km": 1432000000,
        "gravity_ms2": 10.44,
        "survival_chance_percent": 0
    },
    {
        "id": "uranus",
        "name": "Uranus",
        "type": "Ice Giant",
        "radius_km": 25362,
        "distance_from_sun_km": 2867000000,
        "gravity_ms2": 8.87,
        "survival_chance_percent": 0
    },
    {
        "id": "neptune",
        "name": "Neptune",
        "type": "Ice Giant",
        "radius_km": 24622,
        "distance_from_sun_km": 4495000000,
        "gravity_ms2": 11.15,
        "survival_chance_percent": 0
    }
]

SUN = {
    "name": "Sun",
    "type": "G-type Main Sequence Star",
    "surface_temp_K": 5778,
    "core_temp_K": 15000000,
    "age_billion_years": 4.6
}

QUIZ_QUESTIONS = [
    {
        "q": "Which planet is known as the Red Planet?",
        "options": ["Earth", "Mars", "Jupiter", "Venus"],
        "answer": 1
    },
    {
        "q": "Which planet has the most rings?",
        "options": ["Earth", "Saturn", "Mars", "Mercury"],
        "answer": 1
    },
    {
        "q": "Which is the largest planet?",
        "options": ["Venus", "Earth", "Jupiter", "Neptune"],
        "answer": 2
    }
]

@app.route('/')
def home():
    return jsonify({
        "message": "CosmoLearn Flask Backend Running",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/health')
def health():
    return jsonify({
        "success": True,
        "status": "healthy"
    })

@app.route('/api/planets')
def get_planets():
    return jsonify({
        "success": True,
        "data": PLANETS
    })

@app.route('/api/planets/<planet_id>')
def get_planet(planet_id):
    planet = next((p for p in PLANETS if p["id"] == planet_id), None)

    if not planet:
        return jsonify({
            "success": False,
            "error": "Planet not found"
        }), 404

    return jsonify({
        "success": True,
        "data": planet
    })

@app.route('/api/sun')
def get_sun():
    return jsonify({
        "success": True,
        "data": SUN
    })

@app.route('/api/quiz')
def get_quiz():
    random_questions = random.sample(
        QUIZ_QUESTIONS,
        min(3, len(QUIZ_QUESTIONS))
    )

    return jsonify({
        "success": True,
        "data": random_questions
    })

@app.route('/api/ai/ask', methods=['POST'])
def ai_ask():
    data = request.get_json()

    question = data.get('question', '')

    responses = {
        "mars": "Mars is called the Red Planet because of iron oxide on its surface.",
        "jupiter": "Jupiter is the largest planet in our solar system.",
        "sun": "The Sun contains 99.86% of the solar system's mass.",
        "earth": "Earth is the only known planet to support life."
    }

    answer = "Space is vast and full of mysteries waiting to be explored!"

    for key, value in responses.items():
        if key in question.lower():
            answer = value
            break

    return jsonify({
        "success": True,
        "answer": answer
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
