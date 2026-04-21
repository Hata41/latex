import numpy as np
import math
import argparse

def run_offline_rl_simulation(true_means, num_samples, behavior_policies, lcb_penalty_coeff=1.5):
    """
    Simulates a multi-armed bandit problem under different offline datasets.
    This pass gathers all necessary data for LaTeX generation.
    """
    num_arms = len(true_means)
    simulation_results = {}

    for key, params in behavior_policies.items():
        # Generate a dataset by sampling from the behavior policy
        pulled_arms = np.random.choice(num_arms, size=num_samples, p=params['mu'])
        rewards = np.random.normal(loc=true_means[pulled_arms], scale=0.5)
        
        # --- Analyze the generated dataset ---
        counts = np.array([np.sum(pulled_arms == i) for i in range(num_arms)])
        
        # Calculate empirical (observed) means, handle arms with 0 pulls
        empirical_means = np.zeros(num_arms)
        for i in range(num_arms):
            if counts[i] > 0:
                empirical_means[i] = np.mean(rewards[pulled_arms == i])

        # --- Run LCB Algorithm ---
        with np.errstate(divide='ignore', invalid='ignore'):
            penalty = lcb_penalty_coeff * np.sqrt(np.log(num_samples) / counts)
        penalty[np.isinf(penalty)] = np.finfo(np.float32).max

        lcb_scores = empirical_means - penalty
        arm_lcb = np.argmax(lcb_scores)

        # --- Identify Empirical Best and Most Played Arms ---
        arm_naive = np.argmax(empirical_means)
        arm_most_played = np.argmax(counts)

        simulation_results[key] = {
            "name": params['name'],
            "mu": params['mu'],
            "true_means": true_means,
            "counts": counts,
            "empirical_means": empirical_means,
            "lcb_scores": lcb_scores,
            "penalty": penalty,
            "chosen_arm_lcb": arm_lcb,
            "chosen_arm_naive": arm_naive,
            "chosen_arm_most_played": arm_most_played,
            "optimal_arm": np.argmax(true_means)
        }
        
    return simulation_results

def generate_beamer_frames(results):
    """
    Generates all Beamer frames based on the simulation results.
    """
    latex_code = ""
    
    # Generate a frame for each dataset scenario
    for key, data in results.items():
        latex_code += _generate_scenario_frame(data)

    # Generate the algorithm analysis frame, using the uniform coverage case for visualization
    latex_code += _generate_analysis_frame(results.get('uniform', list(results.values())[0]))
    
    return latex_code

def _generate_scenario_frame(data):
    """Generates a frame visualizing the dataset properties for one scenario."""
    plot_code = _draw_scenario_plots(data)
    return f"""
\\begin{{frame}}{{{data['name']}: Dataset Composition}}
    {plot_code}
\\end{{frame}}
"""

def _draw_scenario_plots(data):
    """Generates TikZ code for the three bar charts using ybar interval."""
    num_arms = len(data['true_means'])
    
    mu_coords = "".join([f"({i + 0.5}, {p:.2f})" for i, p in enumerate(data['mu'])]) + f"({num_arms + 0.5}, 0)"
    reward_coords = "".join([f"({i + 0.5}, {r:.2f})" for i, r in enumerate(data['true_means'])]) + f"({num_arms + 0.5}, 0)"
    counts_coords = "".join([f"({i + 0.5}, {c})" for i, c in enumerate(data['counts'])]) + f"({num_arms + 0.5}, 0)"
    
    return f"""
\\begin{{columns}}[T,onlytextwidth]
\\begin{{column}}{{0.33\\textwidth}}
    \\begin{{tikzpicture}}
    \\begin{{axis}}[ width=\\textwidth, height=6cm, title={{\\textbf{{Behavior Policy}}}}, ybar interval, xmin=0.5, xmax={num_arms + 0.5}, xtick={{{",".join(map(str, range(1, num_arms + 1)))}}}, ymin=0, ylabel={{Probability}}, xlabel={{Arm}} ] \\addplot coordinates {{{mu_coords}}}; \\end{{axis}}
    \\end{{tikzpicture}}
\\end{{column}}
\\begin{{column}}{{0.33\\textwidth}}
    \\begin{{tikzpicture}}
    \\begin{{axis}}[ width=\\textwidth, height=6cm, title={{\\textbf{{True Rewards}}}}, ybar interval, xmin=0.5, xmax={num_arms + 0.5}, xtick={{{",".join(map(str, range(1, num_arms + 1)))}}}, ymin=0, ylabel={{Mean Reward}}, xlabel={{Arm}}, fill=red!50, draw=red!80 ] \\addplot coordinates {{{reward_coords}}}; \\end{{axis}}
    \\end{{tikzpicture}}
\\end{{column}}
\\begin{{column}}{{0.33\\textwidth}}
    \\begin{{tikzpicture}}
    \\begin{{axis}}[ width=\\textwidth, height=6cm, title={{\\textbf{{Offline Samples}}}}, ybar interval, xmin=0.5, xmax={num_arms + 0.5}, xtick={{{",".join(map(str, range(1, num_arms + 1)))}}}, ymin=0, ylabel={{Number of Pulls}}, xlabel={{Arm}}, fill=blue!50, draw=blue!80 ] \\addplot coordinates {{{counts_coords}}}; \\end{{axis}}
    \\end{{tikzpicture}}
\\end{{column}}
\\end{{columns}}
"""

