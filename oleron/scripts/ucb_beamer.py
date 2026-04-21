import numpy as np
import math
import argparse

def run_ucb_simulation(num_arms, num_steps, true_means):
    """
    Pass 1: Run the simulation to gather data and find the max UCB score.
    This function does NOT generate any LaTeX code.
    """
    history = []
    max_ucb_value = 0.0

    # --- Initialization Step ---
    num_pulls = np.zeros(num_arms)
    estimated_means = np.zeros(num_arms)
    for i in range(num_arms):
        reward = np.random.normal(true_means[i], 1)
        num_pulls[i] = 1
        estimated_means[i] = reward
    
    total_steps = num_arms
    
    # Save initial state
    ucb_scores = estimated_means + np.sqrt(2 * np.log(total_steps) / num_pulls)
    max_ucb_value = max(max_ucb_value, np.max(ucb_scores))
    history.append({
        'time': total_steps,
        'means': estimated_means.copy(),
        'ucb_scores': ucb_scores.copy(),
        'chosen_arm': None, # No arm is "chosen" in the initial state view
        'type': 'Initialization'
    })

    # --- Main Simulation Loop ---
    for t in range(num_steps):
        current_time = total_steps + t + 1
        
        # --- Decision State ---
        ucb_scores = estimated_means + np.sqrt(2 * np.log(current_time) / num_pulls)
        max_ucb_value = max(max_ucb_value, np.max(ucb_scores))
        chosen_arm = np.argmax(ucb_scores)
        history.append({
            'time': current_time,
            'means': estimated_means.copy(),
            'ucb_scores': ucb_scores.copy(),
            'chosen_arm': chosen_arm,
            'type': 'Decision'
        })

        # --- Update State ---
        reward = np.random.normal(true_means[chosen_arm], 1)
        estimated_means[chosen_arm] = (estimated_means[chosen_arm] * num_pulls[chosen_arm] + reward) / (num_pulls[chosen_arm] + 1)
        num_pulls[chosen_arm] += 1
        
        # The state after the update
        updated_ucb_scores = estimated_means + np.sqrt(2 * np.log(current_time) / num_pulls)
        max_ucb_value = max(max_ucb_value, np.max(updated_ucb_scores))
        history.append({
            'time': current_time,
            'means': estimated_means.copy(),
            'ucb_scores': updated_ucb_scores.copy(),
            'chosen_arm': chosen_arm, # We still know which arm was just chosen
            'type': 'Update'
        })
        
    return history, max_ucb_value

def generate_beamer_frames(history, max_ucb):
    """
    Pass 2: Generate the LaTeX frames using the pre-computed simulation data.
    """
    # Determine a clean upper limit for the Y-axis
    plot_ymax = math.ceil(max_ucb)
    latex_code = ""

    for state in history:
        frame_title = "UCB Algorithm"
        if state['type'] == 'Initialization':
            frame_title = "UCB Algorithm"
            
        latex_code += f"\\begin{{frame}}{{{frame_title}}}\n"
        latex_code += "\\centering\n"
        latex_code += _draw_ucb_plot(
            state,
            plot_ymax=plot_ymax,
            num_arms=len(state['means'])
        )
        latex_code += "\n\\end{frame}\n"
        
    return latex_code

def generate_animate_frames(history, max_ucb):
    """
    Pass 2: Generate the LaTeX frames using the pre-computed simulation data for animate package.
    """
    plot_ymax = math.ceil(max_ucb)
    latex_code = ""
    frame_title = "UCB Algorithm"

    latex_code += f"\\begin{{frame}}{{{frame_title}}}\n"
    latex_code += r"\centering" + "\n"
    latex_code += r"\begin{animateinline}[controls, loop]{2}" + "\n"

    for i, state in enumerate(history):
        latex_code += _draw_ucb_plot(
            state,
            plot_ymax=plot_ymax,
            num_arms=len(state['means'])
        )
        if i < len(history) - 1:
            latex_code += "\n\\newframe\n"

    latex_code += "\n\\end{animateinline}\n"
    latex_code += "\\end{frame}\n"
    return latex_code

