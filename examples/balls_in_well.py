"""
Balls In A Well
===============

A nice looking video of balls in a gravity well.
"""
import squap
from squap import var
import numpy as np
from matplotlib import colormaps
from scipy import optimize
from matplotlib import pyplot as plt


def func(x):
    # return -4*np.exp(-np.abs(x))
    return np.exp(np.abs(x))


def dfunc(x):
    # return 2*x
    return np.sign(x)*np.exp(np.abs(x))


def opt_func(t):
    v_x, v_y = vpoints[index]
    return r_0[1]+v_y*t - func(r_0[0]+v_x*t)


def set_cmap():
    curve.set_data(c=squap.cmap_to_colors(colormaps.get_cmap(var.cmap), N))
    # curve_2.set_data(c=rb_grad)
    # curve_1.set_data(c=rb_grad)


# def solve_pol2(a, b, c):
#     print((-b+np.sqrt(b**2-4*a*c))/(2*a), (-b-np.sqrt(b**2-4*a*c))/(2*a))
#     return (-b+np.sqrt(b**2-4*a*c))/(2*a)



squap.add_checkbox("pause")
squap.add_inputbox("dt", 0.005)
squap.add_inputbox("skip_frames", 1, int)
squap.add_inputbox("cmap", "hsv").bind(set_cmap)
g = 9.81
N = 200
N_half = int(N/2)
rb_grad = np.zeros((N_half, 3))
for i in range(N_half):
    rb_grad[i] = [i/(N_half-1)*255, 0, 0]

x = 0.5e-5
points = np.zeros([N, 2])
vpoints = np.zeros([N, 2])
for i in range(N):
    points[i] = np.array([-x+i/N*2*x, 4])
    vpoints[i] = np.array([1e-8, 0])

    # points[i] = np.array([1+0.001*i, 41])

x_min, x_max = -2.2, 2.2
x_lin = np.linspace(x_min, x_max, 500)
y_plot = func(x_lin)
squap.plot(x_lin, y_plot-0.02, w=1, c="white")
curve = squap.scatter(points[:, 0], points[:, 1])
# curve_2 = squap.scatter(points[N_half:, 0], points[N_half:, 1])
set_cmap()
squap.set_xlim(x_min, x_max)
squap.set_ylim(np.min(y_plot), np.max(y_plot))
squap.show_window()
squap.display_fps()

save_video = False      # change this to True to save the recording

if save_video:
    stop_recording = squap.start_recording("test_recording.mp4", fps=60, skip_frames=0)

while squap.is_alive():
    if not var.pause:
        for _ in range(var.skip_frames+1):
            vpoints[:, 1] -= g * var.dt
            # prev_prev_points = prev_points
            prev_points = points
            points += vpoints * var.dt
            for index in range(N):
                if points[index, 1] < func(points[index, 0]):
                    r_0 = points[index] - vpoints[index]*var.dt
                    time_left = var.dt
                    j = 0
                    while points[index, 1] < func(points[index, 0]):
                        try:
                            collision_t = optimize.brentq(opt_func, 1e-11, time_left)
                        except ValueError:
                            print(f"{opt_func(1e-11) = }")
                            print(f"{opt_func(1e-3) = }")
                            # collision_t = optimize.brentq(opt_func, 1e-10, 1e-3)
                            t_lin = np.linspace(1e-13, time_left, 1000)
                            plt.plot(t_lin, opt_func(t_lin))
                            plt.show()
                        collision_pos = r_0 + vpoints[index]*collision_t
                        slope = dfunc(collision_pos[0])
                        n = 1/(np.sqrt(1+slope**2))*np.array([-slope, 1])
                        vpoints[index] = vpoints[index] - 2*np.dot(vpoints[index], n)*n
                        points[index] = collision_pos + vpoints[index]*(time_left-collision_t)

                        r_0 = collision_pos
                        time_left = time_left-collision_t
                        j += 1
                    if j > 1:
                        print(f"{j = }")


    curve.set_data(points[:, 0], points[:, 1])
    squap.refresh()

if save_video:
    stop_recording()
