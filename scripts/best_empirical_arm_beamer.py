import numpy as np
import math

def run_offline_simulation(true_means, num_samples, behavior_policies):
    """
    Simulates offline datasets and determines the choice of the 'Best Empirical Arm' algorithm.
    """
    num_arms = len(true_means)
    simulation_results = {}

    for key, params in behavior_policies.items():
        # Generate an offline dataset from the behavior policy
        pulled_arms = np.random.choice(num_arms, size=num_samples, p=params['mu'])
        rewards = np.random.normal(loc=true_means[pulled_arms], scale=0.5)
        
        counts = np.array([np.sum(pulled_arms == i) for i in range(num_arms)])
        
        # Calculate empirical means, handling arms with 0 pulls
        empirical_means = np.zeros(num_arms)
        for i in range(num_arms):
            if counts[i] > 0:
                empirical_means[i] = np.mean(rewards[pulled_arms == i])

        # Algorithm decision: choose arm with the highest empirical mean
        chosen_arm = np.argmax(empirical_means)

        simulation_results[key] = {
            "name": params['name'],
            "mu": params['mu'],
            "true_means": true_means,
            "counts": counts,
            "empirical_means": empirical_means,
            "chosen_arm": chosen_arm,
            "optimal_arm": np.argmax(true_means)
        }
        
    return simulation_results

def generate_beamer_frames(results):
    """
    Generates all Beamer frames based on the simulation results.
    """
    latex_code = ""
    
    # Generate a frame for each dataset scenario to show data composition
    for key, data in results.items():
        latex_code += _generate_scenario_frame(data)

    # Generate the algorithm explanation frame using the more interesting uniform case
    uniform_data = results.get('uniform', list(results.values())[0])
    latex_code += _generate_algorithm_frame(uniform_data)
    
    return latex_code

def _generate_scenario_frame(data):
    """Generates a frame visualizing the properties of a single offline dataset."""
    plot_code = _draw_scenario_plots(data)
    return f"""
\\begin{{frame}}{{{data['name']} Dataset}}
    {plot_code}
\\end{{frame}}
"""

def _draw_scenario_plots(data):
    """Generates TikZ code for the three bar charts: policy, rewards, and sample counts."""
    num_arms = len(data['true_means'])
    mu_coords = "".join([f"({i + 0.5}, {p:.2f})" for i, p in enumerate(data['mu'])]) + f"({num_arms + 0.5}, 0)"
    reward_coords = "".join([f"({i + 0.5}, {r:.2f})" for i, r in enumerate(data['true_means'])]) + f"({num_arms + 0.5}, 0)"
    counts_coords = "".join([f"({i + 0.5}, {c})" for i, c in enumerate(data['counts'])]) + f"({num_arms + 0.5}, 0)"
    
    return f"""
\\begin{{columns}}[T,onlytextwidth]
\\begin{{column}}{{0.33\\textwidth}}
    \\begin{{tikzpicture}}
    \\begin{{axis}}[
        width=\\textwidth, height=6cm, title={{\\textbf{{Behavior Policy}}}}, ybar interval,
        xmin=0.5, xmax={num_arms + 0.5}, xtick={{{",".join(map(str, range(1, num_arms + 1)))}}},
        ymin=0, ylabel={{Probability}}, xlabel={{Arm}},
    ]
    \\addplot coordinates {{{mu_coords}}};
    \\end{{axis}}\\end{{tikzpicture}}
\\end{{column}}
\\begin{{column}}{{0.33\\textwidth}}
    \\begin{{tikzpicture}}
    \\begin{{axis}}[
        width=\\textwidth, height=6cm, title={{\\textbf{{True Rewards}}}}, ybar interval,
        xmin=0.5, xmax={num_arms + 0.5}, xtick={{{",".join(map(str, range(1, num_arms + 1)))}}},
        ymin=0, ylabel={{Mean Reward}}, xlabel={{Arm}}, fill=red!50, draw=red!80
    ]
    \\addplot coordinates {{{reward_coords}}};
    \\end{{axis}}\\end{{tikzpicture}}
\\end{{column}}
\\begin{{column}}{{0.33\\textwidth}}
    \\begin{{tikzpicture}}
    \\begin{{axis}}[
        width=\\textwidth, height=6cm, title={{\\textbf{{Offline Samples}}}}, ybar interval,
        xmin=0.5, xmax={num_arms + 0.5}, xtick={{{",".join(map(str, range(1, num_arms + 1)))}}},
        ymin=0, ylabel={{Number of Pulls}}, xlabel={{Arm}}, fill=blue!50, draw=blue!80
    ]
    \\addplot coordinates {{{counts_coords}}};
    \\end{{axis}}\\end{{tikzpicture}}
\\end{{column}}
\\end{{columns}}
"""

def _generate_algorithm_frame(data):
    """Generates the frame explaining the 'Best Empirical Arm' selection logic."""
    num_arms = len(data['true_means'])
    chosen_arm_idx = data['chosen_arm']

    # Generate coordinates for the empirical means plot
    emp_coords = ""
    for i, mean in enumerate(data['empirical_means']):
        # Add an optional argument to color the chosen bar
        color_option = "[fill=green!60, draw=green!80]" if i == chosen_arm_idx else ""
        emp_coords += f"\\addplot+[ybar, bar width=15pt, fill=orange!60, draw=orange!80]{color_option} coordinates {{({i+1}, {mean:.3f})}};\n"
    
    return f"""
\\begin{{frame}}{{Strategy 1: Best Empirical Arm}}
\\begin{{center}}
\\begin{{tikzpicture}}
    \\begin{{axis}}[
        width=0.8\\textwidth, height=6cm,
        title={{Select arm with highest \\textbf{{empirical mean}} from "{data['name']}" data}},
        symbolic x coords={{{",".join([f"Arm {i+1}" for i in range(num_arms)])}}},
        xtick=data, ymin=0,
        ylabel={{Empirical Mean Reward}},
        nodes near coords, nodes near coords align={{vertical}},
        node near coords style={{font=\\small}},
    ]
    {emp_coords}
    \\end{{axis}}
\\end{{tikzpicture}}
\\end{{center}}
\\vfill
\\begin{{itemize}}
    \\item Simple and intuitive approach.
    \\item \\color{{red!80!black}}Warning: Highly sensitive to sampling noise. A suboptimal arm with few samples can appear best by chance.
\\end{{itemize}}
\\end{{frame}}
"""

if __name__ == '__main__':
    NUM_ARMS = 5
    NUM_SAMPLES = 200
    np.random.seed(42) 

    TRUE_MEANS = np.random.uniform(low=0.1, high=0.9, size=NUM_ARMS)
    
    # Define a near-expert policy using softmax
    def softmax(x, temp):
        e_x = np.exp(x * temp)
        return e_x / e_x.sum()
    expert_mu = softmax(TRUE_MEANS, 10.0)

    BEHAVIOR_POLICIES = {
        "expert": {"name": "Near-Expert", "mu": expert_mu},
        "uniform": {"name": "Uniform Coverage", "mu": np.ones(NUM_ARMS) / NUM_ARMS}
    }

    simulation_data = run_offline_simulation(TRUE_MEANS, NUM_SAMPLES, BEHAVIOR_POLICIES)
    beamer_frames_output = generate_beamer_frames(simulation_data)
    print(beamer_frames_output)