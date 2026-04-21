import numpy as np
import math
import argparse

def run_elimination_simulation(num_arms, pulls_per_stage, true_means):
    """
    Pass 1: Simulate the Successive Elimination algorithm to gather data for each animation frame.
    Now eliminates at most one arm per stage.
    """
    history = []
    active_arms = list(range(num_arms))
    eliminated_arms = []
    stage_num = 0
    
    # Initial state
    history.append({'type': 'Initial', 'stage': 0, 'arm_data': [], 'active_arms': active_arms, 'eliminated_arms': []})

    # Main loop: Continue as long as there is more than one active arm
    while len(active_arms) > 1 and stage_num < len(pulls_per_stage):
        stage_num += 1
        num_pulls = pulls_per_stage[stage_num - 1]
        
        # --- Simulate pulling arms for the current stage ---
        arm_data = []
        for i in range(num_arms):
            if i in active_arms:
                # Simulate new pulls and calculate CI
                rewards = np.random.normal(true_means[i], 0.5, size=num_pulls)
                mean = np.mean(rewards)
                ci_width = 2.0 / np.sqrt(num_pulls) # Confidence interval width shrinks with more pulls
                arm_data.append({'status': 'active', 'mean': mean, 'ci': [mean - ci_width, mean + ci_width]})
            else:
                # Keep the data from the last stage it was active, but mark as eliminated
                arm_data.append(history[-1]['arm_data'][i])

        history.append({'type': 'Stage_Update', 'stage': stage_num, 'arm_data': arm_data, 'active_arms': active_arms, 'eliminated_arms': eliminated_arms})

        # --- Determine eliminations for this stage ---
        active_arm_data = [(i, arm_data[i]) for i in active_arms]
        
        # Find the arm with the highest Lower Confidence Bound (LCB) among active arms
        best_lcb = -float('inf')
        best_lcb_arm_idx = -1
        for idx, data in active_arm_data:
            if data['ci'][0] > best_lcb:
                best_lcb = data['ci'][0]
                best_lcb_arm_idx = idx

        # MODIFIED LOGIC: Find all potential arms to eliminate
        elimination_candidates = []
        for idx, data in active_arm_data:
            # An arm is a candidate if its UCB is less than the best LCB
            if idx != best_lcb_arm_idx and data['ci'][1] < best_lcb:
                elimination_candidates.append({'ucb': data['ci'][1], 'idx': idx})
        
        arms_to_eliminate_this_stage = []
        justification_pairs = []

        # If there are candidates, eliminate only the one with the lowest UCB
        if elimination_candidates:
            # Sort candidates by their UCB to find the worst one
            worst_candidate = min(elimination_candidates, key=lambda x: x['ucb'])
            worst_arm_idx = worst_candidate['idx']
            
            arms_to_eliminate_this_stage.append(worst_arm_idx)
            justification_pairs.append((worst_arm_idx, best_lcb_arm_idx))
        
        # If any arms are to be eliminated, create justification and result frames
        if arms_to_eliminate_this_stage:
            history.append({'type': 'Stage_Justify', 'stage': stage_num, 'arm_data': arm_data, 'active_arms': active_arms, 'eliminated_arms': eliminated_arms, 'justifications': justification_pairs})
            
            # Update the lists of active and eliminated arms
            new_active_arms = [i for i in active_arms if i not in arms_to_eliminate_this_stage]
            eliminated_arms.extend(arms_to_eliminate_this_stage)
            active_arms = new_active_arms

            # Update the status in arm_data for the result frame
            for i in arms_to_eliminate_this_stage:
                arm_data[i]['status'] = 'eliminated'
            history.append({'type': 'Stage_Result', 'stage': stage_num, 'arm_data': arm_data, 'active_arms': active_arms, 'eliminated_arms': eliminated_arms})

    # Final "Winner" state if we have a single arm left
    if len(active_arms) == 1:
        history.append({'type': 'Winner', 'stage': stage_num + 1, 'arm_data': history[-1]['arm_data'], 'active_arms': active_arms, 'eliminated_arms': eliminated_arms})
    
    return history

def generate_beamer_frames(history, num_arms):
    """
    Pass 2: Generate the LaTeX frames using the pre-computed simulation data.
    """
    latex_code = ""
    plot_ymax = 2.0  # We can use a fixed Y-axis for this algorithm
    frame_title = "Action Elimination" # MODIFIED: Title is now constant

    for state in history:
        latex_code += f"\\begin{{frame}}{{{frame_title}}}\n"
        latex_code += _draw_elimination_plot(state, plot_ymax, num_arms)
        latex_code += "\n\\end{frame}\n"
        
    return latex_code

def generate_animate_frames(history, num_arms):
    """
    Pass 2: Generate the LaTeX frames using the pre-computed simulation data for animate package.
    """
    latex_code = ""
    plot_ymax = 2.0
    frame_title = "Action Elimination"

    latex_code += f"\\begin{{frame}}{{{frame_title}}}\n"
    latex_code += r"\centering" + "\n"
    latex_code += r"\begin{animateinline}[controls, loop]{2}" + "\n"

    for i, state in enumerate(history):
        latex_code += _draw_elimination_plot(state, plot_ymax, num_arms)
        if i < len(history) - 1:
            latex_code += "\n\\newframe\n"

    latex_code += "\n\\end{animateinline}\n"
    latex_code += "\\end{frame}\n"
    return latex_code

