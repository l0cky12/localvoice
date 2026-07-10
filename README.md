# LocalVoice

LocalVoice is a local-only desktop dictation application for **Hyprland on Wayland**. It records with PipeWire, transcribes with `faster-whisper`, copies with `wl-copy`, restores the previously focused Hyprland window, and pastes without placing transcription text in shell arguments.

No GNOME, KDE, Sway, X11, cloud API, transcription history, or recording archive support is included. Audio is held in a private temporary directory and removed after transcription.

## Paste and clipboard behavior (and its limits)

On success LocalVoice copies the transcription to the clipboard, focuses the
window that was active when recording began, and sends the configured paste
shortcut (default Ctrl+V) **to that specific window**. If the window has
disappeared or the shortcut cannot be delivered, the transcription is left on
the clipboard so you can paste it manually. Either way the result is never
silently discarded.

Before overwriting the clipboard, LocalVoice snapshots your existing **text**
clipboard and restores it after a successful paste. This restoration is
best-effort: Wayland provides no signal that a paste has completed, so a short
settle delay is used, and only `text/plain` content is preserved — images and
other MIME types on the clipboard are not snapshotted.

**Text-field detection limitation.** Wayland deliberately isolates clients, and
Hyprland exposes no accessibility API to report whether the focused control is a
writable text box (or a password field). LocalVoice therefore cannot verify the
paste destination beyond confirming the target window still exists. Do not use
push-to-talk while a password or other secure field is focused; prefer the
clipboard and paste manually in that case.

## Native installation (recommended)

Requirements: Python 3.12+, Hyprland, PipeWire (`pw-record`, `pw-play`, `wpctl`), `wl-clipboard`, and optionally Piper.

```bash
python3 -m venv ~/.local/share/localvoice/venv
~/.local/share/localvoice/venv/bin/pip install .
mkdir -p ~/.local/bin
ln -sf ~/.local/share/localvoice/venv/bin/localvoice ~/.local/bin/localvoice
localvoice doctor
localvoice hyprland-config
```

Source `~/.config/hypr/localvoice.conf` from your main Hyprland configuration yourself. LocalVoice never edits the main file.

```ini
source = ~/.config/hypr/localvoice.conf
```

Default PTT is Ctrl+Alt+Space. The GUI also provides toggle and continuous modes. Models are downloaded by `faster-whisper` on first use unless `LOCALVOICE_MODEL` points to an existing local model directory. Inference is always local.

## CLI

```text
localvoice [--gui]
localvoice doctor
localvoice clipboard-test
localvoice hyprland-test
localvoice hyprland-config
localvoice ptt-start|ptt-stop|toggle|start|stop|continuous-start|continuous-stop
```

`clipboard-test` copies a fixed non-private test string. `hyprland-test` reports compositor state but never emits window titles.

## Configuration

Optional personal configuration is read from `~/.config/localvoice/config.toml` and is ignored by Git. Supported environment overrides: `LOCALVOICE_MODEL`, `LOCALVOICE_COMPUTE_TYPE`, and `LOCALVOICE_LANGUAGE`.

```toml
model = "small.en"
compute_type = "int8"
language = "en"
input_device = ""
output_device = ""
paste_modifiers = "CTRL"
paste_key = "V"
```

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/mypy src/localvoice
python -m build
```

## Docker

Native installation is recommended because containers require explicit Wayland, PipeWire, and runtime socket mounts. The Compose file runs unprivileged and grants no blanket device access. Review and adjust UID/GID and socket paths before use. Never use `--privileged`.
