<h1 align="center">OpenAI Assistant</h1>
<br>
<p align="center">
  The Pixel Art voice chatbot powered by OpenAI's <a href="https://platform.openai.com/docs/guides/realtime">Realtime API</a>.
</p>
<p align="center">
  Currently doesn't support any tool calling and is limited by the AI model's <a href="https://platform.openai.com/docs/models/gpt-4o-realtime-preview">knowledge cutoff</a> date.
</p>
<br>

## Examples

Example AI responses can be downloaded from [assets/examples](assets/examples).

## Requirements

### Hardware

The following Pixel Art I/O hardware is required to support this plugin: `microphone`, `speaker`.

### API Keys

The following API keys must be set as system environment variables:

- [Picovoice](https://console.picovoice.ai/signup#free): `PICOVOICE_TOKEN`
- [OpenAI](https://platform.openai.com/api-keys): `OPENAI_API_KEY`

## Plugins

1. [assistant_wake](#assistant_wake)
1. [assistant_run](#assistant_run)

---

### `assistant_wake`

Listens for the wake phrase "Hey Pixel Art." Once the wake phrase is detected, this plugin exits.

#### Modalities

- **in**: audio
- **out**: none

#### Usage

Pair with an RGB plugin that expects no values from the `ai_result_queue`.

For example, pair with the Random Pixel [display_heart_rand](../../rgb/random_pixel/README.md#display_heart_rand) RGB plugin.

##### Steps

1. Set in Pixel Art's [config.toml](../../../config.toml):
```toml
[plugins]

ai = [
  # openai assistant
  "openai_assistant.OpenAIAssistantPlugins.assistant_wake" # this plugin
]

rgb = [
  # openai assistant
  "random_pixel_plugins.RandomPixelPlugins.display_heart_rand"
]
```
2. Launch or restart Pixel Art
3. `assistant_wake`: Say "Hey Pixel Art!"

---

### `assistant_run`

A voice chatbot that follows a natural conversation flow.

#### Modalities

- **in**: audio
- **out**: audio

#### Usage

Once the plugin starts, the OpenAI Assistant will greet you first and then follows a natural conversation flow.
It disables the mic when responding and enables it again once finished.

Highly recommend to pair the Assistant's `assistant_run` plugin with the RGB plugin [display_emotion_avatar](../../rgb/display_image/README.md#display_emotion_avatar).
This RGB plugin listens for the emotion classification of each Assistant response and chooses the appropriate emoting gif (joy, sadness, etc.).
Additionally, the avatar's eyes will be `white` when listening/speaking and `light blue` when thinking/processing.

##### Steps

1. Set in Pixel Art's [config.toml](../../../config.toml):
```toml
[plugins]

ai = [
  # openai assistant
  "openai_assistant.OpenAIAssistantPlugins.assistant_wake",
  "openai_assistant.OpenAIAssistantPlugins.assistant_run" # this plugin
]

rgb = [
  # openai assistant
  "random_pixel_plugins.RandomPixelPlugins.display_heart_rand",
  "display_image_plugins.DisplayImagePlugins.display_emotion_avatar"
]
```
2. Launch or restart Pixel Art
3. `assistant_wake`: Say "Hey Pixel Art!"
4. `assistant_run`: Chat with the OpenAI Assistant

---

## Configuration

Plugin configurations can be set in [plugin.toml](plugin.toml).

## Troubleshoot

TBD

## License

[MIT](LICENSE)