def _draw_elimination_plot(state, plot_ymax, num_arms):
    """
    Draws a single TikZ plot for a given state in the elimination simulation.
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
    elim_ci/.style={line width=8pt, cap=round, gray, opacity=0.4},
    mean_dot/.style={circle, fill=red, inner sep=2.5pt},
    elim_dot/.style={circle, fill=gray, inner sep=2.5pt, opacity=0.5},
    winner_box/.style={draw=green!50!black, thick, rounded corners, fill=green, fill opacity=0.1},
    elim_line/.style={draw=red, dashed, thick, ->},
]
"""
    # --- Static Axis Generation ---
    plot_code += f"""
    % Axes and Labels
    \\draw[axis] (0,0) -- (0, {Y_AXIS_HEIGHT + 0.5}) node[above] {{Mean Reward}};
    \\draw[axis] (0,0) -- ({PLOT_WIDTH + 0.75}, 0) node[right] {{Actions}};
    \\foreach \\y in {{0, 0.5, ..., {plot_ymax}}} {{
        \\pgfmathsetmacro{{\\ycoord}}{{\\y / {plot_ymax} * {Y_AXIS_HEIGHT}}}
        \\draw (-0.1, \\ycoord) -- (0.1, \\ycoord) node[left] {{\\pgfmathprintnumber[fixed, precision=1]{{\\y}}}};
    }}
    \\foreach \\i in {{1,...,{num_arms}}} {{ \\node[arm_label] at (\\i*{x_step}, 0) {{Action \\i}}; }}
    """

    # --- Dynamic Data Plotting ---
    if state['type'] == 'Initial':
        for i in range(num_arms):
            plot_code += f"\\draw[ci_bar, opacity=0.2] ({(i+1)*x_step}, 0) -- ({(i+1)*x_step}, {Y_AXIS_HEIGHT});\n"
    else:
        # Draw CIs and dots for all arms based on their status
        for i, data in enumerate(state['arm_data']):
            x_pos = (i + 1) * x_step
            mean_y = (data['mean'] / plot_ymax) * Y_AXIS_HEIGHT
            ci_low_y = max(0, (data['ci'][0] / plot_ymax) * Y_AXIS_HEIGHT)
            ci_high_y = (data['ci'][1] / plot_ymax) * Y_AXIS_HEIGHT
            
            style_prefix = "elim_" if data['status'] == 'eliminated' else ""
            ci_style = f"{style_prefix}ci" if style_prefix else "ci_bar"
            dot_style = f"{style_prefix}dot" if style_prefix else "mean_dot"
            
            plot_code += f"\\draw[{ci_style}] ({x_pos}, {ci_low_y}) -- ({x_pos}, {ci_high_y});\n"
            plot_code += f"\\node[{dot_style}] at ({x_pos}, {mean_y}) {{}};\n"

        # REMOVED: The elimination crosses are no longer drawn

        # Draw justification lines
        if state['type'] == 'Stage_Justify':
            for elim_idx, best_idx in state['justifications']:
                elim_data = state['arm_data'][elim_idx]
                best_data = state['arm_data'][best_idx]
                elim_x, best_x = (elim_idx + 1) * x_step, (best_idx + 1) * x_step
                elim_ucb_y = (elim_data['ci'][1] / plot_ymax) * Y_AXIS_HEIGHT
                best_lcb_y = (best_data['ci'][0] / plot_ymax) * Y_AXIS_HEIGHT
                plot_code += f"\\draw[elim_line] ({elim_x}, {elim_ucb_y}) -- ({best_x}, {best_lcb_y});\n"

        # Draw winner box
        if state['type'] == 'Winner' and state['active_arms']:
            winner_idx = state['active_arms'][0]
            winner_data = state['arm_data'][winner_idx]
            x_pos = (winner_idx + 1) * x_step
            ci_low_y = max(0, (winner_data['ci'][0] / plot_ymax) * Y_AXIS_HEIGHT)
            ci_high_y = (winner_data['ci'][1] / plot_ymax) * Y_AXIS_HEIGHT
            box_width = x_step * 0.4
            plot_code += f"\\draw[winner_box] ({x_pos-box_width}, {ci_low_y}) rectangle ({x_pos+box_width}, {ci_high_y});\n"

    plot_code += "\n\\end{tikzpicture}"
    return plot_code

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['slides', 'animate'], default='slides')
    args = parser.parse_args()

    # --- Parameters ---
    NUM_ARMS = 5
    # A constant budget of 20 pulls per active arm in each stage
    PULLS_PER_STAGE = [20] * 50 
    
    np.random.seed(42)
    # Generate true means for the arms, ensuring one is clearly optimal
    TRUE_MEANS = np.random.uniform(low=0.6, high=0.9, size=NUM_ARMS)
    TRUE_MEANS[np.random.randint(NUM_ARMS)] = 1.5

    # 1. First Pass: Run simulation
    simulation_history = run_elimination_simulation(NUM_ARMS, PULLS_PER_STAGE, TRUE_MEANS)

    # 2. Second Pass: Generate LaTeX
    if args.mode == 'animate':
        output = generate_animate_frames(simulation_history, NUM_ARMS)
    else:
        output = generate_beamer_frames(simulation_history, NUM_ARMS)
    
    print(output)