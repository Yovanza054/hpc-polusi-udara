import numpy as np


def simulate(wind_x, wind_y, emission, steps=600, size=80, diffusion=0.4, decay=0.002, dt=0.2):
    field = np.zeros((size, size))
    sy, sx = size // 4, size // 4

    for _ in range(steps):
        field[sy, sx] += emission * dt

        if wind_x >= 0:
            grad_x = field - np.roll(field, 1, axis=1)
        else:
            grad_x = np.roll(field, -1, axis=1) - field

        if wind_y >= 0:
            grad_y = field - np.roll(field, 1, axis=0)
        else:
            grad_y = np.roll(field, -1, axis=0) - field

        laplace = (
            np.roll(field, 1, axis=0)
            + np.roll(field, -1, axis=0)
            + np.roll(field, 1, axis=1)
            + np.roll(field, -1, axis=1)
            - 4.0 * field
        )

        field = field + dt * (
            diffusion * laplace
            - abs(wind_x) * grad_x * np.sign(wind_x if wind_x else 1)
            - abs(wind_y) * grad_y * np.sign(wind_y if wind_y else 1)
            - decay * field
        )

        field[0, :] = 0.0
        field[-1, :] = 0.0
        field[:, 0] = 0.0
        field[:, -1] = 0.0
        np.clip(field, 0.0, None, out=field)

    return field


def run_scenario(params):
    wind_x, wind_y, emission = params
    field = simulate(wind_x, wind_y, emission)
    threshold = 0.5 * field.max() if field.max() > 0 else 0.0
    return {
        "wind_x": wind_x,
        "wind_y": wind_y,
        "emission": emission,
        "max_concentration": float(field.max()),
        "mean_concentration": float(field.mean()),
        "area_above_threshold": int((field > threshold).sum()),
    }
