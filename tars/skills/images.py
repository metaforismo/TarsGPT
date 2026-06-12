"""Image generation skill: pictures saved locally and shown in the dashboard."""
import base64
import time
from . import skill
from ..config import DATA_DIR

IMAGES_DIR = DATA_DIR / "images"


@skill("generate_image",
       "Generate an image from a text description. The image is saved and "
       "shown in the dashboard; include its /images/... path in your reply.",
       {"type": "object", "properties": {"prompt": {"type": "string"}},
        "required": ["prompt"]})
def generate_image(ctx, prompt):
    if not ctx.settings.openai_api_key:
        return "error: image generation requires an OpenAI API key"
    from openai import OpenAI
    client = OpenAI(api_key=ctx.settings.openai_api_key)
    resp = client.images.generate(model="dall-e-3", prompt=prompt[:900],
                                  size="1024x1024", response_format="b64_json", n=1)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    name = f"img-{int(time.time())}.png"
    (IMAGES_DIR / name).write_bytes(base64.b64decode(resp.data[0].b64_json))
    return f"ok: image created at /images/{name} - mention that exact path in your reply"
