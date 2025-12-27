# visual_integrated.py
import tkinter as tk

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class IntegratedVisualizations:
    def __init__(self, logic, parent_frame):
        self.logic = logic
        self.parent_frame = parent_frame
        self.current_visualization = None

    def show_physics_in_main(self):
        """Показ физической анимации в основном окне"""
        self._clear_visualization()

        if not self.logic.current_solution or not self.logic.current_solution['success']:
            return None

        try:
            t = self.logic.current_solution['t_values']
            y = self.logic.current_solution['y_values']

            # Создаем фигуру для основного окна
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            # Левый график - анимация (статичный кадр)
            ax1.set_xlim(-2, 2)
            ax1.set_ylim(-3, 1)
            ax1.set_aspect('equal')
            ax1.set_title('Пружинный маятник (статичный вид)')
            ax1.grid(True, alpha=0.3)

            # Рисуем начальное положение
            y_current = y[0] if y else 0
            ax1.plot([0, 0], [0, y_current], 'b-', linewidth=3, label='Пружина')
            mass = plt.Rectangle((-0.25, y_current - 0.25), 0.5, 0.5, color='red')
            ax1.add_patch(mass)
            ax1.legend()

            # Правый график - траектория с текущей позицией
            ax2.plot(t, y, 'b-', alpha=0.5, label='Траектория')
            ax2.plot([t[0]], [y[0]], 'ro', markersize=8, label='Текущее положение')
            ax2.set_xlabel('Время')
            ax2.set_ylabel('Смещение')
            ax2.set_title('Динамика движения')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            return self._embed_figure(fig)

        except Exception as e:
            print(f"Ошибка физической визуализации: {e}")
            return None

    def show_3d_in_main(self):
        """3D визуализация в основном окне"""
        self._clear_visualization()

        if not self.logic.current_solution:
            return None

        try:
            phase_data = self.logic.get_phase_portrait()
            if not phase_data:
                return None

            t, y, yp = phase_data

            # Создаем 3D график
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')

            # Цветовая схема по времени
            colors = np.linspace(0, 1, len(t))
            scatter = ax.scatter(t, y, yp, c=colors, cmap='viridis', s=20)

            ax.set_xlabel('Время (t)')
            ax.set_ylabel('Положение (y)')
            ax.set_zlabel('Скорость (y\')')
            ax.set_title('3D Фазовое пространство')

            plt.colorbar(scatter, ax=ax, label='Время')
            plt.tight_layout()

            return self._embed_figure(fig)

        except Exception as e:
            print(f"Ошибка 3D визуализации: {e}")
            return None

    def show_comparison_in_main(self):
        """Сравнительная визуализация в основном окне"""
        self._clear_visualization()

        if not self.logic.current_solution:
            return None

        try:
            t = self.logic.current_solution['t_values']
            y = self.logic.current_solution['y_values']
            phase_data = self.logic.get_phase_portrait()

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

            # 1. Основной график
            ax1.plot(t, y, 'b-', linewidth=2)
            ax1.set_title('Решение y(t)')
            ax1.set_xlabel('Время')
            ax1.set_ylabel('y(t)')
            ax1.grid(True, alpha=0.3)

            # 2. Фазовый портрет
            if phase_data:
                t_phase, y_phase, y_prime = phase_data
                ax2.plot(y_phase, y_prime, 'r-')
                ax2.set_title('Фазовый портрет')
                ax2.set_xlabel('y')
                ax2.set_ylabel("y'")
                ax2.grid(True, alpha=0.3)

            # 3. Амплитудный анализ
            envelope = np.abs(y)
            ax3.plot(t, envelope, 'g-', alpha=0.7, label='Огибающая')
            ax3.plot(t, y, 'b-', alpha=0.3, label='Сигнал')
            ax3.set_title('Амплитудная огибающая')
            ax3.set_xlabel('Время')
            ax3.legend()
            ax3.grid(True, alpha=0.3)

            # 4. Частотный анализ (спектр)
            if len(y) > 1:
                from scipy.fft import fft, fftfreq
                N = len(y)
                T = t[1] - t[0]
                yf = fft(y)
                xf = fftfreq(N, T)[:N // 2]
                ax4.plot(xf, 2.0 / N * np.abs(yf[0:N // 2]))
                ax4.set_title('Частотный спектр')
                ax4.set_xlabel('Частота')
                ax4.set_ylabel('Амплитуда')
                ax4.grid(True, alpha=0.3)

            plt.tight_layout()
            return self._embed_figure(fig)

        except Exception as e:
            print(f"Ошибка сравнительной визуализации: {e}")
            return None

    def _embed_figure(self, fig):
        """Встраивает фигуру в интерфейс"""
        canvas = FigureCanvasTkAgg(fig, self.parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.current_visualization = canvas
        return canvas

    def _clear_visualization(self):
        """Очищает текущую визуализацию"""
        if self.current_visualization:
            self.current_visualization.get_tk_widget().destroy()
            self.current_visualization = None