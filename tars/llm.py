"""LLM brain: streaming OpenAI chat with the TARS persona, hybrid memory and
the skills registry exposed as tools.

chat_stream() yields text chunks as they are generated, so the speech
pipeline can start talking on the first sentence; tool calls (movement,
timers, vision, ...) are accumulated from the stream and executed between
generation rounds.
"""
import json
import logging
from . import skills
from .config import Settings
from .memory import Memory
from .personality import system_prompt

log = logging.getLogger("tars.llm")

MAX_TOOL_ROUNDS = 5


class Brain:
    def __init__(self, s: Settings, memory: Memory, ctx: skills.SkillContext):
        self.s = s
        self.memory = memory
        self.ctx = ctx
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.s.openai_api_key)
        return self._client

    def chat(self, user_text: str, speaker: str | None = None) -> str:
        return "".join(self.chat_stream(user_text, speaker=speaker))

    def chat_stream(self, user_text: str, speaker: str | None = None):
        """Yield reply text chunks; runs skill calls transparently in between.
        speaker: optional identified speaker name (prefixed into the context)."""
        if not self.s.openai_api_key:
            yield "My cognitive core is offline: no OPENAI_API_KEY configured."
            return

        messages = [{"role": "system", "content": system_prompt(self.s)}]
        kg = self.ctx.extras.get("knowledge")
        if kg is not None:
            facts = kg.search(user_text)
            if facts:
                messages.append({"role": "system",
                                 "content": "Known facts possibly relevant now:\n"
                                            + kg.render(facts)})
        messages += self.memory.context_messages(query=user_text)
        user_content = f"[{speaker} is speaking] {user_text}" if speaker else user_text
        messages.append({"role": "user", "content": user_content})
        self.memory.add_turn("user", user_content)

        reply_parts = []
        try:
            for _ in range(MAX_TOOL_ROUNDS):
                content, tool_calls = yield from self._stream_round(messages, reply_parts)
                if not tool_calls:
                    break
                messages.append({"role": "assistant", "content": content or None,
                                 "tool_calls": tool_calls})
                for tc in tool_calls:
                    name = tc["function"]["name"]
                    args = json.loads(tc["function"]["arguments"] or "{}")
                    log.info("skill call: %s(%s)", name, args)
                    result = skills.run(name, args, self.ctx)
                    messages.append({"role": "tool", "tool_call_id": tc["id"],
                                     "content": result})
        except Exception as e:
            log.exception("LLM stream failed")
            yield f"Cognitive fault: {e}"
        finally:
            reply = "".join(reply_parts).strip()
            if reply:
                self.memory.add_turn("assistant", reply)

    def _stream_round(self, messages: list, reply_parts: list):
        """One streamed completion. Yields content chunks; returns
        (content, tool_calls) where tool_calls is in API message format."""
        stream = self.client.chat.completions.create(
            model=self.s.openai_model, messages=messages,
            tools=skills.tool_schemas(), max_tokens=500, stream=True)

        content = ""
        calls: dict[int, dict] = {}
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                content += delta.content
                reply_parts.append(delta.content)
                yield delta.content
            for tc in delta.tool_calls or []:
                slot = calls.setdefault(tc.index, {
                    "id": "", "type": "function",
                    "function": {"name": "", "arguments": ""}})
                if tc.id:
                    slot["id"] = tc.id
                if tc.function and tc.function.name:
                    slot["function"]["name"] += tc.function.name
                if tc.function and tc.function.arguments:
                    slot["function"]["arguments"] += tc.function.arguments
        return content, [calls[i] for i in sorted(calls)]
