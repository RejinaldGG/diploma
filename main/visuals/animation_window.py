# main/visuals/animation_window.py
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from matplotlib.patches import Circle, Rectangle, Polygon
import time


class WorkingAnimationWindow:
    """Рабочее окно анимации с поддержкой RLC-цепи"""

    def __init__(self, parent, eq_type, t_values, y_values):
        self.parent = parent
        self.eq_type = eq_type
        self.t_values = np.array(t_values)
        self.y_values = np.array(y_values)

        print(f"🎬 СОЗДАЕМ РАБОЧУЮ АНИМАЦИЮ")
        print(f"   Тип: {eq_type}")
        print(f"   Точек: {len(self.t_values)}")

        self.window = tk.Toplevel(parent)
        self.window.title(f"Анимация: {eq_type}")
        self.window.geometry("1100x700")  # Увеличили для цепи

        self.window.transient(parent)
        self.window.grab_set()

        self.current_frame = 0
        self.is_playing = True
        self.animation_type = "spring"  # spring, pendulum, circuit

        self.setup_ui()
        self.create_static_plot()
        self.start_animation_loop()

    def setup_ui(self):
        """Настройка интерфейса"""
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Фрейм для графика
        self.graph_frame = ttk.Frame(main_frame)
        self.graph_frame.pack(fill=tk.BOTH, expand=True)

        # Панель управления
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)

        # Выбор типа визуализации
        ttk.Label(control_frame, text="Тип:").pack(side=tk.LEFT, padx=(0, 5))

        self.viz_type = tk.StringVar(value="auto")
        types = [("Авто", "auto"), ("Пружина", "spring"),
                 ("Маятник", "pendulum"), ("RLC-цепь", "circuit")]

        for text, value in types:
            ttk.Radiobutton(control_frame, text=text, variable=self.viz_type,
                            value=value, command=self.change_visualization).pack(side=tk.LEFT, padx=2)

        # Кнопки управления
        ttk.Button(control_frame, text="▶️ Старт",
                   command=self.start_animation).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="⏸️ Пауза",
                   command=self.pause_animation).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏭️ Следующий",
                   command=self.next_frame).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔄 Сброс",
                   command=self.reset_animation).pack(side=tk.LEFT, padx=5)

        # Слайдер скорости
        ttk.Label(control_frame, text="Скорость:").pack(side=tk.LEFT, padx=(20, 5))
        self.speed_var = tk.DoubleVar(value=100)
        ttk.Scale(control_frame, from_=10, to=500,
                  variable=self.speed_var, orient=tk.HORIZONTAL,
                  length=150).pack(side=tk.LEFT, padx=5)

        # Прогресс
        self.progress_var = tk.StringVar(value="Кадр: 0/0")
        ttk.Label(control_frame, textvariable=self.progress_var).pack(side=tk.RIGHT, padx=10)

    def create_static_plot(self):
        """Создаем статический график"""
        # Определяем тип визуализации
        viz_type = self.viz_type.get()
        if viz_type == "auto":
            if self.eq_type in ['harmonic', 'damped', 'forced']:
                self.animation_type = "spring"
            elif 'pendulum' in self.eq_type:
                self.animation_type = "pendulum"
            elif 'electric' in self.eq_type or 'circuit' in self.eq_type:
                self.animation_type = "circuit"
            else:
                self.animation_type = "spring"
        else:
            self.animation_type = viz_type

        print(f"🔧 Тип визуализации: {self.animation_type}")

        # Создаем фигуру в зависимости от типа
        if self.animation_type == "circuit":
            self.fig, (self.ax_circuit, self.ax_charge, self.ax_current) = plt.subplots(1, 3, figsize=(12, 4))
        else:
            self.fig, (self.ax_phys, self.ax_graph) = plt.subplots(1, 2, figsize=(10, 4))

        if self.animation_type == "circuit":
            self.setup_circuit_visualization()
        else:
            self.setup_mechanical_visualization()

        # Встраиваем в Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        print("✅ График создан")

    def setup_mechanical_visualization(self):
        """Настройка механической визуализации"""
        # Физическая модель (слева)
        self.ax_phys.clear()
        self.ax_phys.set_xlim(-2, 2)
        self.ax_phys.set_ylim(-2, 2)
        self.ax_phys.set_aspect('equal')
        self.ax_phys.set_title('Физическая модель')
        self.ax_phys.grid(True, alpha=0.3)

        # Точка крепления
        self.ax_phys.plot(0, 0, 'ko', markersize=10, label='Крепление')

        # Пружина/маятник
        self.phys_line, = self.ax_phys.plot([], [], 'b-', linewidth=3)

        # Масса
        self.mass = Circle((0, 0), 0.15, color='red', alpha=0.8)
        self.ax_phys.add_patch(self.mass)

        # График решения (справа)
        self.ax_graph.clear()
        self.ax_graph.set_xlim(np.min(self.t_values), np.max(self.t_values))
        self.ax_graph.set_ylim(np.min(self.y_values) * 1.1, np.max(self.y_values) * 1.1)
        self.ax_graph.set_xlabel('Время (с)')
        self.ax_graph.set_ylabel('y(t)')
        self.ax_graph.set_title('Решение уравнения')
        self.ax_graph.grid(True, alpha=0.3)

        # Полный график (серым)
        self.ax_graph.plot(self.t_values, self.y_values, 'gray', alpha=0.3, label='Полное решение')

        # Текущий график
        self.graph_line, = self.ax_graph.plot([], [], 'r-', linewidth=2, label='Текущее')

        # Текущая точка
        self.current_point, = self.ax_graph.plot([], [], 'ro', markersize=8)

        # Легенды
        self.ax_phys.legend()
        self.ax_graph.legend()

    def setup_circuit_visualization(self):
        """Настройка визуализации RLC-цепи"""
        # Схема цепи (слева)
        self.ax_circuit.clear()
        self.ax_circuit.set_xlim(-1, 4)
        self.ax_circuit.set_ylim(-1, 2)
        self.ax_circuit.set_aspect('equal')
        self.ax_circuit.set_title('RLC-цепь')
        self.ax_circuit.axis('off')

        # Рисуем статическую схему
        self.draw_circuit_schematic()

        # Анимированные элементы
        self.current_arrow = None
        self.charge_indicator = None
        self.voltage_indicator = None

        # График заряда (центр)
        self.ax_charge.clear()
        self.ax_charge.set_xlim(np.min(self.t_values), np.max(self.t_values))

        # Вычисляем ток как производную заряда
        if len(self.y_values) > 1:
            self.i_values = np.gradient(self.y_values, self.t_values)
        else:
            self.i_values = np.zeros_like(self.y_values)

        charge_min = np.min(self.y_values) * 1.1
        charge_max = np.max(self.y_values) * 1.1
        if abs(charge_max - charge_min) < 0.01:
            charge_min, charge_max = -1, 1

        self.ax_charge.set_ylim(charge_min, charge_max)
        self.ax_charge.set_xlabel('Время (с)')
        self.ax_charge.set_ylabel('Заряд q(t), Кл')
        self.ax_charge.set_title('Заряд конденсатора')
        self.ax_charge.grid(True, alpha=0.3)

        # Полный график заряда
        self.ax_charge.plot(self.t_values, self.y_values, 'gray', alpha=0.3, label='Заряд')

        # Текущий график заряда
        self.charge_line, = self.ax_charge.plot([], [], 'b-', linewidth=2, label='Текущий')
        self.charge_point, = self.ax_charge.plot([], [], 'bo', markersize=8)

        # График тока (справа)
        self.ax_current.clear()
        self.ax_current.set_xlim(np.min(self.t_values), np.max(self.t_values))

        current_min = np.min(self.i_values) * 1.1
        current_max = np.max(self.i_values) * 1.1
        if abs(current_max - current_min) < 0.01:
            current_min, current_max = -1, 1

        self.ax_current.set_ylim(current_min, current_max)
        self.ax_current.set_xlabel('Время (с)')
        self.ax_current.set_ylabel('Ток I(t), А')
        self.ax_current.set_title('Ток в цепи')
        self.ax_current.grid(True, alpha=0.3)

        # Полный график тока
        self.ax_current.plot(self.t_values, self.i_values, 'gray', alpha=0.3, label='Ток')

        # Текущий график тока
        self.current_line, = self.ax_current.plot([], [], 'g-', linewidth=2, label='Текущий')
        self.current_point, = self.ax_current.plot([], [], 'go', markersize=8)

        # Легенды
        self.ax_charge.legend()
        self.ax_current.legend()

    def draw_circuit_schematic(self):
        """Рисует схему RLC-цепи"""
        ax = self.ax_circuit

        # Батарея (источник напряжения)
        # Корпус батареи
        battery = Rectangle((0.2, 0.7), 0.6, 0.6, fill=False, linewidth=2, edgecolor='black')
        ax.add_patch(battery)
        # Полосы
        ax.plot([0.3, 0.3], [0.8, 1.2], 'k-', linewidth=3)
        ax.plot([0.7, 0.7], [0.9, 1.1], 'k-', linewidth=3)
        ax.text(0.5, 0.65, 'V', ha='center', va='center', fontsize=12, fontweight='bold')

        # Провода от батареи
        ax.plot([0.8, 1.2], [1.0, 1.0], 'k-', linewidth=2)

        # Резистор
        resistor = Rectangle((1.2, 0.8), 0.6, 0.4, fill=False, linewidth=2)
        ax.add_patch(resistor)
        # Зигзаг внутри резистора
        x_res = np.array([1.3, 1.4, 1.5, 1.6, 1.7])
        y_res = np.array([0.9, 1.1, 0.9, 1.1, 0.9])
        ax.plot(x_res, y_res, 'k-', linewidth=2)
        ax.text(1.5, 0.7, 'R', ha='center', va='center', fontsize=12, fontweight='bold')

        # Провод к катушке
        ax.plot([1.8, 2.2], [1.0, 1.0], 'k-', linewidth=2)

        # Катушка индуктивности
        for i in range(4):
            x_coil = 2.2 + i * 0.2
            circle = Circle((x_coil, 1.0), 0.08, fill=False, linewidth=2)
            ax.add_patch(circle)
        ax.text(2.6, 0.7, 'L', ha='center', va='center', fontsize=12, fontweight='bold')

        # Провод к конденсатору
        ax.plot([2.95, 3.3], [1.0, 1.0], 'k-', linewidth=2)

        # Конденсатор
        ax.plot([3.3, 3.3], [0.85, 1.15], 'k-', linewidth=3)
        ax.plot([3.5, 3.5], [0.85, 1.15], 'k-', linewidth=3)
        ax.plot([3.3, 3.5], [1.0, 1.0], 'k-', linewidth=1, linestyle='--')
        ax.text(3.4, 0.7, 'C', ha='center', va='center', fontsize=12, fontweight='bold')

        # Провода обратно к батарее
        ax.plot([3.5, 3.5], [1.0, 0.3], 'k-', linewidth=2)
        ax.plot([3.5, 0.5], [0.3, 0.3], 'k-', linewidth=2)
        ax.plot([0.5, 0.5], [0.3, 0.7], 'k-', linewidth=2)

        # Токовая стрелка (будет анимироваться)
        arrow_points = np.array([[2.0, 1.1], [2.1, 1.15], [2.2, 1.1]])
        self.current_arrow = Polygon(arrow_points, closed=True, color='red', alpha=0.7)
        ax.add_patch(self.current_arrow)
        ax.text(2.1, 1.25, 'I', ha='center', va='center', color='red', fontsize=10, fontweight='bold')

        # Индикатор заряда конденсатора (пластины)
        self.charge_left = Rectangle((3.28, 0.85), 0.04, 0.3, color='blue', alpha=0.5)
        self.charge_right = Rectangle((3.48, 0.85), 0.04, 0.3, color='blue', alpha=0.5)
        ax.add_patch(self.charge_left)
        ax.add_patch(self.charge_right)

    def update_frame(self):
        """Обновляем один кадр анимации"""
        if self.current_frame >= len(self.t_values):
            self.current_frame = 0

        idx = self.current_frame
        t = self.t_values[idx]
        y = self.y_values[idx]

        if self.animation_type == "circuit":
            self.update_circuit_frame(idx, t, y)
        else:
            self.update_mechanical_frame(idx, t, y)

        # Обновляем прогресс
        self.progress_var.set(f"Кадр: {idx + 1}/{len(self.t_values)}")

        # Перерисовываем
        self.canvas.draw_idle()

        # Увеличиваем кадр
        self.current_frame += 1

        # Планируем следующий кадр если играем
        if self.is_playing and self.current_frame < len(self.t_values):
            delay = int(self.speed_var.get())
            self.window.after(delay, self.update_frame)

    def update_mechanical_frame(self, idx, t, y):
        """Обновляем кадр механической системы"""
        # Обновляем физическую модель
        if self.animation_type == "spring":
            # Вертикальная пружина
            self.phys_line.set_data([0, 0], [0, y])
            self.mass.center = (0, y)
            title_suffix = f"Пружина: y={y:.3f}"
        else:  # pendulum
            # Маятник
            L = 1.5  # Длина
            x_bob = L * np.sin(y)
            y_bob = -L * np.cos(y)
            self.phys_line.set_data([0, x_bob], [0, y_bob])
            self.mass.center = (x_bob, y_bob)
            title_suffix = f"Маятник: θ={y:.3f} рад"

        # Обновляем график
        self.graph_line.set_data(self.t_values[:idx + 1], self.y_values[:idx + 1])
        self.current_point.set_data([t], [y])

        # Обновляем заголовок
        self.ax_graph.set_title(f'Решение: t={t:.2f}с, {title_suffix}')

    def update_circuit_frame(self, idx, t, y):
        """Обновляем кадр электрической цепи"""
        # Вычисляем текущий ток
        if idx > 0:
            current = (self.y_values[idx] - self.y_values[idx - 1]) / (self.t_values[idx] - self.t_values[idx - 1])
        else:
            current = 0

        # Анимируем стрелку тока (движется по цепи)
        arrow_pos = 2.1 + (t % 2) * 0.5  # Движется вперед-назад
        if self.current_arrow:
            arrow_points = np.array([[arrow_pos, 1.1],
                                     [arrow_pos + 0.1, 1.15],
                                     [arrow_pos + 0.2, 1.1]])
            self.current_arrow.set_xy(arrow_points)

        # Анимируем заряд конденсатора
        charge_height = 0.3 * abs(y) / max(abs(self.y_values)) if max(abs(self.y_values)) > 0 else 0.1
        if self.charge_left and self.charge_right:
            self.charge_left.set_height(charge_height)
            self.charge_right.set_height(charge_height)

            # Цвет в зависимости от знака заряда
            if y > 0:
                color = 'blue'
            else:
                color = 'red'
            self.charge_left.set_color(color)
            self.charge_right.set_color(color)
            self.charge_left.set_alpha(
                0.3 + 0.5 * abs(y) / max(abs(self.y_values)) if max(abs(self.y_values)) > 0 else 0.5)
            self.charge_right.set_alpha(
                0.3 + 0.5 * abs(y) / max(abs(self.y_values)) if max(abs(self.y_values)) > 0 else 0.5)

        # Обновляем графики
        self.charge_line.set_data(self.t_values[:idx + 1], self.y_values[:idx + 1])
        self.charge_point.set_data([t], [y])

        self.current_line.set_data(self.t_values[:idx + 1], self.i_values[:idx + 1])
        self.current_point.set_data([t], [current])

        # Обновляем заголовки
        self.ax_charge.set_title(f'Заряд: q={y:.3f} Кл')
        self.ax_current.set_title(f'Ток: I={current:.3f} А')

    def change_visualization(self):
        """Смена типа визуализации"""
        self.current_frame = 0
        self.canvas.get_tk_widget().destroy()
        self.create_static_plot()
        self.progress_var.set("Визуализация изменена")

    def start_animation_loop(self):
        """Запускаем цикл анимации"""
        self.is_playing = True
        self.update_frame()

    def start_animation(self):
        """Старт анимации"""
        if not self.is_playing:
            self.is_playing = True
            self.update_frame()

    def pause_animation(self):
        """Пауза анимации"""
        self.is_playing = False

    def next_frame(self):
        """Следующий кадр"""
        self.is_playing = False
        self.update_frame()

    def reset_animation(self):
        """Сброс анимации"""
        self.current_frame = 0
        self.is_playing = False

        if self.animation_type == "circuit":
            # Сбрасываем цепь
            if self.charge_line:
                self.charge_line.set_data([], [])
                self.charge_point.set_data([], [])
                self.current_line.set_data([], [])
                self.current_point.set_data([], [])
            if self.charge_left and self.charge_right:
                self.charge_left.set_height(0.1)
                self.charge_right.set_height(0.1)
        else:
            # Сбрасываем механическую систему
            if hasattr(self, 'phys_line'):
                self.phys_line.set_data([], [])
            if hasattr(self, 'mass'):
                self.mass.center = (0, 0)
            if hasattr(self, 'graph_line'):
                self.graph_line.set_data([], [])
                self.current_point.set_data([], [])

        self.canvas.draw_idle()
        self.progress_var.set("Кадр: 0/0")