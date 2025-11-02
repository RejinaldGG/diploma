# visual_physics.py
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle, Circle
import numpy as np


class PhysicsVisualizer:
    def __init__(self, logic):
        self.logic = logic
        self.fig = None
        self.animation = None

    def create_spring_animation(self, t_values, y_values):
        """Анимация пружинного маятника"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Настройка осей
        ax1.set_xlim(-2, 2)
        ax1.set_ylim(-3, 1)
        ax1.set_aspect('equal')
        ax1.set_title('Пружинный маятник')
        ax1.grid(True, alpha=0.3)

        ax2.set_xlim(min(t_values), max(t_values))
        ax2.set_ylim(min(y_values), max(y_values))
        ax2.set_xlabel('Время')
        ax2.set_ylabel('Смещение')
        ax2.set_title('График колебаний')
        ax2.grid(True, alpha=0.3)

        # Создание объектов анимации
        spring, = ax1.plot([], [], 'b-', linewidth=2)
        mass = Rectangle((0, 0), 0.5, 0.5, fill=True, color='red')
        ax1.add_patch(mass)

        time_line, = ax2.plot([], [], 'r-', linewidth=2)
        current_point, = ax2.plot([], [], 'ro', markersize=8)

        def animate(i):
            # Ограничиваем индекс для плавности
            idx = min(i, len(t_values) - 1)
            y = y_values[idx]

            # Обновление пружины
            x_spring = [0, 0]
            y_spring = [0, y]
            spring.set_data(x_spring, y_spring)

            # Обновление массы
            mass.set_xy([-0.25, y - 0.25])

            # Обновление графика
            time_line.set_data(t_values[:idx], y_values[:idx])
            current_point.set_data([t_values[idx]], [y_values[idx]])

            return spring, mass, time_line, current_point

        self.animation = animation.FuncAnimation(
            fig, animate, frames=len(t_values),
            interval=50, blit=True, repeat=True
        )

        plt.tight_layout()
        return fig

    def create_pendulum_animation(self, t_values, theta_values):
        """Анимация математического маятника"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        ax1.set_xlim(-2, 2)
        ax1.set_ylim(-2, 1)
        ax1.set_aspect('equal')
        ax1.set_title('Математический маятник')

        ax2.set_xlabel('Время')
        ax2.set_ylabel('Угол (рад)')
        ax2.set_title('Угловое смещение')
        ax2.grid(True, alpha=0.3)

        # Создание маятника
        rod, = ax1.plot([], [], 'b-', linewidth=3)
        bob = Circle((0, 0), 0.1, color='red')
        ax1.add_patch(bob)

        angle_line, = ax2.plot([], [], 'r-', linewidth=2)
        current_angle, = ax2.plot([], [], 'ro', markersize=8)

        L = 1.5  # Длина маятника

        def animate(i):
            idx = min(i, len(t_values) - 1)
            theta = theta_values[idx]

            # Координаты маятника
            x_bob = L * np.sin(theta)
            y_bob = -L * np.cos(theta)

            # Обновление стержня
            rod.set_data([0, x_bob], [0, y_bob])

            # Обновление груза
            bob.center = (x_bob, y_bob)

            # Обновление графика
            angle_line.set_data(t_values[:idx], theta_values[:idx])
            current_angle.set_data([t_values[idx]], [theta_values[idx]])

            return rod, bob, angle_line, current_angle

        self.animation = animation.FuncAnimation(
            fig, animate, frames=len(t_values),
            interval=50, blit=True, repeat=True
        )

        plt.tight_layout()
        return fig

    def create_electric_circuit_animation(self, t_values, q_values, i_values):
        """Визуализация RLC-цепи"""
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4))

        # Схема цепи
        ax1.set_xlim(-1, 3)
        ax1.set_ylim(-1, 2)
        ax1.set_aspect('equal')
        ax1.set_title('RLC-цепь')
        ax1.axis('off')

        # Графики
        ax2.set_title('Заряд конденсатора')
        ax2.set_xlabel('Время')
        ax2.set_ylabel('Заряд q(t)')
        ax2.grid(True, alpha=0.3)

        ax3.set_title('Ток в цепи')
        ax3.set_xlabel('Время')
        ax3.set_ylabel('Ток I(t)')
        ax3.grid(True, alpha=0.3)

        # Рисуем схему цепи
        self._draw_circuit(ax1)

        # Графики заряда и тока
        charge_line, = ax2.plot([], [], 'b-', linewidth=2)
        current_line, = ax3.plot([], [], 'g-', linewidth=2)

        def animate(i):
            idx = min(i, len(t_values) - 1)

            charge_line.set_data(t_values[:idx], q_values[:idx])
            current_line.set_data(t_values[:idx], i_values[:idx])

            return charge_line, current_line

        self.animation = animation.FuncAnimation(
            fig, animate, frames=len(t_values),
            interval=50, blit=True, repeat=True
        )

        plt.tight_layout()
        return fig

    def _draw_circuit(self, ax):
        """Рисует схему RLC-цепи"""
        # Источник напряжения
        ax.plot([0, 0], [0, 1], 'k-', linewidth=2)
        ax.plot([0, 0.5], [1, 1], 'k-', linewidth=2)

        # Резистор
        ax.add_patch(Rectangle((0.5, 0.8), 0.5, 0.4, fill=False, edgecolor='black'))
        ax.text(0.75, 1.0, 'R', ha='center', va='center')

        # Катушка
        ax.plot([1.0, 1.5], [1, 1], 'k-', linewidth=2)
        for i in range(3):
            x = 1.5 + i * 0.1
            ax.add_patch(Circle((x, 1), 0.05, fill=False, color='black'))
        ax.text(1.8, 1.0, 'L', ha='center', va='center')

        # Конденсатор
        ax.plot([1.8, 2.0], [1, 1], 'k-', linewidth=2)
        ax.plot([2.0, 2.0], [0.8, 1.2], 'k-', linewidth=2)
        ax.plot([2.2, 2.2], [0.8, 1.2], 'k-', linewidth=2)
        ax.plot([2.2, 2.4], [1, 1], 'k-', linewidth=2)
        ax.text(2.1, 0.7, 'C', ha='center', va='center')

        # Замыкаем цепь
        ax.plot([2.4, 2.4], [1, 0], 'k-', linewidth=2)
        ax.plot([2.4, 0], [0, 0], 'k-', linewidth=2)