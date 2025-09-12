import streamlit as st
import pandas as pd
import plotly.express as px
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import time

# ---------------- Voice Setup ---------------- #
recognizer = sr.Recognizer()

def record_audio(duration=4, fs=44100):
    st.write("🎙️ Listening...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    return np.squeeze(audio)

def audio_to_text():
    audio_data = record_audio()
    audio_bytes = audio_data.tobytes()
    audio = sr.AudioData(audio_bytes, 44100, 2)
    try:
        text = recognizer.recognize_google(audio)
        st.success(f"🗣️ You said: {text}")
        return text.lower().strip()
    except sr.UnknownValueError:
        st.error("❌ Could not understand")
        return ""
    except sr.RequestError:
        st.error("⚠️ API error")
        return ""

# ---------------- Device Setup ---------------- #
if "devices" not in st.session_state:
    st.session_state.devices = {
        "Light": False,
        "Fan": False,
        "Air Conditioner": False,
        "TV": False,
        "Heater": False,
        "Curtains": False,
        "Window": False,
        "Projector": False,
        
        "Fridge": False,
        "EV Charger": False,
        "Water Pump": False,
        "Sprinkler": False,
        "Parking Lights": False,
        "Terrace Gate": False,
        "Main Gate": False,
        "Back Gate": False,
    }

# ⚡ Updated Power Ratings
DEVICE_POWER = {
    "Light": 12,
    "Fan": 75,
    "Air Conditioner": 1500,
    "TV": 120,
    "Heater": 2000,
    "Curtains": 20,
    "Window": 50,
    "Projector": 90,
    
    "Fridge": 150,
    "EV Charger": 2200,
    "Water Pump": 500,
    "Sprinkler": 100,
    "Parking Lights": 60,
    "Terrace Gate": 40,
    "Main Gate": 0,
    "Back Gate": 0,
}

if "energy_log" not in st.session_state:
    st.session_state.energy_log = {}
if "energy_used" not in st.session_state:
    st.session_state.energy_used = {d: 0.0 for d in st.session_state.devices}

def update_energy(device, state):
    if state:
        st.session_state.energy_log[device] = time.time()
    else:
        if device in st.session_state.energy_log:
            duration = (time.time() - st.session_state.energy_log[device]) / 3600
            power = DEVICE_POWER.get(device, 0) / 1000  # ✅ safe fallback
            st.session_state.energy_used[device] += duration * power
            del st.session_state.energy_log[device]

def get_current_usage():
    return sum(DEVICE_POWER[d] for d, state in st.session_state.devices.items() if state)

def get_total_energy():
    return round(sum(st.session_state.energy_used.values()), 3)

# ---------------- Command Processing ---------------- #
on_commands = ["on", "turn on", "switch on", "open", "start", "activate", "set", "unlock"]
off_commands = ["off", "turn off", "switch off", "close", "stop", "shutdown", "lock"]

# 🔥 Modes
modes = {
    "Energy Saver": {"Light": False, "Fan": True, "Air Conditioner": False, "TV": False, "Heater": False, "Curtains": False, "Window": False, "Projector": False},
    "Sleep Mode": {"Light": False, "Fan": True, "Air Conditioner": True, "TV": False, "Heater": False, "Curtains": False, "Window": False, "Projector": False},
    "Entertainment Mode": {"Light": True, "Fan": False, "Air Conditioner": True, "TV": True, "Heater": False, "Curtains": False, "Window": False, "Projector": False},
    "Leaving Mode": {"Light": False, "Fan": False, "Air Conditioner": False, "TV": False, "Heater": False, "Curtains": False, "Window": False, "Projector": False},
    "Study Mode": {"Light": True, "Fan": True, "Air Conditioner": True, "TV": False, "Heater": False, "Curtains": False, "Window": False, "Projector": False},
}

def process_command(command):
    devices = st.session_state.devices
    if not command:
        return

    if "status" in command:
        st.info(f"Current room status → {devices}")
        return

    if "all" in command and any(word in command for word in on_commands):
        for d in devices:
            if not devices[d]:
                update_energy(d, True)
            devices[d] = True
        st.success("✅ All appliances turned ON")
        return

    if "all" in command and any(word in command for word in off_commands):
        for d in devices:
            if devices[d]:
                update_energy(d, False)
            devices[d] = False
        st.warning("❌ All appliances turned OFF")
        return

    # Mode detection
    for mode, config in modes.items():
        if mode.lower() in command:
            for d, state in config.items():
                if devices[d] != state:
                    update_energy(d, state)
                devices[d] = state
            st.success(f"🎯 {mode} activated")
            return

    devices_found = [d for d in devices if d.lower() in command]
    if not devices_found:
        st.error("❌ Device not found")
        return

    if any(word in command for word in on_commands):
        for d in devices_found:
            if devices[d]:
                st.info(f"{d} is already ON ✅")
            else:
                devices[d] = True
                update_energy(d, True)
                st.success(f"{d} turned ON ✅")

    elif any(word in command for word in off_commands):
        for d in devices_found:
            if not devices[d]:
                st.info(f"{d} is already OFF ❌")
            else:
                devices[d] = False
                update_energy(d, False)
                st.warning(f"{d} turned OFF ❌")
    else:
        st.warning("⚠️ Action not understood")

# ---------------- Streamlit UI ---------------- #
st.set_page_config(page_title="SmartEase Dashboard", layout="wide")

st.markdown("<h2 style='text-align: center;'>👋 Welcome to SmartEase</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Control your home with Voice & UI ✨</p>", unsafe_allow_html=True)
st.write("---")

# ---- Top Summary ----
col1, col2, col3 = st.columns(3)
col1.metric("Devices ON", sum(st.session_state.devices.values()))
col2.metric("Devices OFF", len(st.session_state.devices) - sum(st.session_state.devices.values()))
col3.metric("Current Usage", f"{get_current_usage()} W")
st.write("---")
    
# ---- Master Toggles ----
colA, colB = st.columns(2)
with colA:
    if st.button("✅ Turn ON All Devices", key="on_all"):
        for d in st.session_state.devices:
            if not st.session_state.devices[d]:
                update_energy(d, True)
            st.session_state.devices[d] = True
with colB:
    if st.button("❌ Turn OFF All Devices", key="off_all"):
        for d in st.session_state.devices:
            if st.session_state.devices[d]:
                update_energy(d, False)
            st.session_state.devices[d] = False
st.write("---")

# ---- Sidebar Navigation ----
st.sidebar.title("SmartEase Navigation")
page = st.sidebar.radio("Go to:", ["Home", "Living Room", "Bedroom", "Terrace", "Parking"], key="nav")

# ---- Page Specific Controls ----
colp, colq = st.columns(2)

if page == "Home":
    with colp:
        st.title("🏠 Home Controls")
        for dev in ["Main Gate", "Back Gate"]:
            state = st.toggle(dev, value=st.session_state.devices[dev], key=f"home_{dev}")
            if state != st.session_state.devices[dev]:
                update_energy(dev, state)
            st.session_state.devices[dev] = state

elif page == "Living Room":
    with colp:
        st.title("🛋 Living Room")
        for dev in ["TV", "Light", "Curtains", "Air Conditioner"]:   # ✅ fixed name
            state = st.toggle(dev, value=st.session_state.devices.get(dev, False), key=f"living_{dev}")
            if state != st.session_state.devices.get(dev, False):
                update_energy(dev, state)
            st.session_state.devices[dev] = state

elif page == "Bedroom":
    st.title("🛏 Bedroom")
    col3, col4 = st.columns(2)
    with col4:
        st.subheader("🎚 Bedroom Modes")
        for mode, config in modes.items():
            if st.toggle(mode, key=f"bed_mode_{mode}"):
                for dev, state in config.items():
                    update_energy(dev, state)
                    st.session_state.devices[dev] = state
                st.success(f"{mode} applied!")
        st.markdown("---")
    with col3:
        for dev in ["Light", "Fan", "Air Conditioner", "TV", "Projector", "Curtains", "Window"]:  # ✅ fixed
            state = st.toggle(dev, value=st.session_state.devices.get(dev, False), key=f"bed_{dev}")
            if state != st.session_state.devices.get(dev, False):
                update_energy(dev, state)
            st.session_state.devices[dev] = state

elif page == "Terrace":
    with colp:
        st.title("🌞 Terrace")
        for dev in ["Light", "Terrace Gate", "Water Pump", "Sprinkler"]:
            state = st.toggle(dev, value=st.session_state.devices.get(dev, False), key=f"terrace_{dev}")
            if state != st.session_state.devices.get(dev, False):
                update_energy(dev, state)
            st.session_state.devices[dev] = state

elif page == "Parking":
    with colp:
        st.title("🚗 Parking Area")
        for dev in ["EV Charger", "Parking Lights", "Terrace Gate"]:
            state = st.toggle(dev, value=st.session_state.devices.get(dev, False), key=f"park_{dev}")
            if state != st.session_state.devices.get(dev, False):
                update_energy(dev, state)
            st.session_state.devices[dev] = state

# ---- Voice Assistant + Energy Chart ----
colx, coly = st.columns(2)
with colx:
    st.markdown("### 🎙️ Voice Assistant")
    if st.button("🎤 Start Listening", key="voice"):
        command = audio_to_text()
        process_command(command)

    text_cmd = st.text_input("⌨️ Or type a command:", key="cmd_input")
    if st.button("Run Command", key="run_cmd"):
        process_command(text_cmd)

with coly:
    st.markdown("### 📊 Energy Consumption")
    df = pd.DataFrame({
        "Device": list(st.session_state.devices.keys()),
        "Energy (kWh)": [round(st.session_state.energy_used[d], 3) for d in st.session_state.devices]
    })
    fig = px.bar(df, x="Device", y="Energy (kWh)", title="Energy Consumption by Device")
    st.plotly_chart(fig, use_container_width=True)
    st.metric("🔋 Total Energy", f"{get_total_energy()} kWh")

st.write("---")

# ---- Live Device Status Block ----
st.markdown("### ⚡ Live Device Performance")
status_live_df = pd.DataFrame(
    [
        (d, "ON" if state else "OFF", f"{DEVICE_POWER[d]} W" if state else "0 W")
        for d, state in st.session_state.devices.items()
    ],
    columns=["Device", "Status", "Current Power"]
)
st.dataframe(status_live_df, use_container_width=True)
