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

    def close(self):
        """Закрытие сессии"""
        if self.session:
            self.session.terminate()