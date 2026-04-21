import numpy as np
import argparse
import sys

def generate_ellipsoid_tikz(center, cov_inv, alpha=0.5, resolution=15):
    """
    Generates TikZ/pgfplots code for a 3D ellipsoid.
    The ellipsoid is defined by (x-theta)^T A (x-theta) <= beta
    Here cov_inv is A / beta.
    """
    # Eigen decomposition to find axes
    # (x-c)^T M (x-c) = 1
    eigenvalues, eigenvectors = np.linalg.eigh(cov_inv)
    
    # Radii are 1/sqrt(eigenvalues)
    radii = 1.0 / np.sqrt(eigenvalues)
    
    # Parametric equations of a sphere
    u = np.linspace(0, 2 * np.pi, resolution)
    v = np.linspace(0, np.pi, resolution)
    
    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones(np.size(u)), np.cos(v))
    
    # Scale and rotate
    # Points in sphere space
    pts = np.stack([x.flatten() * radii[0], y.flatten() * radii[1], z.flatten() * radii[2]], axis=0)
    # Rotate to aligned space
    pts_rotated = eigenvectors @ pts
    # Translate to center
    pts_final = pts_rotated + center.reshape(3, 1)
    
    x_final = pts_final[0, :].reshape(x.shape)
    y_final = pts_final[1, :].reshape(y.shape)
    z_final = pts_final[2, :].reshape(z.shape)
    
    tikz = []
    tikz.append(f"\\addplot3[surf, colormap/cool, opacity={alpha}, shader=flat, samples={resolution}] coordinates {{")
    for i in range(resolution):
        line = ""
        for j in range(resolution):
            line += f"({x_final[i,j]:.3f}, {y_final[i,j]:.3f}, {z_final[i,j]:.3f}) "
        tikz.append(line)
    tikz.append("};")
    
    return "\n".join(tikz)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="animate")
    args = parser.parse_args()

    # Parameters
    d = 3
    T = 40
    lambda_reg = 1.0
    delta = 0.5
    true_theta = np.array([0.5, 0.5, 0.5])
    
    # Initialize
    A = lambda_reg * np.eye(d)
    b = np.zeros(d)
    theta_hat = np.zeros(d)
    
    # Random context vectors (arms) for simulation
    np.random.seed(42)
    
    frames = []
    
    # Axis limits - we'll keep them fixed
    LIM = 2.0
    
    for t in range(T):
        # Construct current ellipsoid
        # Confidence bound beta_t
        # Simplified beta_t for visualization: beta = sqrt(d * log(t+1))
        # We cap the scale so it's not "immense" at the start
        beta = 0.8 * np.sqrt(d * np.log((t + 2) / delta))
        
        # Ellipsoid matrix M = A / beta^2
        M = A / (beta**2)
        
        frame_code = []
        frame_code.append(f"% Frame {t}")
        frame_code.append("\\begin{tikzpicture}")
        frame_code.append(f"\\begin{{axis}}[view={{120}}{{30}}, width=10cm, height=10cm, xmin=-{LIM}, xmax={LIM}, ymin=-{LIM}, ymax={LIM}, zmin=-{LIM}, zmax={LIM}, axis lines=center, xlabel={{$x_1$}}, ylabel={{$x_2$}}, zlabel={{$x_3$}}]")
        
        # Plot True Theta
        frame_code.append(f"\\addplot3[only marks, mark=*, mark size=2pt, blue] coordinates {{({true_theta[0]}, {true_theta[1]}, {true_theta[2]})}};")
        frame_code.append(f"\\node[above, blue] at (axis cs:{true_theta[0]}, {true_theta[1]}, {true_theta[2]}) {{$\\theta^*$}};")
        
        # Plot Current Estimate
        frame_code.append(f"\\addplot3[only marks, mark=x, mark size=3pt, red] coordinates {{({theta_hat[0]}, {theta_hat[1]}, {theta_hat[2]})}};")
        frame_code.append(f"\\node[below, red] at (axis cs:{theta_hat[0]}, {theta_hat[1]}, {theta_hat[2]}) {{$\\hat{{\\theta}}_t$}};")
        
        # Plot Ellipsoid
        frame_code.append(generate_ellipsoid_tikz(theta_hat, M))
        
        frame_code.append("\\end{axis}")
        frame_code.append("\\end{tikzpicture}")
        frames.append("\n".join(frame_code))
        
        # Choose action (random for demo, or UCB)
        # For demo purposes, we pick a random unit vector and update
        x_t = np.random.normal(0, 1, d)
        x_t = x_t / np.linalg.norm(x_t)
        
        # Observe reward
        r_t = np.dot(x_t, true_theta) + np.random.normal(0, 0.1)
        
        # Update
        A += np.outer(x_t, x_t)
        b += r_t * x_t
        theta_hat = np.linalg.solve(A, b)

    if args.mode == "animate":
        print("\\begin{animateinline}[controls, autoplay, loop]{2}")
        for i, frame in enumerate(frames):
            print(frame)
            if i < len(frames) - 1:
                print("\\newframe")
        print("\\end{animateinline}")
    else:
        # Just print the last frame
        print(frames[-1])

if __name__ == "__main__":
    main()
