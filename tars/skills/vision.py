"""Vision skill: capture a camera frame and describe it with a multimodal LLM.

Tries the Raspberry Pi camera tools first, then any USB webcam via OpenCV.
"""
import base64
import shutil
import subprocess
import tempfile
from . import skill


def capture() -> str | None:
    """Grab one camera frame to a jpg; tries Pi camera tools then OpenCV.
    Shared with the gait optimizer's camera reward."""
    path = tempfile.mktemp(suffix=".jpg", prefix="tars_eye_")
    for tool, args in (("rpicam-still", ["-n", "--immediate", "-o"]),
                       ("libcamera-still", ["-n", "--immediate", "-o"]),
                       ("fswebcam", ["--no-banner"])):
        if shutil.which(tool):
            result = subprocess.run([tool, *args, path], capture_output=True, timeout=20)
            if result.returncode == 0:
                return path
    try:
        import cv2
        cam = cv2.VideoCapture(0)
        ok, frame = cam.read()
        cam.release()
        if ok:
            cv2.imwrite(path, frame)
            return path
    except ImportError:
        pass
    return None


@skill("look",
       "Look through your camera and describe what you see. Optionally focus on a question.",
       {"type": "object", "properties": {
           "question": {"type": "string",
                        "description": "optional: what to look for or answer about the scene"}}})
def look(ctx, question=""):
    if not ctx.settings.openai_api_key:
        return "error: vision requires an OpenAI API key"
    path = capture()
    if path is None:
        return "error: no camera available"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    from openai import OpenAI
    client = OpenAI(api_key=ctx.settings.openai_api_key)
    prompt = question or "Describe what you see, briefly, from a robot's point of view."
    resp = client.chat.completions.create(
        model=ctx.settings.openai_model, max_tokens=200,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}}]}])
    return resp.choices[0].message.content or "I see nothing of note."
