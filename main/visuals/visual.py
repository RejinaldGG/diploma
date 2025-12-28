# visual.py
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import numpy as np
import traceback
import sys
from main.logic.logic import ODELogic
from main.visuals.visual_integrated import IntegratedVisualizations
from main.visuals.visual_3d_plotly import Plotly3DModels as plotly_models

class ODEVisualizer:
    def __init__(self, root, logic):
        self.root = root
        self.logic = logic
        self.plotly_models = plotly_models()
        self.setup_ui()

        # Инициализируем интегрированные визуализации
        self.viz_manager = IntegratedVisualizations(self.logic, self.plot_frame)

        # Настройка matplotlib
        plt.rcParams.update({'font.size': 10})

        # Инициализируем 3D модели
        from main.visuals.visual_3d_models import ThreeDModels
        self.models_3d = ThreeDModels(logic.solver)

        self.setup_3d_models_ui()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.root.title("Визуализация ОДУ второго порядка")
        self.root.geometry("1400x900")

        # Основной фрейм
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Левая панель - управление
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Фрейм для параметров уравнения (использует grid)
        self.control_frame = ttk.LabelFrame(left_panel, text="Параметры уравнения", padding=10)
        self.control_frame.pack(fill=tk.BOTH, expand=True)

        # Фрейм для 3D моделей (будет внизу левой панели)
        self.models_frame_container = ttk.LabelFrame(left_panel, text="3D Модели", padding=10)
        self.models_frame_container.pack(fill=tk.X, pady=(10, 0))

        # Правая панель - графики и визуализации
        self.plot_frame = ttk.LabelFrame(main_frame, text="Визуализации", padding=10)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.setup_control_panel(self.control_frame)
        self.setup_visualization_controls(self.control_frame)
        self.setup_3d_models_ui()

    def setup_3d_models_ui(self):
        """Добавление кнопок для 3D моделей"""
        if not hasattr(self, 'models_frame_container'):
            return

        # Очищаем контейнер если там что-то есть
        for widget in self.models_frame_container.winfo_children():
            widget.destroy()

        # Создаем кнопки
        ttk.Button(self.models_frame_container, text="🎯 Маятник (3D)",
                   command=self.show_pendulum_3d).pack(fill=tk.X, pady=2)

        ttk.Button(self.models_frame_container, text="🔄 Двойной маятник",
                   command=self.show_double_pendulum).pack(fill=tk.X, pady=2)

        ttk.Button(self.models_frame_container, text="🔄 Пружинная система (3D)",
                   command=self.show_spring_3d).pack(fill=tk.X, pady=2)


    # В классе ODEVisualizer обновляем методы:
    def show_pendulum_3d(self):
        """Показ 3D маятника с Plotly"""
        try:
            # Параметры маятника
            params = {
                'L': 1.0,  # длина
                'g': 9.81,  # ускорение
                'beta': 0.1  # затухание
            }

            # Используем текущие начальные условия
            initial_conditions = [self.y0.get(), self.yp0.get()]
            t_range = (self.t_min.get(), self.t_max.get())
            solution = self.logic.solve_equation('custom',params, initial_conditions, t_range)
            # Запускаем интерактивную визуализацию
            success = self.plotly_models.create_interactive_pendulum(solution, params)

            if not success:
                # Fallback на matplotlib
                self.models_3d.show_simple_pendulum(
                    params, initial_conditions, t_range
                )

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать визуализацию: {e}")
            import traceback
            traceback.print_exc()

    def show_double_pendulum(self):
        """Показ двойного маятника с Plotly"""
        try:
            # Параметры
            params = {
                'L1': 1.0,
                'L2': 0.8,
                'm1': 1.0,
                'm2': 1.0,
                'g': 9.81
            }

            # Начальные условия
            initial_conditions = [np.pi / 4, 0, np.pi / 2, 0]
            t_range = (0, 20)

            # Запускаем интерактивную визуализацию
            success = self.plotly_models.create_double_pendulum_interactive(
                params, initial_conditions, t_range
            )

            if not success:
                # Fallback на matplotlib
                self.models_3d.show_double_pendulum_simple()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать визуализацию: {e}")

    def show_spring_3d(self):
        """Пружинная система с Plotly"""
        if not self.logic.current_solution:
            messagebox.showwarning("Предупреждение", "Сначала рассчитайте решение")
            return

        try:
            # Параметры пружины
            params = {'k': 1.0, 'm': 1.0}

            # Используем Plotly
            success = self.plotly_models.create_spring_system_interactive(
                self.logic.current_solution, params
            )

            if not success:
                # Fallback на matplotlib
                fig, anim = self.models_3d.create_spring_system(self.logic.current_solution)
                if fig:
                    plt.show()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать визуализацию: {e}")

    def show_3d_phase_space(self):
        """3D фазовое пространство с Plotly"""
        if not self.logic.current_solution:
            messagebox.showwarning("Предупреждение", "Сначала рассчитайте решение")
            return

        try:
            # Используем Plotly
            success = self.plotly_models.create_3d_phase_space_interactive(
                self.logic.current_solution
            )

            if not success:
                # Fallback на matplotlib
                fig, _ = self.models_3d.create_3d_phase_space(self.logic.current_solution)
                if fig:
                    plt.show()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать визуализацию: {e}")

    # Обновляем кнопки:
    def setup_3d_models_ui(self):
        """Добавление кнопок для 3D моделей"""
        if not hasattr(self, 'control_frame'):
            return

        models_frame = ttk.LabelFrame(self.control_frame, text="3D Модели (Plotly)", padding=10)
        models_frame.grid(row=100, column=0, sticky=tk.W + tk.E, pady=10, padx=5)

        ttk.Button(models_frame, text="🎯 Маятник (интерактивный 3D)",
                   command=self.show_pendulum_3d).grid(row=0, column=0, sticky=tk.W + tk.E, pady=2)

        ttk.Button(models_frame, text="🔄 Двойной маятник (3D)",
                   command=self.show_double_pendulum).grid(row=1, column=0, sticky=tk.W + tk.E, pady=2)

        ttk.Button(models_frame, text="🔄 Пружинная система (3D)",
                   command=self.show_spring_3d).grid(row=2, column=0, sticky=tk.W + tk.E, pady=2)

        ttk.Button(models_frame, text="🌐 3D Фазовое пространство",
                   command=self.show_3d_phase_space).grid(row=3, column=0, sticky=tk.W + tk.E, pady=2)

        # Добавляем информацию
        info_label = ttk.Label(models_frame,
                               text="Plotly создаст интерактивные 3D графики в браузере",
                               font=('Arial', 8))
        info_label.grid(row=4, column=0, sticky=tk.W + tk.E, pady=(10, 0))

        models_frame.columnconfigure(0, weight=1)


    def setup_visualization_controls(self, parent):
        """Кнопки управления визуализациями"""
        viz_control_frame = ttk.LabelFrame(parent, text="Типы визуализаций", padding=10)
        viz_control_frame.grid(row=25, column=0, sticky=tk.W + tk.E, pady=10)

        ttk.Button(viz_control_frame, text="📈 Основные графики",
                   command=self.show_basic_plots).pack(fill=tk.X, pady=2)

        ttk.Button(viz_control_frame, text="🔧 Физическая модель",
                   command=self.show_physics_viz).pack(fill=tk.X, pady=2)

        ttk.Button(viz_control_frame, text="🌐 3D фазовое пространство",
                   command=self.show_3d_viz).pack(fill=tk.X, pady=2)

        ttk.Button(viz_control_frame, text="📊 Сравнительный анализ",
                   command=self.show_comparison_viz).pack(fill=tk.X, pady=2)

        ttk.Button(viz_control_frame, text="❌ Очистить визуализации",
                   command=self.clear_visualizations).pack(fill=tk.X, pady=2)
        models_frame = ttk.LabelFrame(parent, text="3D Модели", padding=10)
        # Укажите большой номер строки, чтобы было внизу
        models_frame.grid(row=100, column=0, sticky=tk.W + tk.E, pady=20, padx=5)

        # Кнопки внутри models_frame
        ttk.Button(models_frame, text="🎯 Маятник (3D)",
                   command=self.show_pendulum_3d).grid(row=0, column=0, sticky=tk.W + tk.E, pady=2, padx=5)

        ttk.Button(models_frame, text="🔄 Двойной маятник",
                   command=self.show_double_pendulum).grid(row=1, column=0, sticky=tk.W + tk.E, pady=2, padx=5)

        ttk.Button(models_frame, text="🔄 Пружинная система (3D)",
                   command=self.show_spring_3d).grid(row=2, column=0, sticky=tk.W + tk.E, pady=2, padx=5)


        # Настраиваем расширение столбца
        models_frame.columnconfigure(0, weight=1)

    def show_basic_plots(self):
        """Показ основных графиков (решение + фазовый портрет)"""
        if not self.logic.current_solution or not self.logic.current_solution['success']:
            messagebox.showwarning("Предупреждение", "Сначала рассчитайте решение")
            return
        self.plot_solution(self.logic.current_solution)

    def show_physics_viz(self):
        """Физическая визуализация"""
        if not self.logic.current_solution or not self.logic.current_solution['success']:
            messagebox.showwarning("Предупреждение", "Сначала рассчитайте решение")
            return
        self.viz_manager.show_physics_in_main()

    def show_3d_viz(self):
        """3D визуализация"""
        if not self.logic.current_solution or not self.logic.current_solution['success']:
            messagebox.showwarning("Предупреждение", "Сначала рассчитайте решение")
            return
        self.viz_manager.show_3d_in_main()

    def show_comparison_viz(self):
        """Сравнительная визуализация"""
        if not self.logic.current_solution or not self.logic.current_solution['success']:
            messagebox.showwarning("Предупреждение", "Сначала рассчитайте решение")
            return
        self.viz_manager.show_comparison_in_main()

    def clear_visualizations(self):
        """Очистка всех визуализаций"""
        self.viz_manager._clear_visualization()
        self.clear_plots()

    def setup_control_panel(self, parent):
        """Панель управления"""
        # Выбор типа уравнения
        ttk.Label(parent, text="Тип уравнения:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.eq_type = tk.StringVar(value="harmonic")
        eq_types = [
            ("Гармонический осциллятор", "harmonic"),
            ("Затухающие колебания", "damped"),
            ("Вынужденные колебания", "forced"),
            ("Пользовательское", "custom")
        ]

        for i, (text, value) in enumerate(eq_types):
            ttk.Radiobutton(parent, text=text, variable=self.eq_type,
                            value=value, command=self.on_equation_change).grid(
                row=i + 1, column=0, sticky=tk.W, pady=2)

        # Параметры
        params_frame = ttk.Frame(parent)
        params_frame.grid(row=5, column=0, sticky=tk.W + tk.E, pady=10)

        self.params = {}
        self.setup_parameters(params_frame)

        # Начальные условия
        ttk.Label(parent, text="Начальные условия:").grid(row=10, column=0, sticky=tk.W, pady=(10, 5))

        ic_frame = ttk.Frame(parent)
        ic_frame.grid(row=11, column=0, sticky=tk.W + tk.E, pady=5)

        ttk.Label(ic_frame, text="y(0) =").grid(row=0, column=0)
        self.y0 = tk.DoubleVar(value=1.0)
        ttk.Entry(ic_frame, textvariable=self.y0, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(ic_frame, text="y'(0) =").grid(row=0, column=2)
        self.yp0 = tk.DoubleVar(value=0.0)
        ttk.Entry(ic_frame, textvariable=self.yp0, width=10).grid(row=0, column=3, padx=5)

        # Время
        ttk.Label(parent, text="Время моделирования:").grid(row=12, column=0, sticky=tk.W, pady=(10, 5))

        time_frame = ttk.Frame(parent)
        time_frame.grid(row=13, column=0, sticky=tk.W + tk.E, pady=5)

        ttk.Label(time_frame, text="от").grid(row=0, column=0)
        self.t_min = tk.DoubleVar(value=0.0)
        ttk.Entry(time_frame, textvariable=self.t_min, width=8).grid(row=0, column=1, padx=5)

        ttk.Label(time_frame, text="до").grid(row=0, column=2)
        self.t_max = tk.DoubleVar(value=20.0)
        ttk.Entry(time_frame, textvariable=self.t_max, width=8).grid(row=0, column=3, padx=5)

        # Кнопки
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=20, column=0, sticky=tk.W + tk.E, pady=20)

        ttk.Button(button_frame, text="Рассчитать",
                   command=self.calculate).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Очистить",
                   command=self.clear_plots).pack(side=tk.LEFT)

        # Информация
        self.info_text = tk.Text(parent, height=8, width=35)
        self.info_text.grid(row=21, column=0, sticky=tk.W + tk.E, pady=10)

    def show_physics_animation(self):
        """Показ физической анимации"""
        if not self.logic.current_solution or not self.logic.current_solution['success']:
            messagebox.showwarning("Предупреждение", "Сначала рассчитайте решение")
            return

        try:
            from main.visuals.visual_physics import PhysicsVisualizer
            t = self.logic.current_solution['t_values']
            y = self.logic.current_solution['y_values']

            physics_viz = PhysicsVisualizer(self.logic)
            eq_type = self.eq_type.get()

            if eq_type in ['harmonic', 'damped', 'forced']:
                fig = physics_viz.create_spring_animation(t, y)
            elif 'pendulum' in eq_type:  # если будешь добавлять маятник
                fig = physics_viz.create_pendulum_animation(t, y)
            else:
                fig = physics_viz.create_spring_animation(t, y)  # по умолчанию

            plt.show()

        except ImportError as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить модуль физической визуализации: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании анимации: {e}")

    def show_3d_phase(self):
        """3D визуализация фазового пространства"""
        if not self.logic.current_solution or not self.logic.current_solution['success']:
            messagebox.showwarning("Предупреждение", "Сначала рассчитайте решение")
            return

        try:
            from main.visuals.visual_3d import ThreeDVisualizer

            phase_data = self.logic.get_phase_portrait()
            if phase_data:
                t, y, yp = phase_data
                viz_3d = ThreeDVisualizer(self.logic)
                fig = viz_3d.plot_3d_phase_space(t, y, yp)
                plt.show()
            else:
                messagebox.showwarning("Предупреждение", "Недостаточно данных для 3D визуализации")

        except ImportError as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить модуль 3D визуализации: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании 3D графика: {e}")

    def show_interactive_explorer(self):
        """Интерактивный исследователь параметров"""
        try:
            from main.visuals.visual_interactive import InteractiveVisualizer

            # Параметры для исследования
            param_ranges = {
                'omega': (0.1, 5.0, 1.0),
                'beta': (0.01, 1.0, 0.1),
                'force': (0.1, 3.0, 1.0),
                'frequency': (0.1, 3.0, 0.5)
            }

            viz_interactive = InteractiveVisualizer(self.logic)
            fig = viz_interactive.create_parameter_explorer(
                self._build_current_equation(),
                param_ranges
            )
            plt.show()

        except ImportError as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить модуль интерактивной визуализации: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании интерактивного исследователя: {e}")

    def show_bifurcation(self):
        """Бифуркационная диаграмма"""
        try:
            from main.visuals.visual_interactive import InteractiveVisualizer

            viz_interactive = InteractiveVisualizer(self.logic)
            fig = viz_interactive.create_bifurcation_diagram(
                'beta',  # параметр для исследования
                (0.01, 1.0),  # диапазон параметра
                self._build_current_equation()
            )
            plt.show()

        except ImportError as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить модуль для бифуркационной диаграммы: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при создании бифуркационной диаграммы: {e}")

    def _build_current_equation(self):
        """Строит уравнение из текущих параметров"""
        eq_type = self.eq_type.get()
        params = self._collect_parameters(eq_type)
        return self.logic._build_equation(eq_type, params)

    def setup_parameters(self, parent):
        """Параметры уравнений"""
        # Гармонический
        self.harmonic_frame = ttk.Frame(parent)
        self.params['omega_harmonic'] = tk.DoubleVar(value=1.0)
        ttk.Label(self.harmonic_frame, text="ω =").grid(row=0, column=0)
        ttk.Entry(self.harmonic_frame, textvariable=self.params['omega_harmonic'], width=10).grid(row=0, column=1)

        # Затухающий
        self.damped_frame = ttk.Frame(parent)
        self.params['omega_damped'] = tk.DoubleVar(value=1.0)
        self.params['beta_damped'] = tk.DoubleVar(value=0.1)
        ttk.Label(self.damped_frame, text="ω =").grid(row=0, column=0)
        ttk.Entry(self.damped_frame, textvariable=self.params['omega_damped'], width=8).grid(row=0, column=1)
        ttk.Label(self.damped_frame, text="β =").grid(row=0, column=2)
        ttk.Entry(self.damped_frame, textvariable=self.params['beta_damped'], width=8).grid(row=0, column=3)

        # Вынужденный
        self.forced_frame = ttk.Frame(parent)
        self.params['omega_forced'] = tk.DoubleVar(value=1.0)
        self.params['beta_forced'] = tk.DoubleVar(value=0.1)
        self.params['force_forced'] = tk.DoubleVar(value=1.0)
        self.params['freq_forced'] = tk.DoubleVar(value=0.5)
        ttk.Label(self.forced_frame, text="ω =").grid(row=0, column=0)
        ttk.Entry(self.forced_frame, textvariable=self.params['omega_forced'], width=6).grid(row=0, column=1)
        ttk.Label(self.forced_frame, text="β =").grid(row=0, column=2)
        ttk.Entry(self.forced_frame, textvariable=self.params['beta_forced'], width=6).grid(row=0, column=3)
        ttk.Label(self.forced_frame, text="F =").grid(row=1, column=0)
        ttk.Entry(self.forced_frame, textvariable=self.params['force_forced'], width=6).grid(row=1, column=1)
        ttk.Label(self.forced_frame, text="Ω =").grid(row=1, column=2)
        ttk.Entry(self.forced_frame, textvariable=self.params['freq_forced'], width=6).grid(row=1, column=3)

        # Пользовательский
        self.custom_frame = ttk.Frame(parent)
        self.custom_equation = tk.StringVar(value="y''[t] + y[t] == 0")
        ttk.Label(self.custom_frame, text="Уравнение:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(self.custom_frame, textvariable=self.custom_equation, width=30).grid(row=1, column=0, columnspan=2)

        self.show_equation_params()

    def show_equation_params(self):
        """Показ параметров для выбранного уравнения"""
        # Скрываем все фреймы
        for frame in [self.harmonic_frame, self.damped_frame, self.forced_frame, self.custom_frame]:
            frame.grid_forget()

        # Показываем нужный фрейм
        eq_type = self.eq_type.get()
        if eq_type == "harmonic":
            self.harmonic_frame.grid(row=0, column=0, sticky=tk.W)
        elif eq_type == "damped":
            self.damped_frame.grid(row=0, column=0, sticky=tk.W)
        elif eq_type == "forced":
            self.forced_frame.grid(row=0, column=0, sticky=tk.W)
        elif eq_type == "custom":
            self.custom_frame.grid(row=0, column=0, sticky=tk.W)

    def on_equation_change(self):
        """При изменении типа уравнения"""
        self.show_equation_params()

    def setup_plot_area(self, parent):
        """Область для графиков"""
        # Создаем фигуру matplotlib
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 8))

        # Холст для matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def calculate(self):
        """Расчет и визуализация в отдельном потоке"""
        try:
            # Собираем параметры
            eq_type = self.eq_type.get()
            params = self._collect_parameters(eq_type)
            initial_conditions = [self.y0.get(), self.yp0.get()]
            t_range = (self.t_min.get(), self.t_max.get())

            # Проверяем корректность введенных данных
            validation_error = self._validate_inputs(params, initial_conditions, t_range)
            if validation_error:
                messagebox.showerror("Ошибка ввода", validation_error)
                return

            # Блокируем кнопки на время расчета
            self._set_ui_state(False)

            # Запускаем расчет в отдельном потоке
            thread = threading.Thread(
                target=self._calculate_thread,
                args=(eq_type, params, initial_conditions, t_range)
            )
            thread.daemon = True
            thread.start()

        except Exception as e:
            self._handle_error(f"Ошибка при запуске расчета: {str(e)}")
            self._set_ui_state(True)

    def _calculate_thread(self, eq_type, params, initial_conditions, t_range):
        """Поток для расчета"""
        try:
            # Вычисляем
            result = self.logic.solve_equation(eq_type, params, initial_conditions, t_range)

            # Обновляем GUI в главном потоке
            self.root.after(0, self._handle_calculation_result, result)

        except Exception as e:
            self.root.after(0, self._handle_error, f"Ошибка в потоке расчета: {str(e)}")

    def _handle_calculation_result(self, result):
        """Обработка результата расчета в главном потоке"""
        try:
            if result['success']:
                self.plot_solution(result)
                self.show_analysis()
            else:
                messagebox.showerror("Ошибка решения", f"Не удалось решить уравнение: {result['error']}")
        finally:
            # Разблокируем UI
            self._set_ui_state(True)

    def _handle_error(self, error_msg):
        """Обработка ошибки в главном потоке"""
        messagebox.showerror("Ошибка", error_msg)
        self._set_ui_state(True)

    def _set_ui_state(self, enabled):
        """Блокировка/разблокировка UI"""
        state = 'normal' if enabled else 'disabled'

        # Блокируем все основные элементы управления
        for widget in self.find_all_widgets(self.root):
            if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Combobox)):
                try:
                    # Не блокируем кнопку закрытия
                    if hasattr(widget, 'winfo_class') and widget.winfo_class() == 'TButton':
                        if 'рассчет' not in str(widget.cget('text')).lower():
                            widget.configure(state=state)
                except:
                    pass

        # Показываем/скрываем индикатор прогресса
        if hasattr(self, 'progress_label'):
            if enabled:
                self.progress_label.pack_forget()
            else:
                self.progress_label.pack(pady=10)

    def find_all_widgets(self, widget):
        """Рекурсивно находит все виджеты"""
        widgets = [widget]
        for child in widget.winfo_children():
            widgets.extend(self.find_all_widgets(child))
        return widgets

    def _validate_inputs(self, params, initial_conditions, t_range):
        """Проверка корректности введенных данных"""
        errors = []

        # Проверка времени
        t_min, t_max = t_range
        if t_min >= t_max:
            errors.append("Начальное время должно быть меньше конечного")
        if t_max - t_min > 1000:
            errors.append("Слишком большой диапазон времени. Рекомендуется до 1000 единиц")

        # Проверка начальных условий
        y0, yp0 = initial_conditions
        if abs(y0) > 1e6 or abs(yp0) > 1e6:
            errors.append("Слишком большие начальные условия")

        # Проверка параметров
        for param_name, param_value in params.items():
            if isinstance(param_value, (int, float)):
                if abs(param_value) > 1e6:
                    errors.append(f"Слишком большое значение параметра {param_name}")
                if param_value < 0 and param_name in ['omega', 'frequency']:
                    errors.append(f"Параметр {param_name} не может быть отрицательным")

        # Проверка пользовательского уравнения
        if self.eq_type.get() == 'custom':
            custom_eq = params.get('equation', '')
            if not self._validate_custom_equation(custom_eq):
                errors.append("Некорректное пользовательское уравнение")

        return "\n".join(errors) if errors else None

    def _validate_custom_equation(self, equation):
        """Проверка корректности пользовательского уравнения"""
        if not equation:
            return False

        required_elements = ["y''", "t"]
        for element in required_elements:
            if element not in equation:
                return False

        # Дополнительные проверки
        forbidden_patterns = ["System`", "DeleteFile", "Run", "Import"]
        for pattern in forbidden_patterns:
            if pattern in equation:
                return False

        return True

    def _format_error_message(self, error):
        """Форматирование сообщения об ошибке от Wolfram"""
        error_mapping = {
            "Failed to communicate with kernel": "Ошибка связи с Wolfram Engine",
            "NDSolve::ndnum": "Ошибка численного решения",
            "NDSolve::ndsz": "Слишком резкое изменение решения",
            "NDSolve::ndstf": "Система слишком жесткая",
            "Syntax::sntxf": "Синтаксическая ошибка в уравнении"
        }

        # Ищем известные ошибки
        for pattern, message in error_mapping.items():
            if pattern in str(error):
                return f"{message}\n\nТехническая информация:\n{error}"

        return f"Ошибка при решении уравнения:\n{error}"

    def _format_exception_message(self, exception):
        """Форматирование полного сообщения об исключении"""
        # Получаем полный стектрейс
        exc_type, exc_value, exc_traceback = sys.exc_info()
        stack_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)

        # Форматируем понятное сообщение
        error_type = type(exception).__name__
        error_message = str(exception)

        # Создаем понятное сообщение для пользователя
        user_friendly_msg = self._get_user_friendly_error(error_type, error_message)

        # Полное техническое сообщение (можно показать в отдельном окне или записать в лог)
        full_technical_msg = f"""🚨 КРИТИЧЕСКАЯ ОШИБКА

    Тип ошибки: {error_type}
    Сообщение: {error_message}

    Стек вызовов:
    {''.join(stack_trace)}

    Рекомендации:
    1. Проверьте корректность введенных параметров
    2. Убедитесь, что Wolfram Engine установлен и работает
    3. Попробуйте уменьшить диапазон времени
    4. Проверьте начальные условия"""

        # Показываем упрощенное сообщение пользователю
        simplified_msg = f"""{user_friendly_msg}

    Техническая информация:
    Тип: {error_type}
    Сообщение: {error_message}

    Для подробной информации смотрите консоль."""

        # Выводим полную информацию в консоль
        print("=" * 80)
        print("ПОЛНАЯ ИНФОРМАЦИЯ ОБ ОШИБКЕ:")
        print("=" * 80)
        print(full_technical_msg)
        print("=" * 80)

        return simplified_msg

    def _get_user_friendly_error(self, error_type, error_message):
        """Понятные сообщения для пользователя"""
        friendly_messages = {
            "ConnectionError": "Ошибка подключения к Wolfram Engine",
            "TimeoutError": "Превышено время ожидания расчета",
            "ValueError": "Некорректные значения параметров",
            "TypeError": "Ошибка в типах данных",
            "KeyError": "Ошибка в параметрах уравнения",
            "AttributeError": "Внутренняя ошибка программы",
            "ImportError": "Ошибка загрузки модулей",
            "MemoryError": "Недостаточно памяти для расчета",
        }

        # Ищем конкретные паттерны в сообщениях
        if "only integer scalar arrays" in error_message:
            return "Ошибка обработки данных от Wolfram Engine. Попробуйте другие параметры."
        elif "period_estimate" in error_message:
            return "Ошибка анализа результатов. Расчет выполнен, но анализ не удался."
        elif "wolfram" in error_message.lower():
            return "Проблема с Wolfram Engine. Проверьте установку и подключение."

        # Возвращаем общее сообщение по типу ошибки
        return friendly_messages.get(error_type, "Произошла непредвиденная ошибка")

    # Дополнительно можно добавить метод для логирования
    def _log_error(self, error_data):
        """Логирование ошибок в файл"""
        import datetime
        try:
            with open("ode_solver_errors.log", "a", encoding="utf-8") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n{'=' * 60}\n")
                f.write(f"ОШИБКА [{timestamp}]\n")
                f.write(f"{error_data}\n")
                f.write(f"{'=' * 60}\n")
        except Exception as e:
            print(f"Не удалось записать лог ошибки: {e}")

    def _collect_parameters(self, eq_type):
        """Сбор параметров для выбранного типа уравнения"""
        params = {}

        if eq_type == "harmonic":
            params['omega'] = self.params['omega_harmonic'].get()
        elif eq_type == "damped":
            params['omega'] = self.params['omega_damped'].get()
            params['beta'] = self.params['beta_damped'].get()
        elif eq_type == "forced":
            params['omega'] = self.params['omega_forced'].get()
            params['beta'] = self.params['beta_forced'].get()
            params['force'] = self.params['force_forced'].get()
            params['frequency'] = self.params['freq_forced'].get()
        elif eq_type == "custom":
            params['equation'] = self.custom_equation.get()

        return params

    def plot_solution(self, result):
        """Построение основных графиков (решение + фазовый портрет)"""
        if not result['success']:
            return

        try:
            # Очищаем предыдущие визуализации
            self.viz_manager._clear_visualization()

            t = result['t_values']
            y = result['y_values']
            phase_data = self.logic.get_phase_portrait()

            # Создаем фигуру с двумя subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            fig.subplots_adjust(hspace=0.4)

            # График решения
            ax1.plot(t, y, 'b-', linewidth=2, label='y(t)')
            ax1.set_xlabel('Время t')
            ax1.set_ylabel('y(t)')
            ax1.set_title('Решение ОДУ')
            ax1.grid(True, alpha=0.3)
            ax1.legend()

            # Фазовый портрет
            if phase_data:
                t_phase, y_phase, y_prime = phase_data
                ax2.plot(y_phase.tolist(), y_prime.tolist(), 'r-', linewidth=1, label='Фазовый портрет')
                ax2.set_xlabel('y')
                ax2.set_ylabel("y'")
                ax2.set_title('Фазовый портрет')
                ax2.grid(True, alpha=0.3)
                ax2.legend()
            else:
                ax2.text(0.5, 0.5, 'Недостаточно данных\nдля фазового портрета',
                         ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('Фазовый портрет')

            # Встраиваем в интерфейс
            self.viz_manager._embed_figure(fig)

        except Exception as e:
            print(f"Ошибка при построении графиков: {e}")

    def show_analysis(self):
        """Показ анализа решения"""
        analysis = self.logic.analyze_solution()

        if analysis:
            info_text = f"""
АНАЛИЗ РЕШЕНИЯ:
Максимальное значение: {analysis['max_value']:.4f}
Минимальное значение: {analysis['min_value']:.4f}
Амплитуда: {analysis['amplitude']:.4f}
Оценка периода: {analysis['period_estimate']:.4f}
Время моделирования: {analysis['final_time']:.1f}
"""
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)

    def clear_plots(self):
        """Очистка графиков"""
        self.viz_manager._clear_visualization()
        self.info_text.delete(1.0, tk.END)

    def close(self):
        """Закрытие приложения"""
        self.logic.close()
        plt.close('all')


# Главная функция
def main():
    root = tk.Tk()

    # Создаем экземпляры классов
    from main.logic.logic import ODELogic
    logic = ODELogic()

    app = ODEVisualizer(root, logic)

    # Обработка закрытия окна
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, app))

    root.mainloop()


def on_closing(root, app):
    app.close()
    root.destroy()


if __name__ == "__main__":
    main()