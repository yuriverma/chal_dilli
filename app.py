#!/usr/bin/env python3
"""
Hugging Face Space entrypoint.

Why this file exists
--------------------
The Docker SDK on Spaces is a paid feature, so the free option that can still
run Python is the Gradio SDK. A Gradio Space runs this file and proxies
whatever is listening on port 7860 -- it does not require that the app be
*only* Gradio. So this mounts a small Gradio chat UI onto the existing FastAPI
app and serves both from one process:

    /            the Gradio chat, so the Space is usable on its own
    /chat        the JSON API the Netlify frontend calls
    /health      readiness, as before
    /docs        FastAPI's generated docs

The Gradio UI is not a second implementation. It calls the same orchestrator
the API route calls, in-process, and keeps its own conversation id in session
state -- so follow-ups ("and from there to Saket?") work in the Space UI
exactly as they do through the frontend.

Running locally is the same command Spaces runs:

    python app.py
"""

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_BACKEND = _ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import uvicorn  # noqa: E402

from api_server import app as fastapi_app  # noqa: E402
from conversation_state import ConversationStore  # noqa: E402

# Spaces sets PORT; 7860 is the port it proxies by default.
PORT = int(os.getenv("PORT", "7860"))

DESCRIPTION = """\
Ask about getting around Delhi. Real routes over the DMRC and DTC timetables,
with fares, interchanges and which station gate to use.

Follow-ups work, so you can say **"and from there to Saket?"** or
**"and by bus?"** without repeating yourself.
"""

EXAMPLES = [
    "dwarka se cp kaise jaun",
    "and from there to saket",
    "and by bus?",
    "best momos in dwarka",
    "food near there",
]


def _orchestrator():
    """The initialised orchestrator, or None while the app is still booting.

    api_server builds it on a background task during startup, so this is read
    at call time rather than captured at import.
    """
    import api_server

    return api_server.chal_dilli


def respond(message, history, conversation_id):
    """Answer one message from the Gradio UI.

    `conversation_id` is Gradio session state, so each visitor to the Space
    gets an independent conversation, the same way each browser tab does
    through the frontend.
    """
    if not conversation_id:
        conversation_id = ConversationStore.new_id()

    chal_dilli = _orchestrator()
    if chal_dilli is None:
        return (
            "Still loading Delhi's metro and bus maps - this takes a few "
            "seconds after the Space wakes up. Try again in a moment.",
            conversation_id,
        )

    try:
        result = chal_dilli.get_delhi_response(message, conversation_id)
    except Exception as exc:  # surface the error rather than a blank reply
        return f"Sorry bhai, error aaya: {exc}", conversation_id

    reply = result.get("response", "")
    # Show the same assumption the frontend shows, so a wrong anchor is
    # visible here too.
    if result.get("resolved_context"):
        reply = f"_({result['resolved_context']})_\n\n{reply}"
    return reply, result.get("conversation_id") or conversation_id


def build_ui():
    import gradio as gr

    with gr.Blocks(title="Chal Dilli", fill_height=True) as demo:
        gr.Markdown("# Chal Dilli\n" + DESCRIPTION)
        # Per-visitor conversation id. gr.State is per-session, not global.
        conversation = gr.State(value="")
        # Gradio 6 dropped Chatbot's `type` argument; the openai-style
        # {role, content} message list is the format it takes now.
        chatbot = gr.Chatbot(height=420, show_label=False)
        box = gr.Textbox(
            placeholder="dwarka se cp kaise jaun",
            show_label=False,
            submit_btn=True,
        )
        gr.Examples(examples=EXAMPLES, inputs=box, label="Try")

        def on_submit(message, history, conversation_id):
            history = history or []
            if not message.strip():
                return history, conversation_id, ""
            reply, conversation_id = respond(message, history, conversation_id)
            history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": reply},
            ]
            return history, conversation_id, ""

        box.submit(
            on_submit,
            inputs=[box, chatbot, conversation],
            outputs=[chatbot, conversation, box],
        )

    return demo


def _hand_root_to_gradio(app):
    """Move the API's index listing off "/" so the UI can live there.

    api_server registers `GET /` returning a listing of endpoints, and an
    explicitly registered route always wins over a mounted sub-application --
    so mounting Gradio at "/" without this leaves visitors looking at JSON.
    On a Space, "/" is what people and the Space iframe load.

    Done here rather than in api_server so that running the API on its own
    (`uvicorn backend.api_server:app`) keeps its current behaviour exactly.
    """
    from fastapi.routing import APIRoute

    for route in list(app.router.routes):
        if isinstance(route, APIRoute) and route.path == "/":
            app.router.routes.remove(route)
            # Same handler, still reachable, just not squatting on the root.
            app.add_api_route("/api", route.endpoint, methods=["GET"])
            break


def main():
    import gradio as gr

    _hand_root_to_gradio(fastapi_app)
    # Gradio at the root; /chat, /health and friends are explicit routes on the
    # same app, so they are matched before the mount and keep working.
    #
    # ssr_mode=False is required, not a preference. A Space sets
    # GRADIO_SSR_MODE=true in the environment, and with SSR on, Gradio spawns a
    # Node server that binds mount_gradio_app's server_port -- 7860, the same
    # port we then hand to uvicorn. Node wins the race and uvicorn dies with
    # "[Errno 98] address already in use". Reproduce it locally with:
    #
    #     GRADIO_SSR_MODE=true PORT=7860 python app.py
    #
    # We serve Gradio through our own uvicorn process, so its SSR server has
    # nothing to do here anyway.
    app = gr.mount_gradio_app(fastapi_app, build_ui(), path="/", ssr_mode=False)
    uvicorn.run(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
