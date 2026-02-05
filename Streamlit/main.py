import torch
import streamlit as st

from audio_pipeline import abc_to_audio
from gemini_abc import GeminiABCError, generate_abc_from_prompt
from gemini_music import GeminiMusicError, generate_gemini_music_audio
from samplings import top_p_sampling, temperature_sampling
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Set page config
st.set_page_config(
    page_title="Raga x Jazz Generation",
    layout="wide"
)

MAX_LENGTH = 1024
DEFAULT_PROMPT = "A meditative Indian jazz fusion performance with graceful sitar and warm Rhodes chords."


@st.cache_resource(show_spinner=False)
def load_music_components():
    tokenizer = AutoTokenizer.from_pretrained("sander-wood/text-to-music")
    model = AutoModelForSeq2SeqLM.from_pretrained("sander-wood/text-to-music")
    model.eval()
    if torch.cuda.is_available():
        model.to("cuda")
    return tokenizer, model


def generate_music(
    prompt: str,
    tokenizer: AutoTokenizer,
    model: AutoModelForSeq2SeqLM,
    top_p: float = 0.9,
    temperature: float = 1.0,
    max_length: int = MAX_LENGTH,
) -> str:
    clean_prompt = prompt.strip() or DEFAULT_PROMPT
    input_ids = tokenizer(
        clean_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    )["input_ids"]

    device = next(model.parameters()).device
    input_ids = input_ids.to(device)
    decoder_start_token_id = model.config.decoder_start_token_id
    if decoder_start_token_id is None:
        decoder_start_token_id = tokenizer.bos_token_id or tokenizer.cls_token_id or tokenizer.pad_token_id or 0

    decoder_input_ids = torch.tensor(
        [[decoder_start_token_id]], device=device, dtype=torch.long
    )
    eos_token_id = model.config.eos_token_id

    with torch.no_grad():
        for _ in range(max_length):
            outputs = model(input_ids=input_ids, decoder_input_ids=decoder_input_ids)
            logits = outputs.logits[:, -1, :]
            probs = torch.nn.functional.softmax(logits, dim=-1).squeeze(0).cpu().numpy()
            filtered = top_p_sampling(probs, top_p=top_p, return_probs=True)
            sampled_id = temperature_sampling(filtered, temperature=temperature)
            next_token = torch.tensor([[sampled_id]], device=device)
            decoder_input_ids = torch.cat((decoder_input_ids, next_token), dim=1)

            if eos_token_id is not None and sampled_id == eos_token_id:
                break

    tune = tokenizer.decode(decoder_input_ids[0], skip_special_tokens=True)
    if not tune.strip():
        raise RuntimeError("Model returned an empty music sequence.")
    return f"X:1\n{tune}"

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Home", "Project", "Chatbot", "AI Tone", "About", "Contact"]
)

# Home page
if page == "Home":
    st.title("Indian x Jazz Fusion")
    
    # Container 1
    with st.container():
        st.header("Introduction")
        st.write("""
        This platform explores the creative intersection between **Indian classical ragas**
        and **jazz harmony and improvisation**. The goal is to design an intelligent system
        capable of generating musical tones, progressions, and stylistic suggestions that
        blend the structural depth of ragas with the expressive freedom of jazz.
        """)

    with st.container():
        st.header("Objectives")
        st.write("""
        - Analyze core melodic and tonal structures of Indian ragas  
        - Identify compatible jazz scales, chords, and improvisational frameworks  
        - Use AI-assisted generation to suggest fusion-based musical ideas  
        - Provide an interactive interface for experimentation and exploration  
        """)

    with st.container():
        st.header("Current Development Stage")
        st.write("""
        The project is currently focused on **UI development and system design**.
        The chatbot and tone generation logic will be integrated in later phases.
        """)

