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
        ("DUEL DEFENSIVO WON", 3.15, 69.59, None),
        ("DUEL DEFENSIVO WON", 8.80, 63.77, None),
        ("DUEL DEFENSIVO WON", 21.60, 49.64, None),
        ("DUEL DEFENSIVO WON", 20.27, 53.30, None),
        ("DUEL DEFENSIVO WON", 31.08, 54.79, None),
        ("INTERCEPTACAO", 79.12, 16.89, None),
        ("INTERCEPTACAO", 71.14, 69.26, None),
    ],
    "Vs Nagoya": [
        ("DUEL DEFENSIVO WON", 7.47, 66.43, None),
        ("DUEL DEFENSIVO WON", 78.95, 75.91, None),
        ("INTERCEPTACAO", 37.39, 69.09, None),
    ],
    "Vs Busan Park": [
        ("INTERCEPTACAO", 14.78, 42.66, None),
    ],
    "Vs Atlanta": [
        ("DUEL DEFENSIVO WON", 8.30, 60.45, None),
        ("DUEL DEFENSIVO WON", 9.13, 75.24, None),
        ("DUEL DEFENSIVO WON", 19.27, 71.42, None),
        ("DUEL DEFENSIVO WON", 21.93, 48.81, None),
        ("DUEL DEFENSIVO LOST", 1.82, 69.26, None),
        ("DUEL DEFENSIVO LOST", 27.25, 69.59, None),
        ("DUEL DEFENSIVO LOST", 36.89, 71.58, None),
        ("INTERCEPTACAO", 2.48, 72.42, None),
        ("INTERCEPTACAO", 28.75, 48.48, None),
        ("INTERCEPTACAO", 15.95, 40.50, None),
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

    # 1. DUELOS DEFENSIVOS (Defensive Duels)
    if "DEFENSIVO" in event_type:
        if "WON" in event_type:
            # Square (Strong green)
            return 's', (0.0, 0.75, 0.2, 0.95), 130, 0.5
        if "LOST" in event_type:
            # Diamond (Strong red)
            alpha = 0.95 if has_video else 0.85
            return 'D', (0.85, 0.1, 0.1, alpha), 130, 2.5

    # 2. INTERCEPTAÇÕES
    if "INTERCEPT" in event_type or "INTERCEPTACAO" in event_type:
        # Star (Bright blue)
        return '*', (0.2, 0.6, 0.95, 0.95), 180, 0.8

    # Default
    return 'o', (0.5, 0.5, 0.5, 0.8), 90, 0.5


def compute_stats(df: pd.DataFrame) -> dict:
    """Compute defensive duel and interception statistics"""
    total = len(df)

    # Defensive duels
    is_def_duel = df['type'].str.contains('DEFENSIVO', case=False)
    is_won = df['type'].str.contains('WON', case=False)
    is_lost = df['type'].str.contains('LOST', case=False)

    def_duels = df[is_def_duel]
    def_total = len(def_duels)
    def_wins = len(def_duels[def_duels['type'].str.contains('WON', case=False)])
    def_losses = len(def_duels[def_duels['type'].str.contains('LOST', case=False)])
    def_rate = (def_wins / def_total * 100) if def_total > 0 else 0

    # Interceptions
    is_intercept = df['type'].str.contains('INTERCEPT|INTERCEPTACAO', case=False)
    intercepts = len(df[is_intercept])

    # Zone stats - Split into 3 corridors
    # Left corridor: y < 26.6
    # Central corridor: 26.6 <= y <= 53.3
    # Right corridor: y > 53.3

    left_mask = df['y'] < 26.6
    left_def = df[left_mask & is_def_duel]
    left_total = len(left_def)
    left_wins = len(left_def[left_def['type'].str.contains('WON', case=False)])
    left_rate = (left_wins / left_total * 100) if left_total > 0 else 0
    left_intercepts = len(df[left_mask & is_intercept])

    central_mask = (df['y'] >= 26.6) & (df['y'] <= 53.3)
    central_def = df[central_mask & is_def_duel]
    c_total = len(central_def)
    c_wins = len(central_def[central_def['type'].str.contains('WON', case=False)])
    c_rate = (c_wins / c_total * 100) if c_total > 0 else 0
    c_intercepts = len(df[central_mask & is_intercept])

    right_mask = df['y'] > 53.3
    right_def = df[right_mask & is_def_duel]
    right_total = len(right_def)
    right_wins = len(right_def[right_def['type'].str.contains('WON', case=False)])
    right_rate = (right_wins / right_total * 100) if right_total > 0 else 0
    right_intercepts = len(df[right_mask & is_intercept])

    # Defensive third (x < 40)
    def_third_mask = df['x'] < 40
    def_third_duels = df[def_third_mask & is_def_duel]
    def_third_total = len(def_third_duels)
    def_third_wins = len(def_third_duels[def_third_duels['type'].str.contains('WON', case=False)])
    def_third_rate = (def_third_wins / def_third_total * 100) if def_third_total > 0 else 0
    def_third_intercepts = len(df[def_third_mask & is_intercept])

    return {
        "total": total,
        "def_total": def_total,
        "def_wins": def_wins,
        "def_losses": def_losses,
        "def_rate": def_rate,
        "intercepts": intercepts,
        "left_total": left_total,
        "left_wins": left_wins,
        "left_rate": left_rate,
        "left_intercepts": left_intercepts,
        "central_total": c_total,
        "central_wins": c_wins,
        "central_rate": c_rate,
        "central_intercepts": c_intercepts,
        "right_total": right_total,
        "right_wins": right_wins,
        "right_rate": right_rate,
        "right_intercepts": right_intercepts,
        "def_third_total": def_third_total,
        "def_third_wins": def_third_wins,
        "def_third_rate": def_third_rate,
        "def_third_intercepts": def_third_intercepts,
    }


# ==========================
# Sidebar Configuration
# ==========================
st.sidebar.header("📋 Filter Configuration")
selected_match = st.sidebar.radio("Select a match", list(full_data.keys()), index=0)

st.sidebar.divider()

# Additional filter
filter_event_type = st.sidebar.multiselect(
    "Event Type",
    ["Defensive Duels", "Interceptions"],
    default=["Defensive Duels", "Interceptions"]
)

st.sidebar.divider()
st.sidebar.caption("Match filtered by selected options above")

# Get selected data
df = full_data[selected_match].copy()

# Apply event type filter
if not all(x in filter_event_type for x in ["Defensive Duels", "Interceptions"]):
    mask = pd.Series([False] * len(df))
    if "Defensive Duels" in filter_event_type:
        mask |= df['type'].str.contains('DEFENSIVO', case=False)
    if "Interceptions" in filter_event_type:
        mask |= df['type'].str.contains('INTERCEPT|INTERCEPTACAO', case=False)
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
        # Black border for events that contain video
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
        # --- Defensive Duels ---
        Line2D([0], [0], marker='s', color='w', label='Defensive Duel Won',
               markerfacecolor=(0.0, 0.75, 0.2, 0.95), markersize=10, linestyle='None'),

        Line2D([0], [0], marker='D', color='w', label='Defensive Duel Lost',
               markeredgecolor=(0.85, 0.1, 0.1, 0.95), markerfacecolor=(0.85, 0.1, 0.1, 0.95),
               markersize=10, markeredgewidth=2.0, linestyle='None'),

        # --- Interceptions ---
        Line2D([0], [0], marker='*', color='w', label='Interception',
               markerfacecolor=(0.2, 0.6, 0.95, 0.95), markersize=14, linestyle='None'),
    ]

    # Apply legend to graphic
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

    # Use fixed width to ensure coordinate scaling works
    click = streamlit_image_coordinates(img_obj, width=700)

