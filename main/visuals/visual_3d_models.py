# main/visuals/visual_3d_models.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import json
from wolframclient.language import wlexpr

# main/visuals/visual_3d_models.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D


class ThreeDModels:
    def __init__(self, wolfram_solver):
        self.wolfram = wolfram_solver

    def show_simple_pendulum(self, params, initial_conditions, t_range):
        """
        Простая 2D анимация маятника
        """
        solution = self.solve_pendulum_equation(params, initial_conditions, t_range)

        if not solution['success']:
            print(f"Ошибка решения: {solution.get('error', 'Неизвестная ошибка')}")
            return False

        t = solution['t_values']
        theta = solution['y_values']
        L = params.get('L', 1.0)

        # Создаем фигуру
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # График угла
        ax1.plot(t, theta, 'b-', linewidth=2)
        ax1.set_xlabel('Время (с)')
        ax1.set_ylabel('Угол (рад)')
        ax1.set_title('Угол маятника vs время')
        ax1.grid(True)

        # Анимация маятника
        ax2.set_xlim(-L * 1.2, L * 1.2)
        ax2.set_ylim(-L * 1.2, L * 0.2)
        ax2.set_aspect('equal')
        ax2.set_title('Маятник')
        ax2.grid(True)

        # Элементы анимации
        line, = ax2.plot([], [], 'b-', lw=3)
        bob, = ax2.plot([], [], 'ro', markersize=20)

        def animate(i):
            # Координаты маятника
            x = L * np.sin(theta[i])
            y = -L * np.cos(theta[i])

            # Обновляем стержень
            line.set_data([0, x], [0, y])

            # Обновляем груз
            bob.set_data([x], [y])

            return line, bob

        # Создаем анимацию
        anim = FuncAnimation(fig, animate, frames=min(200, len(t)),
                             interval=30, blit=True, repeat=True)

        plt.tight_layout()
        plt.show()
        return True

    def show_double_pendulum_simple(self):
        """
        Упрощенная визуализация двойного маятника
        """
        L1, L2 = 1.0, 0.8

        # Генерация тестовых данных
        t = np.linspace(0, 20, 500)
        theta1 = 0.5 * np.sin(2 * np.pi * 0.5 * t) * np.exp(-0.05 * t)
        theta2 = 0.8 * np.sin(2 * np.pi * 0.7 * t + 1) * np.exp(-0.03 * t)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Графики углов
        ax1.plot(t, theta1, 'b-', label='θ1')
        ax1.plot(t, theta2, 'r-', label='θ2')
        ax1.set_xlabel('Время (с)')
        ax1.set_ylabel('Угол (рад)')
        ax1.set_title('Углы двойного маятника')
        ax1.legend()
        ax1.grid(True)

        # Анимация
        ax2.set_xlim(-(L1 + L2) * 1.2, (L1 + L2) * 1.2)
        ax2.set_ylim(-(L1 + L2) * 1.2, (L1 + L2) * 0.2)
        ax2.set_aspect('equal')
        ax2.set_title('Двойной маятник')
        ax2.grid(True)

        # Элементы
        line1, = ax2.plot([], [], 'b-', lw=3)
        line2, = ax2.plot([], [], 'r-', lw=2)
        bob1, = ax2.plot([], [], 'bo', markersize=15)
        bob2, = ax2.plot([], [], 'ro', markersize=12)

        # Траектория
        trace_line, = ax2.plot([], [], 'g-', alpha=0.5, lw=1)
        trace_x, trace_y = [], []

        def animate(i):
            # Координаты первого маятника
            x1 = L1 * np.sin(theta1[i])
            y1 = -L1 * np.cos(theta1[i])

            # Координаты второго маятника
            x2 = x1 + L2 * np.sin(theta2[i])
            y2 = y1 - L2 * np.cos(theta2[i])

            # Обновляем линии
            line1.set_data([0, x1], [0, y1])
            line2.set_data([x1, x2], [y1, y2])

            # Обновляем грузы
            bob1.set_data([x1], [y1])
            bob2.set_data([x2], [y2])

            # Траектория
            trace_x.append(x2)
            trace_y.append(y2)
            if len(trace_x) > 100:
                trace_x.pop(0)
                trace_y.pop(0)
            trace_line.set_data(trace_x, trace_y)

            return line1, line2, bob1, bob2, trace_line

        anim = FuncAnimation(fig, animate, frames=min(200, len(t)),
                             interval=30, blit=True, repeat=True)

        plt.tight_layout()
        plt.show()
        return True

    def create_spring_system(self, solution_data):
        """
        Визуализация пружинной системы
        """
        if not solution_data['success']:
            return None, None

        t = solution_data['t_values']
        y = solution_data['y_values']

        # Ограничиваем количество кадров для производительности
        if len(t) > 200:
            indices = np.linspace(0, len(t) - 1, 200, dtype=int)
            t = np.array(t)[indices]
            y = np.array(y)[indices]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # График решения
        ax1.plot(t, y, 'b-', linewidth=2)
        ax1.set_xlabel('Время (с)')
        ax1.set_ylabel('Смещение (м)')
        ax1.set_title('Колебания пружины')
        ax1.grid(True)

        # Анимация пружины
        ax2.set_xlim(-2, 2)
        ax2.set_ylim(-3, 1)
        ax2.set_aspect('equal')
        ax2.set_title('Пружинная система')
        ax2.grid(True)

        # Элементы анимации
        spring, = ax2.plot([], [], 'b-', lw=3)
        mass = plt.Rectangle((0, 0), 0.5, 0.5, color='red')
        ax2.add_patch(mass)
        ceiling = ax2.plot([-1, 1], [0, 0], 'k-', lw=3)[0]

        def animate(i):
            # Положение массы
            y_pos = y[i]

            # Пружина (вертикальная линия)
            spring.set_data([0, 0], [0, y_pos])

            # Масса
            mass.set_xy((-0.25, y_pos - 0.25))

            return spring, mass

        anim = FuncAnimation(fig, animate, frames=len(t),
                             interval=30, blit=True, repeat=True)

        plt.tight_layout()
        return fig, anim

    def create_3d_phase_space(self, solution_data):
        """
        3D фазовое пространство
        """
        if not solution_data['success']:
            return None, None

        t = solution_data['t_values']
        y = solution_data['y_values']

        # Ограничиваем количество точек
        if len(t) > 500:
            indices = np.linspace(0, len(t) - 1, 500, dtype=int)
            t = np.array(t)[indices]
            y = np.array(y)[indices]

        # Вычисляем производную
        if len(y) > 1:
            dt = t[1] - t[0]
            y_prime = np.gradient(y, dt)
        else:
            y_prime = np.zeros_like(y)

        # Создаем 3D график
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Фазовый портрет в 3D
        ax.plot(t, y, y_prime, 'b-', linewidth=1)

        # Настройка
        ax.set_xlabel('Время (t)')
        ax.set_ylabel('Положение (y)')
        ax.set_zlabel("Скорость (y')")
        ax.set_title('3D Фазовое пространство')

        plt.tight_layout()
        return fig, None  # Нет анимации, только статичный график

    # Для совместимости со старым кодом
    def create_pendulum_animation(self, solution_data, L=1.0):
        """Заглушка для совместимости"""
        print("Используйте show_simple_pendulum()")
        return None, None

    def create_double_pendulum_animation(self, solution_data):
        """Заглушка для совместимости"""
        print("Используйте show_double_pendulum_simple()")
        return None, None

    def create_spring_mass_3d(self, solution_data, k=1.0, m=1.0):
        """Заглушка для совместимости"""
        return self.create_spring_system(solution_data)

    def solve_pendulum_equation(self, params, initial_conditions, t_range):
        """
        Решение уравнения маятника
        """
        L = params.get('L', 1.0)
        g = params.get('g', 9.81)
        beta = params.get('beta', 0.0)

        theta0, omega0 = initial_conditions

        equation_str = f"theta''[t] + ({g}/{L})*Sin[theta[t]] + {beta}*theta'[t] == 0"

        result = self.wolfram.solve_second_order_ode(
            equation_str,
            [theta0, omega0],
            t_range
        )

        return result

    def solve_double_pendulum(self, params, initial_conditions, t_range):
        """
        Заглушка для двойного маятника
        """
        return {'success': False, 'error': 'Используйте упрощенную визуализацию'}