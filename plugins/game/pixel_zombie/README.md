<h1 align="center">Pixel Zombie</h1>
<br>

<p align="center">
  Game plugin for the Pixel Zombie game.
</p>
<p align="center">
  You are now a Pixel Zombie!
  Grow you zombie horde (🟩) by eating humans (⬜️) and avoiding zombie hunters (🟥).
</p>

<br>
<p align="center">
  <img src="https://github.com/user-attachments/assets/253deb56-ef8e-4581-84c0-5dc97827ae95" alt="gameplay" title="gameplay" width="128" height="128"/>
</p>

## Requirements

### Hardware

The following Pixel Art I/O hardware is required to support this plugin: `speaker`, `SNES-style USB controller`.

## Plugins

1. [play](#play)

---

### `play`

Launch the Pixel Zombie game by running the main game loop. 

#### Controls

##### SNES Controller

This game uses the [SNES-style USB controller](https://www.adafruit.com/product/6285?gad_source=1&gad_campaignid=21079227318&gbraid=0AAAAADx9JvRGD68sbyMjjhT1Fhrceg537&gclid=Cj0KCQjw2IDFBhDCARIsABDKOJ4L4NV8xEHM87qcGoungttUBP52k7LBaVILXLBm_HZ6mZ135SE3yC4aAudfEALw_wcB).

Controls allowed: `D-Pad`, `Start`, `B`

#### Rules

1. move zombie horde using the D-Pad
1. zombie horde eats 1 human on pixel collision 
1. hunter destroys 1 zombie from horde on pixel collision 
1. zombie horde's pixel dimensions grow every 3 humans eaten
1. humans run away from zombie horde when close enough for detection
1. hunters continually chase zombie horde
1. hunter freezes for a short time after destroying 1 zombie from zombie horde
1. as levels increase, humans can detect zombie horde from longer distances
1. as levels increase, humans and hunters get faster
1. win level by eating all humans
1. game ends when hunters reduce zombie horde to zero

#### Usage

Pair with the Display Image [display_game](../../rgb/display_image/README.md#display_game) RGB plugin.

Along with gameplay, the screen displays level number (ex. "L1") and zombie horde size (ex. "H25").

##### Steps

1. Set in Pixel Art's [config.toml](../../../config.toml):
```toml
[plugins]

ai = [
  # pixel zombie game
  "pixel_zombie.PixelZombieGame.play" # this plugin
]

rgb = [
  # pixel zombie game
  "display_image_plugins.DisplayImagePlugins.display_game",
]
```
2. Launch or restart Pixel Art
3. `play`: Play game

---

## Configuration

Plugin configurations can be set in [plugin.toml](plugin.toml).

## Troubleshoot

TBD

## License

[MIT](LICENSE)