elif page == "Project":
    st.title("Fusion Concept: Indian Ragas × Jazz")

    with st.container():
        st.header("Why Raga and Jazz?")
        st.write("""
        Indian classical music and jazz share a strong emphasis on **improvisation,
        modal exploration, and emotional expression**. While ragas provide strict
        melodic rules and time-based moods, jazz contributes harmonic complexity
        and rhythmic flexibility.
        """)

    with st.container():
        st.header("Fusion Approach")
        st.write("""
        This project investigates:
        - Mapping raga scales to jazz modes  
        - Preserving raga identity while introducing jazz chord voicings  
        - Generating fusion-compatible tones and motifs  
        - Supporting experimentation without violating musical theory  
        """)

    with st.container():
        st.info("The interactive chatbot interface is available in the Chatbot tab.")

elif page == "Chatbot":
    st.title("Tone Generation Chatbot")

    st.write("""
    Provide a prompt describing mood, instrumentation, or stylistic focus and the system will generate a short fusion-inspired stanza of **ABC notation**.
    Use the controls below to tune randomness and shape the fusion feel before downloading MIDI/WAV.
    """)

    with st.form("music_generation_form"):
        user_input = st.text_area(
            "Enter a prompt (e.g., raga name, jazz style, mood, tempo):",
            height=150,
            placeholder="Gently sway between raga Bhairavi and 7th-chord jazz vocab..."
        )

        st.caption("Tweak the sampling controls to experiment with randomness.")
        col1, col2 = st.columns(2)
        with col1:
            top_p = st.slider(
                "Top-p cutoff",
                min_value=0.3,
                max_value=1.0,
                value=0.9,
                step=0.05
            )
        with col2:
            temperature = st.slider(
                "Temperature",
                min_value=0.2,
                max_value=2.0,
                value=1.0,
                step=0.1
            )

        submitted = st.form_submit_button("Generate")

    if submitted:
        with st.spinner("Generating ABC notation..."):
            try:
                tokenizer, model = load_music_components()
                tune = generate_music(
                    prompt=user_input,
                    tokenizer=tokenizer,
                    model=model,
                    top_p=top_p,
                    temperature=temperature,
                )
                st.success("Music generated successfully.")
                st.code(tune, language="abc")
                midi_bytes, wav_bytes = abc_to_audio(tune)
                col_audio, col_downloads = st.columns([3, 1])
                with col_audio:
                    st.caption("Listen to the synthesized output.")
                    st.audio(wav_bytes, format="audio/wav")
                with col_downloads:
                    st.download_button(
                        "Download MIDI",
                        data=midi_bytes,
                        file_name="fusion.mid",
                        mime="audio/midi",
                    )
                    st.download_button(
                        "Download WAV",
                        data=wav_bytes,
                        file_name="fusion.wav",
                        mime="audio/wav",
                    )
            except Exception as exc:
                st.error("Could not generate music from that prompt.")
                st.write(f"`{exc}`")

    prompt_examples = [
        {
            "title": "North Indian raga meditation",
            "details": "Raga – Yaman · Meter – 6/8 · Key – D · Tempo – Medium · Style – Calm, flowing",
        },
        {
            "title": "Rhodes-laced Bhairavi stroll",
            "details": "Folk-inspired raga Bhairavi with lush Rhodes chords and vibraphone accents over a walking bass.",
        },
    ]

    with st.expander("Prompt Examples"):
        for example in prompt_examples:
            st.markdown(f"**{example['title']}**")
            st.markdown(example["details"])
            st.markdown("")

