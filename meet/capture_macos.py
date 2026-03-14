"""macOS audio capture module using AVFoundation via ffmpeg.

Captures dual-channel audio: microphone (your voice) on one channel,
system audio (via BlackHole virtual audio driver) on the other.

Prerequisites:
- ffmpeg: brew install ffmpeg
- BlackHole: brew install blackhole-2ch
- Audio MIDI Setup: Create a Multi-Output Device combining your speakers + BlackHole
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from meet.capture import AudioDevice, RecordingSession


# ─── Device discovery ────────────────────────────────────────────────────────


@dataclass
class MacOSAudioDevice:
    """Represents a macOS audio device discovered via AVFoundation."""

    index: int
    name: str
    device_type: str  # "audio" or "video"

    @property
    def is_monitor(self) -> bool:
        """BlackHole acts as the macOS equivalent of a PulseAudio monitor."""
        return "blackhole" in self.name.lower()


def _list_avfoundation_devices() -> list[MacOSAudioDevice]:
    """List all AVFoundation devices by parsing ffmpeg output."""
    result = subprocess.run(
        ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
        capture_output=True, text=True,
    )
    # ffmpeg prints device list to stderr (the command itself fails with exit 1)
    output = result.stderr

    devices = []
    current_type = None
    for line in output.split("\n"):
        if "AVFoundation video devices:" in line:
            current_type = "video"
        elif "AVFoundation audio devices:" in line:
            current_type = "audio"
        elif current_type:
            match = re.search(r"\[(\d+)\]\s+(.+)", line)
            if match:
                idx = int(match.group(1))
                name = match.group(2).strip()
                devices.append(MacOSAudioDevice(
                    index=idx, name=name, device_type=current_type,
                ))

    return devices


# ─── Module-level helpers (replace PulseAudio equivalents) ────────────────────


def list_sources() -> list[AudioDevice]:
    """List all macOS audio input devices.

    Returns AudioDevice objects for compatibility with the existing CLI.
    """
    macos_devices = _list_avfoundation_devices()
    devices = []
    for dev in macos_devices:
        if dev.device_type == "audio":
            devices.append(AudioDevice(
                index=dev.index,
                name=dev.name,
                driver="avfoundation",
                sample_spec="",
                state="RUNNING",
            ))
    return devices


def get_default_source() -> str:
    """Get the default microphone device index as a string."""
    devices = _list_avfoundation_devices()
    audio_devices = [d for d in devices if d.device_type == "audio"]

    # Prefer built-in microphone
    for dev in audio_devices:
        if "built-in" in dev.name.lower() or "microphone" in dev.name.lower():
            return str(dev.index)

    # Fall back to first audio device that isn't BlackHole or Multi-Output
    for dev in audio_devices:
        lower = dev.name.lower()
        if "blackhole" not in lower and "multi-output" not in lower:
            return str(dev.index)

    if audio_devices:
        return str(audio_devices[0].index)

    raise RuntimeError("No audio input devices found")


def get_blackhole_source() -> str | None:
    """Find the BlackHole audio device index, or None if not installed."""
    devices = _list_avfoundation_devices()
    for dev in devices:
        if dev.device_type == "audio" and "blackhole" in dev.name.lower():
            return str(dev.index)
    return None


def get_monitor_source() -> str:
    """Get the system audio monitor source (BlackHole device index)."""
    bh = get_blackhole_source()
    if bh is None:
        raise RuntimeError(
            "BlackHole not found. Install with: brew install blackhole-2ch\n"
            "Then create a Multi-Output Device in Audio MIDI Setup."
        )
    return bh


def get_default_sink() -> str:
    """Get the default output device name (for display purposes)."""
    devices = _list_avfoundation_devices()
    audio_devices = [d for d in devices if d.device_type == "audio"]
    for dev in audio_devices:
        lower = dev.name.lower()
        if "speaker" in lower or ("built-in" in lower and "output" in lower):
            return dev.name
    for dev in audio_devices:
        if "macbook" in dev.name.lower():
            return dev.name
    return "Default Output"


# ─── macOS Recording Session ─────────────────────────────────────────────────


class MacOSRecordingSession(RecordingSession):
    """Recording session using AVFoundation audio capture on macOS.

    Subclasses RecordingSession, overriding only the platform-specific parts:
    - ffmpeg command construction (AVFoundation instead of PulseAudio)
    - Virtual sink management (not needed on macOS — BlackHole serves this role)
    """

    def _build_ffmpeg_cmd(self, output_path: Path) -> list[str]:
        """Build ffmpeg command for macOS dual-channel recording.

        Uses -f avfoundation instead of -f pulse. The mic_source and
        _actual_monitor fields should be AVFoundation device indices.
        """
        return [
            "ffmpeg",
            "-y",
            # Mic input (AVFoundation audio device by index)
            "-f", "avfoundation",
            "-i", f":{self.mic_source}",
            # System audio input (BlackHole device by index)
            "-f", "avfoundation",
            "-i", f":{self._actual_monitor}",
            # Merge into 2-channel stereo (left=mic, right=system)
            "-filter_complex",
            "[0:a]aformat=sample_fmts=s16:sample_rates=16000:channel_layouts=mono[mic];"
            "[1:a]aformat=sample_fmts=s16:sample_rates=16000:channel_layouts=mono[sys];"
            "[mic][sys]amerge=inputs=2[out]",
            "-map", "[out]",
            "-ac", "2",
            "-ar", "16000",
            # Flush packets for reliable watchdog + clean shutdown
            "-flush_packets", "1",
            "-c:a", "pcm_s16le",
            str(output_path),
        ]

    def _setup_virtual_sink(self) -> str:
        """No-op on macOS — BlackHole serves as the virtual audio sink."""
        return self._actual_monitor

    def _teardown_virtual_sink(self) -> None:
        """No-op on macOS."""
        pass


# ─── Session factory ─────────────────────────────────────────────────────────


def create_session(
    output_dir=None,
    filename=None,
    mic=None,
    monitor=None,
    virtual_sink=False,
) -> MacOSRecordingSession:
    """Create a new macOS recording session.

    Args:
        output_dir: Directory to save recordings. Defaults to ~/meet-recordings.
        filename: Output filename. Defaults to timestamped name.
        mic: Mic device index as string. Defaults to system default.
        monitor: System audio device index (BlackHole). Defaults to auto-detect.
        virtual_sink: Ignored on macOS (BlackHole replaces virtual sinks).

    Returns:
        A MacOSRecordingSession ready to start.
    """
    if output_dir is None:
        output_dir = Path.home() / "meet-recordings"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        session_name = f"meeting-{timestamp}"
        session_dir = output_dir / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{session_name}.wav"
        output_dir = session_dir

    mic_source = mic or get_default_source()
    monitor_source = monitor or get_monitor_source()

    return MacOSRecordingSession(
        output_dir=output_dir,
        output_file=output_dir / filename,
        mic_source=mic_source,
        monitor_source=monitor_source,
        use_virtual_sink=False,  # Not applicable on macOS
    )


# ─── Prerequisites check ─────────────────────────────────────────────────────


def check_prerequisites() -> list[str]:
    """Check macOS-specific prerequisites for audio capture."""
    issues = []

    # Check ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        issues.append("ffmpeg is not installed. Install with: brew install ffmpeg")

    # Check for BlackHole
    try:
        bh = get_blackhole_source()
    except Exception:
        bh = None

    if bh is None:
        issues.append(
            "BlackHole virtual audio driver not found.\n"
            "    Install with: brew install blackhole-2ch\n"
            "    Then set up a Multi-Output Device in Audio MIDI Setup:\n"
            "    1. Open /Applications/Utilities/Audio MIDI Setup.app\n"
            "    2. Click '+' at bottom left -> Create Multi-Output Device\n"
            "    3. Check both your speakers/headphones AND BlackHole 2ch\n"
            "    4. Set the Multi-Output Device as your system output"
        )

    return issues
