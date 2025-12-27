import json
import os
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np


class ODEStorage:
    """ПРОСТОЙ и РАБОЧИЙ ODEStorage с гарантированной записью"""

    def __init__(self, db_path: str = "data/simulations.json"):
        """
        Инициализация хранилища

        Args:
            db_path: путь к JSON файлу
        """
        print(f"🚀 Инициализация ODEStorage: {db_path}")

        self.db_path = db_path
        self._lock = threading.Lock()

        # Создаем директорию если нужно
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Загружаем существующие данные или создаем новые
        self._data = self._load_data()

        print(f"✅ ODEStorage готов. Записей: {len(self._data.get('simulations', []))}")

    def _load_data(self) -> Dict[str, Any]:
        """Загрузить данные из файла"""
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Не удалось загрузить данные: {e}")

        # Создаем новую структуру
        return {
            'simulations': [],
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_id': 0,
                'total_simulations': 0,
                'updated_at': datetime.now().isoformat()
            }
        }

    def _save_data(self) -> bool:
        """ГАРАНТИРОВАННОЕ сохранение на диск"""
        try:
            # 1. Создаем временный файл
            temp_path = self.db_path + '.tmp'

            # 2. Пишем во временный файл
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
                f.flush()  # Сбрасываем буфер
                os.fsync(f.fileno())  # Принудительно пишем на диск

            # 3. Заменяем старый файл новым (атомарная операция)
            if os.path.exists(self.db_path):
                os.replace(temp_path, self.db_path)
            else:
                os.rename(temp_path, self.db_path)

            # 4. ПРОВЕРКА
            if os.path.exists(self.db_path):
                size = os.path.getsize(self.db_path)
                print(f"💾 Данные сохранены! Размер файла: {size} байт")
                return True

        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            # Удаляем временный файл если он есть
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)

        return False

    def save_simulation(self,
                        equation_type: str,
                        equation_params: Dict[str, Any],
                        initial_conditions: List[float],
                        t_range: tuple,
                        results: Dict[str, Any],
                        name: Optional[str] = None,
                        tags: List[str] = None,
                        description: str = "") -> str:
        """
        Сохранить симуляцию - ГАРАНТИРОВАННАЯ запись

        Returns:
            ID сохраненной симуляции
        """
        with self._lock:
            print(f"\n💾 НАЧИНАЕМ СОХРАНЕНИЕ...")
            print(f"   Тип: {equation_type}")
            print(f"   Имя: {name}")
            print(f"   Точек: {len(results.get('y_values', []))}")

            try:
                # Получаем новый ID
                metadata = self._data.get('metadata', {})
                sim_id = metadata.get('last_id', 0) + 1

                # Генерируем имя если не указано
                if not name:
                    name = f"Sim_{sim_id}_{datetime.now().strftime('%H%M%S')}"

                # Рассчитываем статистику
                stats = self._calculate_stats(results)

                # Создаем запись симуляции
                simulation = {
                    'id': sim_id,
                    'metadata': {
                        'id': sim_id,
                        'name': name,
                        'created_at': datetime.now().isoformat(),
                        'equation_type': equation_type,
                        'parameters': equation_params,
                        'initial_conditions': initial_conditions,
                        't_range': list(t_range),
                        'points_count': stats['points_count'],
                        'amplitude': stats['amplitude'],
                        'max_value': stats['max_value'],
                        'min_value': stats['min_value'],
                        'tags': tags or [],
                        'description': description
                    },
                    'results': results,
                    'saved_at': datetime.now().isoformat()
                }

                # Добавляем симуляцию
                if 'simulations' not in self._data:
                    self._data['simulations'] = []

                self._data['simulations'].append(simulation)

                # Обновляем метаданные
                self._data['metadata'] = {
                    'last_id': sim_id,
                    'total_simulations': len(self._data['simulations']),
                    'created_at': metadata.get('created_at', datetime.now().isoformat()),
                    'updated_at': datetime.now().isoformat()
                }

                print(f"📝 Данные подготовлены. ID: {sim_id}")

                # ГАРАНТИРОВАННОЕ СОХРАНЕНИЕ НА ДИСК
                if self._save_data():
                    print(f"✅ УСПЕХ! Симуляция сохранена. ID: {sim_id}")

                    # Дополнительная проверка
                    check_data = self._load_data()
                    check_count = len(check_data.get('simulations', []))
                    print(f"✓ Проверка: в файле {check_count} записей")

                    return str(sim_id)
                else:
                    print("❌ ОШИБКА: Не удалось сохранить на диск!")
                    # Откатываем изменения в памяти
                    self._data['simulations'].pop()
                    return None

            except Exception as e:
                print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
                import traceback
                traceback.print_exc()
                return None

    def _calculate_stats(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Рассчитать статистику результатов"""
        stats = {
            'points_count': 0,
            'amplitude': 0.0,
            'max_value': 0.0,
            'min_value': 0.0
        }

        y_values = results.get('y_values', [])
        if y_values and len(y_values) > 0:
            try:
                y_array = np.array(y_values, dtype=np.float32)
                stats.update({
                    'points_count': len(y_array),
                    'max_value': float(np.max(y_array)),
                    'min_value': float(np.min(y_array)),
                    'amplitude': float((np.max(y_array) - np.min(y_array)) / 2)
                })
            except Exception as e:
                print(f"⚠️ Ошибка расчета статистики: {e}")

        return stats

    def get_simulation(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Получить симуляцию по ID"""
        with self._lock:
            try:
                sim_id = int(simulation_id)
                for sim in self._data.get('simulations', []):
                    if sim.get('id') == sim_id:
                        return sim
            except (ValueError, TypeError):
                pass

            return None

    def list_simulations(self,
                         limit: int = 50,
                         sort_by: str = 'created_at',
                         descending: bool = True) -> List[Dict[str, Any]]:
        """
        Список симуляций

        Args:
            limit: максимальное количество
            sort_by: поле для сортировки
            descending: по убыванию

        Returns:
            Список метаданных симуляций
        """
        with self._lock:
            sims = []

            for sim in self._data.get('simulations', []):
                metadata = sim.get('metadata', {})
                sims.append({
                    'id': metadata.get('id', 0),
                    'name': metadata.get('name', 'Unknown'),
                    'created_at': metadata.get('created_at', ''),
                    'equation_type': metadata.get('equation_type', ''),
                    'points_count': metadata.get('points_count', 0),
                    'amplitude': metadata.get('amplitude', 0.0),
                    'tags': metadata.get('tags', []),
                    'description': metadata.get('description', '')
                })

            # Сортировка
            if sort_by == 'name':
                sims.sort(key=lambda x: x['name'].lower(), reverse=descending)
            elif sort_by == 'amplitude':
                sims.sort(key=lambda x: x['amplitude'], reverse=descending)
            elif sort_by == 'created_at':
                sims.sort(key=lambda x: x['created_at'], reverse=descending)
            else:
                # По ID по умолчанию
                sims.sort(key=lambda x: x['id'], reverse=descending)

            return sims[:limit]

    def search_simulations(self,
                           equation_type: Optional[str] = None,
                           name_contains: Optional[str] = None,
                           tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Поиск симуляций"""
        with self._lock:
            results = []

            for sim in self._data.get('simulations', []):
                metadata = sim.get('metadata', {})
                match = True

                # Фильтр по типу
                if equation_type and metadata.get('equation_type') != equation_type:
                    match = False

                # Фильтр по имени
                if name_contains and name_contains.lower() not in metadata.get('name', '').lower():
                    match = False

                # Фильтр по тегам
                if tags:
                    sim_tags = metadata.get('tags', [])
                    if not any(tag in sim_tags for tag in tags):
                        match = False

                if match:
                    results.append({
                        'id': metadata.get('id'),
                        'name': metadata.get('name'),
                        'equation_type': metadata.get('equation_type'),
                        'created_at': metadata.get('created_at'),
                        'amplitude': metadata.get('amplitude'),
                        'tags': metadata.get('tags', [])
                    })

            return results

    def delete_simulation(self, simulation_id: str) -> bool:
        """Удалить симуляцию"""
        with self._lock:
            try:
                sim_id = int(simulation_id)
                original_count = len(self._data.get('simulations', []))

                # Фильтруем симуляции
                self._data['simulations'] = [
                    sim for sim in self._data.get('simulations', [])
                    if sim.get('id') != sim_id
                ]

                new_count = len(self._data['simulations'])

                if new_count < original_count:
                    # Обновляем метаданные
                    self._data['metadata']['total_simulations'] = new_count
                    self._data['metadata']['updated_at'] = datetime.now().isoformat()

                    # Сохраняем изменения
                    if self._save_data():
                        print(f"🗑️ Симуляция {sim_id} удалена")
                        return True

                return False

            except Exception as e:
                print(f"Ошибка удаления: {e}")
                return False

    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику хранилища"""
        with self._lock:
            import os

            total = len(self._data.get('simulations', []))
            file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

            # Статистика по типам уравнений
            eq_types = {}
            for sim in self._data.get('simulations', []):
                eq_type = sim.get('metadata', {}).get('equation_type', 'unknown')
                eq_types[eq_type] = eq_types.get(eq_type, 0) + 1

            # Рассчитываем сжатие (простая версия)
            total_data_size = 0
            for sim in self._data.get('simulations', []):
                total_data_size += len(str(sim.get('results', {})))

            compression_ratio = 0
            if total_data_size > 0 and file_size > 0:
                compression_ratio = (1 - file_size / total_data_size) * 100

            return {
                'total_simulations': total,
                'last_id': self._data.get('metadata', {}).get('last_id', 0),
                'db_path': self.db_path,
                'file_exists': os.path.exists(self.db_path),
                'file_size_bytes': file_size,
                'db_file_size': self._format_file_size(file_size),  # Добавляем
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'created_at': self._data.get('metadata', {}).get('created_at', ''),
                'updated_at': self._data.get('metadata', {}).get('updated_at', ''),
                'equation_types': eq_types,
                'compression_ratio': f"{compression_ratio:.1f}%"  # Добавляем
            }

    def _format_file_size(self, size_bytes: int) -> str:
        """Форматирование размера файла"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def get_all_tags_with_count(self) -> List[Dict[str, Any]]:
        """Получить все теги с количеством использования"""
        with self._lock:
            tag_counts = {}

            for sim in self._data.get('simulations', []):
                tags = sim.get('metadata', {}).get('tags', [])
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Преобразуем в список словарей
            tags_list = [{'name': tag, 'count': count}
                         for tag, count in tag_counts.items()]

            # Сортируем по количеству
            tags_list.sort(key=lambda x: x['count'], reverse=True)

            return tags_list

    def export_simulation(self, simulation_id: str, export_path: str) -> bool:
        """Экспорт симуляции в файл"""
        try:
            sim = self.get_simulation(simulation_id)
            if not sim:
                return False

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(sim, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Ошибка экспорта: {e}")
            return False

    def import_simulation(self, import_path: str) -> Optional[str]:
        """Импорт симуляции из файла"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                sim_data = json.load(f)

            if 'metadata' not in sim_data or 'results' not in sim_data:
                return None

            metadata = sim_data['metadata']

            # Импортируем как новую симуляцию
            return self.save_simulation(
                equation_type=metadata.get('equation_type', ''),
                equation_params=metadata.get('parameters', {}),
                initial_conditions=metadata.get('initial_conditions', []),
                t_range=tuple(metadata.get('t_range', [0, 10])),
                results=sim_data['results'],
                name=f"{metadata.get('name', 'Imported')}_imported",
                tags=metadata.get('tags', []),
                description=f"Импортировано: {metadata.get('description', '')}"
            )
        except Exception as e:
            print(f"Ошибка импорта: {e}")
            return None

    def close(self):
        """Закрыть хранилище"""
        # Сохраняем данные перед закрытием
        self._save_data()
        print("🔒 ODEStorage закрыт")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Тестовая функция для проверки
def test_ode_storage():
    """Тест ODEStorage"""
    print("🧪 ТЕСТ ODEStorage")

    # Создаем хранилище
    storage = ODEStorage("data/test_simulations.json")

    # Тестовые данные
    test_results = {
        'success': True,
        'y_values': [0.0, 0.8415, 0.9093, 0.1411, -0.7568],
        't_values': [0.0, 1.0, 2.0, 3.0, 4.0],
        'equation': 'sin(t)'
    }

    # Сохраняем тестовую симуляцию
    sim_id = storage.save_simulation(
        equation_type='harmonic',
        equation_params={'omega': 1.0},
        initial_conditions=[0.0, 1.0],
        t_range=(0, 10),
        results=test_results,
        name="ТЕСТОВАЯ_СИМУЛЯЦИЯ",
        tags=['test', 'harmonic'],
        description="Тестовая симуляция для проверки"
    )

    if sim_id:
        print(f"✅ Тест пройден! ID: {sim_id}")

        # Проверяем что сохранилось
        sim = storage.get_simulation(sim_id)
        if sim:
            print(f"✓ Симуляция получена: {sim['metadata']['name']}")

        # Статистика
        stats = storage.get_statistics()
        print(f"📊 Статистика: {stats['total_simulations']} симуляций")

        # Список
        sims = storage.list_simulations(5)
        print(f"📋 Последние симуляции:")
        for s in sims:
            print(f"  • {s['id']}: {s['name']}")

    storage.close()
    return sim_id


if __name__ == "__main__":
    # Запуск теста
    test_ode_storage()