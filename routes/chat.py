"""
Fitness Buddy — Chat Routes (AI Fitness Buddy)
"""
import json
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, ChatSession, ChatMessage
from agent_config import SUGGESTED_PROMPTS, PERSONA, SAFETY_RULES

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat")
@login_required
def index():
    sessions = (
        ChatSession.query
        .filter_by(user_id=current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "chat/index.html",
        sessions        = sessions,
        suggested_prompts = SUGGESTED_PROMPTS,
        persona_name    = PERSONA["name"],
        persona_greeting= PERSONA["greeting"],
    )


@chat_bp.route("/chat/session/new", methods=["POST"])
@login_required
def new_session():
    session = ChatSession(user_id=current_user.id, title="New Chat")
    db.session.add(session)
    db.session.commit()
    return jsonify({"session_id": session.id})


@chat_bp.route("/chat/session/<int:session_id>")
@login_required
def load_session(session_id):
    session = ChatSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

    messages = [
        {"role": m.role, "content": m.content}
        for m in session.messages
    ]
    return jsonify({
        "session_id": session.id,
        "title"     : session.title,
        "messages"  : messages,
    })


@chat_bp.route("/chat/send", methods=["POST"])
@login_required
def send_message():
    data       = request.get_json()
    user_msg   = (data.get("message") or "").strip()
    session_id = data.get("session_id")

    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    # ── Get or create session ──────────────────────────────────
    if session_id:
        chat_session = ChatSession.query.filter_by(
            id=session_id, user_id=current_user.id
        ).first()
        if not chat_session:
            chat_session = ChatSession(user_id=current_user.id)
            db.session.add(chat_session)
    else:
        chat_session = ChatSession(user_id=current_user.id)
        db.session.add(chat_session)

    db.session.flush()

    # ── Persist user message ───────────────────────────────────
    user_record = ChatMessage(
        session_id=chat_session.id, role="user", content=user_msg
    )
    db.session.add(user_record)

    # ── Build history for prompt ───────────────────────────────
    history = [
        {"role": m.role, "content": m.content}
        for m in chat_session.messages[-40:]   # last 40 turns
    ]
    history.append({"role": "user", "content": user_msg})

    # ── Build user context from profile ───────────────────────
    profile = current_user.profile
    user_context = {}
    if profile:
        user_context = {
            "name"      : profile.full_name or current_user.username,
            "age"       : profile.age,
            "gender"    : profile.gender,
            "height"    : profile.height_cm,
            "weight"    : profile.weight_kg,
            "goal"      : profile.fitness_goal,
            "diet"      : profile.diet_preference,
            "experience": profile.experience_level,
        }

    # ── Call IBM watsonx.ai ────────────────────────────────────
    watsonx = current_app.watsonx
    ai_reply = watsonx.chat(history, user_context=user_context)

    # ── Persist AI reply ───────────────────────────────────────
    ai_record = ChatMessage(
        session_id=chat_session.id, role="assistant", content=ai_reply
    )
    db.session.add(ai_record)

    # ── Auto-title session from first message ──────────────────
    if chat_session.title == "New Chat" and len(chat_session.messages) == 0:
        title = user_msg[:60] + ("…" if len(user_msg) > 60 else "")
        chat_session.title = title

    db.session.commit()

    return jsonify({
        "reply"     : ai_reply,
        "session_id": chat_session.id,
        "title"     : chat_session.title,
    })


@chat_bp.route("/chat/session/<int:session_id>/delete", methods=["DELETE"])
@login_required
def delete_session(session_id):
    session = ChatSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(session)
    db.session.commit()
    return jsonify({"success": True})