elif page == "AI Tone":
    st.title("AI Generated Music Tone")
    st.markdown(
        """
        Two options:
        - Fast: generate ABC notation, then synthesize to WAV/MIDI locally (recommended).
        - Direct audio: synthesize audio via Gemini (can be slower).
        """,
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Generation mode",
        ["Fast (ABC -> WAV)", "Direct audio (Gemini)"],
        horizontal=True,
    )

    if mode == "Fast (ABC -> WAV)":
        with st.form("gemini_abc_form"):
            gemini_prompt = st.text_area(
                "Describe the fusion mood or instrumentation:",
                height=150,
                placeholder="Cinematic raga mix with swelling Rhodes, tablas, and layered percussion..."
            )
            col1, col2, col3 = st.columns(3)
            with col1:
                key = st.text_input("Key", value="D")
            with col2:
                meter = st.text_input("Meter", value="4/4")
            with col3:
                bars = st.slider("Bars", min_value=4, max_value=32, value=16, step=4)

            submitted = st.form_submit_button("Generate")

        if submitted:
            with st.spinner("Generating ABC..."):
                try:
                    abc_text = generate_abc_from_prompt(
                        prompt=gemini_prompt,
                        key=key.strip() or "D",
                        meter=meter.strip() or "4/4",
                        bars=bars,
                    )
                    st.success("Generated ABC successfully.")
                    st.code(abc_text, language="abc")

                    midi_bytes, wav_bytes = abc_to_audio(abc_text)
                    col_audio, col_downloads = st.columns([3, 1])
                    with col_audio:
                        st.caption("Listen to the synthesized output.")
                        st.audio(wav_bytes, format="audio/wav")
                    with col_downloads:
                        st.download_button(
                            "Download MIDI",
                            data=midi_bytes,
                            file_name="gemini-abc.mid",
                            mime="audio/midi",
                        )
                        st.download_button(
                            "Download WAV",
                            data=wav_bytes,
                            file_name="gemini-abc.wav",
                            mime="audio/wav",
                        )
                except (GeminiABCError, Exception) as exc:
                    st.error("ABC generation failed.")
                    st.write(f"`{exc}`")
                    st.caption(
                        "If this persists, confirm `Streamlit/.env` contains `GEMINI_API_KEY=...`, "
                        "restart the Streamlit server, and verify your key has API access/quota."
                    )

    else:
        with st.form("gemini_music_form"):
            gemini_prompt = st.text_area(
                "Describe the fusion mood or instrumentation:",
                height=150,
                placeholder="Cinematic raga mix with swelling Rhodes, tablas, and layered percussion..."
            )
            bpm = st.slider("Tempo (BPM)", min_value=60, max_value=180, value=120, step=5)
            density = st.slider("Density", min_value=0.3, max_value=1.0, value=0.8, step=0.05)
            brightness = st.slider("Brightness", min_value=0.0, max_value=1.0, value=0.7, step=0.05)
            guidance_strength = st.slider("Guidance strength", min_value=1.0, max_value=12.0, value=4.0, step=0.5)
            duration_seconds = st.slider("Duration (seconds)", min_value=8, max_value=30, value=12, step=2)
            submitted = st.form_submit_button("Generate")

        if submitted:
            with st.spinner("Generating audio (real-time)..."):
                try:
                    gemini_audio = generate_gemini_music_audio(
                        prompt=gemini_prompt,
                        bpm=bpm,
                        density=density,
                        brightness=brightness,
                        guidance=guidance_strength,
                        duration_seconds=duration_seconds,
                    )
                    st.success("Audio generated successfully.")
                    st.audio(gemini_audio, format="audio/wav")
                    st.download_button(
                        "Download WAV",
                        data=gemini_audio,
                        file_name="gemini-tone.wav",
                        mime="audio/wav",
                    )
                except GeminiMusicError as exc:
                    st.error("Gemini generation failed.")
                    st.write(f"`{exc}`")

elif page == "About":
    st.title("About This Project")

    st.write("""
    This project is a music-technology initiative focused on the fusion of
    **Indian classical ragas and jazz music** through computational and AI-driven methods.

    The motivation behind this work is to explore how structured musical traditions
    can coexist with improvisational systems in a meaningful and theoretically
    sound way. By combining elements from both genres, the project aims to create
    a tool that supports musicians, composers, and learners in discovering new
    creative possibilities.

    The long-term vision includes intelligent tone generation, theoretical explanations,
    and interactive experimentation through a chatbot-driven interface.
    """)

elif page == "Contact":
    st.title("Contact")

    st.write("""
    For questions, collaboration opportunities, or feedback, please reach out via email:
    """)

    st.code("vihaankulkarni28@gmail.com")
