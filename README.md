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
   the password formats.

That last is perhaps the most important. One of the most frustrating
things about romhacking is the lack of good documentation of games'
internal data structures. Retropass gives you that "for free"; it is
impossible to add support for a game without simultaneously documenting
most of its password structure.

### Status

Still beta. CLI and API details are subject to change.

## Installation

1. Install Python 3.6 or above.
2. Install Pip, if needed. On windows platforms, Pip is included in the
   python installation.
3. Run `pip install --user retropass`

## CLI Usage

Retropass is intended as a library for use by other tools, but it has a
command line interface as well. You feed it a file containing the
options you want, and it generates a password that implements those
options:

1. Run `retropass metroid --dump > metroid.conf` to create the file.
2. Edit the file to set whatever options you want.
3. Run `retropass metroid metroid.conf`. It will print the corresponding
   password.

## Usage as a library

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

* So far only Metroid is supported. I started there because
  it's the best-documented format, and I could test my results against
  existing generators.
* There's no great way of handling lists of related bits, e.g. all the
  missile containers in Metroid

## Extra Credits

I used the following as documentation or reference implementations:

* John Ratliff's [Metroid Password Format Guide][mpfg].
* Alex Rasmussen's [True Peace in Space][tpis] generator.

[mpfg]: http://games.technoplaza.net/mpg/password.txt
[tpis]: https://www.truepeacein.space
