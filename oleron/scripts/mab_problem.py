
import numpy as np
import math
import argparse

def generate_random_arm_data(num_arms):
    """
    Generates a list of arm properties with randomized means and standard deviations.
    The positions and colors are assigned algorithmically to ensure good spacing and visuals.
    """
    arm_data = []
    # A list of visually distinct colors to cycle through
    COLORS = ["cyan", "orange", "green!60!black", "violet", "red!80!black", "blue!70!black", "brown"]
    PLOT_WIDTH = 10.0 # The logical width of the plotting area in TikZ units

    for i in range(num_arms):
        # Evenly space the arms across the plot width
        x_position = (i + 1.0) * PLOT_WIDTH / (num_arms + 1.0)
        
        arm = {
            "label": f"A_{{{i+1}}}",
            "x_pos": x_position,
            "mean": np.random.uniform(low=2.0, high=4.5),
            "std": np.random.uniform(low=0.4, high=0.9),
            "color": COLORS[i % len(COLORS)], # Cycle through colors if we have many arms
            "width_scale": 2.0,  # Visual scaling for the plot width
        }
        arm_data.append(arm)
        
    return arm_data

def generate_beamer_frame(arm_data):
    """
    Generates the Beamer frame for the Multi-Armed Bandit problem visualization.
    """
    plot_code = _draw_mab_problem_plot(arm_data)
    
    latex_code = f"""
\\begin{{frame}}{{The Multi-Armed Bandit Problem}}
\\centering
{plot_code}
\\end{{frame}}
"""
    return latex_code

def _draw_mab_problem_plot(arm_data):
    """
    Generates the TikZ code for the animated MAB problem plot.
    The axes are now dynamically sized to fit the data perfectly.
    """
    # --- Dynamic Axis Calculation ---
    if not arm_data:
        return "\\begin{tikzpicture}\\node{No arm data provided.};\\end{tikzpicture}"

    max_x = arm_data[-1]['x_pos'] + 1.5 
    max_y_val = max(arm['mean'] + 3 * arm['std'] for arm in arm_data)
    max_y = math.ceil(max_y_val)
    
    # --- TikZ Code Generation ---
    plot_code = f"""
\\begin{{tikzpicture}}[font=\\small, >=Stealth]

% =======================
% 1) AXES AND ARM LABELS (slide 1)
% =======================
\\only<1->{{
  % Axes (now with dynamic limits)
  \\draw[-{{Stealth[length=3mm]}}, thick] (0,0) -- ({max_x},0) node[below right] {{Actions}};
  \\draw[-{{Stealth[length=3mm]}}, thick] (0,0) -- (0,{max_y + 0.2}) node[above left] {{Reward}};

  % Arm labels
"""
    for arm in arm_data:
        plot_code += f"  \\node[font=\\bfseries] at ({arm['x_pos']},-0.35) {{\\({arm['label']}\\)}};\n"
    plot_code += "}\n"

    # =======================
    # 2) DISTRIBUTIONS (animated)
    # =======================
    for i, arm in enumerate(arm_data):
        slide_num = i + 2
        domain_min = arm['mean'] - 3 * arm['std']
        domain_max = arm['mean'] + 3 * arm['std']
        pdf_formula = f"({arm['width_scale']}*(1/({arm['std']}*sqrt(2*pi)))*exp(-(\\t-{arm['mean']})^2/(2*{arm['std']}^2)))"

        plot_code += f"""
% Arm {i+1} appears on slide {slide_num}
\\only<{slide_num}->{{
  \\path[fill={arm['color']}, fill opacity=0.25, draw={arm['color']}!70!black, line width=0.8pt]
    plot[domain={domain_min}:{domain_max}, samples=160, variable=\\t]
      ({{{arm['x_pos']} + {pdf_formula}}}, {{\\t}})
    -- ({arm['x_pos']},{domain_max}) -- ({arm['x_pos']},{domain_min}) -- cycle;
  \\draw[dashed, {arm['color']}!60!black, thick] ({arm['x_pos']-0.4},{arm['mean']}) -- ({arm['x_pos']+0.4},{arm['mean']});
  \\node[right, {arm['color']}!60!black] at ({arm['x_pos']+0.45},{arm['mean']}) {{\\(\\mu_{{{i+1}}}\\)}};
}}
"""

    # =======================
    # 3) OPTIMAL ARM ANNOTATION (final slide, in top-right corner)
    # =======================
    # The last curve appears on slide N+1. This annotation appears on N+2.
    annotation_slide_num = len(arm_data) + 2
    
    means = [arm['mean'] for arm in arm_data]
    optimal_idx = np.argmax(means)
    optimal_arm_color = arm_data[optimal_idx]['color']
    mu_labels = ",".join([f"\\mu_{{{j+1}}}" for j in range(len(arm_data))])

    # --- THIS IS THE MODIFIED PART ---
    # The node now uses \mu_{\star} and appears on its own dedicated slide.
    plot_code += f"""
% Indicate the optimal mean on its own slide
\\only<{annotation_slide_num}>{{
  \\node[font=\\bfseries, color={optimal_arm_color}!80!black, anchor=north east, align=left] 
    at ({{ {max_x} - 0.2 }}, {{ {max_y} }}) 
    {{\\(\\mu_{{\\star}} = \\max\\{{{mu_labels}\\}}\\)}};
}}
"""

    plot_code += "\n\\end{tikzpicture}"
    return plot_code

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['slides', 'animate'], default='slides')
    args = parser.parse_args()

    # TODO: Implement animate mode for overlay-based scripts

    # --- Configuration ---
    # SET THE DESIRED NUMBER OF ARMS HERE
    NUM_ARMS = 4 

    # Set a seed for reproducibility. Change the number to get a new random layout.
    np.random.seed(42) 

    # --- Data and LaTeX Generation ---
    # 1. Programmatically generate the arm data based on the configuration
    arm_data = generate_random_arm_data(NUM_ARMS)
    
    # 2. Generate the corresponding Beamer frame
    beamer_frame_output = generate_beamer_frame(arm_data)
    
    print(beamer_frame_output)