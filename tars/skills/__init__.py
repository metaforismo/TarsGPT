"""Skills: drop-in plugins that become LLM tools automatically.

A skill is a function decorated with @skill in any module inside this package
(or any module you add). On startup every module here is imported and each
skill is exposed to the LLM as a callable tool.

    from tars.skills import skill

    @skill("weather", "Get the current weather for a city",
           {"type": "object", "properties": {"city": {"type": "string"}},
            "required": ["city"]})
    def weather(ctx, city):
        return f"Sunny in {city}."

The handler receives a SkillContext (settings, memory, gaits, scheduler,
speaker) and returns a string for the LLM. Raise nothing: return error text.
"""
import importlib
import inspect
import logging
import pkgutil
from dataclasses import dataclass, field
from typing import Callable

log = logging.getLogger("tars.skills")

REGISTRY: dict[str, "Skill"] = {}


@dataclass
class Skill:
    name: str
    description: str
    parameters: dict
    handler: Callable


@dataclass
class SkillContext:
    settings: object = None
    memory: object = None
    gaits: object = None
    scheduler: object = None
    speaker: object = None
    extras: dict = field(default_factory=dict)

    def say(self, text: str):
        """Proactive speech (e.g. a timer going off). Safe without a speaker."""
        if self.speaker is not None:
            self.speaker.say(text)
        else:
            log.info("(mute) %s", text)


def skill(name: str, description: str, parameters: dict | None = None):
    def decorator(fn):
        REGISTRY[name] = Skill(name, description,
                               parameters or {"type": "object", "properties": {}}, fn)
        return fn
    return decorator


def load_skills() -> dict[str, Skill]:
    """Import every module in this package so their @skill decorators run."""
    for mod in pkgutil.iter_modules(__path__):
        if mod.name.startswith("_"):
            continue
        try:
            importlib.import_module(f"{__name__}.{mod.name}")
        except Exception:
            log.exception("failed to load skill module %s", mod.name)
    log.info("skills loaded: %s", ", ".join(sorted(REGISTRY)) or "(none)")
    return REGISTRY


def tool_schemas() -> list[dict]:
    return [{"type": "function",
             "function": {"name": s.name, "description": s.description,
                          "parameters": s.parameters}}
            for s in REGISTRY.values()]


def run(name: str, args: dict, ctx: SkillContext) -> str:
    s = REGISTRY.get(name)
    if s is None:
        return f"error: unknown skill {name}"
    try:
        # validate the call shape up front, so a TypeError raised *inside*
        # the handler is reported as a crash, not as bad arguments
        inspect.signature(s.handler).bind(ctx, **args)
    except TypeError as e:
        return f"error: bad arguments for {name}: {e}"
    try:
        return str(s.handler(ctx, **args))
    except Exception as e:
        log.exception("skill %s crashed", name)
        return f"error: {name} failed: {e}"
