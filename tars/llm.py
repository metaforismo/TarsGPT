"""LLM brain: OpenAI chat with the TARS persona, memory and movement tool-calling."""
import json
import logging
from .config import Settings
from .memory import Memory
from .personality import system_prompt

log = logging.getLogger("tars.llm")

TOOLS = [
    {"type": "function", "function": {
        "name": "move",
        "description": "Move the robot body. Use when the user asks you to walk, turn or pose.",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string",
                       "enum": ["step_forward", "turn_left", "turn_right", "pose", "neutral"]},
            "repeat": {"type": "integer", "minimum": 1, "maximum": 10, "default": 1},
        }, "required": ["action"]}}},
    {"type": "function", "function": {
        "name": "remember",
        "description": "Store a fact about the user or the world in long-term memory.",
        "parameters": {"type": "object", "properties": {
            "note": {"type": "string"}}, "required": ["note"]}}},
    {"type": "function", "function": {
        "name": "set_personality",
        "description": "Adjust your own humor/honesty/sarcasm settings (0-100) when asked.",
        "parameters": {"type": "object", "properties": {
            "humor": {"type": "integer"}, "honesty": {"type": "integer"},
            "sarcasm": {"type": "integer"}}}}},
]


class Brain:
    def __init__(self, s: Settings, memory: Memory, gaits=None):
        self.s = s
        self.memory = memory
        self.gaits = gaits
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.s.openai_api_key)
        return self._client

    def chat(self, user_text: str) -> str:
        if not self.s.openai_api_key:
            return "My cognitive core is offline: no OPENAI_API_KEY configured."
        self.memory.add_turn("user", user_text)
        messages = [{"role": "system", "content": system_prompt(self.s)}]
        messages += self.memory.context_messages()

        try:
            for _ in range(4):  # allow a few rounds of tool calls
                resp = self.client.chat.completions.create(
                    model=self.s.openai_model, messages=messages,
                    tools=TOOLS, max_tokens=400)
                msg = resp.choices[0].message
                if not msg.tool_calls:
                    reply = (msg.content or "").strip()
                    self.memory.add_turn("assistant", reply)
                    return reply
                messages.append({"role": "assistant", "content": msg.content,
                                 "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
                for tc in msg.tool_calls:
                    result = self._run_tool(tc.function.name,
                                            json.loads(tc.function.arguments or "{}"))
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            return "Tool loop limit reached. That's on me."
        except Exception as e:
            log.exception("LLM call failed")
            return f"Cognitive fault: {e}"

    def _run_tool(self, name: str, args: dict) -> str:
        if name == "move":
            if self.gaits is None:
                return "error: no servo hardware attached"
            action = args.get("action", "neutral")
            for _ in range(int(args.get("repeat", 1))):
                getattr(self.gaits, action)()
            return f"ok: executed {action}"
        if name == "remember":
            self.memory.add_note(args.get("note", ""))
            return "ok: stored"
        if name == "set_personality":
            for key in ("humor", "honesty", "sarcasm"):
                if key in args and args[key] is not None:
                    setattr(self.s, key, max(0, min(100, int(args[key]))))
            self.s.save()
            return (f"ok: humor={self.s.humor} honesty={self.s.honesty} "
                    f"sarcasm={self.s.sarcasm}")
        return "error: unknown tool"
