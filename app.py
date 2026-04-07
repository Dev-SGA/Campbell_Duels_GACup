import streamlit as st
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates
from io import BytesIO
import numpy as np
from PIL import Image
from matplotlib.lines import Line2D

# ==========================
# Page Configuration
# ==========================
st.set_page_config(layout="wide", page_title="Defensive Duel & Interception Map")

st.title("Defensive Duel & Interception Map - Multiple Matches")
st.caption("Click on the icons on the pitch to view event details.")

# ==========================
# Data Setup
# ==========================
matches_data = {
    "Vs Dallas": [
        ("DEFENSIVE DUEL WON", 3.15, 69.59, "videos/1 - DL.mp4"),
        ("DEFENSIVE DUEL WON", 8.80, 63.77, "videos/5 - DL.mp4"),
        ("DEFENSIVE DUEL WON", 21.60, 49.64, "videos/3 - DL.mp4"),
        ("DEFENSIVE DUEL WON", 20.27, 53.30, "videos/2 - DL.mp4"),
        ("DEFENSIVE DUEL WON", 31.08, 54.79, "videos/4 - DL.mp4"),
        ("INTERCEPTION", 79.12, 16.89, "videos/INT 2 - DL.mp4"),
        ("INTERCEPTION", 71.14, 69.26, "videos/INT 1 - DL.mp4"),
    ],
    "Vs Nagoya": [
        ("DEFENSIVE DUEL WON", 7.47, 66.43, "videos/1 - NG.mp4"),
        ("INTERCEPTION", 37.39, 69.09, "videos/INT 1 - NG.mp4"),
    ],
    "Vs Busan Park": [
        ("DEFENSIVE DUEL WON", 14.78, 42.66, "videos/INT 1 - BP.mp4"),
    ],
    "Vs Atlanta": [
        ("DEFENSIVE DUEL WON", 8.30, 60.45, "videos/7 - AT.mp4"),
        ("DEFENSIVE DUEL WON", 9.13, 75.24, "videos/6 - AT.mp4"),
        ("DEFENSIVE DUEL WON", 19.27, 71.42, "videos/1 - AT.mp4"),
        ("DEFENSIVE DUEL WON", 21.93, 48.81, "videos/3 - AT.mp4"),
        ("DEFENSIVE DUEL LOST", 1.82, 69.26, "videos/2 - AT.mp4"),
        ("DEFENSIVE DUEL LOST", 27.25, 69.59, "videos/4 - AT.mp4"),
        ("DEFENSIVE DUEL LOST", 36.89, 71.58, "videos/5 - AT.mp4"),
        ("BLOCK", 2.48, 72.42, "videos/INT 3 - AT.mp4"),
        ("CLEARANCE", 28.75, 48.48, "videos/INT 1 - AT.mp4"),
        ("DEFENSIVE DUEL WON", 15.95, 40.50, "videos/INT 2 - AT.mp4"),
    ],
}

# Create DataFrames for each match and combined
dfs_by_match = {}
for match_name, events in matches_data.items():
    dfs_by_match[match_name] = pd.DataFrame(events, columns=["type", "x", "y", "video"])

# All games combined
df_all = pd.concat(dfs_by_match.values(), ignore_index=True)
full_data = {"All games": df_all}
full_data.update(dfs_by_match)


def get_style(event_type, has_video):
    """Returns marker, color (rgba), size, and linewidth based on event type"""
    event_type = event_type.upper()

    # 1. DEFENSIVE DUELS
    if "DEFENSIVE DUEL" in event_type:
        if "WON" in event_type:
            return 's', (0.0, 0.75, 0.2, 0.95), 130, 0.5
        if "LOST" in event_type:
            alpha = 0.95 if has_video else 0.85
            return 'D', (0.85, 0.1, 0.1, alpha), 130, 2.5

    # 2. INTERCEPTION - Blue circle
    if "INTERCEPTION" in event_type:
        return 'o', (0.2, 0.6, 0.95, 0.95), 130, 0.5

    # 3. BLOCK - Purple pentagon
    if "BLOCK" in event_type:
        return 'P', (0.7, 0.3, 0.9, 0.95), 130, 0.5

    # 4. CLEARANCE - Orange triangle
    if "CLEARANCE" in event_type:
        return '^', (1.0, 0.65, 0.0, 0.95), 130, 0.5

    # Default
    return 'o', (0.5, 0.5, 0.5, 0.8), 90, 0.5


def compute_stats(df: pd.DataFrame) -> dict:
    """Compute defensive duel, interception, block and clearance statistics"""
    # Defensive duels
    is_def_duel = df['type'].str.contains('DEFENSIVE DUEL', case=False)
    def_duels = df[is_def_duel]
    def_total = len(def_duels)
    def_wins = len(def_duels[def_duels['type'].str.contains('WON', case=False)])
    def_losses = len(def_duels[def_duels['type'].str.contains('LOST', case=False)])
    def_rate = (def_wins / def_total * 100) if def_total > 0 else 0

    # Interceptions
    intercepts = len(df[df['type'].str.contains('INTERCEPTION', case=False)])

    # Blocks
    blocks = len(df[df['type'].str.contains('BLOCK', case=False)])

    # Clearances
    clearances = len(df[df['type'].str.contains('CLEARANCE', case=False)])

    return {
        "def_total": def_total,
        "def_wins": def_wins,
        "def_losses": def_losses,
        "def_rate": def_rate,
        "intercepts": intercepts,
        "blocks": blocks,
        "clearances": clearances,
    }


# ==========================
# Sidebar Configuration
# ==========================
st.sidebar.header("📋 Filter Configuration")
selected_match = st.sidebar.radio("Select a match", list(full_data.keys()), index=0)

