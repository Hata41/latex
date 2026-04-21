import numpy as np
import math

def run_eac_simulation(num_arms, exploration_pulls, commitment_pulls, true_means):
    """
    Pass 1: Simulate the entire Explore-and-Commit process to gather data for each frame.
    """
    history = []
    
    # --- State 1: Initial Frame ---
    # Nothing is known yet.
    history.append({
        'type': 'Initial',
        'arm_data': [{'mean': 0, 'ci': [0, 0], 'pulls': 0} for _ in range(num_arms)],
        'best_arm': None
    })

    # --- Phase 1: Exploration ---
    arm_data = [{'mean': 0, 'ci': [0, 0], 'pulls': 0} for _ in range(num_arms)]
    
    for i in range(num_arms):
        # Simulate 'exploration_pulls' for the current arm
        rewards = np.random.normal(true_means[i], 0.5, size=exploration_pulls)
        arm_data[i]['pulls'] = exploration_pulls
        arm_data[i]['mean'] = np.mean(rewards)
        
        # Calculate a simple confidence interval (proportional to 1/sqrt(n))
        ci_width = 1.0 / np.sqrt(exploration_pulls)
        arm_data[i]['ci'] = [arm_data[i]['mean'] - ci_width, arm_data[i]['mean'] + ci_width]

        # Add a frame to the history after each arm is explored
        history.append({
            'type': 'Exploration',
            'arm_data': [d.copy() for d in arm_data], # Store a snapshot
            'explored_upto': i, # Note which arm was just revealed
            'best_arm': None
        })

    # --- State 3: Highlight Best Arm ---
    # Find the best arm based on the highest estimated mean after exploration
    estimated_means = [d['mean'] for d in arm_data]
    best_arm_idx = np.argmax(estimated_means)
    
    history.append({
        'type': 'Highlight',
        'arm_data': [d.copy() for d in arm_data],
        'explored_upto': num_arms - 1,
        'best_arm': best_arm_idx
    })

    # --- Phase 2: Commitment ---
    for t in range(commitment_pulls):
        # Store the state of the best arm's CI *before* this pull, for the ghost
        previous_ci = arm_data[best_arm_idx]['ci'][:]

        # Simulate one more pull for the best arm
        reward = np.random.normal(true_means[best_arm_idx], 0.5)
        
        # Update mean and pull count incrementally
        current_mean = arm_data[best_arm_idx]['mean']
        current_pulls = arm_data[best_arm_idx]['pulls']
        new_mean = (current_mean * current_pulls + reward) / (current_pulls + 1)
        arm_data[best_arm_idx]['pulls'] += 1
        arm_data[best_arm_idx]['mean'] = new_mean
        
        # Recalculate and narrow the confidence interval
        new_ci_width = 1.0 / np.sqrt(arm_data[best_arm_idx]['pulls'])
        arm_data[best_arm_idx]['ci'] = [new_mean - new_ci_width, new_mean + new_ci_width]

        history.append({
            'type': 'Commitment',
            'arm_data': [d.copy() for d in arm_data],
            'explored_upto': num_arms - 1,
            'best_arm': best_arm_idx,
            'previous_ci': previous_ci # Remember the last CI for the ghost effect
        })

    return history

def generate_beamer_frames(history, num_arms):
    """
    Pass 2: Generate the LaTeX frames using the pre-computed simulation data.
    """
    latex_code = ""
    # For this algorithm, reward is often normalized, so we can use a fixed Y-axis.
    plot_ymax = 1.5 

    for i, state in enumerate(history):
        # Determine the frame title
        if state['type'] == 'Initial':
            frame_title = "Explore and Commit Algorithm"
        elif state['type'] == 'Exploration' or state['type'] == 'Highlight':
            frame_title =  "Explore and Commit Algorithm"
        else: # Commitment
            frame_title =  "Explore and Commit Algorithm"

        latex_code += f"\\begin{{frame}}{{{frame_title}}}\n"
        # We also pass the full history and current index to handle slide overlays correctly
        latex_code += _draw_eac_plot(state, plot_ymax, num_arms)
        latex_code += "\n\\end{frame}\n"
        
    return latex_code

