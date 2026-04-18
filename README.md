# 🎮 Proyecto Integrador - Juego de Lucha 2D

**Materia:** Práctica Profesional 4 - Proyecto Integrador  
**Equipo:** Natalia Laime / Desarrollo conjunto  

---

##  Descripción

Desarrollamos un juego de lucha 2D como proyecto integrador, enfocado en la implementación de un motor de combate modular y escalable. El objetivo principal es aplicar conceptos de programación orientada a objetos, arquitectura de videojuegos y manejo de estados en un entorno real de desarrollo con Python.

El juego está construido utilizando **Python + Pygame-CE**, con un enfoque técnico en la separación de lógica, renderizado y sistema de combate.

---

## ⚙️ Características Técnicas

### 🧠 Máquina de Estados Finitos (FSM)
Implementamos una **FSM (Finite State Machine)** para el control de comportamiento de los personajes. Cada entidad puede transicionar entre estados como:

- `IDLE`
- `WALK`
- `ATTACK`
- `HURT`

Esto permite una lógica desacoplada, escalable y fácil de mantener para la gestión de animaciones y comportamiento.

---

###  Sistema de profundidad (Y-Sorting)
El renderizado utiliza un sistema de **Y-Sorting dinámico** para simular profundidad en un entorno 2.5D.

- Los sprites se ordenan en función de su posición en el eje Y.
- Permite superposición natural entre personajes y elementos del escenario.
- Mejora la percepción de profundidad sin necesidad de un motor 3D.

---

###  Sistema de combate: Hitbox / Hurtbox
El sistema de combate está basado en la separación de colisiones en:

- **Hitbox:** área de impacto del ataque
- **Hurtbox:** área vulnerable del personaje

Esto permite un control preciso de los intercambios de daño y una detección de colisiones más justa y consistente.

---

### 🧩 Arquitectura modular de personajes
El sistema está diseñado para ser escalable, permitiendo la implementación de múltiples personajes.

- Base común de lógica de personaje
- Herencia para comportamientos específicos
- Preparado para soportar al menos **3 personajes jugables**

---

##  Tecnologías

- Python
- Pygame-CE
- Aseprite (Pixel Art y animaciones)

---

