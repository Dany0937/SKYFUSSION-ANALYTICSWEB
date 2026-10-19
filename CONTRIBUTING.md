# 🛡️ Skyfusion Analytics - Lineamientos de Contribución

Gracias por tu interés en contribuir a **Skyfusion Analytics**. Este documento establece las directrices para mantener la calidad, consistencia y trazabilidad del proyecto.

## 📋 Código de Conducta

Se espera un trato respetuoso y profesional en todas las interacciones. No toleramos conducta discriminatoria, acosadora o destructiva.

## 🌟 Formas de Contribuir

### 1. Reportar Issues
- Usa el template de issues para reportar bugs o solicitudes de características
- Incluye pasos para reproducir, entorno y evidencia si es un bug
- Etiqueta adecuadamente: `bug`, `enhancement`, `documentation`, `question`

### 2. Mejorar Documentación
- Corrige errores tipográficos o información desactualizada
- Añade ejemplos claros para nuevos usuarios
- Traduce documentación a otros idiomas
- Mejora diagrams yREADMEs

### 3. Contribuir Código
- Fork el repositorio y crea una rama feature: `git checkout -b feature/descripcion`
- Cumple las **Conventional Commits** para los mensajes
- Asegúrate de que los tests pasen (`npm test` o `python -m pytest`)
- Haz push a tu rama y abre un Pull Request

### 4. Mejorar Tests
- Añade cobertura para nuevos módulos
- Mejora tests existentes para mayor robustness
- Mantén el 80%+ de cobertura en módulos críticos

## 📦 Convenciones del Proyecto

### Commits (Conventional Commits)
Todos los commits deben seguir este formato:
```
<tipo>(<ámbito>): <descripción corta>

[pie de página opcional]

Tipos permitidos:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Documentación
- `style`: Formato, missing semicolons, etc.
- `refactor`: Refactorización sin cambio de comportamiento
- `test`: Adding missing tests
- `chore`: Tareas mantenimiento

Ejemplo: `feat(analysis): add NDWI time series calculation`
```

### Branching Strategy
- **main**: Versiones estables publicadas
- **desarroll**: Rama principal de desarrollo
- **feature/**: Nuevas funcionalidades
- **bugfix/**: Correcciones de bugs
- **docs/**: Cambios exclusivamente en documentación

### Pull Request Process
1. Asegúrate de que la rama esté actualizada con `development`
2. Ejecuta la suite de tests localmente
3. Llena el template del Pull Request
4. Un miembro del equipo revisará y aprobará

## 🛠️ Guía Rápida

```bash
# 1. Clonar y crear rama
git clone https://github.com/Dany0937/SKYFUSSION-ANALYTICSWEB.git
git checkout -b feature/nueva-caracteristica

# 2. Realizar cambios y commitear
git add .
git commit -m "feat: descripción del cambio"

# 3. Subir y abrir PR
git push origin feature/nueva-caracteristica
```

## 📄 Template de Pull Request

### Descripción
- **Problem**: ¿Qué problema resuelve este PR?
- **Solución**: ¿Qué cambio se hizo?
- **Tests**: ¿Se ejecutaron las pruebas?

### Checklist
- [ ] He leído las guías de contribución
- [ ] Mi código sigue el estilo del proyecto
- [ ] He añadido/actualizado documentación si es necesario
- [ ] Los tests pasan localmente
- [ ] He verificado que no hay warnings de lint

---

**¡Gracias por contribuir a Skyfusion Analytics!** 🌊