def _draw_eac_plot(state, plot_ymax, num_arms):
    """
    Draws a single TikZ plot for a given state in the EAC simulation.
    """
    Y_AXIS_HEIGHT = 5.0
    PLOT_WIDTH = 11.0
    x_step = PLOT_WIDTH / (num_arms + 1)

    plot_code = r"""
\centering
\begin{tikzpicture}[
    axis/.style={->, >=Stealth, thick},
    arm_label/.style={font=\bfseries, below, yshift=-5pt},
    ci_bar/.style={line width=8pt, cap=round, blue!60, opacity=0.8},
    ghost_ci/.style={line width=8pt, cap=round, blue!60, opacity=0.15},
    mean_dot/.style={circle, fill=red, inner sep=2.5pt},
    highlight_box/.style={draw=red, thick, rounded corners, fill=red, fill opacity=0.1}
]
"""
    # --- Static Axis Generation ---
    plot_code += f"""
    % Axes
    \\draw[axis] (0,0) -- (0, {Y_AXIS_HEIGHT + 0.5}) node[above] {{Mean Reward}};
    \\draw[axis] (0,0) -- ({PLOT_WIDTH + 0.75}, 0) node[right] {{Arms}};

    % Y-axis labels
    \\foreach \\y in {{0, 0.5, ..., {plot_ymax}}} {{
        \\pgfmathsetmacro{{\\ycoord}}{{\\y / {plot_ymax} * {Y_AXIS_HEIGHT}}}
        \\draw (-0.1, \\ycoord) -- (0.1, \\ycoord) node[left] {{\\pgfmathprintnumber[fixed, precision=1]{{\\y}}}};
    }}

    % Arm labels
    \\foreach \\i in {{1,...,{num_arms}}} {{ \\node[arm_label] at (\\i*{x_step}, 0) {{Arm \\i}}; }}
    """

    # --- Dynamic Data Plotting based on state type ---
    arm_data = state['arm_data']
    
    if state['type'] == 'Initial':
        for i in range(num_arms):
             plot_code += f"\\draw[ci_bar, opacity=0.3] ({(i+1)*x_step}, 0) -- ({(i+1)*x_step}, {Y_AXIS_HEIGHT});\n"

    elif state['type'] in ['Exploration', 'Highlight', 'Commitment']:
        # Draw all explored arms
        for i in range(state['explored_upto'] + 1):
            mean, ci = arm_data[i]['mean'], arm_data[i]['ci']
            mean_y = (mean / plot_ymax) * Y_AXIS_HEIGHT
            ci_low_y = max(0, (ci[0] / plot_ymax) * Y_AXIS_HEIGHT)
            ci_high_y = (ci[1] / plot_ymax) * Y_AXIS_HEIGHT
            x_pos = (i + 1) * x_step

            # For the commitment phase, the non-best arms are static
            # The best arm has special drawing rules
            if state['type'] == 'Commitment' and i == state['best_arm']:
                # Draw the ghost of the previous CI
                prev_ci = state['previous_ci']
                prev_low_y = max(0, (prev_ci[0] / plot_ymax) * Y_AXIS_HEIGHT)
                prev_high_y = (prev_ci[1] / plot_ymax) * Y_AXIS_HEIGHT
                plot_code += f"\\draw[ghost_ci] ({x_pos}, {prev_low_y}) -- ({x_pos}, {prev_high_y});\n"

            plot_code += f"\\draw[ci_bar] ({x_pos}, {ci_low_y}) -- ({x_pos}, {ci_high_y});\n"
            plot_code += f"\\node[mean_dot] at ({x_pos}, {mean_y}) {{}};\n"
    
    # Add highlight box for Highlight and Commitment phases
    if state['type'] in ['Highlight', 'Commitment']:
        best_arm_idx = state['best_arm']
        ci = arm_data[best_arm_idx]['ci']
        ci_low_y = max(0, (ci[0] / plot_ymax) * Y_AXIS_HEIGHT)
        ci_high_y = (ci[1] / plot_ymax) * Y_AXIS_HEIGHT
        x_pos = (best_arm_idx + 1) * x_step
        box_width = x_step * 0.4 # Make the box proportional to the arm spacing
        plot_code += f"\\draw[highlight_box] ({x_pos-box_width}, {ci_low_y}) rectangle ({x_pos+box_width}, {ci_high_y});\n"
        
    plot_code += "\n\\end{tikzpicture}"
    return plot_code

if __name__ == '__main__':
    # --- Parameters ---
    NUM_ARMS = 5
    EXPLORATION_PULLS = 20 # How many times each arm is pulled in Phase 1
    COMMITMENT_PULLS = 15   # How many times the best arm is pulled in Phase 2
    
    # Set a seed for reproducibility
    np.random.seed(123)
    TRUE_MEANS = np.random.uniform(low=0.2, high=0.9, size=NUM_ARMS)

    # 1. First Pass: Run simulation to get the history of states
    simulation_history = run_eac_simulation(NUM_ARMS, EXPLORATION_PULLS, COMMITMENT_PULLS, TRUE_MEANS)

    # 2. Second Pass: Generate LaTeX frames from the history
    beamer_frames = generate_beamer_frames(simulation_history, NUM_ARMS)
    
    print(beamer_frames)