import random
import sys
import argparse
from collections import deque
import colorsys

sys.setrecursionlimit(2000)

class MazeGenerator:
    """Generates a perfect maze using an iterative DFS backtracker algorithm."""
    def __init__(self, width=41, height=31, seed=None):
        if seed is not None:
            random.seed(seed)
        self.width = width if width % 2 == 1 else width + 1
        self.height = height if height % 2 == 1 else height + 1
        self.grid, self.solution_path = [], []

    def generate(self):
        """Main method to create the maze and find its primary solution."""
        self.grid = [[1] * self.width for _ in range(self.height)]
        dirs = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        start_y, start_x = random.randrange(1, self.height, 2), random.randrange(1, self.width, 2)
        self.grid[start_y][start_x] = 0
        
        stack = [(start_y, start_x)]
        while stack:
            y, x = stack[-1]
            neighbors = []
            for dy, dx in dirs:
                ny, nx = y + dy, x + dx
                if 1 <= ny < self.height - 1 and 1 <= nx < self.width - 1 and self.grid[ny][nx] == 1:
                    neighbors.append((ny, nx, y + dy // 2, x + dx // 2))
            
            if neighbors:
                ny, nx, wy, wx = random.choice(neighbors)
                self.grid[wy][wx], self.grid[ny][nx] = 0, 0
                stack.append((ny, nx))
            else:
                stack.pop()

        border_cells = self._get_border_cells()
        entry_pair = max(((a, b) for i, a in enumerate(border_cells) for b in border_cells[i+1:]),
                         key=lambda t: abs(t[0][0] - t[1][0]) + abs(t[0][1] - t[1][1]))
        
        (ey1, ex1, start_y_inner, start_x_inner), (ey2, ex2, end_y_inner, end_x_inner) = entry_pair
        start_pos, end_pos = (start_y_inner, start_x_inner), (end_y_inner, end_x_inner)
        self.grid[ey1][ex1], self.grid[ey2][ex2] = 0, 0
        
        self.solution_path = self._bfs(start_pos, end_pos)
        assert self.solution_path is not None, "Maze must be solvable."
        return self.grid, self.solution_path

    def _get_border_cells(self):
        cells = []
        for x in range(1, self.width - 1, 2):
            if self.grid[1][x] == 0: cells.append((0, x, 1, x))
            if self.grid[self.height - 2][x] == 0: cells.append((self.height - 1, x, self.height - 2, x))
        for y in range(1, self.height - 1, 2):
            if self.grid[y][1] == 0: cells.append((y, 0, y, 1))
            if self.grid[y][self.width - 2] == 0: cells.append((y, self.width - 1, y, self.width - 2))
        return cells

    def _bfs(self, start, goal):
        q = deque([start])
        parent = {start: None}
        while q:
            y, x = q.popleft()
            if (y, x) == goal:
                path = []
                curr = goal
                while curr is not None:
                    path.append(curr)
                    curr = parent.get(curr)
                return path[::-1]
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < self.height and 0 <= nx < self.width and self.grid[ny][nx] == 0 and (ny, nx) not in parent:
                    parent[(ny, nx)] = (y, x)
                    q.append((ny, nx))
        return None

class MazePathfinder:
    """Finds all dead-end paths branching off the main solution path using DFS."""
    def __init__(self, grid, solution_path):
        self.grid, self.rows, self.cols = grid, len(grid), len(grid[0])
        self.solution_cells, self.dead_end_paths = set(solution_path), []
        self.visited = set(self.solution_cells)

    def _get_neighbors(self, r, c):
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr][nc] == 0:
                yield (nr, nc)
    
    def _dfs_trace(self, node, current_path):
        self.visited.add(node)
        current_path.append(node)
        unvisited_neighbors = [n for n in self._get_neighbors(*node) if n not in self.visited]
        if not unvisited_neighbors:
            self.dead_end_paths.append(list(current_path))
        else:
            for i, neighbor in enumerate(unvisited_neighbors):
                self._dfs_trace(neighbor, list(current_path) if i > 0 else current_path)

    def find_dead_ends(self):
        # PATCH A: Start tracing from the first off-solution neighbor.
        for r_sol, c_sol in self.solution_cells:
            for neighbor in self._get_neighbors(r_sol, c_sol):
                if neighbor not in self.visited:
                    self._dfs_trace(neighbor, current_path=[])
        return self.dead_end_paths

class BeamerGenerator:
    """Generates Beamer frames with adaptive scaling and unique non-overlapping colors."""
    def __init__(self, grid, solution_path, dead_end_paths):
        self.grid, self.rows, self.cols = grid, len(grid), len(grid[0])
        self.solution_path, self.dead_end_paths = solution_path, dead_end_paths

    def _generate_latex_color_definitions(self, num_colors):
        color_defs = ""
        golden_ratio_conjugate = 0.61803398875
        current_hue = random.random()
        for i in range(num_colors):
            current_hue = (current_hue + golden_ratio_conjugate) % 1.0
            (r, g, b) = colorsys.hsv_to_rgb(current_hue, 0.85, 0.9)
            color_defs += f"    \\definecolor{{deadendcolor{i}}}{{rgb}}{{{r:.4f},{g:.4f},{b:.4f}}}\n"
        return color_defs

    def _draw_maze_walls(self):
        return "".join([f"    \\fill[black] ({c}, {-r}) rectangle ({c+1}, {-r-1});\n" 
                        for r, row in enumerate(self.grid) for c, cell in enumerate(row) if cell == 1])

    # PATCH B (Helper 1): New function to split paths into unique segments.
    def _split_unique_segments(self, path, occupied):
        segs, cur = [], []
        for cell in path:
            if cell in occupied:
                if cur:
                    segs.append(cur)
                    cur = []
            else:
                if cur and (abs(cur[-1][0] - cell[0]) + abs(cur[-1][1] - cell[1]) != 1):
                    segs.append(cur)
                    cur = [cell]
                else:
                    cur.append(cell)
        if cur:
            segs.append(cur)
        return segs

    # PATCH B (Helper 2): New function to draw segments.
    def _draw_path_segments(self, segments, color_name, line_width="10pt"):
        code = ""
        for seg in segments:
            if len(seg) == 1:
                r, c = seg[0]
                code += f"    \\draw[{color_name}, line width={line_width}, line cap=round] ({c + 0.5}, {-r - 0.5}) -- ({c + 0.5}, {-r - 0.5});\n"
            else:
                path_coords = " --\n".join([f"      ({c + 0.5}, {-r - 0.5})" for r, c in seg])
                code += f"    \\draw[{color_name}, line width={line_width}, line cap=round, line join=round]\n{path_coords};\n"
        return code

    def _draw_solution_path(self, color_name="red!80!black", line_width="10pt"):
        # This is the original _draw_path, now specifically for the single-segment solution.
        path_coords = " --\n".join([f"      ({c + 0.5}, {-r - 0.5})" for r, c in self.solution_path])
        return f"    \\draw[{color_name}, line width={line_width}, line cap=round, line join=round]\n{path_coords};\n"

    # PATCH C: Corrected coordinates in marker placement.
    def _draw_markers(self, dead_paths_to_mark):
        end_r, end_c = self.solution_path[-1]
        code = f"    \\node[scale=2] at ({end_c + 0.5}, {-end_r - 0.5}) {{\\color{{green!60!black}}\\ding{{52}}}};\n"
        for i, path in enumerate(dead_paths_to_mark):
            end_r, end_c = path[-1]
            # The typo `end_r` in the x-coordinate is now corrected to `end_c`.
            code += f"    \\node[scale=1.5, text=deadendcolor{i}] at ({end_c + 0.5}, {-end_r - 0.5}) {{\\bfseries\\ding{{55}}}};\n"
        return code

    def generate_frames(self, num_dead_ends_to_show=5):
        sorted_dead_ends = sorted(self.dead_end_paths, key=len, reverse=True)
        paths_to_show = sorted_dead_ends[:num_dead_ends_to_show]
        color_definitions = self._generate_latex_color_definitions(len(paths_to_show))
        
        preamble = f"""
\\begin{{adjustbox}}{{width=0.95\\textwidth, height=0.85\\textheight, keepaspectratio, center}}
\\begin{{tikzpicture}}
{color_definitions}
    \\path[use as bounding box] (0, 1) rectangle ({self.cols}, -{self.rows});
"""
        frame_closer = "\\end{tikzpicture}\n\\end{adjustbox}\n\\end{frame}\n"
        
        all_frames = []
        all_frames.append(f"\\begin{{frame}}{{The Generated Maze}}\n{preamble}{self._draw_maze_walls()}{frame_closer}")

        frame2_content = preamble + "  \\begin{scope}[on background layer]\n"
        frame2_content += self._draw_solution_path()
        frame2_content += "  \\end{scope}\n" + self._draw_maze_walls() + self._draw_markers([]) + frame_closer
        all_frames.append(f"\\begin{{frame}}{{The Solution}}\n{frame2_content}")
        
        # PATCH B: Main logic change using the new helper functions.
        for i in range(len(paths_to_show)):
            frame_content = preamble + "  \\begin{scope}[on background layer]\n"
            frame_content += self._draw_solution_path()
            
            # Ensure dead-end colors never overlap each other
            occupied = set() # Cells already colored by previous dead ends (this frame)
            for j in range(i + 1):
                unique_segments = self._split_unique_segments(paths_to_show[j], occupied)
                frame_content += self._draw_path_segments(unique_segments, f"deadendcolor{j}")
                # Mark newly painted cells
                for seg in unique_segments:
                    occupied.update(seg)

            frame_content += "  \\end{scope}\n" + self._draw_maze_walls() + self._draw_markers(paths_to_show[:i+1]) + frame_closer
            all_frames.append(f"\\begin{{frame}}{{Exploring Dead Ends ({i + 1}/{len(paths_to_show)})}}\n{frame_content}")

        return "\n".join(all_frames)

    def generate_animate_frames(self, num_dead_ends_to_show=5):
        sorted_dead_ends = sorted(self.dead_end_paths, key=len, reverse=True)
        paths_to_show = sorted_dead_ends[:num_dead_ends_to_show]
        color_definitions = self._generate_latex_color_definitions(len(paths_to_show))
        
        preamble_start = f"""
\\begin{{frame}}{{The Generated Maze}}
{color_definitions}
\\begin{{adjustbox}}{{width=0.95\\textwidth, height=0.85\\textheight, keepaspectratio, center}}
\\begin{{animateinline}}[controls, loop]{{2}}
"""
        
        def frame_setup():
            return f"    \\begin{{tikzpicture}}\n    \\path[use as bounding box] (0, 1) rectangle ({self.cols}, -{self.rows});\n"
        
        def frame_close():
            return "    \\end{tikzpicture}"

        frames = []
        
        # Frame 1: Pure Maze
        f1 = frame_setup() + self._draw_maze_walls() + frame_close()
        frames.append(f1)

        # Frame 2: Solution
        f2 = frame_setup()
        f2 += "  \\begin{scope}[on background layer]\n"
        f2 += self._draw_solution_path()
        f2 += "  \\end{scope}\n" + self._draw_maze_walls() + self._draw_markers([])
        f2 += frame_close()
        frames.append(f2)

        # Dead ends
        for i in range(len(paths_to_show)):
            f_de = frame_setup()
            f_de += "  \\begin{scope}[on background layer]\n"
            f_de += self._draw_solution_path()
            occupied = set()
            for j in range(i + 1):
                unique_segments = self._split_unique_segments(paths_to_show[j], occupied)
                f_de += self._draw_path_segments(unique_segments, f"deadendcolor{j}")
                for seg in unique_segments:
                    occupied.update(seg)
            f_de += "  \\end{scope}\n" + self._draw_maze_walls() + self._draw_markers(paths_to_show[:i+1])
            f_de += frame_close()
            frames.append(f_de)

        latex_code = preamble_start
        latex_code += "\n\\newframe\n".join(frames)
        latex_code += "\n\\end{animateinline}\n\\end{adjustbox}\n\\end{frame}\n"
        
        return latex_code

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['slides', 'animate'], default='slides')
    args = parser.parse_args()

    # --- Configuration ---
    WIDTH_CELLS = 40  # Reduced from 80
    HEIGHT_CELLS = 25 # Reduced from 50
    MAZE_SEED = 123 
    NUM_DEAD_ENDS_TO_SHOW = 8
    # -------------------
    
    maze_gen = MazeGenerator(width=WIDTH_CELLS, height=HEIGHT_CELLS, seed=MAZE_SEED)
    grid, solution_path = maze_gen.generate()
    
    pathfinder = MazePathfinder(grid, solution_path)
    dead_ends = pathfinder.find_dead_ends()
    
    beamer_gen = BeamerGenerator(grid, solution_path, dead_ends)
    
    if args.mode == 'animate':
        output = beamer_gen.generate_animate_frames(num_dead_ends_to_show=NUM_DEAD_ENDS_TO_SHOW)
    else:
        output = beamer_gen.generate_frames(num_dead_ends_to_show=NUM_DEAD_ENDS_TO_SHOW)
        
    print(output)