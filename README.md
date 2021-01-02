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

## Known Issues

* The alpha currently only supports Metroid. I started there because
  it's the best-documented format, and I could test my results against
  existing generators.
* No great way of handling lists of related bits, e.g. all the missile
  containers in Metroid

## Extra Credits

I used the following as documentation or reference implementations:

* John Ratliff's [Metroid Password Format Guide][mpfg].
* Alex Rasmussen's [True Peace in Space][tpis] generator.

[mpfg]: http://games.technoplaza.net/mpg/password.txt
[tpis]: https://www.truepeacein.space
