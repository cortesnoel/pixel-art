<h1 align="center">Basic</h1>
<br>

<p align="center">
  Game plugin for the Basic game.
</p>
<p align="center">
  Move a pixel on the screen by directional voice commands.
</p>

<br>
<p align="center">
  <img src="https://github.com/user-attachments/assets/560a5424-80d7-421b-b8e7-a849cf8c079f" alt="gameplay" title="gameplay" width="128" height="128"/>
</p>

## Requirements

### Hardware

The following Pixel Art I/O hardware is required to support this plugin: `microphone`.

### API Keys

The following API keys must be set as system environment variables:

- [Picovoice](https://console.picovoice.ai/signup#free): `PICOVOICE_TOKEN`

## Plugins

1. [play](#play)

---

### `play`

Launch the Basic game by running the main game loop. 

#### Controls

##### Voice Controller

This game uses the `stt` voice controller which uses the Picovoice [Leopard](https://picovoice.ai/docs/leopard/) AI model to transcribe speech and parse out directional commands.
Say `quit` to end the game early.

Voice commands allowed: `up`, `down`, `left`, `right`, `quit`

⚠️ **Note**: The voice controllers are *WIP* and may have a high error rate, especially for smaller words like `up`. 

#### Rules

1. pixel moves one space in the direction of voice command (e.g., `up`)
1. game `runtime` is set in [plugin.toml](plugin.toml)
1. say `quit` to end game before `runtime` completes

#### Usage

Pair with the Display Image [display_game](../../rgb/display_image/README.md#display_game) RGB plugin.

##### Steps

1. Set in Pixel Art's [config.toml](../../../config.toml):
```toml
[plugins]

ai = [
  # basic game
  "basic.BasicGame.play" # this plugin
]

rgb = [
  # basic game
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
