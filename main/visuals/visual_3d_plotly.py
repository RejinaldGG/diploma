# main/visuals/visual_3d_plotly.py
# main/visuals/visual_3d_plotly.py
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from plotly.offline import iplot
import json
from wolframclient.language import wlexpr


class Plotly3DModels:
    """3D визуализация с использованием Plotly (интерактивная, WebGL)"""

    def __init__(self, wolfram_solver):
        self.wolfram = wolfram_solver
        pio.templates.default = "plotly_dark"

    def solve_pendulum_equation(self, params, initial_conditions, t_range):
        """
        Решение уравнения маятника через Wolfram
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
        Решение системы уравнений для двойного маятника
        """
        L1, L2 = params.get('L1', 1.0), params.get('L2', 0.8)
        m1, m2 = params.get('m1', 1.0), params.get('m2', 1.0)
        g = params.get('g', 9.81)

        theta1_0, omega1_0, theta2_0, omega2_0 = initial_conditions

        equations = [
            f"(m1 + m2)*L1*theta1''[t] + m2*L2*theta2''[t]*Cos[theta1[t]-theta2[t]] "
            f"+ m2*L2*theta2'[t]^2*Sin[theta1[t]-theta2[t]] + (m1 + m2)*g*Sin[theta1[t]] == 0",

            f"m2*L2*theta2''[t] + m2*L1*theta1''[t]*Cos[theta1[t]-theta2[t]] "
            f"- m2*L1*theta1'[t]^2*Sin[theta1[t]-theta2[t]] + m2*g*Sin[theta2[t]] == 0"
        ]

        wolfram_command = f"""
        solution = NDSolve[{{
            {equations[0]},
            {equations[1]},
            theta1[0] == {theta1_0},
            theta1'[0] == {omega1_0},
            theta2[0] == {theta2_0},
            theta2'[0] == {omega2_0}
        }}, {{theta1, theta2}}, {{t, {t_range[0]}, {t_range[1]}}}, 
        MaxSteps -> 10000]
        """

        try:
            result = self.wolfram.session.evaluate(wlexpr(wolfram_command))

            data_command = f"""
            tmin = {t_range[0]};
            tmax = {t_range[1]};
            data = Table[{{{{t, theta1[t] /. First[solution]}}, {{t, theta2[t] /. First[solution]}}}}, 
                     {{t, tmin, tmax, (tmax-tmin)/500}}];
            ExportString[data, "JSON"]
            """

            json_data = self.wolfram.session.evaluate(wlexpr(data_command))
            data_points = json.loads(json_data)

            t_values = [point[0][0] for point in data_points]
            theta1_values = [point[0][1] for point in data_points]
            theta2_values = [point[1][1] for point in data_points]

            return {
                'success': True,
                't_values': t_values,
                'theta1': theta1_values,
                'theta2': theta2_values,
                'params': params
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_interactive_pendulum(self, params, initial_conditions, t_range):
        """
        Полная интерактивная визуализация маятника
        """
        # Решаем уравнение
        solution = self.solve_pendulum_equation(params, initial_conditions, t_range)

        if not solution['success']:
            print(f"Ошибка решения: {solution.get('error', 'Неизвестная ошибка')}")
            return False

        return self._plot_pendulum_solution(solution, params)

    def _plot_pendulum_solution(self, solution, params):
        """
        Построение графика маятника из решения
        """
        t = solution['t_values']
        theta = solution['y_values']
        L = params.get('L', 1.0)

        # Ограничиваем количество точек для производительности
        if len(t) > 500:
            indices = np.linspace(0, len(t) - 1, 500, dtype=int)
            t = np.array(t)[indices]
            theta = np.array(theta)[indices]

        # Вычисляем координаты
        x = L * np.sin(theta)
        y = np.zeros_like(x)
        z = -L * np.cos(theta)

        # Создаем фигуру
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'scene'}, {'type': 'xy'}],
                   [{'type': 'xy'}, {'type': 'xy'}]],
            subplot_titles=('3D Маятник', 'Траектория груза',
                            'Угол vs время', 'Фазовый портрет'),
            horizontal_spacing=0.1,
            vertical_spacing=0.15
        )

        # 1. 3D маятник (первый кадр)
        fig.add_trace(
            go.Scatter3d(
                x=[0, x[0]], y=[0, y[0]], z=[0, z[0]],
                mode='lines+markers',
                line=dict(color='blue', width=5),
                marker=dict(size=[8, 20], color=['red', 'green']),
                name='Маятник'
            ),
            row=1, col=1
        )

        # 2. Траектория (2D проекция)
        fig.add_trace(
            go.Scatter(
                x=x, y=z,
                mode='lines',
                line=dict(color='yellow', width=2),
                name='Траектория'
            ),
            row=1, col=2
        )

        # 3. График угла
        fig.add_trace(
            go.Scatter(
                x=t, y=theta,
                mode='lines',
                line=dict(color='cyan', width=2),
                name='Угол θ(t)'
            ),
            row=2, col=1
        )

        # 4. Фазовый портрет (θ vs ω)
        if len(theta) > 1:
            dt = t[1] - t[0]
            omega = np.gradient(theta, dt)
            fig.add_trace(
                go.Scatter(
                    x=theta, y=omega,
                    mode='lines',
                    line=dict(color='magenta', width=2),
                    name='Фазовый портрет'
                ),
                row=2, col=2
            )

        # Обновляем layout
        fig.update_layout(
            title=f'Математический маятник (L={L} м)',
            height=800,
            showlegend=True,
            scene=dict(
                xaxis=dict(range=[-L * 1.5, L * 1.5], title='X'),
                yaxis=dict(range=[-L * 0.5, L * 0.5], title='Y'),
                zaxis=dict(range=[-L * 1.5, L * 0.5], title='Z'),
                aspectmode='manual',
                aspectratio=dict(x=1, y=0.3, z=1)
            )
        )

        # Обновляем оси
        fig.update_xaxes(title_text='X (м)', row=1, col=2)
        fig.update_yaxes(title_text='Z (м)', row=1, col=2)
        fig.update_xaxes(title_text='Время (с)', row=2, col=1)
        fig.update_yaxes(title_text='θ (рад)', row=2, col=1)
        fig.update_xaxes(title_text='θ (рад)', row=2, col=2)
        fig.update_yaxes(title_text='ω (рад/с)', row=2, col=2)

        # Создаем кадры для анимации
        frames = []
        step = max(1, len(theta) // 50)  # 50 кадров

        for i in range(0, len(theta), step):
            frames.append(
                go.Frame(
                    data=[
                        # 3D маятник
                        go.Scatter3d(
                            x=[0, x[i]], y=[0, y[i]], z=[0, z[i]],
                            mode='lines+markers',
                            line=dict(color='blue', width=5),
                            marker=dict(size=[8, 20], color=['red', 'green'])
                        ),
                        # Текущая точка на траектории
                        go.Scatter(
                            x=[x[i]], y=[z[i]],
                            mode='markers',
                            marker=dict(size=10, color='red'),
                            showlegend=False
                        ),
                        # Текущая точка на графике угла
                        go.Scatter(
                            x=[t[i]], y=[theta[i]],
                            mode='markers',
                            marker=dict(size=8, color='red'),
                            showlegend=False
                        )
                    ],
                    name=f'frame_{i}'
                )
            )

        fig.frames = frames

        # Добавляем кнопки анимации
        fig.update_layout(
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'buttons': [
                    {
                        'label': '▶️ Воспроизвести',
                        'method': 'animate',
                        'args': [None, {
                            'frame': {'duration': 50, 'redraw': True},
                            'fromcurrent': True,
                            'transition': {'duration': 0}
                        }]
                    },
                    {
                        'label': '⏸️ Пауза',
                        'method': 'animate',
                        'args': [[None], {
                            'frame': {'duration': 0, 'redraw': False},
                            'mode': 'immediate'
                        }]
                    }
                ],
                'x': 0.1,
                'y': 0,
                'xanchor': 'right',
                'yanchor': 'top'
            }]
        )

        # Добавляем слайдер времени
        steps = []
        for i in range(0, len(theta), step):
            step_dict = {
                'args': [
                    [f'frame_{i}'],
                    {'frame': {'duration': 0, 'redraw': True},
                     'mode': 'immediate'}
                ],
                'label': f'{t[i]:.1f} с',
                'method': 'animate'
            }
            steps.append(step_dict)

        sliders = [{
            'active': 0,
            'yanchor': 'top',
            'xanchor': 'left',
            'currentvalue': {
                'font': {'size': 16},
                'prefix': 'Время: ',
                'visible': True,
                'xanchor': 'right'
            },
            'transition': {'duration': 0},
            'pad': {'b': 10, 't': 50},
            'len': 0.9,
            'x': 0.1,
            'y': 0,
            'steps': steps
        }]

        fig.update_layout(sliders=sliders)

        # Показываем
        fig.show()
        return True

    def create_double_pendulum_interactive(self, params, initial_conditions, t_range):
        """
        Полная интерактивная визуализация двойного маятника
        """
        solution = self.solve_double_pendulum(params, initial_conditions, t_range)

        if not solution['success']:
            print(f"Ошибка решения: {solution.get('error', 'Неизвестная ошибка')}")
            return False

        return self._plot_double_pendulum_solution(solution)

    def _plot_double_pendulum_solution(self, solution):
        """
        Построение графика двойного маятника
        """
        t = solution['t_values']
        theta1 = solution['theta1']
        theta2 = solution['theta2']
        params = solution['params']

        L1, L2 = params.get('L1', 1.0), params.get('L2', 0.8)

        # Ограничиваем количество точек
        if len(t) > 500:
            indices = np.linspace(0, len(t) - 1, 500, dtype=int)
            t = np.array(t)[indices]
            theta1 = np.array(theta1)[indices]
            theta2 = np.array(theta2)[indices]

        # Вычисляем координаты
        x1 = L1 * np.sin(theta1)
        z1 = -L1 * np.cos(theta1)

        x2 = x1 + L2 * np.sin(theta2)
        z2 = z1 - L2 * np.cos(theta2)

        # Создаем фигуру
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'scene'}, {'type': 'xy'}],
                   [{'type': 'xy'}, {'type': 'xy'}]],
            subplot_titles=('3D Двойной маятник', 'Траектория конца',
                            'Углы vs время', 'Фазовый портрет θ1 vs θ2'),
            horizontal_spacing=0.1,
            vertical_spacing=0.15
        )

        # 1. 3D двойной маятник (первый кадр)
        fig.add_trace(
            go.Scatter3d(
                x=[0, x1[0], x2[0]],
                y=[0, 0, 0],
                z=[0, z1[0], z2[0]],
                mode='lines+markers',
                line=dict(color='blue', width=4),
                marker=dict(
                    size=[10, 15, 12],
                    color=['red', 'blue', 'green'],
                    symbol=['circle', 'circle', 'circle']
                ),
                name='Двойной маятник'
            ),
            row=1, col=1
        )

        # 2. Траектория конца
        fig.add_trace(
            go.Scatter(
                x=x2, y=z2,
                mode='lines',
                line=dict(color='yellow', width=2, opacity=0.7),
                name='Траектория конца'
            ),
            row=1, col=2
        )

        # 3. Графики углов
        fig.add_trace(
            go.Scatter(
                x=t, y=theta1,
                mode='lines',
                line=dict(color='cyan', width=2),
                name='θ1'
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=t, y=theta2,
                mode='lines',
                line=dict(color='magenta', width=2),
                name='θ2'
            ),
            row=2, col=1
        )

        # 4. Фазовый портрет θ1 vs θ2
        fig.add_trace(
            go.Scatter(
                x=theta1, y=theta2,
                mode='lines',
                line=dict(color='orange', width=2),
                name='θ1 vs θ2'
            ),
            row=2, col=2
        )

        # Обновляем layout
        fig.update_layout(
            title=f'Двойной маятник (L1={L1} м, L2={L2} м)',
            height=800,
            showlegend=True,
            scene=dict(
                xaxis=dict(
                    range=[-(L1 + L2) * 1.2, (L1 + L2) * 1.2],
                    title='X (м)'
                ),
                yaxis=dict(
                    range=[-(L1 + L2) * 0.2, (L1 + L2) * 0.2],
                    title='Y (м)'
                ),
                zaxis=dict(
                    range=[-(L1 + L2) * 1.2, (L1 + L2) * 0.2],
                    title='Z (м)'
                ),
                aspectmode='manual',
                aspectratio=dict(x=1, y=0.1, z=1)
            )
        )

        # Обновляем оси
        fig.update_xaxes(title_text='X (м)', row=1, col=2)
        fig.update_yaxes(title_text='Z (м)', row=1, col=2)
        fig.update_xaxes(title_text='Время (с)', row=2, col=1)
        fig.update_yaxes(title_text='Угол (рад)', row=2, col=1)
        fig.update_xaxes(title_text='θ1 (рад)', row=2, col=2)
        fig.update_yaxes(title_text='θ2 (рад)', row=2, col=2)

        # Создаем кадры для анимации
        frames = []
        step = max(1, len(t) // 50)

        for i in range(0, len(t), step):
            frames.append(
                go.Frame(
                    data=[
                        # 3D двойной маятник
                        go.Scatter3d(
                            x=[0, x1[i], x2[i]],
                            y=[0, 0, 0],
                            z=[0, z1[i], z2[i]],
                            mode='lines+markers',
                            line=dict(color='blue', width=4),
                            marker=dict(
                                size=[10, 15, 12],
                                color=['red', 'blue', 'green']
                            )
                        ),
                        # Текущая точка траектории
                        go.Scatter(
                            x=[x2[i]], y=[z2[i]],
                            mode='markers',
                            marker=dict(size=8, color='red'),
                            showlegend=False
                        )
                    ],
                    name=f'frame_{i}'
                )
            )

        fig.frames = frames

        # Добавляем кнопки анимации
        fig.update_layout(
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'buttons': [
                    {
                        'label': '▶️ Воспроизвести',
                        'method': 'animate',
                        'args': [None, {
                            'frame': {'duration': 50, 'redraw': True},
                            'fromcurrent': True
                        }]
                    },
                    {
                        'label': '⏸️ Пауза',
                        'method': 'animate',
                        'args': [[None], {
                            'frame': {'duration': 0, 'redraw': False},
                            'mode': 'immediate'
                        }]
                    }
                ]
            }]
        )

        # Показываем
        fig.show()
        return True

    def create_spring_system_interactive(self, solution_data, params=None):
        """
        Интерактивная визуализация пружинной системы
        """
        if not solution_data['success']:
            return False

        t = solution_data['t_values']
        y = solution_data['y_values']

        # Параметры
        k = params.get('k', 1.0) if params else 1.0
        m = params.get('m', 1.0) if params else 1.0

        # Ограничиваем точки
        if len(t) > 500:
            indices = np.linspace(0, len(t) - 1, 500, dtype=int)
            t = np.array(t)[indices]
            y = np.array(y)[indices]

        # Создаем фигуру
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'scene'}, {'type': 'xy'}],
                   [{'type': 'xy'}, {'type': 'xy'}]],
            subplot_titles=('3D Пружинная система', 'Смещение vs время',
                            'Скорость vs время', 'Фазовый портрет'),
            horizontal_spacing=0.1,
            vertical_spacing=0.15
        )

        # 1. 3D пружинная система (статичная)
        spring_length = 2.0
        spring_radius = 0.3
        spring_coils = 10

        def create_spring_coords(compression):
            z = np.linspace(0, spring_length - compression, 100)
            theta = z * 2 * np.pi * spring_coils / spring_length
            x = spring_radius * np.cos(theta)
            y = spring_radius * np.sin(theta)
            return x, y, z

        # Первый кадр пружины
        x_spring, y_spring, z_spring = create_spring_coords(y[0] if y[0] > 0 else 0)

        fig.add_trace(
            go.Scatter3d(
                x=x_spring, y=y_spring, z=z_spring,
                mode='lines',
                line=dict(color='blue', width=4),
                name='Пружина'
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter3d(
                x=[0], y=[0], z=[spring_length - (y[0] if y[0] > 0 else 0)],
                mode='markers',
                marker=dict(size=15, color='red', symbol='cube'),
                name='Масса'
            ),
            row=1, col=1
        )

        # 2. График смещения
        fig.add_trace(
            go.Scatter(
                x=t, y=y,
                mode='lines',
                line=dict(color='green', width=2),
                name='Смещение y(t)'
            ),
            row=1, col=2
        )

        # 3. График скорости
        if len(y) > 1:
            dt = t[1] - t[0]
            velocity = np.gradient(y, dt)
            fig.add_trace(
                go.Scatter(
                    x=t, y=velocity,
                    mode='lines',
                    line=dict(color='orange', width=2),
                    name='Скорость v(t)'
                ),
                row=2, col=1
            )

        # 4. Фазовый портрет
        if len(y) > 1:
            fig.add_trace(
                go.Scatter(
                    x=y, y=velocity,
                    mode='lines',
                    line=dict(color='purple', width=2),
                    name='Фазовый портрет'
                ),
                row=2, col=2
            )

        # Обновляем layout
        fig.update_layout(
            title=f'Пружинная система (k={k}, m={m})',
            height=800,
            showlegend=True,
            scene=dict(
                xaxis=dict(range=[-1, 1], title='X'),
                yaxis=dict(range=[-1, 1], title='Y'),
                zaxis=dict(range=[0, spring_length + 0.5], title='Z'),
                aspectmode='manual',
                aspectratio=dict(x=1, y=1, z=2)
            )
        )

        # Обновляем оси
        fig.update_xaxes(title_text='Время (с)', row=1, col=2)
        fig.update_yaxes(title_text='Смещение (м)', row=1, col=2)
        fig.update_xaxes(title_text='Время (с)', row=2, col=1)
        fig.update_yaxes(title_text='Скорость (м/с)', row=2, col=1)
        fig.update_xaxes(title_text='Смещение (м)', row=2, col=2)
        fig.update_yaxes(title_text='Скорость (м/с)', row=2, col=2)

        # Создаем кадры для анимации
        frames = []
        step = max(1, len(t) // 50)

        for i in range(0, len(t), step):
            x_s, y_s, z_s = create_spring_coords(y[i] if y[i] > 0 else 0)
            mass_z = spring_length - (y[i] if y[i] > 0 else 0)

            frames.append(
                go.Frame(
                    data=[
                        # Пружина
                        go.Scatter3d(
                            x=x_s, y=y_s, z=z_s,
                            mode='lines',
                            line=dict(color='blue', width=4)
                        ),
                        # Масса
                        go.Scatter3d(
                            x=[0], y=[0], z=[mass_z],
                            mode='markers',
                            marker=dict(size=15, color='red', symbol='cube')
                        ),
                        # Текущая точка на графике
                        go.Scatter(
                            x=[t[i]], y=[y[i]],
                            mode='markers',
                            marker=dict(size=8, color='red'),
                            showlegend=False
                        )
                    ],
                    name=f'frame_{i}'
                )
            )

        fig.frames = frames

        # Добавляем анимацию
        fig.update_layout(
            updatemenus=[{
                'type': 'buttons',
                'buttons': [
                    {
                        'label': '▶️ Воспроизвести',
                        'method': 'animate',
                        'args': [None, {
                            'frame': {'duration': 50, 'redraw': True},
                            'fromcurrent': True
                        }]
                    }
                ]
            }]
        )

        fig.show()
        return True

    def create_3d_phase_space_interactive(self, solution_data):
        """
        Интерактивная 3D визуализация фазового пространства
        """
        if not solution_data['success']:
            return False

        t = solution_data['t_values']
        y = solution_data['y_values']

        if len(y) > 500:
            indices = np.linspace(0, len(t) - 1, 500, dtype=int)
            t = np.array(t)[indices]
            y = np.array(y)[indices]

        # Вычисляем производные
        if len(y) > 1:
            dt = t[1] - t[0]
            y_prime = np.gradient(y, dt)
            y_double_prime = np.gradient(y_prime, dt)
        else:
            y_prime = np.zeros_like(y)
            y_double_prime = np.zeros_like(y)

        # Создаем 3D график
        fig = go.Figure()

        # Траектория в фазовом пространстве
        fig.add_trace(go.Scatter3d(
            x=y, y=y_prime, z=y_double_prime,
            mode='lines',
            line=dict(
                color=t,  # Цвет по времени
                colorscale='Viridis',
                width=4,
                showscale=True,
                colorbar=dict(title="Время")
            ),
            name='Фазовая траектория'
        ))

        # Начальная точка
        fig.add_trace(go.Scatter3d(
            x=[y[0]], y=[y_prime[0]], z=[y_double_prime[0]],
            mode='markers',
            marker=dict(size=10, color='red'),
            name='Начало'
        ))

        # Конечная точка
        fig.add_trace(go.Scatter3d(
            x=[y[-1]], y=[y_prime[-1]], z=[y_double_prime[-1]],
            mode='markers',
            marker=dict(size=10, color='green'),
            name='Конец'
        ))

        # Обновляем layout
        fig.update_layout(
            title='3D Фазовое пространство',
            scene=dict(
                xaxis_title='y (положение)',
                yaxis_title="y' (скорость)",
                zaxis_title="y'' (ускорение)",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            height=700,
            showlegend=True
        )

        fig.show()
        return True