# IdleZ - A zombie idle game for Discord

## Usage

`idlez` provides a Discord bot which handles the idle game.
The game channel on any Discord server is called `#idlez`. The bot only reacts to messages posted in that channel.

### Running the bot

The python module provides an executable called `idlez`.
Use the `--help` flag to see a list of options. These are:

```
usage: idlez [-h] [--token-file TOKEN_FILE] [--data-dir DATA_DIR] [--env-file ENV_FILE]

idleZ bot

options:
  -h, --help            show this help message and exit
  --token-file TOKEN_FILE
                        A file containing a single line with the token
  --data-dir DATA_DIR   The path to the directory which is used to store data
  --env-file ENV_FILE   Read env variables from the given file, if provided.
```

The `idlez` executable starts the discord bot. It needs a discord bot token
which is read either from the given `TOKEN_FILE` or from the `IDLEZ_TOKEN`
environment variable. If `ENV_FILE` is given, the environment variables are
loaded from the given file before reading the token from `IDLEZ_TOKEN`.

### Nix

We provide a nix flake which exposes the `idlez` package for all default systems.
### NixOS

We provide a NixOS module in `nixos-module.nix` and via the flake.
The options with their defaults are:

* `services.idlez.enable = false`
* `services.idlez.dataDir = "/var/lib/idlez"`
* `services.idlez.tokenFile = "/private/idlez.token"`

# License

Copyright (C) 2023  Wanja Chresta

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