def _draw_ucb_plot(state, plot_ymax, num_arms):
    """
    Draws a single TikZ plot inside a center environment for robust scaling.
    """
    # TikZ constants
    Y_AXIS_HEIGHT = 4.5
    PLOT_WIDTH = 11.0 
    x_step = PLOT_WIDTH / (num_arms + 1)

    # --- CORRECTED CODE STARTS HERE ---
    # Use the \centering command outside of this function if needed.
    # It provides better vertical spacing and is more robust for large blocks.
    # Also, added '%' to prevent spurious spaces.
    plot_code = r"""
\resizebox{0.95\textwidth}{!}{%
\begin{tikzpicture}[
    axis/.style={->, >=Stealth, thick},
    ci_bar/.style={line width=8pt, cap=round, blue!60, opacity=0.5},
    mean_dot/.style={circle, fill=red, inner sep=2.5pt},
    chosen_arrow/.style={-{Stealth[length=5pt,width=7pt]}, ultra thick, draw=green!60!black},
    chosen_tag/.style={font=\bfseries\footnotesize, fill=green!10, draw=green!60!black, rounded corners, inner sep=2pt, yshift=3pt}
]
"""
    # Unpack state
    means = state['means']
    ucb_scores = state['ucb_scores']
    chosen_arm = state['chosen_arm']

    # --- Static Axis Generation ---
    plot_code += f"""
    % Axes
    \\draw[axis] (0,0) -- (0, {Y_AXIS_HEIGHT + 0.5}) node[above] {{UCB Score}};
    \\draw[axis] (0,0) -- ({PLOT_WIDTH + 0.75}, 0) node[right] {{Arms}};

    % Y-axis labels, scaled to the global maximum UCB score
    \\foreach \\y in {{0, 0.5, ..., {plot_ymax}}} {{
        \\pgfmathsetmacro{{\\ycoord}}{{\\y / {plot_ymax} * {Y_AXIS_HEIGHT}}}
        \\draw (-0.1, \\ycoord) -- (0.1, \\ycoord) node[left] {{\\pgfmathprintnumber[fixed, precision=1]{{\\y}}}};
    }}

    % Arm labels
    \\foreach \\i in {{1,...,{num_arms}}} {{ \\node[font=\\bfseries, below, yshift=-5pt] at (\\i*{x_step}, 0) {{Arm \\i}}; }}
    """

    # --- Dynamic Data Plotting ---
    for i in range(num_arms):
        mean_y = (means[i] / plot_ymax) * Y_AXIS_HEIGHT
        ucb_y = (ucb_scores[i] / plot_ymax) * Y_AXIS_HEIGHT
        lower_bound_y = max(0, (2 * means[i] - ucb_scores[i]) / plot_ymax * Y_AXIS_HEIGHT)
        current_x_pos = (i + 1) * x_step

        plot_code += f"""
        \\draw[ci_bar] ({current_x_pos}, {lower_bound_y}) -- ({current_x_pos}, {ucb_y});
        \\node[mean_dot] at ({current_x_pos}, {mean_y}) {{}};
        """

    # Show chosen arm only on "Decision" frames for clarity
    if state['type'] == 'Decision' and chosen_arm is not None:
        chosen_x = (chosen_arm + 1) * x_step
        ucb_y = (ucb_scores[chosen_arm] / plot_ymax) * Y_AXIS_HEIGHT
        plot_code += f"""
        \\draw[chosen_arrow] ({chosen_x}, {Y_AXIS_HEIGHT + 0.4}) -- ({chosen_x}, {ucb_y});
        \\node[chosen_tag, above] at ({chosen_x}, {Y_AXIS_HEIGHT + 0.4}) {{Chosen}};
        """
        
    # --- CORRECTED CODE ENDS HERE ---
    # Properly close the tikzpicture and resizebox.
    plot_code += "\n\\end{tikzpicture}%\n}" 
    return plot_code

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['slides', 'animate'], default='slides')
    args = parser.parse_args()

    # --- Parameters ---
    NUM_ARMS = 6
    NUM_STEPS = 20 # Number of steps to animate *after* the initial pulls
    
    # Set a seed for reproducibility so the random means are the same every time
    np.random.seed(42)
    TRUE_MEANS = np.random.uniform(low=0, high=5, size=NUM_ARMS)

    # 1. First Pass: Run simulation to get data and max value
    simulation_history, max_ucb = run_ucb_simulation(NUM_ARMS, NUM_STEPS, TRUE_MEANS)

    # 2. Second Pass: Generate LaTeX
    if args.mode == 'animate':
        output = generate_animate_frames(simulation_history, max_ucb)
    else:
        output = generate_beamer_frames(simulation_history, max_ucb)
    
    print(output)