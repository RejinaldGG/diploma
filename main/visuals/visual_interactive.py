# visual_interactive.py
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import numpy as np


class InteractiveVisualizer:
    def __init__(self, logic):
        self.logic = logic
        self.fig = None
        self.current_solution = None

    def create_parameter_explorer(self, base_equation, param_ranges):
        """Интерактивное исследование параметров"""
        fig, ax = plt.subplots(figsize=(10, 7))
        plt.subplots_adjust(bottom=0.4)

        # Создаем слайдеры для каждого параметра
        sliders = []
        slider_axes = []

        for i, (param_name, (min_val, max_val, init_val)) in enumerate(param_ranges.items()):
            slider_ax = plt.axes([0.25, 0.3 - i * 0.05, 0.65, 0.03])
            slider = Slider(slider_ax, param_name, min_val, max_val, valinit=init_val)
            sliders.append((param_name, slider))
            slider_axes.append(slider_ax)

        # Кнопка сброса
        reset_ax = plt.axes([0.8, 0.1, 0.1, 0.04])
        reset_button = Button(reset_ax, 'Сброс')

        # Начальный график
        t_initial = np.linspace(0, 10, 100)
        line, = ax.plot(t_initial, np.zeros_like(t_initial), 'r-', linewidth=2)
        ax.set_xlabel('Время')
        ax.set_ylabel('y(t)')
        ax.set_title('Интерактивное исследование параметров')
        ax.grid(True, alpha=0.3)

        def update(val=None):
            # Собираем текущие значения параметров
            params = {name: slider.val for name, slider in sliders}

            # Решаем уравнение с новыми параметрами
            # (здесь нужно интегрировать с логикой решения)
            try:
                # Временная заглушка - в реальности здесь вызов solver
                t = np.linspace(0, 10, 100)
                y = self._simulate_equation(params, t)
                line.set_ydata(y)
                fig.canvas.draw_idle()
            except Exception as e:
                print(f"Ошибка: {e}")

        def reset(event):
            for name, slider in sliders:
                slider.reset()

        # Подключаем обработчики
        for name, slider in sliders:
            slider.on_changed(update)

        reset_button.on_clicked(reset)

        # Первоначальное обновление
        update()

        return fig

    def _simulate_equation(self, params, t):
        """Заглушка для симуляции уравнения"""
        # В реальной реализации здесь будет вызов Wolfram
        omega = params.get('omega', 1.0)
        beta = params.get('beta', 0.1)

        # Простая симуляция затухающих колебаний
        return np.exp(-beta * t) * np.cos(omega * t)

    def create_bifurcation_diagram(self, param_name, param_range, equation_template):
        """Диаграмма бифуркаций"""
        fig, ax = plt.subplots(figsize=(10, 6))

        param_values = np.linspace(param_range[0], param_range[1], 100)
        bifurcation_data = []

        # Для каждого значения параметра находим установившееся состояние
        for param_val in param_values:
            # Здесь будет вызов решателя для каждого параметра
            # Временная заглушка:
            steady_states = self._find_steady_states(param_val)
            bifurcation_data.extend([(param_val, state) for state in steady_states])

        if bifurcation_data:
            params, states = zip(*bifurcation_data)
            ax.scatter(params, states, s=1, alpha=0.5, color='blue')

        ax.set_xlabel(param_name)
        ax.set_ylabel('Установившееся состояние')
        ax.set_title(f'Диаграмма бифуркаций по параметру {param_name}')
        ax.grid(True, alpha=0.3)

        return fig

    def _find_steady_states(self, param_val):
        """Заглушка для поиска установившихся состояний"""
        # В реальной реализации здесь анализ решения
        return [0.0]  # Простой пример