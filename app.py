"""
Fitness Buddy — Flask Application Factory
"""
import os
from pathlib import Path

# Load .env before EVERYTHING else — must be before config import
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

from config import get_config
from models import db, bcrypt, User
from watsonx_client import WatsonXClient


login_manager = LoginManager()
migrate       = Migrate()
watsonx       = None      # module-level singleton, set during create_app


def create_app():
    global watsonx

    app = Flask(__name__)
    cfg = get_config()
    app.config.from_object(cfg)

    # ── Extensions ────────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view     = "auth.login"
    login_manager.login_message  = "Please log in to access Fitness Buddy."
    login_manager.login_message_category = "info"

    # ── IBM watsonx.ai client — read directly from os.environ
    # so Flask's debug reloader child process always gets fresh values
    watsonx = WatsonXClient(
        api_key   = os.environ.get("IBM_API_KEY", ""),
        project_id= os.environ.get("IBM_PROJECT_ID", ""),
        url       = os.environ.get("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
        model_id  = os.environ.get("IBM_GRANITE_MODEL_ID", "meta-llama/llama-3-3-70b-instruct"),
    )
    app.watsonx = watsonx

    # ── Blueprints ────────────────────────────────────────────
    from routes.auth       import auth_bp
    from routes.dashboard  import dashboard_bp
    from routes.chat       import chat_bp
    from routes.workout    import workout_bp
    from routes.nutrition  import nutrition_bp
    from routes.calculators import calculators_bp
    from routes.profile    import profile_bp
    from routes.api        import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(workout_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(calculators_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # ── DB init ───────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == "__main__":
    application = create_app()

    # ── Startup banner ────────────────────────────────────────────────────────
    cfg = get_config()
    # Trigger lazy init now so banner shows correct status
    application.watsonx._try_init()
    ai_status = "READY" if application.watsonx.is_available else "NOT CONFIGURED (set IBM_API_KEY in .env)"
    print("\n" + "=" * 60)
    print("  Fitness Buddy — AI-Powered Indian Fitness Coach")
    print("=" * 60)
    print(f"  URL        : http://127.0.0.1:5000")
    print(f"  Environment: {cfg.FLASK_ENV}")
    print(f"  Database   : {cfg.SQLALCHEMY_DATABASE_URI}")
    print(f"  AI Model   : {cfg.IBM_GRANITE_MODEL_ID}")
    print(f"  AI Status  : {ai_status}")
    print("=" * 60)
    print("  Press Ctrl+C to stop\n")

    application.run(debug=True, port=5000)
