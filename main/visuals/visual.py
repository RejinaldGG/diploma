# visual.py
import sys
import threading
import tkinter as tk
import traceback
from datetime import datetime
from tkinter import ttk, messagebox

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from main.db.storage_manager import StorageManager
from main.visuals.visual_integrated import IntegratedVisualizations


class ODEVisualizer:
    def __init__(self, root, logic):
        self.root = root
        self.logic = logic

        try:
            self.storage_manager = StorageManager()
            print(f"StorageManager initialized. DB path: {self.storage_manager.storage.db_path}")
        except Exception as e:
            print(f"Error initializing StorageManager: {e}")
            self.storage_manager = None

        self.setup_ui()
        self.viz_manager = IntegratedVisualizations(self.logic, self.plot_frame)
        plt.rcParams.update({'font.size': 10})

    def setup_storage_ui(self, control_frame):
        """Добавление UI для работы с хранилищем"""
        storage_frame = ttk.LabelFrame(control_frame, text="Хранилище результатов", padding=10)
        storage_frame.grid(row=110, column=0, sticky=tk.W + tk.E, pady=10, padx=5)

        # Кнопки
        ttk.Button(storage_frame, text="💾 Сохранить решение",
                   command=self.save_current_solution).grid(row=0, column=0, sticky=tk.W + tk.E, pady=2)

        ttk.Button(storage_frame, text="📂 История симуляций",
                   command=self.show_simulation_history).grid(row=1, column=0, sticky=tk.W + tk.E, pady=2)

        ttk.Button(storage_frame, text="🔍 Поиск",
                   command=self.show_search_dialog).grid(row=2, column=0, sticky=tk.W + tk.E, pady=2)

        ttk.Button(storage_frame, text="📊 Статистика",
                   command=self.show_storage_stats).grid(row=3, column=0, sticky=tk.W + tk.E, pady=2)

        ttk.Button(storage_frame, text="🔄 Импорт/Экспорт",
                   command=self.show_import_export_dialog).grid(row=4, column=0, sticky=tk.W + tk.E, pady=2)

        storage_frame.columnconfigure(0, weight=1)

    def save_current_solution(self):
        """Сохранение текущего решения"""
        print("Save current solution called")

        if not self.storage_manager:
            messagebox.showerror("Ошибка", "Хранилище не инициализировано")
            return

        if not self.logic or not self.logic.current_solution:
            messagebox.showwarning("Предупреждение", "Нет данных для сохранения")
            return

        # Диалог для ввода имени и тегов
        dialog = tk.Toplevel(self.root)
        dialog.title("Сохранение симуляции")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Название
        ttk.Label(dialog, text="Название:").pack(pady=(10, 5))
        name_var = tk.StringVar(value=f"Simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=40)
        name_entry.pack(pady=5)
        name_entry.focus_set()

        # Теги
        ttk.Label(dialog, text="Теги (через запятую):").pack(pady=(10, 5))
        tags_var = tk.StringVar()
        tags_entry = ttk.Entry(dialog, textvariable=tags_var, width=40)
        tags_entry.pack(pady=5)

        # Описание
        ttk.Label(dialog, text="Описание:").pack(pady=(10, 5))
        desc_text = tk.Text(dialog, height=4, width=40)
        desc_text.pack(pady=5)

        def save():
            name = name_var.get().strip()
            tags = [tag.strip() for tag in tags_var.get().split(',') if tag.strip()]
            description = desc_text.get("1.0", tk.END).strip()

            if not name:
                messagebox.showerror("Ошибка", "Введите название симуляции")
                return

            print(f"Attempting to save: name={name}, tags={tags}")

            # Сохраняем
            sim_id = self.storage_manager.save_current_simulation(
                self.logic, self, name, tags, description
            )

            if sim_id:
                messagebox.showinfo("Успех", f"Симуляция сохранена (ID: {sim_id})")
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить симуляцию")

        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Сохранить", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Бинд Enter для сохранения
        dialog.bind('<Return>', lambda e: save())

    def show_simulation_history(self):
        """Показать историю симуляций"""
        simulations = self.storage_manager.get_recent_simulations(limit=50)

        if not simulations:
            messagebox.showinfo("История", "Нет сохраненных симуляций")
            return

        # Создаем диалог с таблицей
        dialog = tk.Toplevel(self.root)
        dialog.title("История симуляций")
        dialog.geometry("1200x900")

        # Таблица
        columns = ('ID', 'Название', 'Тип', 'Дата', 'Точек', 'Амплитуда', 'Теги')
        tree = ttk.Treeview(dialog, columns=columns, show='headings', height=20)

        # Заголовки
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        # Данные
        for sim in simulations:
            tags_str = ', '.join(sim.get('tags', []))[:30]
            tree.insert('', tk.END, values=(
                sim['id'],
                sim['name'][:30],
                sim.get('equation_type', ''),
                sim['created_at'][:19],
                sim.get('points_count', 0),
                f"{sim.get('amplitude', 0):.4f}",
                tags_str
            ))

        scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        # Кнопки
        button_frame = ttk.Frame(dialog)


        ttk.Button(button_frame, text="Загрузить",
                   command=lambda: self.load_selected_simulation(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Удалить",
                   command=lambda: self.delete_selected_simulation(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Экспорт",
                   command=lambda: self.export_selected_simulation(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Закрыть",
                   command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

    def load_selected_simulation(self, tree):
        """Загрузка выбранной симуляции"""
        selected = tree.selection()
        if not selected:
            return

        item = tree.item(selected[0])
        sim_id = item['values'][0]

        sim_data = self.storage_manager.load_simulation_for_ui(str(sim_id))
        if sim_data:
            self._load_simulation_into_ui(sim_data)
            messagebox.showinfo("Успех", f"Симуляция '{sim_data['metadata']['name']}' загружена")
        else:
            messagebox.showerror("Ошибка", "Не удалось загрузить симуляцию")

    def _load_simulation_into_ui(self, sim_data):
        """Загрузка симуляции в UI"""
        metadata = sim_data['metadata']
        results = sim_data['results']

        # Устанавливаем тип уравнения
        self.eq_type.set(metadata['equation_type'])
        self.on_equation_change()

        # Устанавливаем параметры
        params = metadata['parameters']
        eq_type = metadata['equation_type']

        if eq_type == 'harmonic':
            if 'omega' in params:
                self.params['omega_harmonic'].set(params['omega'])
        elif eq_type == 'damped':
            if 'omega' in params:
                self.params['omega_damped'].set(params['omega'])
            if 'beta' in params:
                self.params['beta_damped'].set(params['beta'])
        elif eq_type == 'forced':
            if 'omega' in params:
                self.params['omega_forced'].set(params['omega'])
            if 'beta' in params:
                self.params['beta_forced'].set(params['beta'])
            if 'force' in params:
                self.params['force_forced'].set(params['force'])
            if 'frequency' in params:
                self.params['freq_forced'].set(params['frequency'])
        elif eq_type == 'custom':
            if 'equation' in params:
                self.custom_equation.set(params['equation'])

        # Начальные условия
        if metadata['initial_conditions'] and len(metadata['initial_conditions']) >= 2:
            self.y0.set(metadata['initial_conditions'][0])
            self.yp0.set(metadata['initial_conditions'][1])

        # Диапазон времени
        if metadata['t_range'] and len(metadata['t_range']) >= 2:
            self.t_min.set(metadata['t_range'][0])
            self.t_max.set(metadata['t_range'][1])

        # Устанавливаем решение
        self.logic.current_solution = results

        # Обновляем графики
        self.plot_solution(results)
        self.show_analysis()

    def show_storage_stats(self):
        """Показать статистику хранилища"""
        try:
            stats = self.storage_manager.get_statistics()

            if not stats:
                messagebox.showinfo("Статистика", "Нет данных о хранилище")
                return

            # Форматируем статистику
            stats_text = f"""
    📊 СТАТИСТИКА ХРАНИЛИЩА

    📁 Общая информация:
    • Всего симуляций: {stats.get('total_simulations', 0)}
    • Последний ID: {stats.get('last_id', 0)}
    • Создано: {stats.get('created_at', 'N/A')}
    • Обновлено: {stats.get('updated_at', 'N/A')}
    • Файл БД: {stats.get('db_path', 'N/A')}
    • Файл существует: {'✅ ДА' if stats.get('file_exists') else '❌ НЕТ'}

    📈 Распределение по типам уравнений:
    """

            # Типы уравнений
            eq_types = stats.get('equation_types', {})
            if eq_types:
                for eq_type, count in eq_types.items():
                    stats_text += f"  • {eq_type}: {count} симуляций\n"
            else:
                stats_text += "  • Нет данных\n"

            # Дополнительная информация
            stats_text += f"\n💾 Размер в байтах: {stats.get('file_size_bytes', 0)}"
            stats_text += f"\n📏 Размер в MB: {stats.get('file_size_mb', 0):.2f}"

            messagebox.showinfo("Статистика хранилища", stats_text)

            # Также выводим в консоль для отладки
            print("\n📊 СТАТИСТИКА ХРАНИЛИЩА:")
            print(f"   Всего симуляций: {stats.get('total_simulations', 0)}")
            print(f"   Размер файла: {stats.get('db_file_size', '0 B')}")
            print(f"   Сжатие: {stats.get('compression_ratio', '0%')}")

        except Exception as e:
            print(f"❌ Ошибка при получении статистики: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Ошибка", f"Не удалось получить статистику: {e}")

    def show_search_dialog(self):
        """Диалог поиска симуляций"""
        if not self.storage_manager:
            messagebox.showwarning("Предупреждение", "Хранилище недоступно")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Поиск симуляций")
        dialog.geometry("500x400")

        # Поля для поиска
        ttk.Label(dialog, text="Тип уравнения:").pack(pady=(10, 5))
        eq_type_var = tk.StringVar(value="")
        eq_types = ["", "harmonic", "damped", "forced", "custom", "pendulum"]
        eq_combo = ttk.Combobox(dialog, textvariable=eq_type_var, values=eq_types, state="readonly")
        eq_combo.pack(pady=5)

        ttk.Label(dialog, text="Название содержит:").pack(pady=(10, 5))
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=40).pack(pady=5)

        ttk.Label(dialog, text="Теги (через запятую):").pack(pady=(10, 5))
        tags_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=tags_var, width=40).pack(pady=5)

        ttk.Label(dialog, text="Минимальная амплитуда:").pack(pady=(10, 5))
        amp_var = tk.DoubleVar(value=0.0)
        ttk.Entry(dialog, textvariable=amp_var, width=20).pack(pady=5)

        # Результаты поиска
        result_frame = ttk.LabelFrame(dialog, text="Результаты", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        result_listbox = tk.Listbox(result_frame, height=8)
        result_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=result_listbox.yview)
        result_listbox.configure(yscrollcommand=result_scrollbar.set)

        result_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def perform_search():
            """Выполнить поиск"""
            result_listbox.delete(0, tk.END)

            eq_type = eq_type_var.get()
            if eq_type == "":
                eq_type = None

            name_text = name_var.get().strip()
            if not name_text:
                name_text = None

            tags_text = tags_var.get().strip()
            tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()] if tags_text else None

            min_amp = amp_var.get()
            if min_amp <= 0:
                min_amp = None

            # Выполняем поиск
            results = self.storage_manager.search_simulations(
                equation_type=eq_type,
                search_text=name_text,
                tags=tags
            )

            # Фильтруем по амплитуде
            if min_amp is not None:
                results = [r for r in results if r.get('amplitude', 0) >= min_amp]

            # Отображаем результаты
            if not results:
                result_listbox.insert(tk.END, "Ничего не найдено")
                return

            for sim in results:
                display_text = f"{sim['id']}: {sim['name']} ({sim['equation_type']}) - A={sim.get('amplitude', 0):.3f}"
                result_listbox.insert(tk.END, display_text)
                result_listbox.selection_data[result_listbox.size() - 1] = sim['id']

        def load_selected():
            """Загрузить выбранную симуляцию"""
            selection = result_listbox.curselection()
            if not selection:
                return

            # Получаем ID из скрытых данных
            index = selection[0]
            try:
                sim_id = result_listbox.selection_data.get(index)
                if sim_id:
                    sim_data = self.storage_manager.load_simulation_for_ui(str(sim_id))
                    if sim_data:
                        self._load_simulation_into_ui(sim_data)
                        dialog.destroy()
                        messagebox.showinfo("Успех", "Симуляция загружена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")

        # Создаем скрытое хранилище для ID
        result_listbox.selection_data = {}

        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="🔍 Поиск", command=perform_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📥 Загрузить", command=load_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Закрыть", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def show_import_export_dialog(self):
        """Диалог импорта/экспорта"""
        if not self.storage_manager:
            messagebox.showwarning("Предупреждение", "Хранилище недоступно")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Импорт/Экспорт")
        dialog.geometry("400x300")

        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Вкладка экспорта
        export_frame = ttk.Frame(notebook)
        notebook.add(export_frame, text="Экспорт")

        ttk.Label(export_frame, text="ID симуляции для экспорта:").pack(pady=(20, 5))
        export_id_var = tk.StringVar()
        ttk.Entry(export_frame, textvariable=export_id_var, width=30).pack(pady=5)

        ttk.Label(export_frame, text="Путь для сохранения:").pack(pady=(10, 5))
        export_path_var = tk.StringVar(value="simulation_export.json")
        ttk.Entry(export_frame, textvariable=export_path_var, width=30).pack(pady=5)

        def export_simulation():
            """Экспортировать симуляцию"""
            sim_id = export_id_var.get().strip()
            export_path = export_path_var.get().strip()

            if not sim_id or not export_path:
                messagebox.showerror("Ошибка", "Заполните все поля")
                return

            success = self.storage_manager.export_to_file(sim_id, export_path)
            if success:
                messagebox.showinfo("Успех", f"Симуляция экспортирована в {export_path}")
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать симуляцию")

        ttk.Button(export_frame, text="📤 Экспорт", command=export_simulation).pack(pady=20)

        # Вкладка импорта
        import_frame = ttk.Frame(notebook)
        notebook.add(import_frame, text="Импорт")

        ttk.Label(import_frame, text="Путь к файлу для импорта:").pack(pady=(20, 5))
        import_path_var = tk.StringVar()
        ttk.Entry(import_frame, textvariable=import_path_var, width=30).pack(pady=5)

        def browse_file():
            """Выбрать файл"""
            from tkinter import filedialog
            filename = filedialog.askopenfilename(
                title="Выберите файл симуляции",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                import_path_var.set(filename)

        ttk.Button(import_frame, text="📁 Обзор", command=browse_file).pack(pady=5)

        def import_simulation():
            """Импортировать симуляцию"""
            import_path = import_path_var.get().strip()

            if not import_path:
                messagebox.showerror("Ошибка", "Укажите путь к файлу")
                return

            sim_id = self.storage_manager.import_from_file(import_path)
            if sim_id:
                messagebox.showinfo("Успех", f"Симуляция импортирована (ID: {sim_id})")
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось импортировать симуляцию")

        ttk.Button(import_frame, text="📥 Импорт", command=import_simulation).pack(pady=20)

        # Кнопка закрытия
        ttk.Button(dialog, text="Закрыть", command=dialog.destroy).pack(pady=10)

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.root.title("Визуализация ОДУ второго порядка")
        self.root.geometry("1400x900")
        self.root.state('zoomed')
        # Основной фрейм
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Левая панель - управление
        control_frame = ttk.LabelFrame(main_frame, text="Параметры уравнения", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.plot_frame = ttk.LabelFrame(main_frame, text="Визуализации", padding=10)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.setup_control_panel(control_frame)
        self.setup_visualization_controls(control_frame)
        self.setup_storage_ui(control_frame)

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

    def delete_selected_simulation(self, tree):
        """Удаление выбранной симуляции"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите симуляцию для удаления")
            return

        item = tree.item(selected[0])
        sim_id = item['values'][0]
        sim_name = item['values'][1]

        # Подтверждение
        if not messagebox.askyesno("Подтверждение",
                                   f"Удалить симуляцию '{sim_name}' (ID: {sim_id})?\n"
                                   "Это действие нельзя отменить."):
            return

        # Удаление
        if self.storage_manager and self.storage_manager.delete_simulation(str(sim_id)):
            tree.delete(selected[0])
            messagebox.showinfo("Успех", "Симуляция удалена")
        else:
            messagebox.showerror("Ошибка", "Не удалось удалить симуляцию")

    def export_selected_simulation(self, tree):
        """Экспорт выбранной симуляции в файл"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите симуляцию для экспорта")
            return

        item = tree.item(selected[0])
        sim_id = item['values'][0]
        sim_name = item['values'][1]

        # Диалог выбора файла
        from tkinter import filedialog
        default_filename = f"simulation_{sim_id}_{sim_name.replace(' ', '_')}.json"

        filepath = filedialog.asksaveasfilename(
            title="Экспорт симуляции",
            defaultextension=".json",
            initialfile=default_filename,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not filepath:
            return  # Пользователь отменил

        try:
            # Экспорт
            success = self.storage_manager.export_to_file(str(sim_id), filepath)

            if success:
                messagebox.showinfo("Успех", f"Симуляция экспортирована в:\n{filepath}")
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать симуляцию")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {str(e)}")

    def show_search_dialog(self):
        """Диалог поиска симуляций (упрощенная версия)"""
        if not self.storage_manager:
            messagebox.showwarning("Предупреждение", "Хранилище недоступно")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Поиск симуляций")
        dialog.geometry("500x400")

        # Простой поиск по имени
        ttk.Label(dialog, text="Поиск по имени:").pack(pady=(20, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(dialog, textvariable=search_var, width=40)
        search_entry.pack(pady=5)

        # Результаты
        result_frame = ttk.LabelFrame(dialog, text="Результаты", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Список результатов
        columns = ('ID', 'Название', 'Тип', 'Дата')
        result_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=8)

        for col in columns:
            result_tree.heading(col, text=col)
            result_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=result_tree.yview)
        result_tree.configure(yscroll=scrollbar.set)

        result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def perform_search():
            """Выполнить поиск"""
            # Очищаем предыдущие результаты
            for item in result_tree.get_children():
                result_tree.delete(item)

            search_text = search_var.get().strip()
            if not search_text:
                messagebox.showwarning("Предупреждение", "Введите текст для поиска")
                return

            # Получаем все симуляции и фильтруем
            all_sims = self.storage_manager.get_recent_simulations(limit=1000)
            results = []

            for sim in all_sims:
                if search_text.lower() in sim.get('name', '').lower():
                    results.append(sim)
                elif search_text.lower() in sim.get('equation_type', '').lower():
                    results.append(sim)
                elif search_text.lower() in ', '.join(sim.get('tags', [])).lower():
                    results.append(sim)

            if not results:
                result_tree.insert('', tk.END, values=("", "Ничего не найдено", "", ""))
                return

            # Отображаем результаты
            for sim in results[:50]:  # Ограничиваем 50 результатами
                result_tree.insert('', tk.END, values=(
                    sim['id'],
                    sim['name'][:30],
                    sim.get('equation_type', ''),
                    sim['created_at'][:10]
                ))

        def load_selected():
            """Загрузить выбранную симуляцию"""
            selection = result_tree.selection()
            if not selection:
                return

            item = result_tree.item(selection[0])
            sim_id = item['values'][0]

            if not sim_id:  # Пустая строка "Ничего не найдено"
                return

            sim_data = self.storage_manager.load_simulation_for_ui(str(sim_id))
            if sim_data:
                self._load_simulation_into_ui(sim_data)
                dialog.destroy()
                messagebox.showinfo("Успех", "Симуляция загружена")
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить симуляцию")

        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="🔍 Найти", command=perform_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📥 Загрузить", command=load_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Закрыть", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Поиск по нажатию Enter
        search_entry.bind('<Return>', lambda e: perform_search())

    def show_import_export_dialog(self):
        """Диалог импорта/экспорта (упрощенная версия)"""
        if not self.storage_manager:
            messagebox.showwarning("Предупреждение", "Хранилище недоступно")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Импорт/Экспорт симуляций")
        dialog.geometry("500x300")

        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Вкладка экспорта
        export_frame = ttk.Frame(notebook)
        notebook.add(export_frame, text="📤 Экспорт")

        ttk.Label(export_frame, text="ID симуляции для экспорта:").pack(pady=(20, 5))

        # Выбор из списка сохраненных
        recent_sims = self.storage_manager.get_recent_simulations(limit=20)
        sim_ids = [str(sim['id']) for sim in recent_sims]
        sim_names = [sim['name'] for sim in recent_sims]

        export_combo_var = tk.StringVar()
        if sim_ids:
            export_combo = ttk.Combobox(export_frame, textvariable=export_combo_var,
                                        values=[f"{id}: {name}" for id, name in zip(sim_ids, sim_names)],
                                        state="readonly", width=40)
            export_combo.pack(pady=5)
            if sim_ids:
                export_combo.current(0)

        def export_selected():
            """Экспортировать выбранную симуляцию"""
            if not sim_ids:
                messagebox.showwarning("Предупреждение", "Нет сохраненных симуляций")
                return

            selection = export_combo_var.get()
            if not selection:
                messagebox.showerror("Ошибка", "Выберите симуляцию")
                return

            # Извлекаем ID
            sim_id = selection.split(':')[0].strip()

            # Диалог сохранения файла
            from tkinter import filedialog
            default_name = f"simulation_export_{sim_id}.json"

            filepath = filedialog.asksaveasfilename(
                title="Сохранить симуляцию",
                defaultextension=".json",
                initialfile=default_name,
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if not filepath:
                return

            # Экспорт
            success = self.storage_manager.export_to_file(sim_id, filepath)
            if success:
                messagebox.showinfo("Успех", f"Симуляция экспортирована в:\n{filepath}")
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать симуляцию")

        ttk.Button(export_frame, text="📤 Экспорт в файл", command=export_selected).pack(pady=20)

        # Вкладка импорта
        import_frame = ttk.Frame(notebook)
        notebook.add(import_frame, text="📥 Импорт")

        ttk.Label(import_frame, text="Выберите файл симуляции для импорта:").pack(pady=(20, 5))

        import_path_var = tk.StringVar()
        ttk.Entry(import_frame, textvariable=import_path_var, width=40, state='readonly').pack(pady=5)

        def browse_import_file():
            """Выбрать файл для импорта"""
            from tkinter import filedialog
            filename = filedialog.askopenfilename(
                title="Выберите файл симуляции",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                import_path_var.set(filename)

        ttk.Button(import_frame, text="📁 Выбрать файл", command=browse_import_file).pack(pady=5)

        def import_simulation():
            """Импортировать симуляцию"""
            import_path = import_path_var.get().strip()
            if not import_path:
                messagebox.showerror("Ошибка", "Выберите файл для импорта")
                return

            try:
                sim_id = self.storage_manager.import_from_file(import_path)
                if sim_id:
                    messagebox.showinfo("Успех", f"Симуляция импортирована (ID: {sim_id})")
                    dialog.destroy()

                    # Предложить загрузить импортированную симуляцию
                    if messagebox.askyesno("Импорт", "Хотите загрузить импортированную симуляцию?"):
                        sim_data = self.storage_manager.load_simulation_for_ui(sim_id)
                        if sim_data:
                            self._load_simulation_into_ui(sim_data)
                else:
                    messagebox.showerror("Ошибка", "Не удалось импортировать симуляцию")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка импорта: {str(e)}")

        ttk.Button(import_frame, text="📥 Импортировать", command=import_simulation).pack(pady=20)

        # Кнопка закрытия
        ttk.Button(dialog, text="Закрыть", command=dialog.destroy).pack(pady=10)

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