# ==========================
# Interaction Logic
# ==========================
selected_event = None

if click is not None:
    real_w, real_h = img_obj.size
    disp_w, disp_h = click["width"], click["height"]

    # Map pixel click to actual image pixels
    pixel_x = click["x"] * (real_w / disp_w)
    pixel_y = click["y"] * (real_h / disp_h)

    # Invert Y for Matplotlib logic and transform to pitch data coordinates
    mpl_pixel_y = real_h - pixel_y
    coords = ax.transData.inverted().transform((pixel_x, mpl_pixel_y))
    field_x, field_y = coords[0], coords[1]

    # Calculate distance to markers
    df["dist"] = np.sqrt((df["x"] - field_x)**2 + (df["y"] - field_y)**2)

    # Radius threshold for easier selection
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
        # Color-coded event display
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

    # Row 1: Defensive Duels Overview
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Defensive Duels",
        f"{stats['def_wins']}/{stats['def_total']}",
        f"{stats['def_rate']:.1f}% Won"
    )
    col2.metric(
        "Duels Won",
        stats['def_wins'],
        f"of {stats['def_total']} total"
    )
    col3.metric(
        "Duels Lost",
        stats['def_losses']
    )

    st.divider()

    # Row 2: Interceptions & Defensive Third
    col4, col5, col6 = st.columns(3)
    col4.metric(
        "Interceptions",
        stats['intercepts']
    )
    col5.metric(
        "Defensive Third Duels",
        f"{stats['def_third_wins']}/{stats['def_third_total']}",
        f"{stats['def_third_rate']:.1f}% Won"
    )
    col6.metric(
        "Def. Third Interceptions",
        stats['def_third_intercepts']
    )

    st.divider()

    # Row 3: Zone Breakdown
    st.subheader("Zone Breakdown")
    col7, col8, col9 = st.columns(3)
    col7.metric(
        "Left Corridor",
        f"Duels: {stats['left_wins']}/{stats['left_total']}",
        f"Intercepts: {stats['left_intercepts']}"
    )
    col8.metric(
        "Central Corridor",
        f"Duels: {stats['central_wins']}/{stats['central_total']}",
        f"Intercepts: {stats['central_intercepts']}"
    )
    col9.metric(
        "Right Corridor",
        f"Duels: {stats['right_wins']}/{stats['right_total']}",
        f"Intercepts: {stats['right_intercepts']}"
    )
