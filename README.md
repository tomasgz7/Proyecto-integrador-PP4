# 🎮 Proyecto Integrador - Juego de Lucha 2D

**Materia:** Práctica Profesional 4 - Proyecto Integrador  
**Equipo:** Desarrollo conjunto  
- Desarrollo y arquitectura: (Tomas Guzman)  
- UX / Diseño: Natalia Laime  

---

##  Descripción

Desarrollamos un juego de lucha 2D como proyecto integrador, enfocado en la construcción de un motor de combate modular, escalable y basado en buenas prácticas de ingeniería de software.

El proyecto está desarrollado en **Python + Pygame-CE**, con gestión de dependencias mediante **uv**, y separado en capas de lógica, renderizado y sistema de combate.

El diseño visual, dirección artística y experiencia de usuario (UX) están a cargo de Natalia Laime, quien define la identidad visual del juego, paleta de colores, diseño de personajes y consistencia estética general.

---

## ⚙️ Características Técnicas

###  Máquina de Estados Finitos (FSM)
Implementamos una **FSM (Finite State Machine)** para controlar el comportamiento de los personajes.

Estados principales:
- `IDLE`
- `WALK`
- `ATTACK`
- `HURT`

Este enfoque permite desacoplar lógica de animación, entradas y comportamiento, facilitando la escalabilidad del sistema.

---

###  Sistema de profundidad (Y-Sorting)
El sistema de renderizado utiliza **Y-Sorting dinámico** para simular profundidad en un entorno 2.5D.

- Ordenamiento de sprites basado en posición Y
- Superposición natural entre personajes y escenario
- Simulación de profundidad sin motor 3D

---

### 🥊 Sistema de combate: Hitbox / Hurtbox
El sistema de combate está basado en una separación explícita de colisiones:

- **Hitbox:** área activa de ataque
- **Hurtbox:** área vulnerable del personaje

Esto permite detección precisa de impactos y control fino del balance de combate.

---

### 🧩 Arquitectura modular de personajes
El sistema está diseñado con escalabilidad en mente.

- Clase base de personaje con lógica común
- Herencia para comportamientos específicos
- Preparado para soportar múltiples personajes jugables (mínimo 3)

---

##  UX / Diseño (Natalia Laime)

Responsable del diseño integral del juego:

- Diseño de personajes (pixel art)
- Definición de paleta de colores
- Consistencia visual del entorno y UI
- Dirección artística general
- Recomendaciones de experiencia de usuario (UX)
- Creación de assets en **Aseprite**

Los assets se integran posteriormente al motor de juego para pruebas iterativas.

---

## 🧰 Tecnologías

- Python 3.x
- Pygame-CE
- uv (gestión de dependencias)
- Aseprite (Pixel Art)

---

## 📦 Instalación y ejecución

```bash
# Instalar dependencias
uv add pygame-ce

# Ejecutar el proyecto
uv run python main.py
