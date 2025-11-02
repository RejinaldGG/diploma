# visual_3d.py
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np


class ThreeDVisualizer:
    def __init__(self, logic):
        self.logic = logic

    def plot_3d_phase_space(self, t_values, y_values, y_prime_values):
        """3D фазовое пространство"""
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Создаем 3D траекторию
        ax.plot(t_values, y_values, y_prime_values, 'b-', alpha=0.7, linewidth=2)
        ax.scatter(t_values[0], y_values[0], y_prime_values[0],
                   color='green', s=100, label='Начало')
        ax.scatter(t_values[-1], y_values[-1], y_prime_values[-1],
                   color='red', s=100, label='Конец')

        ax.set_xlabel('Время (t)')
        ax.set_ylabel('Положение (y)')
        ax.set_zlabel('Скорость (y\')')
        ax.set_title('3D Фазовое пространство')
        ax.legend()

        return fig

    def plot_parametric_3d(self, x_values, y_values, z_values):
        """Параметрические 3D графики"""
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Цветовая схема по времени
        colors = np.linspace(0, 1, len(x_values))

        scatter = ax.scatter(x_values, y_values, z_values,
                             c=colors, cmap='viridis', alpha=0.7)

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('Параметрическое движение в 3D')

        plt.colorbar(scatter, label='Время')
        return fig

    def plot_multiple_trajectories(self, trajectories):
        """Множественные траектории в 3D"""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        colors = plt.cm.tab10(np.linspace(0, 1, len(trajectories)))

        for i, (t, y, yp) in enumerate(trajectories):
            ax.plot(t, y, yp, color=colors[i], linewidth=2,
                    label=f'Траектория {i + 1}')

        ax.set_xlabel('Время')
        ax.set_ylabel('Положение')
        ax.set_zlabel('Скорость')
        ax.set_title('Сравнение траекторий')
        ax.legend()

        return fig