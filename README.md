# Maze Lock

> Simple local multiplayer maze/lock demo (server + two clients).

This repository contains a small Python-based demo with a server and two client variants: a text client and a Pygame-based graphical client.

Prerequisites
- Python 3.8 or newer
- Optional: `pygame` (only required to run `client_pygame.py`)

Install optional dependency (recommended for graphical client):

```powershell
pip install pygame
```

Quick start

1. Start the server in a terminal:

```powershell
python server.py
```

2. Start a text client in another terminal:

```powershell
python client.py
```

3. (Optional) Start the graphical client in a separate terminal:

```powershell
python client_pygame.py
```

4. There may be a `main.py` launcher or demo harness—run it directly if provided:

```powershell
python main.py
```

Files
- `server.py`: the server process — accepts client connections and coordinates the demo.
- `client.py`: a simple text-based client.
- `client_pygame.py`: a graphical client using Pygame (optional dependency).
- `main.py`: launcher / demo entrypoint (may orchestrate server+clients locally).

Notes
- These scripts are intended as a small demo. They assume a local network/loopback environment.
- If you see import errors, confirm you're using the correct Python version and that optional packages (like `pygame`) are installed.

Contributing
- Feel free to open issues or PRs. Keep changes focused and add tests/examples where helpful.

License
- Add your preferred license (no license file included by default).

Questions or changes?
- Tell me if you want the README expanded with protocol details, example screenshots, or a `requirements.txt`.
