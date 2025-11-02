# logic.py
import numpy as np
from main.wolfram.wolfram import WolframSolver


class ODELogic:
    def __init__(self):
        self.solver = WolframSolver()
        self.current_solution = None

    def solve_equation(self, equation_type, params, initial_conditions, t_range):
        """
        Решение уравнения в зависимости от типа

        Args:
            equation_type: тип уравнения ('harmonic', 'damped', 'forced', 'custom')
            params: параметры уравнения
            initial_conditions: начальные условия
            t_range: диапазон времени
        """
        equation_str = self._build_equation(equation_type, params)

        if equation_str:
            result = self.solver.solve_second_order_ode(
                equation_str, initial_conditions, t_range
            )
            self.current_solution = result
            return result
        else:
            return {'success': False, 'error': 'Неизвестный тип уравнения'}

    def _build_equation(self, equation_type, params):
        """Построение строки уравнения"""
        if equation_type == 'harmonic':
            # y'' + ω²y = 0
            ω = params.get('omega', 1.0)
            return f"y''[t] + {ω}*{ω} * y[t] == 0"

        elif equation_type == 'damped':
            # y'' + 2βy' + ω²y = 0
            β = params.get('beta', 0.1)
            ω = params.get('omega', 1.0)
            return f"y''[t] + 2*{β}*y'[t] + {ω}*{ω} * y[t] == 0"

        elif equation_type == 'forced':
            # y'' + 2βy' + ω²y = Fcos(Ωt)
            β = params.get('beta', 0.1)
            ω = params.get('omega', 1.0)
            F = params.get('force', 1.0)
            Ω = params.get('frequency', 0.5)
            return f"y''[t] + 2*{β}*y'[t] + {ω}*{ω} * y[t] == {F}*Cos[{Ω}*t]"

        elif equation_type == 'custom':
            # Пользовательское уравнение
            return params.get('equation', "y''[t] + y[t] == 0")

        return None

    def get_phase_portrait(self):
        """Получение данных для фазового портрета"""
        if not self.current_solution or not self.current_solution['success']:
            return None

        t = self.current_solution['t_values']
        y = self.current_solution['y_values']

        # Простая численная производная для скорости
        if len(y) > 1:
            # Конвертируем в numpy для gradient
            t_np = np.array(t)
            y_np = np.array(y)
            dt = t_np[1] - t_np[0]
            y_prime = np.gradient(y_np, dt)
            return t_np, y_np, y_prime  # Возвращаем numpy arrays

        return None

    def analyze_solution(self):
        """Анализ решения"""
        if not self.current_solution or not self.current_solution['success']:
            return None

        t = self.current_solution['t_values']
        y = self.current_solution['y_values']

        analysis = {
            'max_value': max(y) if y else 0,
            'min_value': min(y) if y else 0,
            'amplitude': (max(y) - min(y)) / 2 if y else 0,
            'period_estimate': self._estimate_period(t, y),
            'final_time': t[-1] if t else 0
        }

        return analysis

    def _estimate_period(self, t, y):
        """Оценка периода колебаний"""
        if len(y) < 10:
            return 0

        # Конвертируем в numpy arrays для работы с find_peaks
        t_np = np.array(t)
        y_np = np.array(y)

        # Находим нули производной (экстремумы)
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(np.abs(y_np))

        if len(peaks) >= 2:
            periods = np.diff(t_np[peaks])  # Теперь работает, т.к. t_np - numpy array
            return float(np.mean(periods))  # Конвертируем в Python float

        return 0

    def close(self):
        """Закрытие солвера"""
        self.solver.close()