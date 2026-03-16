from flask import Blueprint, jsonify, request
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
        return jsonify(e.errors()), 400

    user_id = int(get_jwt_identity())

    conn = get_db_connection()
    cursor = conn.cursor()

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

    return jsonify(
        {"message": "Encuesta creada correctamente", "survey_id": survey_id}
    ), 201


@survey_bp.route("/surveys", methods=["GET"])
@jwt_required()
def get_surveys():
    conn = get_db_connection()
    cursor = conn.cursor()

    surveys = cursor.execute("SELECT id, title, created_by FROM surveys").fetchall()

    conn.close()

    return jsonify([dict(row) for row in surveys])


@survey_bp.route("/surveys/<int:survey_id>/questions", methods=["POST"])
@jwt_required()
def add_questions(survey_id):
    try:
        data = QuestionsCreate(**request.get_json())
    except ValidationError as e:
        return jsonify(e.errors()), 400

    user_id = int(get_jwt_identity())

    conn = get_db_connection()
    cursor = conn.cursor()

    survey = cursor.execute(
        "SELECT * FROM surveys WHERE id = ?", (survey_id,)
    ).fetchone()
    if not survey:
        return jsonify({"ERROR": "Encuesta no existe"})

    if not (survey["created_by"] == user_id):
        return jsonify({"ERROR": "No puede cambiar esta encuesta"})

    for q in data.questions:
        cursor.execute(
            "INSERT INTO questions (survey_id, question) VALUES (?, ?)", (survey_id, q)
        )

    conn.commit()
    conn.close()

    return jsonify({"message": "Questions added successfully"}), 201


@survey_bp.route("/surveys/<int:survey_id>/responses", methods=["POST"])
@jwt_required()
def submit_responses(survey_id):
    try:
        data = SurveyResponse(**request.get_json())
    except ValidationError as e:
        return jsonify(e.errors()), 400

    user_id = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()

    for r in data.responses:
        cursor.execute(
            """INSERT INTO responses 
            (user_id, survey_id, question_id, answer)
            VALUES (?, ?, ?, ?)""",
            (user_id, survey_id, r.question_id, r.answer),
        )

    conn.commit()
    conn.close()

    return jsonify({"message": "Responses submitted successfully"}), 201


@survey_bp.route("/surveys/<int:survey_id>/results", methods=["GET"])
@jwt_required()
def get_results(survey_id):

    conn = get_db_connection()
    cursor = conn.cursor()

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
