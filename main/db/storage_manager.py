# main/storage/storage_manager_simple.py
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .ode_storage_simple import ODEStorage


class StorageManager:
    """Простейший менеджер для работы с ODEStorage"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            print("=" * 60)
            print("🔥 ИНИЦИАЛИЗАЦИЯ STORAGE MANAGER")
            print("=" * 60)

            # Путь к файлу данных
            project_root = Path(__file__).parent.parent
            db_path = str(project_root / "data" / "simulations.json")

            print(f"📁 Файл данных: {db_path}")

            # Создаем хранилище
            self.storage = ODEStorage(db_path)

            # Запускаем тест
            self._test_storage()

            self._initialized = True
            print("✅ StorageManager готов!")

    def _test_storage(self):
        """Тестируем хранилище при запуске"""
        print("\n🧪 ТЕСТИРУЕМ ХРАНИЛИЩЕ...")

        # Создаем тестовые данные
        import numpy as np
        test_data = {
            'success': True,
            'y_values': list(np.sin(np.linspace(0, 2 * np.pi, 50))),
            't_values': list(np.linspace(0, 2 * np.pi, 50)),
            'equation': 'sin(x)'
        }

        # Сохраняем тест
        sim_id = self.storage.save_simulation(
            equation_type='harmonic',
            equation_params={'omega': 1.0},
            initial_conditions=[0.0, 1.0],
            t_range=(0, 2 * np.pi),
            results=test_data,
            name="ТЕСТ_ПРИ_ЗАПУСКЕ",
            tags=['test', 'startup'],
            description="Тестовое сохранение при запуске программы"
        )

        if sim_id:
            print(f"✅ Хранилище работает! Тестовый ID: {sim_id}")
        else:
            print("❌ Хранилище не работает!")

    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Получить все теги с количеством"""
        return self.storage.get_all_tags_with_count()  # Используем новый метод

    def get_statistics(self) -> Dict[str, Any]:
        """Статистика хранилища"""
        return self.storage.get_statistics()
    def save_current_simulation(self,
                                logic,
                                visualizer,
                                name: str,
                                tags: List[str] = None,
                                description: str = "") -> Optional[str]:
        """
        Сохранить текущую симуляцию

        Args:
            logic: объект ODELogic
            visualizer: объект ODEVisualizer
            name: имя симуляции
            tags: теги
            description: описание

        Returns:
            ID сохраненной симуляции
        """
        print(f"\n💾 СОХРАНЕНИЕ СИМУЛЯЦИИ: {name}")

        # Проверяем наличие данных
        if not logic or not logic.current_solution:
            print("❌ Нет данных для сохранения")
            return None

        try:
            # Получаем параметры из визуализатора
            eq_type = visualizer.eq_type.get()

            # Параметры уравнения
            params = {}
            if eq_type == 'harmonic':
                params = {'omega': float(visualizer.params['omega_harmonic'].get())}
            elif eq_type == 'damped':
                params = {
                    'omega': float(visualizer.params['omega_damped'].get()),
                    'beta': float(visualizer.params['beta_damped'].get())
                }
            elif eq_type == 'forced':
                params = {
                    'omega': float(visualizer.params['omega_forced'].get()),
                    'beta': float(visualizer.params['beta_forced'].get()),
                    'force': float(visualizer.params['force_forced'].get()),
                    'frequency': float(visualizer.params['freq_forced'].get())
                }
            elif eq_type == 'custom':
                params = {'equation': visualizer.custom_equation.get()}

            # Начальные условия
            initial_conditions = [
                float(visualizer.y0.get()),
                float(visualizer.yp0.get())
            ]

            # Диапазон времени
            t_range = (
                float(visualizer.t_min.get()),
                float(visualizer.t_max.get())
            )

            print(f"📊 Параметры сохранения:")
            print(f"  • Тип: {eq_type}")
            print(f"  • Начальные условия: {initial_conditions}")
            print(f"  • Диапазон времени: {t_range}")
            print(f"  • Параметры: {params}")

            # Сохраняем
            sim_id = self.storage.save_simulation(
                equation_type=eq_type,
                equation_params=params,
                initial_conditions=initial_conditions,
                t_range=t_range,
                results=logic.current_solution,
                name=name,
                tags=tags or [],
                description=description
            )

            if sim_id:
                print(f"✅ Симуляция сохранена! ID: {sim_id}")

                # Показываем статистику
                stats = self.storage.get_statistics()
                print(f"📊 Всего симуляций: {stats['total_simulations']}")

            return sim_id

        except Exception as e:
            print(f"❌ ОШИБКА сохранения: {e}")
            import traceback
            traceback.print_exc()
            return None

    def load_simulation(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Загрузить симуляцию"""
        return self.storage.get_simulation(simulation_id)

    def load_simulation_for_ui(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """
        Загрузить симуляцию для UI

        Returns:
            Структура для загрузки в UI
        """
        sim_data = self.storage.get_simulation(simulation_id)
        if not sim_data:
            return None

        return {
            'metadata': sim_data['metadata'],
            'results': sim_data['results']
        }

    def get_recent_simulations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить последние симуляции"""
        return self.storage.list_simulations(limit=limit, sort_by='created_at', descending=True)

    def search_simulations(self,
                           equation_type: Optional[str] = None,
                           search_text: Optional[str] = None,
                           tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Поиск симуляций"""
        return self.storage.search_simulations(
            equation_type=equation_type,
            name_contains=search_text,
            tags=tags
        )

    def get_all_tags(self) -> List[str]:
        """Получить все теги"""
        all_tags = set()
        sims = self.storage.list_simulations(limit=1000)

        for sim in sims:
            for tag in sim.get('tags', []):
                all_tags.add(tag)

        return sorted(list(all_tags))

    def get_statistics(self) -> Dict[str, Any]:
        """Статистика хранилища"""
        return self.storage.get_statistics()

    def export_to_file(self, simulation_id: str, filepath: str) -> bool:
        """Экспорт в файл"""
        return self.storage.export_simulation(simulation_id, filepath)

    def import_from_file(self, filepath: str) -> Optional[str]:
        """Импорт из файла"""
        return self.storage.import_simulation(filepath)

    def delete_simulation(self, simulation_id: str) -> bool:
        """Удалить симуляцию"""
        return self.storage.delete_simulation(simulation_id)

    def close(self):
        """Закрыть хранилище"""
        self.storage.close()