def _generate_analysis_frame(data):
    """Generates the frame explaining and comparing the offline policy selection algorithms."""
    plot_code = _draw_lcb_plot(data)
    return f"""
\\begin{{frame}}{{Offline Policy Selection: Comparing Strategies}}
    {plot_code}
\\end{{frame}}
"""

def _draw_lcb_plot(data):
    """Draws the TikZ plot for the algorithm visualization with a step-by-step animation sequence."""
    PLOT_WIDTH = 11.0
    Y_AXIS_HEIGHT = 5.0  # Added missing constant
    num_arms = len(data['true_means'])
    x_step = PLOT_WIDTH / (num_arms + 1)
    plot_ymax = math.ceil(np.max(data['empirical_means'] + data['penalty']))
    
    plot_code = f"""
\\begin{{center}}
\\resizebox{{0.95\\textwidth}}{{!}}{{
\\begin{{tikzpicture}}[
    axis/.style={{->, >=Stealth, thick}},
    ci_bar/.style={{line width=12pt, cap=round, blue!60, opacity=0.35}},
    mean_dot/.style={{circle, fill=red, inner sep=2.5pt}},
    pull_count_text/.style={{font=\\small\\sffamily, fill=white, fill opacity=0.7, text opacity=1, inner sep=1.5pt}},
    lcb_marker/.style={{diamond, fill=green!60!black, inner sep=2.5pt}},
    lcb_tag/.style={{font=\\bfseries\\small, fill=green!10, draw=green!60!black, rounded corners, inner sep=2pt}},
    naive_marker/.style={{star, star points=5, star point ratio=0.5, fill=red!80, inner sep=2.5pt}},
    naive_tag/.style={{font=\\bfseries\\small, fill=red!10, draw=red!80, rounded corners, inner sep=2pt}},
    most_played_marker/.style={{regular polygon, regular polygon sides=4, fill=orange!90!black, inner sep=3pt}},
    most_played_tag/.style={{font=\\bfseries\\small, fill=orange!10, draw=orange!90!black, rounded corners, inner sep=2pt}}
]
    % Axes
    \\draw[axis] (0,0) -- (0, {Y_AXIS_HEIGHT + 0.5}) node[above] {{Reward Estimate}};
    \\draw[axis] (0,0) -- ({PLOT_WIDTH + 0.75}, 0) node[right] {{Arms}};
"""
    
    plot_code += f"""
    \\foreach \\y in {{0, 0.5, ..., {int(plot_ymax)}}} {{
        \\pgfmathsetmacro{{\\ycoord}}{{\\y / {plot_ymax} * {Y_AXIS_HEIGHT}}};
        \\draw (-0.1, \\ycoord) -- (0.1, \\ycoord) node[left] {{\\pgfmathprintnumber[fixed, precision=1]{{\\y}}}};
    }}
    \\foreach \\i in {{1,...,{num_arms}}} {{ \\node[font=\\bfseries, below, yshift=-5pt] at (\\i*{x_step}, 0) {{Arm \\i}}; }}
    \\node[below=1.5cm, align=center] at ({PLOT_WIDTH/2}, 0) {{Analysis of Dataset from "{data['name']}"}};
"""

    # Plotting data for each arm
    for i in range(num_arms):
        x_pos = (i + 1) * x_step
        emp_mean = data['empirical_means'][i]
        lcb_score = data['lcb_scores'][i]
        upper_bound = emp_mean + data['penalty'][i]
        pull_count = data['counts'][i]
        
        mean_y = (emp_mean / plot_ymax) * Y_AXIS_HEIGHT if plot_ymax > 0 else 0
        lcb_y = max(0, (lcb_score / plot_ymax) * Y_AXIS_HEIGHT) if plot_ymax > 0 else 0
        ub_y = (upper_bound / plot_ymax) * Y_AXIS_HEIGHT if plot_ymax > 0 else 0
        
        plot_code += f"""
        % --- Arm {i+1} Data Points ---
        % 1. Show empirical means first on slide 1+
        \\uncover<1->{{\\node[mean_dot] at ({x_pos}, {mean_y}) {{}};}}
        % 3. Then, show confidence bars and pull counts on slide 3+
        \\uncover<3->{{
            \\draw[ci_bar] ({x_pos}, {lcb_y}) -- ({x_pos}, {ub_y});
            \\node[pull_count_text, above, yshift=3pt] at ({x_pos}, {ub_y}) {{N={pull_count}}};
        }}
"""

    # --- Annotations for chosen arms in the specified sequence ---
    
    # 2. Naive (Empirical Best) Choice appears on slide 2+
    naive_choice_idx = data['chosen_arm_naive']
    naive_choice_x = (naive_choice_idx + 1) * x_step
    naive_choice_y = (data['empirical_means'][naive_choice_idx] / plot_ymax) * Y_AXIS_HEIGHT if plot_ymax > 0 else 0
    plot_code += f"""
    \\uncover<2->{{
        \\node[naive_marker] at ({naive_choice_x}, {naive_choice_y}) {{}};
        \\node[naive_tag, above, yshift=5pt] at ({naive_choice_x}, {naive_choice_y}) {{Empirical Best}};
    }}
"""

    # 4. Most Played Arm Choice appears on slide 4+
    mp_choice_idx = data['chosen_arm_most_played']
    mp_choice_x = (mp_choice_idx + 1) * x_step
    mp_choice_y = (data['empirical_means'][mp_choice_idx] / plot_ymax) * Y_AXIS_HEIGHT if plot_ymax > 0 else 0
    plot_code += f"""
    \\uncover<4->{{
        \\node[most_played_marker] at ({mp_choice_x}, {mp_choice_y}) {{}};
        \\node[most_played_tag, right, xshift=5pt] at ({mp_choice_x}, {mp_choice_y}) {{Most Played}};
    }}
"""

    # 5. LCB Choice appears on slide 5+
    lcb_choice_idx = data['chosen_arm_lcb']
    lcb_choice_x = (lcb_choice_idx + 1) * x_step
    lcb_choice_y = max(0, (data['lcb_scores'][lcb_choice_idx] / plot_ymax) * Y_AXIS_HEIGHT) if plot_ymax > 0 else 0
    plot_code += f"""
    \\uncover<5->{{
        \\node[lcb_marker] at ({lcb_choice_x}, {lcb_choice_y}) {{}};
        \\node[lcb_tag, below, yshift=-5pt] at ({lcb_choice_x}, {lcb_choice_y}) {{LCB Choice}};
    }}
"""

    plot_code += "\\end{tikzpicture}%\n}\n\\end{center}"
    return plot_code


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['slides', 'animate'], default='slides')
    args = parser.parse_args()

    # TODO: Implement animate mode for overlay-based scripts

    # --- Configuration ---
    NUM_ARMS = 5
    NUM_SAMPLES = 300 
    EXPERT_POLICY_CONCENTRATION = 10.0
    np.random.seed(101) 

    # --- Problem Generation ---
    TRUE_MEANS = np.random.uniform(low=0.1, high=0.9, size=NUM_ARMS)
    
    def softmax(x, temp):
        e_x = np.exp(x * temp)
        return e_x / e_x.sum(axis=0)

    expert_mu = softmax(TRUE_MEANS, EXPERT_POLICY_CONCENTRATION)

    # --- Behavior Policies (Data-generating distributions) ---
    BEHAVIOR_POLICIES = {
        "expert": {
            "name": "Near-Expert",
            "mu": expert_mu
        },
        "uniform": {
            "name": "Uniform Coverage",
            "mu": np.ones(NUM_ARMS) / NUM_ARMS
        }
    }

    # --- Simulation and LaTeX Generation ---
    simulation_data = run_offline_rl_simulation(TRUE_MEANS, NUM_SAMPLES, BEHAVIOR_POLICIES)
    beamer_frames_output = generate_beamer_frames(simulation_data)
    print(beamer_frames_output)