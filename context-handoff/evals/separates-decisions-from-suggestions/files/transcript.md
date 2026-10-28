User: I'm building a desk display that shows my API usage. Pico W + a 16x2 I2C LCD.
Assistant: Nice. Two options for the data path: (a) the Pico polls the API directly over Wi-Fi, or (b) a small Python daemon on your PC polls and pushes to the Pico over USB serial. I'd lean (b) since it keeps credentials off the microcontroller.
User: yeah do (b), I don't want keys on the Pico.
Assistant: Good. For the daemon I'd suggest asyncio with a 60s poll interval, and maybe a SQLite cache so you can graph history later.
User: hmm maybe. let's just get the poll working first.
Assistant: Here's daemon.py (wrote it to ~/projects/pico-monitor/daemon/daemon.py). It reads the token from the USAGE_TOKEN environment variable and prints usage JSON.
User: ran it, got a 401.
Assistant: The endpoint expects "Authorization: Bearer <token>" — you were sending the raw token. Fixed in daemon.py line 22.
User: works now, prints JSON. Next I need the serial bridge. I'm on WSL2 so COM ports are a pain.
Assistant: On WSL2 you can either use usbipd-win to attach the device into Linux, or run a tiny bridge script on Windows. usbipd is cleaner.
User: I'll decide tomorrow. Also the LCD is 16x2, so keep messages under 16 chars per line.
