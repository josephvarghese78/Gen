import asyncio
import os

from copilot import CopilotClient
from copilot.session import PermissionHandler
from copilot.session_events import (
    AssistantMessageData,
    AssistantReasoningData,
    ToolExecutionStartData,
)

BLUE = "\033[34m"
RESET = "\033[0m"

# ── Resolve a GitHub Copilot token ──────────────────────────────────────────
# The bundled Copilot CLI requires authentication for every session.
# Priority (matches `copilot login --help`):
#   1. COPILOT_GITHUB_TOKEN env var
#   2. GH_TOKEN env var
#   3. GITHUB_TOKEN env var
#   4. .copilot_oauth_token file next to this script (created by
#      list_copilot_models.py via GitHub device flow)
_HERE = os.path.dirname(os.path.abspath(__file__))

def _load_token() -> str:
    for env in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        v = os.environ.get(env, "").strip()
        if v:
            return v
    cached = os.path.join(_HERE, ".copilot_oauth_token")
    if os.path.exists(cached):
        return open(cached).read().strip()
    return ""

GITHUB_TOKEN = _load_token()
if not GITHUB_TOKEN:
    raise SystemExit(
        "No Copilot token found. Either:\n"
        "  - run `python list_copilot_models.py` once (creates .copilot_oauth_token), OR\n"
        "  - set COPILOT_GITHUB_TOKEN=<your-token> in the environment.\n"
        "Supported token types: fine-grained PAT with 'Copilot Requests' permission,\n"
        "OAuth from the Copilot CLI app, or OAuth from the gh CLI app.\n"
        "Classic ghp_ PATs are NOT supported."
    )


async def main():
    client = CopilotClient()
    await client.start()
    session = await client.create_session(
        on_permission_request=PermissionHandler.approve_all,
        github_token=GITHUB_TOKEN,       # ← REQUIRED for session-mode auth
    )

    def on_event(event):
        output = None
        match event.data:
            case AssistantReasoningData() as data:
                output = f"[reasoning: {data.content}]"
            case ToolExecutionStartData() as data:
                output = f"[tool: {data.tool_name}]"
        if output:
            print(f"{BLUE}{output}{RESET}")

    session.on(on_event)

    print("Chat with Copilot (Ctrl+C to exit)\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        print()

        reply = await session.send_and_wait(user_input)
        assistant_output = None
        if reply:
            match reply.data:
                case AssistantMessageData() as data:
                    assistant_output = data.content
        print(f"\nAssistant: {assistant_output}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye!")