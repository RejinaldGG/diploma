# main/visuals/physics_engine.py
import pygame
import numpy as np
import math
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame.locals


class PhysicsRenderer:
    """Рендерер для физических моделей с использованием PyGame и OpenGL"""

    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        self.clock = None
        self.screen = None
        self.font = None
        self.camera_distance = 10.0
        self.camera_angle = 45.0
        self.init_pygame()

    def init_pygame(self):
        """Инициализация PyGame и OpenGL"""
        pygame.init()
        pygame.display.set_mode((self.width, self.height),
                                pygame.locals.DOUBLEBUF | pygame.locals.OPENGL)

        # Настройка OpenGL
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Настройка света
        glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 5.0, 5.0, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1.0))

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 16)

    def set_camera(self):
        """Настройка камеры"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (self.width / self.height), 0.1, 50.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            self.camera_distance * math.sin(math.radians(self.camera_angle)),
            self.camera_distance * math.cos(math.radians(self.camera_angle)),
            self.camera_distance,
            0, 0, 0,
            0, 0, 1
        )

    def draw_grid(self, size=10, step=1):
        """Отрисовка сетки"""
        glBegin(GL_LINES)
        glColor3f(0.3, 0.3, 0.3)
        for i in range(-size, size + 1, step):
            glVertex3f(i, -size, 0)
            glVertex3f(i, size, 0)
            glVertex3f(-size, i, 0)
            glVertex3f(size, i, 0)
        glEnd()

    def draw_sphere(self, x, y, z, radius, color):
        """Отрисовка сферы"""
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(*color)

        quadric = gluNewQuadric()
        gluSphere(quadric, radius, 32, 32)
        gluDeleteQuadric(quadric)

        glPopMatrix()

    def draw_cylinder(self, x1, y1, z1, x2, y2, z2, radius, color):
        """Отрисовка цилиндра между двумя точками"""
        glPushMatrix()
        glColor3f(*color)

        # Вектор направления
        dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
        length = math.sqrt(dx * dx + dy * dy + dz * dz)

        if length > 0:
            # Перемещаем в первую точку
            glTranslatef(x1, y1, z1)

            # Вращаем чтобы совместить с осью Z
            if abs(dz) < length:
                rx, ry, rz = dy, -dx, 0
                angle = math.degrees(math.acos(dz / length))
                glRotatef(angle, rx, ry, rz)

            # Рисуем цилиндр
            quadric = gluNewQuadric()
            gluCylinder(quadric, radius, radius, length, 32, 32)
            gluDeleteQuadric(quadric)

        glPopMatrix()

    def draw_text(self, text, x, y, color=(255, 255, 255)):
        """Отрисовка текста на экране"""
        text_surface = self.font.render(text, True, color)
        text_data = pygame.image.tostring(text_surface, "RGBA", True)

        glWindowPos2d(x, self.height - y - 20)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                     GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    def render_pendulum(self, theta, L=1.0, time=0.0, trace_points=None):
        """Рендеринг маятника в 3D"""
        # Очистка
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Настройка камеры
        self.set_camera()

        # Отрисовка сетки
        self.draw_grid()

        # Координаты маятника
        x = L * math.sin(theta)
        y = 0
        z = -L * math.cos(theta)

        # Точка подвеса (красная)
        self.draw_sphere(0, 0, 0, 0.1, (1.0, 0.0, 0.0))

        # Стержень (синий)
        self.draw_cylinder(0, 0, 0, x, y, z, 0.03, (0.0, 0.0, 1.0))

        # Груз (зеленый)
        self.draw_sphere(x, y, z, 0.2, (0.0, 1.0, 0.0))

        # Траектория (желтая)
        if trace_points and len(trace_points) > 1:
            glBegin(GL_LINE_STRIP)
            glColor3f(1.0, 1.0, 0.0)
            for point in trace_points:
                glVertex3f(point[0], point[1], point[2])
            glEnd()

        # Информация
        self.draw_text(f"Маятник: θ = {theta:.3f} рад", 10, 30)
        self.draw_text(f"Длина: {L} м", 10, 50)
        self.draw_text(f"Время: {time:.2f} с", 10, 70)
        self.draw_text(f"Управление: Стрелки - камера, ESC - выход", 10, 90)

        # Обновление экрана
        pygame.display.flip()

    def render_double_pendulum(self, theta1, theta2, L1=1.0, L2=0.8, time=0.0, trace_points=None):
        """Рендеринг двойного маятника"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.set_camera()
        self.draw_grid()

        # Координаты
        x1 = L1 * math.sin(theta1)
        y1 = 0
        z1 = -L1 * math.cos(theta1)

        x2 = x1 + L2 * math.sin(theta2)
        y2 = 0
        z2 = z1 - L2 * math.cos(theta2)

        # Опора
        self.draw_sphere(0, 0, 0, 0.1, (1.0, 0.0, 0.0))

        # Первое звено
        self.draw_cylinder(0, 0, 0, x1, y1, z1, 0.03, (0.0, 0.0, 1.0))
        self.draw_sphere(x1, y1, z1, 0.15, (0.0, 1.0, 0.0))

        # Второе звено
        self.draw_cylinder(x1, y1, z1, x2, y2, z2, 0.025, (1.0, 0.0, 0.0))
        self.draw_sphere(x2, y2, z2, 0.12, (1.0, 0.5, 0.0))

        # Траектория
        if trace_points and len(trace_points) > 1:
            glBegin(GL_LINE_STRIP)
            glColor3f(1.0, 1.0, 0.0)
            for point in trace_points:
                glVertex3f(point[0], point[1], point[2])
            glEnd()

        # Информация
        self.draw_text(f"Двойной маятник", 10, 30)
        self.draw_text(f"θ1 = {theta1:.3f} рад, θ2 = {theta2:.3f} рад", 10, 50)
        self.draw_text(f"L1 = {L1} м, L2 = {L2} м", 10, 70)
        self.draw_text(f"Время: {time:.2f} с", 10, 90)

        pygame.display.flip()

    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_UP:
                    self.camera_angle = min(90, self.camera_angle + 5)
                elif event.key == pygame.K_DOWN:
                    self.camera_angle = max(0, self.camera_angle - 5)
                elif event.key == pygame.K_LEFT:
                    self.camera_distance = min(20, self.camera_distance + 0.5)
                elif event.key == pygame.K_RIGHT:
                    self.camera_distance = max(2, self.camera_distance - 0.5)

        return True

    def close(self):
        """Закрытие рендерера"""
        pygame.quit()