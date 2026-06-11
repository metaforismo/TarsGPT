"""Music skill: internet radio and local files through mpv."""
import shutil
import subprocess
from pathlib import Path
from . import skill

STATIONS = {
    "lofi": "https://play.streamafrica.net/lofiradio",
    "jazz": "https://stream.zeno.fm/0r0xa792kwzuv",
    "classical": "https://live.musopen.org:8085/streamvbr0",
    "synthwave": "https://stream.nightride.fm/nightride.mp3",
}

_player: dict = {"proc": None, "what": None}


def _stop():
    proc = _player["proc"]
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    _player["proc"] = None
    _player["what"] = None


@skill("play_music",
       "Play music: a named radio station (lofi, jazz, classical, synthwave), "
       "a direct stream URL, or a local file name from the music folder.",
       {"type": "object", "properties": {"what": {"type": "string"}},
        "required": ["what"]})
def play_music(ctx, what):
    player = shutil.which("mpv") or shutil.which("mpg123")
    if not player:
        return "error: no audio player installed (install mpv)"

    target = STATIONS.get(what.lower().strip())
    if target is None and what.startswith(("http://", "https://")):
        target = what
    if target is None:
        music_dir = Path(ctx.settings.music_dir).expanduser()
        matches = sorted(music_dir.glob(f"*{what}*")) if music_dir.is_dir() else []
        if matches:
            target = str(matches[0])
    if target is None:
        return (f"error: unknown station/file '{what}'. "
                f"Stations: {', '.join(STATIONS)}")

    _stop()
    args = [player, "--no-video", "--really-quiet", target] if "mpv" in player \
        else [player, "-q", target]
    _player["proc"] = subprocess.Popen(args, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
    _player["what"] = what
    return f"ok: playing {what}"


@skill("stop_music", "Stop any music that is currently playing.")
def stop_music(ctx):
    if _player["proc"] is None or _player["proc"].poll() is not None:
        return "nothing is playing"
    what = _player["what"]
    _stop()
    return f"ok: stopped {what}"
