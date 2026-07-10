"""
Fitness Buddy — IBM watsonx.ai Client
Uses the modern chat completions API (/ml/v1/text/chat) which works with
all models including Llama 3.3 and Mistral on the eu-gb region.
"""
import logging
import warnings
from agent_config import SYSTEM_PROMPT, GENERATION_PARAMS, SAFETY_RULES

logger = logging.getLogger(__name__)

# Suppress IBM SDK deprecation warnings in console
warnings.filterwarnings("ignore", category=Warning, module="ibm_watsonx_ai")


class WatsonXClient:
    """
    Wraps IBM watsonx.ai using the chat completions API.
    Lazy-initialises on first chat() call — app starts instantly even
    when IBM_API_KEY is not yet configured.
    """

    def __init__(self, api_key: str, project_id: str, url: str, model_id: str):
        self._api_key    = api_key
        self._project_id = project_id
        self._url        = url
        self._model_id   = model_id
        self._model      = None
        self._init_tried = False
        self._init_ok    = False

        if not api_key or api_key.startswith("your-"):
            logger.info("[WatsonX] IBM_API_KEY not set — AI chat disabled until configured in .env")
        elif not project_id or project_id.startswith("your-"):
            logger.info("[WatsonX] IBM_PROJECT_ID not set — AI chat disabled until configured in .env")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _try_init(self) -> bool:
        """Attempt connection once, lazily on first chat() call."""
        if self._init_tried:
            return self._init_ok

        self._init_tried = True

        if not self._api_key or self._api_key.startswith("your-"):
            return False
        if not self._project_id or self._project_id.startswith("your-"):
            return False

        try:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference

            creds = Credentials(url=self._url, api_key=self._api_key)
            self._model = ModelInference(
                model_id   = self._model_id,
                credentials= creds,
                project_id = self._project_id,
            )
            self._init_ok = True
            logger.info(f"[WatsonX] Connected — model: {self._model_id} region: {self._url}")
        except Exception as e:
            self._init_ok = False
            logger.error(f"[WatsonX] Connection failed: {e}")

        return self._init_ok

    def _build_messages(
        self,
        messages    : list[dict],
        user_context: dict | None = None,
    ) -> list[dict]:
        """
        Build the messages list for the chat API.
        Prepends the system prompt (with optional user profile context).
        """
        context_block = ""
        if user_context:
            parts = []
            if user_context.get("name"):       parts.append(f"User Name: {user_context['name']}")
            if user_context.get("age"):        parts.append(f"Age: {user_context['age']}")
            if user_context.get("gender"):     parts.append(f"Gender: {user_context['gender']}")
            if user_context.get("height"):     parts.append(f"Height: {user_context['height']} cm")
            if user_context.get("weight"):     parts.append(f"Weight: {user_context['weight']} kg")
            if user_context.get("goal"):       parts.append(f"Fitness Goal: {user_context['goal']}")
            if user_context.get("diet"):       parts.append(f"Diet Preference: {user_context['diet']}")
            if user_context.get("experience"): parts.append(f"Experience Level: {user_context['experience']}")
            if parts:
                context_block = "\n\nUSER PROFILE:\n" + "\n".join(parts)

        chat_messages = [{"role": "system", "content": SYSTEM_PROMPT + context_block}]

        # Add conversation history (last 20 turns to stay within token limits)
        for msg in messages[-20:]:
            role    = msg.get("role", "user")
            content = msg.get("content", "").strip()
            if role in ("user", "assistant") and content:
                chat_messages.append({"role": role, "content": content})

        return chat_messages

    # ── Public API ────────────────────────────────────────────────────────────

    def chat(
        self,
        messages    : list[dict],
        user_context: dict | None = None,
    ) -> str:
        """Send messages to IBM watsonx and return the assistant reply."""

        if not self._try_init():
            if not self._api_key or self._api_key.startswith("your-"):
                return (
                    "**AI Coach not configured yet.**\n\n"
                    "To enable the AI:\n"
                    "1. Open the `.env` file in the `fitness_buddy/` folder\n"
                    "2. Set `IBM_API_KEY` to your real IBM Cloud API key\n"
                    "3. Set `IBM_PROJECT_ID` to your watsonx.ai Project ID\n"
                    "4. Restart the app\n\n"
                    "Get free credentials at **cloud.ibm.com** → watsonx.ai"
                )
            return (
                "**Could not connect to IBM watsonx.ai.**\n\n"
                "Please check:\n"
                "- `IBM_API_KEY` is correct\n"
                "- `IBM_PROJECT_ID` matches your watsonx.ai project\n"
                "- `IBM_WATSONX_URL` region matches your account (try `eu-gb`, `us-south`, `eu-de`)\n\n"
                "Restart the app after updating `.env`."
            )

        chat_messages = self._build_messages(messages, user_context)
        gp = GENERATION_PARAMS

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                response = self._model.chat(
                    messages   = chat_messages,
                    params     = {
                        "max_tokens" : gp.get("max_new_tokens", 2048),
                        "temperature": gp.get("temperature", 0.7),
                        "top_p"      : gp.get("top_p", 0.95),
                    },
                )

            # Extract text from chat response
            reply = (
                response
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            if not reply:
                raise ValueError("Empty response from model")

            return reply

        except Exception as e:
            logger.error(f"[WatsonX] Chat error: {e}")
            # Retry once with generate_text as fallback
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    # Build legacy prompt for fallback
                    prompt = f"{SYSTEM_PROMPT}\n\n"
                    for msg in messages[-10:]:
                        role    = msg.get("role", "user")
                        content = msg.get("content", "").strip()
                        if role == "user":
                            prompt += f"Human: {content}\n"
                        elif role == "assistant":
                            prompt += f"Assistant: {content}\n"
                    prompt += "Assistant:"
                    reply = self._model.generate_text(prompt=prompt)
                    return reply.strip() if reply else "I couldn't generate a response. Please try again."
            except Exception as e2:
                logger.error(f"[WatsonX] Fallback also failed: {e2}")
                return "I'm having trouble responding right now. Please try again in a moment."

    @property
    def is_available(self) -> bool:
        return self._init_ok
