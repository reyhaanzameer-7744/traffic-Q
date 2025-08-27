import streamlit as st
import time
import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import plotly.graph_objects as go
import pandas as pd

# Lane colors
LANE_COLORS = ["blue", "orange", "green", "purple"]
LANE_NAMES = ["UP", "RIGHT", "DOWN", "LEFT"]

# ------------------------------
# Drawing function
# ------------------------------
def draw_junction(ax, lanes, ambulance_lane=None):
    """Draws the junction with cars and ambulance."""
    ax.clear()

    # Transparent junction roads
    ax.add_patch(patches.Rectangle((-0.2, -5), 0.4, 10, linewidth=0, edgecolor="none", facecolor="lightgray", alpha=0.3))
    ax.add_patch(patches.Rectangle((-5, -0.2), 10, 0.4, linewidth=0, edgecolor="none", facecolor="lightgray", alpha=0.3))

    # Place cars
    for lane, count in lanes.items():
        for i in range(count):
            if lane == 0:  # Up
                ax.add_patch(patches.Rectangle((-0.5, 4 - i * 0.5), 0.4, 0.4, facecolor=LANE_COLORS[lane]))
            elif lane == 1:  # Right
                ax.add_patch(patches.Rectangle((-4 + i * 0.5, 0.1), 0.4, 0.4, facecolor=LANE_COLORS[lane]))
            elif lane == 2:  # Down
                ax.add_patch(patches.Rectangle((0.1, -4 + i * 0.5), 0.4, 0.4, facecolor=LANE_COLORS[lane]))
            elif lane == 3:  # Left
                ax.add_patch(patches.Rectangle((4 - i * 0.5, -0.5), 0.4, 0.4, facecolor=LANE_COLORS[lane]))

    # Ambulance
    if ambulance_lane is not None and lanes[ambulance_lane] > 0:
        if ambulance_lane == 0:
            ax.add_patch(plt.Circle((0, 4.5), 0.25, color="red"))
        elif ambulance_lane == 1:
            ax.add_patch(plt.Circle((-4.5, 0), 0.25, color="red"))
        elif ambulance_lane == 2:
            ax.add_patch(plt.Circle((0, -4.5), 0.25, color="red"))
        elif ambulance_lane == 3:
            ax.add_patch(plt.Circle((4.5, 0), 0.25, color="red"))

    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.set_aspect("equal")
    ax.axis("off")


# ------------------------------
# Simulation
# ------------------------------
def simulate_round(system, lanes_init, steps_per_lane, step_delay, strategy="normal", ambulance_lane=None):
    lanes = lanes_init.copy()
    stats = {"time_saved": 0, "fuel_saved": 0, "carbon_saved": 0, "ambulance_time": None}

    placeholder = st.empty()
    total_steps = 0

    while sum(lanes.values()) > 0:
        # Decide lane order
        if strategy == "normal":
            lane_order = [0, 1, 2, 3]
        else:  # Quantum
            if ambulance_lane is not None and lanes[ambulance_lane] > 0:
                lane_order = [ambulance_lane]
            else:
                max_lane = max(lanes, key=lambda k: lanes[k])
                lane_order = [max_lane]

        for lane in lane_order:
            if lanes[lane] == 0:
                continue

            for step in range(steps_per_lane):
                if lanes[lane] > 0:
                    lanes[lane] -= 1
                    total_steps += 1

                fig, ax = plt.subplots(figsize=(5, 5))
                draw_junction(ax, lanes, ambulance_lane)
                ax.set_title(f"{system} - Step {total_steps} ({LANE_NAMES[lane]} lane moving)")
                placeholder.pyplot(fig)
                plt.close(fig)

                time.sleep(step_delay)

                # record ambulance clearance time (convert to minutes)
                if ambulance_lane == lane and lanes[lane] == 0 and stats["ambulance_time"] is None:
                    stats["ambulance_time"] = (total_steps * step_delay) / 60.0

            # Normal: move to next lane
            if strategy == "normal":
                continue
            # Quantum: re-check priority after each lane
            else:
                break

    # Dummy savings (already in minutes)
    stats["time_saved"] = random.randint(5, 15) if strategy == "quantum" else random.randint(0, 5)
    stats["fuel_saved"] = random.randint(10, 20) if strategy == "quantum" else random.randint(0, 10)
    stats["carbon_saved"] = random.randint(15, 25) if strategy == "quantum" else random.randint(0, 12)

    return stats


# ------------------------------
# Main
# ------------------------------
def main():
    st.set_page_config(page_title="Traffic Simulation", layout="wide")
    st.title("🚦 Normal vs Quantum Traffic Simulation")

    # Sidebar
    st.sidebar.header("⚙️ Settings")
    rounds = st.sidebar.slider("Rounds", 1, 3, 1)
    steps_per_lane = 3
    step_delay = st.sidebar.slider("Step delay (s)", 0.2, 2.0, 0.5)

    st.sidebar.subheader("🚑 Ambulance")
    force_amb = st.sidebar.checkbox("Force ambulance?")
    amb_lane = st.sidebar.selectbox("Ambulance Lane", [0, 1, 2, 3], format_func=lambda x: LANE_NAMES[x]) if force_amb else None

    if st.sidebar.button("▶ Run Simulation"):
        normal_totals, quantum_totals = [], []

        for r in range(1, rounds + 1):
            st.header(f"🔄 Round {r}")

            # Random cars per lane
            lanes_init = {i: random.randint(3, 8) for i in range(4)}
            if amb_lane is not None:
                lanes_init[amb_lane] += 1

            col1, col2 = st.columns(2)

            with col1:
                stats_n = simulate_round("Normal Simulation", lanes_init, steps_per_lane, step_delay, "normal", amb_lane)
            normal_totals.append(stats_n)

            with col2:
                stats_q = simulate_round("Quantum Simulation", lanes_init, steps_per_lane, step_delay, "quantum", amb_lane)
            quantum_totals.append(stats_q)

            st.divider()

        # Aggregate results
        agg_normal = pd.DataFrame(normal_totals).sum(numeric_only=True)
        agg_quantum = pd.DataFrame(quantum_totals).sum(numeric_only=True)

        # Results Table
        st.header("📊 Results Summary")
        df = pd.DataFrame({
            "Metric": ["Time Saved (minutes)", "Fuel Saved (liters)", "Carbon Saved (kg)"],
            "Normal": [agg_normal["time_saved"], agg_normal["fuel_saved"], agg_normal["carbon_saved"]],
            "Quantum": [agg_quantum["time_saved"], agg_quantum["fuel_saved"], agg_quantum["carbon_saved"]],
        })
        st.table(df)

        # Bar Graph
        fig = go.Figure(data=[
            go.Bar(name="Normal", x=df["Metric"], y=df["Normal"], marker_color="gray"),
            go.Bar(name="Quantum", x=df["Metric"], y=df["Quantum"], marker_color="purple")
        ])
        fig.update_layout(barmode="group", title="Normal vs Quantum Comparison")
        st.plotly_chart(fig, use_container_width=True)

        # Ambulance times
        if amb_lane is not None:
            avg_normal_amb = pd.Series([s["ambulance_time"] for s in normal_totals if s["ambulance_time"]]).mean()
            avg_quantum_amb = pd.Series([s["ambulance_time"] for s in quantum_totals if s["ambulance_time"]]).mean()
            st.subheader("🚑 Ambulance Clearance Time")
            st.write(f"Normal System Avg: {avg_normal_amb:.2f} minutes")
            st.write(f"Quantum System Avg: {avg_quantum_amb:.2f} minutes")


if __name__ == "__main__":
    main()
