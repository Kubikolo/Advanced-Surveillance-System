import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg

def main():
    plt.rcParams['toolbar'] = 'None'
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, '..', 'shared', 'simulation_base.json')
    drone_img_path = os.path.join(base_path, 'drone.png')

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find file: {json_path}")
        return

    initial_steps = data.get("initial_steps", [])
    loop_steps = data.get("loop_steps", [])
    objects = data.get("objects", [])
    drones_data = data.get("drones", [])
    dimensions = data.get("dimensions", [10, 10])

    width, height = dimensions[0], dimensions[1]
    
    full_path = initial_steps + loop_steps * 3

    if not full_path:
        print("Error: Drone path data is missing.")
        return

    circle_radius = drones_data[0]["radius"] if drones_data else 1
    
    color_bg = '#000000'
    color_obstacle = '#E69F00'
    color_path = '#0072B2'
    color_vision = '#56B4E9'

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor(color_bg)
    
    ax.set_aspect('equal', adjustable='box')

    ax.grid(True, color='#333333', linestyle='-', linewidth=0.5, zorder=0)

    for obj in objects:
        for block in obj:
            rect = patches.Rectangle(
                (block[0] - 0.5, block[1] - 0.5), 1, 1,
                linewidth=1, edgecolor='#111111', facecolor=color_obstacle, alpha=1.0, zorder=2
            )
            ax.add_patch(rect)

    boundary = patches.Rectangle(
        (-0.5, -0.5), width, height,
        linewidth=2, edgecolor='#FF3366', facecolor='none', linestyle='-.', 
        zorder=5, label='Declared boundary'
    )
    ax.add_patch(boundary)

    drone_trail, = ax.plot([], [], color=color_path, linewidth=2, alpha=0.6, zorder=8)
    
    vision_range = patches.Rectangle((0, 0), circle_radius*2, circle_radius*2, color=color_vision, fill=True, alpha=0.25, zorder=9)
    ax.add_patch(vision_range)
    
    has_drone_img = os.path.exists(drone_img_path)
    drone_img_obj = None
    drone_dot = None

    if has_drone_img:
        try:
            arr_img = mpimg.imread(drone_img_path)
            drone_img_obj = ax.imshow(arr_img, extent=[0, 1, 0, 1], zorder=10)
            drone_img_obj.set_visible(False)
        except Exception as e:
            print(f"Error loading drone.png: {e}")
            has_drone_img = False

    if not has_drone_img:
        drone_dot, = ax.plot([], [], marker='o', color=color_path, markersize=12, markeredgecolor='white', zorder=10)

    all_x = [p[0] for p in full_path]
    all_y = [p[1] for p in full_path]
    
    min_x = min(min(all_x) - circle_radius, -0.5)
    max_x = max(max(all_x) + circle_radius, width - 0.5)
    min_y = min(min(all_y) - circle_radius, -0.5)
    max_y = max(max(all_y) + circle_radius, height - 0.5)
    
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)

    path_history_x = []
    path_history_y = []

    def init():
        drone_trail.set_data([], [])
        path_history_x.clear()
        path_history_y.clear()
        vision_range.set_xy((-circle_radius, -circle_radius))
        
        if has_drone_img and drone_img_obj:
            drone_img_obj.set_visible(True)
        elif drone_dot:
            drone_dot.set_data([], [])
        return []

    def update(frame):
        current_pos = full_path[frame]
        
        path_history_x.append(current_pos[0])
        path_history_y.append(current_pos[1])
        
        drone_trail.set_data(path_history_x, path_history_y)
        vision_range.set_xy((current_pos[0] - circle_radius, current_pos[1] - circle_radius))
        
        if has_drone_img and drone_img_obj:
            drone_img_obj.set_extent([current_pos[0]-0.5, current_pos[0]+0.5, current_pos[1]-0.5, current_pos[1]+0.5])
        elif drone_dot:
            drone_dot.set_data([current_pos[0]], [current_pos[1]])
        
        ax.set_title(
            f"Frame: {frame:03d} | Pos: {current_pos}",
            color='#FFFFFF', fontsize=14, loc='center', pad=15, fontweight='bold'
        )
        return []
    
    ani = animation.FuncAnimation(
        fig, update, frames=len(full_path),
        init_func=init, blit=False, interval=150, repeat=False
    )

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
