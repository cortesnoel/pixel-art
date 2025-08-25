<h1 align="center">Random Pixel</h1>
<br>
<p align="center">RGB Plugin to display randomized patterns on the Pixel Art screen.</p>

<br>
<p align="center">
  <img src="assets/examples/pixel.gif" alt="pixel.gif" title="pixel.gif" width="128" height="128"/>
  <img src="assets/examples/heart.gif" alt="heart.gif" title="heart.gif" width="128" height="128" hspace="10"/>
  <img src="assets/examples/smiley.gif" alt="smiley.gif" title="smiley.gif" width="128" height="128" hspace="20"/>
  <img src="assets/examples/snake.gif" alt="snake.gif" title="snake.gif" width="128" height="128" hspace="30"/>
</p>

## Requirements

Basic build of Pixel Art.

Reference your chosen AI or game plugin(s) for additional requirements.

## Plugins

1. [display_pixel_rand](#display_pixel_rand)
1. [display_heart_rand](#display_heart_rand)
1. [display_smiley_rand](#display_smiley_rand)
1. [display_snake_rand](#display_snake_rand)

---

### `display_pixel_rand`

Display colored pixel(s) randomly on the Pixel Art screen.

#### Usage

Pair with an AI plugin meant for background tasks. This plugin doesn't use any value from the `ai_result_queue`.

For example, pair with the Retro Diffusion [rd_wake](../../ai/retro_diffusion/README.md#rd_wake) AI plugin.

##### Steps

1. Set in Pixel Art's [config.toml](../../../config.toml):
```toml
[plugins]

ai = [
  # retro diffusion
  "retro_diffusion_plugins.RetroDiffusionPlugins.rd_wake"
]

rgb = [
  # retro diffusion
  "random_pixel_plugins.RandomPixelPlugins.display_pixel_rand" # this plugin
]
```
2. Launch or restart Pixel Art
3. View random pixel(s) on screen
4. `rd_wake`: Say "Hey Pixel Art!"

#### Examples

<img src="assets/examples/pixel.gif" alt="pixel.gif" title="pixel.gif" width="128" height="128"/>

---

### `display_heart_rand`

Display colored heart(s) randomly on the Pixel Art screen.

#### Usage

Pair with an AI plugin meant for background tasks. This plugin doesn't use any value from the `ai_result_queue`.

For example, pair with the Retro Diffusion [rd_wake](../../ai/retro_diffusion/README.md#rd_wake) AI plugin.

##### Steps

1. Set in Pixel Art's [config.toml](../../../config.toml):
```toml
[plugins]

ai = [
  # retro diffusion
  "retro_diffusion_plugins.RetroDiffusionPlugins.rd_wake"
]

rgb = [
  # retro diffusion
  "random_pixel_plugins.RandomPixelPlugins.display_heart_rand" # this plugin
]
```
2. Launch or restart Pixel Art
3. View random heart(s) on screen
4. `rd_wake`: Say "Hey Pixel Art!"

#### Examples

<img src="assets/examples/heart.gif" alt="heart.gif" title="heart.gif" width="128" height="128"/>

---

### `display_smiley_rand`

Display a smiley randomly on the Pixel Art screen.

#### Usage

Pair with an AI plugin meant for background tasks. This plugin doesn't use any value from the `ai_result_queue`.

For example, pair with the Retro Diffusion [rd_wake](../../ai/retro_diffusion/README.md#rd_wake) AI plugin.

##### Steps

1. Set in Pixel Art's [config.toml](../../../config.toml):
```toml
[plugins]

ai = [
  # retro diffusion
  "retro_diffusion_plugins.RetroDiffusionPlugins.rd_wake"
]

rgb = [
  # retro diffusion
  "random_pixel_plugins.RandomPixelPlugins.display_smiley_rand" # this plugin
]
```
2. Launch or restart Pixel Art
3. View random smiley on screen
4. `rd_wake`: Say "Hey Pixel Art!"

#### Examples

<img src="assets/examples/smiley.gif" alt="smiley.gif" title="smiley.gif" width="128" height="128"/>

---

### `display_snake_rand`

Display colored pixel snake that grows as it moves randomly on the Pixel Art screen.

#### Usage

Pair with an AI plugin meant for background tasks. This plugin doesn't use any value from the `ai_result_queue`.

For example, pair with the Retro Diffusion [rd_wake](../../ai/retro_diffusion/README.md#rd_wake) AI plugin.

##### Steps

1. Set in Pixel Art's [config.toml](../../../config.toml):
```toml
[plugins]

ai = [
  # retro diffusion
  "retro_diffusion_plugins.RetroDiffusionPlugins.rd_wake"
]

rgb = [
  # retro diffusion
  "random_pixel_plugins.RandomPixelPlugins.display_snake_rand" # this plugin
]
```
2. Launch or restart Pixel Art
3. View pixel snake on screen
4. `rd_wake`: Say "Hey Pixel Art!"

#### Examples

<img src="assets/examples/snake.gif" alt="snake.gif" title="snake.gif" width="128" height="128"/>

---

## Configuration

Plugin configurations can be set in [plugin.toml](plugin.toml).

## Troubleshoot

TBD

## License

[MIT](LICENSE)
