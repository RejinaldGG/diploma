# wolfram.py
from wolframclient.evaluation import WolframLanguageSession
from wolframclient.language import wl, wlexpr
import json


class WolframSolver:
    def __init__(self):
        self.session = None
        self.connect_to_wolfram()

    def connect_to_wolfram(self):
        """Подключение к Wolfram Engine"""
        try:
            self.session = WolframLanguageSession()
            return True
        except Exception as e:
            print(f"Ошибка подключения к Wolfram: {e}")
            return False

    def solve_second_order_ode(self, equation_str, initial_conditions, t_range=(0, 10)):
        """
        Решение ОДУ второго порядка

        Args:
            equation_str: строка с уравнением
            initial_conditions: начальные условия [y0, y'0]
            t_range: диапазон времени (t_min, t_max)
        """
        try:
            t_min, t_max = t_range
            y0, yp0 = initial_conditions

            # Формируем команду для решения ОДУ
            wolfram_command = f"""
            solution = NDSolve[{{
                {equation_str},
                y[0] == {y0},
                y'[0] == {yp0}
            }}, y, {{t, {t_min}, {t_max}}}, Method -> "StiffnessSwitching"]
            """

            # Выполняем вычисление
            result = self.session.evaluate(wlexpr(wolfram_command))

            # Получаем данные для графика
            data_command = """
            data = Table[{{t, y[t] /. First[solution]}}, {t, """ + str(t_min) + """, """ + str(t_max) + """, 0.1}];
            ExportString[data, "JSON"]
            """

            json_data = self.session.evaluate(wlexpr(data_command))
            data_points = json.loads(json_data)

            # Извлекаем t и y
            t_values = [point[0][0] for point in data_points]
            y_values = [point[0][1] for point in data_points]

            return {
                'success': True,
                't_values': t_values,
                'y_values': y_values,
                'equation': equation_str
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def solve_system(self, equations, initial_conditions, t_range=(0, 10)):
        """
        Решение системы ОДУ
        """
        try:
            t_min, t_max = t_range

            # Формируем систему уравнений
            eq_system = ", ".join(equations)
            ic_system = ", ".join(initial_conditions)

            wolfram_command = f"""
            solution = NDSolve[{{
                {eq_system},
                {ic_system}
            }}, {{{', '.join(['y', 'x'][:len(equations)])}}}, {{t, {t_min}, {t_max}}}]"""

            result = self.session.evaluate(wlexpr(wolfram_command))

            return {'success': True, 'result': str(result)}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def solve_pendulum_system(self, pendulum_type, params, initial_conditions, t_range):
        """
        Решение систем уравнений для различных маятников

        Args:
            pendulum_type: 'simple', 'damped', 'double', 'spherical'
            params: параметры системы
            initial_conditions: начальные условия
            t_range: диапазон времени
        """
        try:
            t_min, t_max = t_range

            if pendulum_type == 'spherical':
                # Сферический маятник: θ'' - φ'²sinθcosθ + (g/L)sinθ = 0
                # φ'' + 2θ'φ'cotθ = 0
                L = params.get('L', 1.0)
                g = params.get('g', 9.81)

                theta0, omega0, phi0, phi_dot0 = initial_conditions

                equations = [
                    f"theta''[t] - phi'[t]^2*Sin[theta[t]]*Cos[theta[t]] + ({g}/{L})*Sin[theta[t]] == 0",
                    f"phi''[t] + 2*theta'[t]*phi'[t]*Cot[theta[t]] == 0"
                ]

                wolfram_command = f"""
                   solution = NDSolve[{{
                       {equations[0]},
                       {equations[1]},
                       theta[0] == {theta0},
                       theta'[0] == {omega0},
                       phi[0] == {phi0},
                       phi'[0] == {phi_dot0}
                   }}, {{theta, phi}}, {{t, {t_min}, {t_max}}}, MaxSteps -> 20000]
                   """

            elif pendulum_type == 'cart':
                # Маятник на тележке
                M = params.get('M', 1.0)  # масса тележки
                m = params.get('m', 0.2)  # масса маятника
                L = params.get('L', 0.5)  # длина
                g = params.get('g', 9.81)

                x0, v0, theta0, omega0 = initial_conditions

                equations = [
                    f"({M}+{m})*x''[t] + {m}*{L}*theta''[t]*Cos[theta[t]] - {m}*{L}*theta'[t]^2*Sin[theta[t]] == 0",
                    f"{m}*{L}*x''[t]*Cos[theta[t]] + {m}*{L}^2*theta''[t] + {m}*{g}*{L}*Sin[theta[t]] == 0"
                ]

                wolfram_command = f"""
                   solution = NDSolve[{{
                       {equations[0]},
                       {equations[1]},
                       x[0] == {x0},
                       x'[0] == {v0},
                       theta[0] == {theta0},
                       theta'[0] == {omega0}
                   }}, {{x, theta}}, {{t, {t_min}, {t_max}}}, MaxSteps -> 15000]
                   """

            # Выполняем вычисление
            result = self.session.evaluate(wlexpr(wolfram_command))

            # Извлекаем данные в JSON
            data_command = f"""
               data = Table[{{t, x[t] /. First[solution], theta[t] /. First[solution]}}, 
                        {{t, {t_min}, {t_max}, ({t_max}-{t_min})/500}}];
               ExportString[data, "JSON"]
               """

            json_data = self.session.evaluate(wlexpr(data_command))
            data_points = json.loads(json_data)

            # Парсим результаты
            t_values = [point[0] for point in data_points]
            x_values = [point[1] for point in data_points]
            theta_values = [point[2] for point in data_points]

            return {
                'success': True,
                't_values': t_values,
                'x': x_values,
                'theta': theta_values,
                'type': pendulum_type,
                'params': params
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def close(self):
        """Закрытие сессии"""
        if self.session:
            self.session.terminate()