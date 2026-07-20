---
title: Dev Containers
description: Entorno de desarrollo reproducible con VS Code Dev Containers.
order: 2
---

# Dev Containers

El proyecto incluye configuración de **Dev Containers** para VS Code, proporcionando un entorno de desarrollo completo y reproducible.

## Beneficios

- Mismas versiones de herramientas para todo el equipo
- Sin necesidad de instalar dependencias localmente
- Aislamiento del entorno de desarrollo
- Configuración de extensiones y settings predefinidos

## Configuración

```
.devcontainer/
├── dockerfile
└── devcontainer.json
```

## Uso

1. Abrir el proyecto en VS Code
2. Ejecutar `Ctrl+Shift+P` → `Dev Containers: Reopen in Container`
3. El contenedor se construye automáticamente con todas las dependencias

El Dev Container incluye Node.js 20.x, Python 3.11+, y todas las herramientas necesarias para el desarrollo de los agentes y servicios.
