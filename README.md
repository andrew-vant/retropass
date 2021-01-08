# Retropass

## An NES password generation tool

Retropass is a library and cli tool for generating passwords for NES-era
video games. Yes, there's quite a few, but I had a few goals not shared
(or at least not satisfied) by existing tools:

1. Retropass is intended to support multiple games.
2. Retropass can be incorporated into other generation tools. If you
   like writing UI's, you don't need to get bogged down in binary to get
   anywhere.
3. Retropass's CLI is easily scriptable, if for whatever reason you want
   that.
4. Retropass ships with machine- and human- readable specifications of
   the password formats. It can be used as a reference when developing
   other programs.

### Status

Still beta. CLI and API details are subject to change. The following
games are supported (so far):

* Mega Man 2
* Metroid
* Kid Icarus
* Solar Jetman

## Installation

1. Install Python 3.6 or above.
2. Install Pip, if needed. On windows platforms, Pip is included in the
   python installation.
3. Run `pip install --user retropass`

## Usage (by players)

Retropass is intended as a library for use by other tools, but it has a
command line interface as well. You feed it a file containing the
options you want, and it generates a password that implements those
options.

`retropass --help` will print the available games and options.

An example, from metroid:

1. Run `retropass metroid --dump > metroid.conf` to create the file.
2. Edit the file to set whatever options you want.
3. Run `retropass metroid --conf metroid.conf`. It will print the corresponding
   password.
4. Enter it in your game of choice and play.

## Usage (by developers)

The API is minimal. There is a Password class. It has subclasses for
each game, and a .make classmethod that creates the appropriate type of
object given the game's name. A list of available names is available via
retropass.Password.supported_games()

The options available for a given password can be set either
attribute-style (`pw.option = 1`) or dictionary-style (`pw['option'] =
1`). You can get the available options and their current settings as a
dictionary with `dict(pw)`, or as a pretty-printed string with
`print(pw.dump())`. Stringifying or printing the password object will
produce the resulting password.

Usage example:

```
from retropass import Password

pw = Password.make('metroid')
pw.has_marumari = 1
pw.has_longbeam = 1
print(pw)
```

## Known Issues

* There's no great way of handling lists of related bits, e.g. all the
  missile containers in Metroid

## Extra Credits

The following links were instrumental, either as documentation or as
reference implementations:

* [Metroid Password Format Guide][mpfg], John Ratliff.
* [True Peace in Space][tpis], Alex Rasmussen.
* [Kid Icarus Password Generator (KIP)][kip], author unknown. Once used the handle "Parasyte" according
  to [archive.org][kiparch].
* StrategyWiki's [Mega Man 2 Password Mechanics][mm2pm] page.
* [Solar Jetman Password Generator][sjpg], CyberN.

[mpfg]: http://games.technoplaza.net/mpg/password.txt
[tpis]: https://www.truepeacein.space
[kip]: http://www.geocities.ws/passgens/pages/Kid_Icarus.htm
[kiparch]: https://web.archive.org/web/20060422233317/http://desnet.fobby.net/index.php?page=utilities&id=19
[sjpg]: https://unoriginal.org/people/cybern/solar_jetman.html
[mm2pm]: https://strategywiki.org/wiki/Mega_Man_2/Password_Mechanics
