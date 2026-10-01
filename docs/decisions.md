# Registro de decisiones técnicas (ADR)

Cada decisión registra qué se eligió, por qué y qué alternativas se descartaron.

## ADR-001: Gestor de dependencias → uv
- **Decisión:** uv en lugar de pip o poetry.
- **Por qué:** es significativamente más rápido, gestiona versión de Python, entorno
  virtual y dependencias en una sola herramienta, y `uv.lock` garantiza instalaciones
  reproducibles.
- **Alternativas:** pip + requirements.txt (sin lockfile real), poetry (más lento).

## ADR-002: LLM → OpenAI (único componente pago)
- **Decisión:** usar la API de OpenAI como modelo generativo.
- **Por qué:** baja latencia y buena calidad en español sin requerir GPU local.
  El costo es acotado porque solo se envían al modelo los fragmentos recuperados.
- **Mitigación:** el proveedor quedará detrás de una abstracción para poder cambiarlo
  por una opción open source (p. ej. Ollama) vía configuración.
- **Resto del stack:** herramientas gratuitas o self-hosted.

## ADR-003: Configuración → pydantic-settings
- **Decisión:** configuración tipada y validada desde variables de entorno / `.env`.
- **Por qué:** detecta valores inválidos al arrancar, centraliza los parámetros y
  evita valores fijos en el código.
- **Patrón:** Singleton mediante `@lru_cache` en `get_settings()`.