import json
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
from matplotlib.widgets import Button, CheckButtons

def normalize_paths(data_list, drone_count):
    if not data_list:
        return [[] for _ in range(drone_count)]
    if not isinstance(data_list[0][0], (list, tuple)):
        result = [data_list]
        for _ in range(drone_count - 1):
            result.append([])
        return result
    return data_list

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

    objects = data.get("objects", [])
    drones_data = data.get("drones", [])
    dimensions = data.get("dimensions", [10, 10])
    width, height = dimensions[0], dimensions[1]

    initial_steps_raw = data.get("initial_steps", [])
    loop_steps_raw = data.get("loop_steps", [])

    drone_count = len(drones_data) if drones_data else 1
    initial_paths = normalize_paths(initial_steps_raw, drone_count)
    loop_paths = normalize_paths(loop_steps_raw, drone_count)

    wong_palette = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#F0E442', '#56B4E9', '#E69F00']
    color_bg = '#000000'
    color_obstacle = '#E69F00'

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor(color_bg)
    ax.set_aspect('equal', adjustable='box')
    
    plt.subplots_adjust(bottom=0.2, right=0.82)
    
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

    drone_artists = []
    has_drone_img = os.path.exists(drone_img_path)
    drone_image_data = None
    if has_drone_img:
        try:
            drone_image_data = mpimg.imread(drone_img_path)
        except Exception as e:
            print(f"Error loading drone.png: {e}")
            has_drone_img = False

    for i in range(drone_count):
        color = wong_palette[i % len(wong_palette)]
        trail, = ax.plot([], [], color=color, linewidth=2, alpha=0.6, zorder=8)
        
        d_config = drones_data[i] if i < len(drones_data) else {}
        radius = d_config.get("radius", 1)
        vision = patches.Rectangle((0, 0), radius*2, radius*2, color=color, fill=True, alpha=0.15, zorder=9)
        ax.add_patch(vision)

        drone_obj = None
        if has_drone_img:
            drone_obj = ax.imshow(drone_image_data, extent=[0, 1, 0, 1], zorder=10)
            drone_obj.set_visible(False)
        else:
            drone_obj, = ax.plot([], [], marker='o', color=color, markersize=10, markeredgecolor='white', zorder=10)

        drone_artists.append({
            'trail': trail,
            'vision': vision,
            'drone': drone_obj,
            'history_x': [],
            'history_y': [],
            'radius': radius,
            'initial': initial_paths[i],
            'loop': loop_paths[i],
            'tickspeed': max(1, d_config.get("tickspeed", 1)),
            'color': color
        })

    all_raw_points = [p for path in (initial_paths + loop_paths) for p in path]
    min_x = min([p[0] for p in all_raw_points] or [0]) - 5
    max_x = max([p[0] for p in all_raw_points] or [width]) + 5
    min_y = min([p[1] for p in all_raw_points] or [0]) - 5
    max_y = max([p[1] for p in all_raw_points] or [height]) + 5
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)

    def init():
        for art in drone_artists:
            art['trail'].set_data([], [])
            art['history_x'].clear()
            art['history_y'].clear()
            r = art['radius']
            art['vision'].set_xy((-r, -r))
            if has_drone_img:
                art['drone'].set_visible(True)
            else:
                art['drone'].set_data([], [])
        return []

    def update(frame):
        for art in drone_artists:
            eff_frame = frame // art['tickspeed']
            initial = art['initial']
            loop = art['loop']
            if not initial and not loop: continue
            
            if eff_frame < len(initial):
                pos = initial[eff_frame]
            elif loop:
                p_idx = (eff_frame - len(initial)) % len(loop)
                pos = loop[p_idx]
            else:
                pos = initial[-1]
            
            art['history_x'].append(pos[0])
            art['history_y'].append(pos[1])
            art['trail'].set_data(art['history_x'], art['history_y'])
            
            r = art['radius']
            art['vision'].set_xy((pos[0] - r, pos[1] - r))
            if has_drone_img:
                art['drone'].set_extent([pos[0]-0.5, pos[0]+0.5, pos[1]-0.5, pos[1]+0.5])
            else:
                art['drone'].set_data([pos[0]], [pos[1]])
        
        ax.set_title(f"Interactive Surveillance System | Tick: {frame:04d}", color='#FFFFFF', fontsize=14, loc='center', pad=15, fontweight='bold')
        return []

    ani = animation.FuncAnimation(fig, update, frames=20000, init_func=init, blit=False, interval=100, repeat=False)

    class UIHandlers:
        def __init__(self, animation_obj, artists, labels):
            self.ani = animation_obj
            self.artists = artists
            self.labels = labels
            self.paused = False
        
        def toggle_pause(self, event):
            if self.paused:
                self.ani.resume()
                self.btn_pause.label.set_text('PAUSE')
            else:
                self.ani.pause()
                self.btn_pause.label.set_text('RESUME')
            self.paused = not self.paused
            plt.draw()

        def toggle_trails(self, label):
            if label in self.labels:
                idx = self.labels.index(label)
                visible = self.artists[idx]['trail'].get_visible()
                self.artists[idx]['trail'].set_visible(not visible)
                plt.draw()

    labels = [f"Drone {i+1} Path" for i in range(drone_count)]
    ui = UIHandlers(ani, drone_artists, labels)

    ax_btn_pause = plt.axes([0.1, 0.05, 0.15, 0.06])
    ui.btn_pause = Button(ax_btn_pause, 'PAUSE', color='#333333', hovercolor='#444444')
    ui.btn_pause.label.set_color('white')
    ui.btn_pause.label.set_fontweight('bold')
    ui.btn_pause.on_clicked(ui.toggle_pause)

    ax_check = plt.axes([0.84, 0.4, 0.14, 0.3])
    ax_check.set_facecolor('#1a1a1a')
    visibility = [True] * drone_count
    check = CheckButtons(
        ax_check, labels, visibility,
        label_props={'color': ['white']*drone_count, 'fontsize': [10]*drone_count},
        check_props={'facecolor': [d['color'] for d in drone_artists]}
    )
    
    check.on_clicked(ui.toggle_trails)

    plt.show()

if __name__ == "__main__":
    main()
