from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import BaseModel, ValidationError
from db import get_db_connection
from typing import Optional, List


class SurveyCreate(BaseModel):
    title: str
    questions: Optional[List[str]] = []


class QuestionsCreate(BaseModel):
    questions: List[str]


class ResponseItem(BaseModel):
    question_id: int
    answer: str


class SurveyResponse(BaseModel):
    responses: List[ResponseItem]


survey_bp = Blueprint("survey", __name__)


@survey_bp.route("/surveys", methods=["POST"])
@jwt_required()
def create_survey():
    try:
        data = SurveyCreate(**request.get_json())
    except ValidationError as e:
        current_app.logger.warning(f"Error de validacion {request.remote_addr}: {e}")
        return jsonify(e.errors()), 400

    user_id = int(get_jwt_identity())

    conn = get_db_connection()
    cursor = conn.cursor()

    current_app.logger.debug(f"Insertando nueva encuesta '{data.title}' por usuario {user_id}")
    cursor.execute(
        "INSERT INTO surveys (title, created_by) VALUES (?, ?)", (data.title, user_id)
    )

    survey_id = cursor.lastrowid

    if hasattr(data, "questions") and data.questions:
        for q in data.questions:
            cursor.execute(
                "INSERT INTO questions (survey_id, question) VALUES (?, ?)",
                (survey_id, q),
            )

    conn.commit()
    conn.close()

    current_app.logger.info(f"Encuesta creada exitosamente de: {request.remote_addr}")
    return jsonify(
        {"message": "Encuesta creada correctamente", "survey_id": survey_id}
    ), 201


@survey_bp.route("/surveys", methods=["GET"])
def get_surveys():
    current_app.logger.info("Petición recibida para listar encuestas")
    conn = get_db_connection()
    cursor = conn.cursor()

    current_app.logger.debug("Ejecutando query SELECT en surveys")
    surveys = cursor.execute("SELECT id, title, created_by FROM surveys").fetchall()

    conn.close()

    return jsonify([dict(row) for row in surveys])


@survey_bp.route("/surveys/<int:survey_id>", methods=["GET"])
def get_survey(survey_id):
    current_app.logger.info(f"Petición recibida para ver encuesta {survey_id}")
    conn = get_db_connection()
    cursor = conn.cursor()

    current_app.logger.debug(f"Ejecutando query SELECT para encuesta {survey_id}")
    survey = cursor.execute(
        "SELECT id, title, created_by FROM surveys WHERE id = ?", (survey_id,)
    ).fetchone()
    if not survey:
        current_app.logger.warning(f"Encuesta {survey_id} no encontrada")
        conn.close()
        return jsonify({"ERROR": "Encuesta no encontrada"}), 404

    current_app.logger.debug(f"Ejecutando query SELECT preguntas para encuesta {survey_id}")
    questions = cursor.execute(
        "SELECT id, question FROM questions WHERE survey_id = ?", (survey_id,)
    ).fetchall()

    survey_data = dict(survey)
    survey_data["questions"] = [dict(q) for q in questions]

    conn.close()

    return jsonify(survey_data)


@survey_bp.route("/surveys/<int:survey_id>/questions", methods=["POST"])
@jwt_required()
def add_questions(survey_id):
    try:
        data = QuestionsCreate(**request.get_json())
    except ValidationError as e:
        current_app.logger.warning(f"Error de validacion en preguntas: {e}")
        return jsonify(e.errors()), 400

    user_id = int(get_jwt_identity())

    conn = get_db_connection()
    cursor = conn.cursor()

    survey = cursor.execute(
        "SELECT * FROM surveys WHERE id = ?", (survey_id,)
    ).fetchone()
    if not survey:
        current_app.logger.warning(f"Intento de añadir preguntas a encuesta inexistente {survey_id}")
        return jsonify({"ERROR": "Encuesta no existe"})

    if not (survey["created_by"] == user_id):
        current_app.logger.warning(f"Usuario {user_id} intentó modificar encuesta de {survey['created_by']}")
        return jsonify({"ERROR": "No puede cambiar esta encuesta"})

    current_app.logger.debug(f"Insertando {len(data.questions)} preguntas a la encuesta {survey_id}")
    for q in data.questions:
        cursor.execute(
            "INSERT INTO questions (survey_id, question) VALUES (?, ?)", (survey_id, q)
        )

    conn.commit()
    conn.close()

    current_app.logger.info(f"Preguntas añadidas correctamente a la encuesta {survey_id}")
    return jsonify({"message": "Questions added successfully"}), 201


@survey_bp.route("/surveys/<int:survey_id>/responses", methods=["POST"])
@jwt_required()
def submit_responses(survey_id):
    try:
        data = SurveyResponse(**request.get_json())
    except ValidationError as e:
        current_app.logger.warning(f"Error de validacion {request.remote_addr}: {e}")
        return jsonify(e.errors()), 400

    user_id = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        current_app.logger.debug(f"Insertando {len(data.responses)} respuestas para la encuesta {survey_id} del usuario {user_id}")
        for r in data.responses:
            cursor.execute(
                """INSERT INTO responses 
                (user_id, survey_id, question_id, answer)
                VALUES (?, ?, ?, ?)""",
                (user_id, survey_id, r.question_id, r.answer),
            )

        conn.commit()
    except Exception as e:
        current_app.logger.error(f"Error al guardar respuestas en DB: {e}")
        conn.close()
        return jsonify({"ERROR": "Error al guardar en DB"}), 500
        
    conn.close()

    current_app.logger.info(f"Respuestas insertadas correctamente por usuario {user_id}")
    return jsonify({"message": "Responses submitted successfully"}), 201


@survey_bp.route("/surveys/<int:survey_id>/results", methods=["GET"])
def get_results(survey_id):
    current_app.logger.info(f"Petición recibida para resultados de encuesta {survey_id}")
    conn = get_db_connection()
    cursor = conn.cursor()

    current_app.logger.debug(f"Buscando preguntas de encuesta {survey_id}")
    questions = cursor.execute(
        "SELECT id, question FROM questions WHERE survey_id = ?", (survey_id,)
    ).fetchall()

    results = []

    for q in questions:
        answers = cursor.execute(
            "SELECT answer FROM responses WHERE question_id = ?", (q["id"],)
        ).fetchall()

        results.append(
            {
                "question_id": q["id"],
                "question": q["question"],
                "answers": [a["answer"] for a in answers],
            }
        )

    conn.close()

    return jsonify(results)
