<h1 align="center">Display Image</h1>
<br>
<p align="center">RGB Plugin to display images, GIFs, gameplay, and an emoting avatar on the Pixel Art screen.</p>

<br>
<p align="center">
  <img src="assets/examples/tree.png" alt="tree.png" title="tree.png" width="128" height="128"/>
  <img src="assets/examples/eyes.gif" alt="eyes.gif" title="eyes.gif" width="128" height="128" hspace="20"/>
  <img src="https://github.com/user-attachments/assets/253deb56-ef8e-4581-84c0-5dc97827ae95" alt="gameplay" title="gameplay" width="128" height="128" hspace="40"/>
  <img src="assets/avatar/joy.gif" alt="joy.gif" title="joy.gif" width="128" height="128" hspace="60"/>
</p>

## Requirements

Basic build of Pixel Art.

Reference your chosen AI or game plugin(s) for additional requirements.

## Plugins

1. [display_image](#display_image)
1. [display_gif](#display_gif)
1. [display_game](#display_game)
1. [display_emotion_avatar](#display_emotion_avatar)

---

### `display_image`

Display an image on the Pixel Art screen.

#### Usage

Pair with an AI plugin that sends a local image path to this plugin using `ai_result_queue`.

```python
self.ai_result_queue.put("path/to/image.png")
```

For example, pair with the Retro Diffusion [rd_text_to_image](../../ai/retro_diffusion/README.md#rd_text_to_image) AI plugin.

##### Steps

1. Set in Pixel Art's [config.toml](../../../config.toml):
```toml
[plugins]

ai = [
  # retro diffusion
  "retro_diffusion_plugins.RetroDiffusionPlugins.rd_wake",
  "retro_diffusion_plugins.RetroDiffusionPlugins.rd_speech_to_text",
  "retro_diffusion_plugins.RetroDiffusionPlugins.rd_text_to_image"
]

rgb = [
  # retro diffusion
  "random_pixel_plugins.RandomPixelPlugins.display_heart_rand",
  "random_pixel_plugins.RandomPixelPlugins.display_snake_rand",
  "display_image_plugins.DisplayImagePlugins.display_image" # this plugin
]
```
2. Launch or restart Pixel Art
3. `rd_wake`: Say "Hey Pixel Art!"
4. `rd_speech_to_text`: Describe the image you want generated
5. `rd_text_to_image`: Wait for image to display on the Pixel Art screen

#### Examples

<p align="left">
  <img src="assets/examples/tree.png" alt="tree.png" title="tree.png" width="128" height="128"/>
  <img src="assets/examples/chimpanzees.png" alt="chimpanzees.png" title="chimpanzees.png" width="128" height="128" hspace="10"/>
  <img src="assets/examples/thunderstorm.png" alt="thunderstorm.png" title="thunderstorm.png" width="128" height="128"/>
</p>

---

### `display_gif`

Display a GIF on the Pixel Art screen.

#### Usage

Pair with an AI plugin that sends a local GIF path to this plugin using `ai_result_queue`.

```python
self.ai_result_queue.put("path/to/image.gif")
```

##### Steps

1. Set in Pixel Art's [config.toml](../../../config.toml):
```toml
[plugins]

ai = [
  "<your custom AI plugin>"
]

rgb = [
  "display_image_plugins.DisplayImagePlugins.display_gif" # this plugin
]
```
2. Launch or restart Pixel Art
3. ...

**Examples**

<img src="assets/examples/eyes.gif" alt="eyes.gif" title="eyes.gif" width="128" height="128"/>

---

### `display_game`

Display gameplay on the Pixel Art screen.

#### Usage

Pair with a game plugin that sends a gameplay frame as an image to this plugin. This is automatically done for you when using the [GamePlugin](../../game_plugin.py) `draw()` method.

```python
self.draw()
```

For example, pair with the [Basic](../../game/basic/README.md) game plugin.

##### Steps

1. Set in Pixel Art's [config.toml](../../../config.toml):
```toml
[plugins]

ai = [
  # basic game
  "basic.BasicGame.play"
]

rgb = [
  # basic game
  "display_image_plugins.DisplayImagePlugins.display_game" # this plugin
]
```
2. Launch or restart Pixel Art
3. `main`: Play your game

**Examples**

<img src="https://github.com/user-attachments/assets/253deb56-ef8e-4581-84c0-5dc97827ae95" alt="gameplay" title="gameplay" width="128" height="128"/>

---

### `display_emotion_avatar`

Display an emoting avatar on the Pixel Art screen. 

#### Usage

Pair with an AI plugin that continuously sends an emotion and display time (in seconds) to this plugin using `ai_result_queue`.

```python
self.ai_result_queue.put(("joy", 10))
```

For example, pair with the OpenAI Assistant [assistant_run](../../ai/openai_assistant/README.md#assistant_run) AI plugin.

##### Steps

1. Set in Pixel Art's [config.toml](../../../config.toml):
```toml
[plugins]

ai = [
  # openai assistant
  "openai_assistant.OpenAI_Assistant_Plugin.assistant_wake",
  "openai_assistant.OpenAI_Assistant_Plugin.run"
]

rgb = [
  # openai assistant
  "random_pixel_plugins.RandomPixelPlugins.display_smiley_rand",
  "display_image_plugins.DisplayImagePlugins.display_emotion_avatar" # this plugin
]
```
2. Launch or restart Pixel Art
3. `assistant_wake`: Say "Hey Pixel Art!"
4. `run`: Conversate with OpenAI Assistant and view emotive GIFs on screen

#### Examples

<p align="left">
  <img src="assets/avatar/joy.gif" alt="joy.gif" title="joy.gif" width="128" height="128"/>
  <img src="assets/avatar/surprise.gif" alt="surprise.gif" title="surprise.gif" width="128" height="128" hspace="10"/>
  <img src="assets/avatar/confusion.gif" alt="confusion.gif" title="confusion.gif" width="128" height="128" hspace="10"/>
  <img src="assets/avatar/fear.gif" alt="fear.gif" title="fear.gif" width="128" height="128" hspace="10"/>
  <img src="assets/avatar/sadness.gif" alt="sadness.gif" title="sadness.gif" width="128" height="128" hspace="10"/>
  <img src="assets/avatar/anger.gif" alt="anger.gif" title="anger.gif" width="128" height="128" hspace="10"/> 
</p>

---

## Configuration

Plugin configurations can be set in [plugin.toml](plugin.toml).

## Troubleshoot

TBD

## License

[MIT](LICENSE)
