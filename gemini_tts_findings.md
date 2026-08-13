# Gemini TTS implementation findings

Official Gemini API TTS documentation: https://ai.google.dev/gemini-api/docs/speech-generation

Key implementation details:

- TTS uses a Gemini 2.5/3.1 TTS-capable model and text-only input with audio-only output.
- The official current Python example uses the Interactions API with model `gemini-3.1-flash-tts-preview`, `response_format={"type": "audio"}`, and `generation_config={"speech_config": [{"voice": "Kore"}]}`.
- The returned audio is base64-encoded PCM. The official example writes it as WAV with mono, 24 kHz sample rate, 16-bit samples.
- Style instructions are included in the input prompt before the spoken text; the TTS model can control pace, tone, accent and delivery.
- The existing project already uses `google-genai`; an HTTP or SDK integration can reuse `GEMINI_API_KEY` without adding OpenAI credentials.

SDK reference: https://googleapis.github.io/python-genai/