st.sidebar.divider()

filter_event_type = st.sidebar.multiselect(
    "Event Type",
    ["Defensive Duels", "Interceptions", "Blocks", "Clearances"],
    default=["Defensive Duels", "Interceptions", "Blocks", "Clearances"]
)

st.sidebar.divider()
st.sidebar.caption("Match filtered by selected options above")

# Get selected data
df = full_data[selected_match].copy()

# Apply event type filter
all_types = ["Defensive Duels", "Interceptions", "Blocks", "Clearances"]
if not all(x in filter_event_type for x in all_types):
    mask = pd.Series([False] * len(df))
    if "Defensive Duels" in filter_event_type:
        mask |= df['type'].str.contains('DEFENSIVE DUEL', case=False)
    if "Interceptions" in filter_event_type:
        mask |= df['type'].str.contains('INTERCEPTION', case=False)
    if "Blocks" in filter_event_type:
        mask |= df['type'].str.contains('BLOCK', case=False)
    if "Clearances" in filter_event_type:
        mask |= df['type'].str.contains('CLEARANCE', case=False)
    df = df[mask]

# Compute stats always from full match data
stats = compute_stats(full_data[selected_match])

# ==========================
# Main Layout
# ==========================
col_map, col_vid = st.columns([1, 1])

with col_map:
    st.subheader("Interactive Pitch Map")
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#f8f8f8', line_color='#4a4a4a')
    fig, ax = pitch.draw(figsize=(10, 7))

    for _, row in df.iterrows():
        has_vid = row["video"] is not None
        marker, color, size, lw = get_style(row["type"], has_vid)
        ec = 'black' if has_vid else 'none'
        pitch.scatter(row.x, row.y, marker=marker, s=size, color=color,
                      edgecolors=ec, linewidths=lw, ax=ax, zorder=3)

    # Attack Arrow
    ax.annotate('', xy=(70, 83), xytext=(50, 83),
        arrowprops=dict(arrowstyle='->', color='#4a4a4a', lw=1.5))
    ax.text(60, 86, "Attack Direction", ha='center', va='center',
        fontsize=9, color='#4a4a4a', fontweight='bold')

    # Legend
    legend_elements = [
        Line2D([0], [0], marker='s', color='w', label='Defensive Duel Won',
               markerfacecolor=(0.0, 0.75, 0.2, 0.95), markersize=10, linestyle='None'),

        Line2D([0], [0], marker='D', color='w', label='Defensive Duel Lost',
               markerfacecolor=(0.85, 0.1, 0.1, 0.95), markersize=10, linestyle='None'),

        Line2D([0], [0], marker='o', color='w', label='Interception',
               markerfacecolor=(0.2, 0.6, 0.95, 0.95), markersize=10, linestyle='None'),

        Line2D([0], [0], marker='P', color='w', label='Block',
               markerfacecolor=(0.7, 0.3, 0.9, 0.95), markersize=10, linestyle='None'),

        Line2D([0], [0], marker='^', color='w', label='Clearance',
               markerfacecolor=(1.0, 0.65, 0.0, 0.95), markersize=10, linestyle='None'),
    ]

    legend = ax.legend(
        handles=legend_elements,
        loc='upper left',
        bbox_to_anchor=(0.01, 0.99),
        frameon=True,
        facecolor='white',
        edgecolor='#333333',
        fontsize='small',
        title="Match Events",
        title_fontsize='medium',
        labelspacing=1.2,
        borderpad=1.0,
        framealpha=0.95
    )

    legend.get_title().set_fontweight('bold')

    # Convert plot to image for coordinate tracking
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_obj = Image.open(buf)

    click = streamlit_image_coordinates(img_obj, width=700)

# ==========================
# Interaction Logic
# ==========================
selected_event = None

if click is not None:
    real_w, real_h = img_obj.size
    disp_w, disp_h = click["width"], click["height"]

    pixel_x = click["x"] * (real_w / disp_w)
    pixel_y = click["y"] * (real_h / disp_h)

    mpl_pixel_y = real_h - pixel_y
    coords = ax.transData.inverted().transform((pixel_x, mpl_pixel_y))
    field_x, field_y = coords[0], coords[1]

    df["dist"] = np.sqrt((df["x"] - field_x)**2 + (df["y"] - field_y)**2)

    RADIUS = 5
    candidates = df[df["dist"] < RADIUS]

    if not candidates.empty:
        selected_event = candidates.loc[candidates["dist"].idxmin()]

# ==========================
# Event Details & Stats
# ==========================
with col_vid:
    st.subheader("Event Details")
    if selected_event is not None:
        event_type = selected_event['type']
        if "WON" in event_type.upper():
            st.success(f"**Selected Event:** {selected_event['type']}")
        elif "LOST" in event_type.upper():
            st.error(f"**Selected Event:** {selected_event['type']}")
        else:
            st.info(f"**Selected Event:** {selected_event['type']}")

        st.info(f"**Position:** X: {selected_event['x']:.2f}, Y: {selected_event['y']:.2f}")

        if selected_event["video"]:
            try:
                st.video(selected_event["video"])
            except:
                st.error(f"Video file not found: {selected_event['video']}")
        else:
            st.warning("No video footage available for this specific event.")
    else:
        st.info("Select a marker on the pitch to view event details.")

    st.divider()
    st.subheader("Performance Statistics")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Defensive Duels",
        f"{stats['def_wins']}/{stats['def_total']}",
        f"{stats['def_rate']:.1f}% Won"
    )
    col2.metric("Interceptions", stats['intercepts'])
    col3.metric("Blocks", stats['blocks'])
    col4.metric("Clearances", stats['clearances'])
