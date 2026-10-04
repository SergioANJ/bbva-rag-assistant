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


## ADR-004: Fuente de datos → Bancolombia (en lugar de BBVA Colombia)

- **Fecha:** 2026-10-01
- **Estado:** Aceptada. Validación de extracción en páginas de producto pendiente.

### Contexto
El enunciado propone https://www.bbva.com.co/ como fuente, pero permite explícitamente
usar el sitio de otro banco.

### Pruebas realizadas sobre BBVA Colombia
Todas las pruebas usaron la página de producto `/personas/productos/inversion/cdt/online.html`.

| # | Prueba | Resultado |
|---|---|---|
| 1 | `scrapy shell` con el User-Agent por defecto de Scrapy | **403 Forbidden** |
| 2 | Análisis de la respuesta 403 | Página de bloqueo propia del banco ("Algo salió mal") con un Reference ID; la cabecera `Server` está oculta. El formato del ID es compatible con un WAF tipo Akamai. |
| 3 | User-Agent identificable (`bbva-rag-assistant/0.1` + enlace al repositorio) | **403** |
| 4 | User-Agent de navegador (Chrome en Windows) | **403** |
| 5 | Script de sondeo con httpx sobre la portada y `robots.txt` | **403** en ambos |

**Conclusión:** el bloqueo no depende solo del User-Agent. El sitio aplica una protección
anti-bots que rechaza deliberadamente a los clientes automatizados.

### Decisión ética
No se intentó evadir la protección (navegadores automatizados con técnicas de camuflaje,
rotación de IPs, etc.). Eludir una medida de seguridad puesta a propósito por un banco no es
una práctica aceptable. Como el enunciado permite otro banco, se buscó una fuente que
autorice el acceso automatizado.

### Evaluación de alternativas
Sondeo de la portada y del `robots.txt` de siete bancos colombianos, con User-Agent identificable:

| Banco | Portada | robots.txt | Restricciones relevantes para `User-agent: *` |
|---|---|---|---|
| Bancolombia | 200 | 200 | Formularios, buscadores, PDFs, `/rest/`, preaprobados y solicitudes. Tiene sitemap índice. |
| Davivienda | 200 | 200 | PDFs, `/documents/` y toda URL con parámetros (`?`). Tiene sitemap. |
| Banco de Bogotá | 200 | 200 | Ninguna. Tiene sitemap. |
| Banco Popular | 200 | 200 | No revisado. |
| Banco de Occidente | 200 | 200 | No revisado. |
| AV Villas | 200 | 200 | PDFs, zonas internas del CMS y URLs con parámetros. Tiene sitemap. |
| Banco Caja Social | 200 | 200 | PDFs, `/portalserver/` y buscador. Tiene sitemap. |

### Por qué Bancolombia
1. Es el banco más grande del país y su sitio tiene amplio contenido de productos.
2. Su `robots.txt` es detallado: indica con precisión qué rutas no deben rastrearse.
3. Distingue entre bots de **entrenamiento** de IA (bloqueados: GPTBot, ClaudeBot,
   Google-Extended, etc.) y bots de **búsqueda y consulta**, con un comentario que menciona
   explícitamente el uso para RAG. Este proyecto no entrena modelos: consulta el contenido y
   cita la fuente, que es el uso permitido.
4. Publica un sitemap índice, que permite obtener la lista oficial de páginas en lugar de
   descubrirlas solo siguiendo enlaces.

**Plan B:** Banco de Bogotá, cuyo `robots.txt` no restringe ninguna ruta.

### Pruebas realizadas sobre Bancolombia (`/personas`)

| # | Prueba | Resultado |
|---|---|---|
| 1 | Ver código fuente (`Ctrl+U`) | El HTML del servidor contiene el contenido de la página. |
| 2 | Recargar con JavaScript desactivado | La página se sigue mostrando: el contenido principal se renderiza en el servidor. |
| 3 | `scrapy shell` | **200**, 219.166 caracteres de HTML. |
| 4 | Extraer texto con `body *::text` | 350 fragmentos, mezclados con CSS embebido y marcadores de plantilla del portal (`${title}`, `Web Content Viewer`). Confirma que se necesita una etapa de limpieza. |
| 5 | Extraer con trafilatura | 629 caracteres de contenido poco representativo. Esperable: `/personas` es una portada de navegación sin un cuerpo principal. |

### Consecuencias para el scraper
- Se respetará `robots.txt` (`ROBOTSTXT_OBEY = True`).
- Se excluyen los PDFs, porque la mayoría de los bancos evaluados los prohíbe en `robots.txt`.
- Las páginas de portada aportan poco contenido. El valor está en las páginas de producto,
  así que el descubrimiento de URLs se hará desde el sitemap.
- Algunos componentes del portal son plantillas que se llenan con JavaScript (`${title}`).
  Se debe verificar que el contenido de producto no dependa de ellos.

### Pendiente
- Validar la extracción con trafilatura en páginas de producto.


### Validación en página de producto
Prueba sobre `/personas/productos-servicios/inversiones/renta-fija`: trafilatura extrajo
Markdown limpio (780 caracteres) con títulos de sección y descripciones reales de productos,
sin menús, estilos ni marcadores de plantilla. Se confirma trafilatura como herramienta de
limpieza.

### Hallazgos del sitemap
- El sitemap índice tiene cuatro secciones: personas, acerca de, centro de ayuda y
  educación financiera.
- El sitemap incluye páginas sin valor para el RAG (simuladores, canales de contacto,
  páginas antiguas con sufijo `-viejo`). Se filtrarán por patrones de URL configurables.


## ADR-005: Motor de scraping, alcance y estrategia de extracción

- **Fecha:** 2026-10-01
- **Estado:** Aceptada.

### Motor: Scrapy con `SitemapSpider`
- El sitio renderiza su contenido en el servidor: el contenido aparece en el código fuente
  y la página se muestra con JavaScript desactivado (ver ADR-004). No se necesita un
  navegador automatizado.
- El sitio publica un sitemap índice con 756 URLs únicas. `SitemapSpider` las obtiene
  directamente, sin depender del menú de navegación, que el portal arma con plantillas
  JavaScript (`${title}`) y por eso no expone sus enlaces en el HTML.
- Scrapy aporta de fábrica el respeto a `robots.txt`, reintentos, control de velocidad
  y deduplicación de URLs.

### Inventario del sitemap
| Sitemap | URLs |
|---|---|
| personas | 440 |
| acerca-de | 119 |
| centro-de-ayuda | 170 |
| educacion-financiera | 28 |
| **Total únicas** | **756** |

5 URLs están prohibidas por `robots.txt` (formularios y solicitudes de productos);
Scrapy las omite con `ROBOTSTXT_OBEY = True`.

### Medición de contenido por tipo de página
Script: `scripts/exploration/measure_content.py`. Caracteres extraídos con trafilatura:

| Tipo | Ejemplo | Caracteres | Observación |
|---|---|---|---|
| Producto | inversiones-digitales | 1.920 | Contenido real, con restos del portal |
| Producto | renta-fija | 780 | Redirige a `valores.bancolombia.com` |
| Simulador | simulador-cdt | 243 | Casi solo restos del portal |
| Contacto | llamanos / chatea-con-nosotros | 169 / 169 | Texto genérico idéntico |
| Ayuda | app-inversiones | 909 | Redirige a otra página del sitio con contenido real |
| Historia | agrollanos | 2.217 | Narrativa institucional, no información de productos |
| Educación | realizar-inversiones-periodicas | 629 | Redirige a la portada (URL obsoleta) |

### Reglas de alcance
| Regla | Evidencia |
|---|---|
| Excluir simuladores (25 URLs) | Contenido interactivo; la extracción da casi solo restos del portal |
| Excluir páginas de contacto y chat | Texto genérico idéntico en páginas distintas |
| Excluir páginas con sufijo `-viejo` | Versiones antiguas de páginas existentes |
| Excluir `historias-que-transforman` (100 URLs, 13 % del sitio) | Narrativa institucional; podría desplazar contenido de productos en la búsqueda. Puede incluirse en una versión futura |
| Excluir PDFs | Prohibidos en `robots.txt` |

### Redirecciones
- **Redirecciones a la portada (`/personas`) se descartan.** Son URLs obsoletas del sitemap
  que el sitio redirige a la portada con estado 200 (*soft 404*).
- **Redirecciones a otras páginas del sitio se conservan.** La página se movió, pero su
  contenido es válido.
- **Se permite `valores.bancolombia.com`** solo para seguir redirecciones, porque los
  productos de inversión del banco (CDT, bonos, fondos) se publican allí. Su `robots.txt`
  permite el acceso. No se rastrea su sitemap completo: el alcance lo define el sitemap
  de Bancolombia.
- **Se eliminan los parámetros `utm_*`** de las URLs, para que una misma página no se
  guarde con direcciones distintas.

### Extracción y limpieza
- **trafilatura en modo por defecto.** `favor_recall=True` produjo exactamente la misma
  cantidad de texto en todas las páginas medidas.
- **Limpieza posterior en dos niveles.** (1) Eliminación de restos conocidos del portal:
  `{}`, `${...}`, `Web Content Viewer`, `Display portlet menu`, `Component Action Menu`,
  `Deferred Modules`, nombres de componentes (`BannerCentroAyuda`, `BuscadorFAQS`) y
  textos de íconos (`*arrow-right*`). (2) Eliminación de bloques que se repiten en un
  alto porcentaje de páginas, porque son plantilla y no contenido.
- **Deduplicación por hash del texto limpio.** Páginas distintas pueden producir el
  mismo texto.
- **Separación crudo / limpio.** El spider guarda el HTML crudo; la limpieza es una etapa
  independiente que se puede re-ejecutar sin volver a descargar el sitio. Esto es
  necesario porque la eliminación de bloques repetidos requiere el corpus completo.

### Cortesía con el servidor
User-Agent identificable con enlace al repositorio, 1,5 s entre peticiones y baja
concurrencia. Tiempo estimado del rastreo completo: unos 20 minutos.

### Pendiente
- Validar la calidad de las preguntas frecuentes individuales del centro de ayuda
  (las páginas medidas eran índices).


  ### Resultados de la corrida completa (2026-10-02)
| Concepto | Cantidad |
|---|---|
| URLs únicas en el sitemap | 756 |
| Excluidas por patrón (sin descargarse) | 133 |
| Prohibidas por `robots.txt` (incluye redirecciones a rutas prohibidas) | 23 |
| *Soft 404* descartados | 2 |
| Redirecciones a dominios fuera del alcance | 11 (6 dominios) |
| Redirecciones a páginas ya descargadas (deduplicadas) | 121 |
| **Páginas guardadas** | **467** |

- Duración: 19,5 minutos (~24 páginas/minuto).
- Volumen: 20 MB transferidos (89 MB de HTML descomprimido).
- 190 respuestas fueron redirecciones 301: una de cada cuatro URLs del sitemap apunta
  a una dirección antigua.
- Se rastreó `valores.bancolombia.com` tras leer su propio `robots.txt`.


## ADR-006: Limpieza del corpus

- **Fecha:** 2026-10-02
- **Estado:** Aceptada.

### Proceso
La limpieza es una etapa independiente del scraping (`python -m bbva_rag.cleaning.run`).
Lee el HTML crudo de `data/raw/` y produce `data/clean/pages.jsonl` y
`data/clean/cleaning_report.json`. Se puede re-ejecutar sin volver a descargar el sitio.

1. **Por página:** extracción con trafilatura, eliminación de restos del portal (nombres de
   componentes, marcadores `${...}`, íconos, títulos vacíos y textos de relleno de páginas
   dinámicas), normalización de espacios. El título se toma del `<h1>` y, si no existe o es
   un marcador, del `<title>`.
2. **Entre páginas:** se eliminan los bloques (no títulos) que aparecen en el 10 % o más de
   las páginas.
3. **Filtro de longitud:** se descartan las páginas con menos de 200 caracteres limpios.
4. **Deduplicación:** se conserva una página por texto idéntico (la URL más corta) y las
   demás URLs se registran en `duplicate_urls`.

### Evidencia (inspección del corpus)
| Decisión | Evidencia |
|---|---|
| Mantener trafilatura | Un extractor de todo el texto visible no aportó contenido nuevo y agregó ruido (nombres de íconos) |
| Umbral de plantilla en 10 % | La plantilla de contacto aparece en el 16 % de las páginas; contenido legítimo de tarjetas aparece en el 5,6 % |
| Nunca eliminar títulos por frecuencia | `## Características` (14,6 %) y `## Beneficios` (11,8 %) son secciones legítimas |
| No eliminar títulos sin texto debajo | trafilatura representa los títulos de tarjetas como títulos consecutivos (página de Tabot); esa regla borraría contenido real |
| Mínimo de 200 caracteres | Debajo: páginas vacías, de redirección a la app y de relleno; arriba: contenido válido corto (IKE Plus: 256, arrendamiento de vehículo: 236) |
| Hipótesis descartada | Las páginas Visa, Mastercard y American Express tienen el mismo texto porque cada una muestra el catálogo completo; no hubo pérdida de contenido |

### Resultados
| Concepto | Cantidad |
|---|---|
| Páginas de entrada | 467 |
| Bloques de plantilla eliminados | 2 |
| Páginas descartadas por cortas | 30 |
| Duplicados fusionados | 21 |
| **Páginas limpias** | **416** |

### Limitaciones conocidas
- **Preguntas frecuentes del centro de ayuda:** las preguntas y respuestas se cargan con
  JavaScript (verificado desactivando JavaScript: aparecen marcadores de carga). Las rutas
  desde donde un sitio de este tipo carga esos datos (`/rest/`,
  `/centro-de-ayuda/preguntas-frecuentes/resultados/`) están prohibidas en `robots.txt`,
  por lo que no se obtuvieron, ni siquiera con un navegador automatizado.
- **Artículos de seguridad bancaria** (fleteo, paquete chileno, suplantación de
  funcionarios, etc.): su contenido propio se carga con JavaScript. En el HTML solo está la
  plantilla común, por lo que se fusionan en una sola página.
- Pueden quedar títulos de plantilla sin texto debajo (por ejemplo, "Preguntas relacionadas").
- La regla de nombres de componentes eliminaría una línea que fuera solo una palabra
  compuesta con mayúsculas internas (por ejemplo, un nombre de marca aislado).
- **Mejora futura:** integración oficial con la fuente de datos de las preguntas
  frecuentes, que son el contenido de mayor valor para un asistente.


  ## ADR-007: Estrategia de fragmentación (chunking)

- **Fecha:** 2026-10-03
- **Estado:** Aceptada.

### Decisión
- `RecursiveCharacterTextSplitter` de LangChain en modo Markdown: corta preferentemente en
  títulos, luego en párrafos, luego en líneas, y agrupa trozos pequeños consecutivos.
- Tamaño de 1.000 caracteres con 150 de superposición (configurables en `.env`). Con la
  mediana de página en ~1.500 caracteres, una página típica queda en 2 fragmentos, y 5
  fragmentos suman ~1.500 tokens de contexto para el LLM.
- Cada fragmento empieza con una línea de contexto (`Fuente: <título> (<sección>)`), para
  que un fragmento del medio de una página no pierda a qué producto se refiere.
- IDs deterministas (UUID v5 a partir de URL y posición): al reindexar, los fragmentos se
  reemplazan en lugar de duplicarse.

### Correcciones basadas en la inspección
| Problema observado | Corrección |
|---|---|
| 65 fragmentos de menos de 100 caracteres, casi todos títulos separados de su contenido (`#### Pasos`, `## Coberturas`) | Los trozos menores a 100 caracteres se unen al siguiente; si son el último, al anterior |
| Tablas del tarifario cortadas: fragmentos con filas de montos sin los encabezados de las columnas | Si un fragmento continúa una tabla abierta, se le antepone la fila de encabezados; una tabla nueva no hereda encabezados ajenos |
| Espacios repetidos dentro de las celdas de las tablas | Se colapsan durante la limpieza |

### Resultados
| Concepto | Antes | Después |
|---|---|---|
| Fragmentos | 1.687 | 1.625 |
| Menores a 100 caracteres | 65 | 0 |
| Tamaño mínimo / mediano / máximo | 10 / 808 / 1.000 | 102 / 822 / 1.260 |

El máximo supera el límite configurado por la unión de títulos y la repetición de
encabezados; se acepta a cambio de fragmentos autocontenidos.

### Limitaciones y mejoras futuras
- Las tablas anchas (por ejemplo, el tarifario con 8 columnas e historial de
  modificaciones) siguen siendo difíciles para la búsqueda semántica. Mejora futura:
  convertir cada fila en una frase del tipo "Tarifa: X; Plan Oro: $ Y".
- El glosario aporta 145 fragmentos (~9 % del corpus); es contenido legítimo, pero puede
  dominar las búsquedas de definiciones.


  ## ADR-008: Embeddings con OpenAI y base vectorial Qdrant

- **Fecha:** 2026-10-03
- **Estado:** Aceptada. Reemplaza el plan inicial de embeddings locales (`bge-m3`).

### Embeddings densos: OpenAI `text-embedding-3-small`
- **Docker:** un modelo local requiere PyTorch y más de 2 GB de modelo, lo que haría
  pesada y lenta de construir la imagen que el evaluador debe levantar.
- **Costo:** $0,02 por millón de tokens. El corpus (~1,4 M de caracteres, ~400 mil tokens)
  cuesta menos de un centavo de dólar por indexación completa.
- **Sin dependencia nueva:** el LLM ya requiere la API de OpenAI.
- **Desventaja aceptada:** es un segundo componente pago. Se mitiga manteniendo locales y
  gratuitos BM25 y el reranker.
- **Patrón Factory:** el proveedor está detrás de la interfaz `Embedder`; agregar un modelo
  local solo requiere una nueva implementación y un caso en `create_embedder`.

### Hallazgo de la prueba de similitud
| Par de frases | Similitud |
|---|---|
| "¿Cuánto me cobran por tener la tarjeta de crédito?" / "Cuota de manejo de la tarjeta de crédito" | 0,69 |
| "Cómo abrir un CDT por la app" / "Invertir a término fijo con certificado de depósito" | 0,26 |
| "Cómo abrir un CDT por la app" / "Horario de atención de las oficinas" | 0,23 |

El modelo captura paráfrasis, pero no relaciona la sigla "CDT" con su significado. Esto
justifica la búsqueda híbrida (BM25 para coincidencias exactas), la reformulación de la
pregunta en el grafo y la comparación con `text-embedding-3-large` en la evaluación.

### Base vectorial: Qdrant (self-hosted en Docker)
- Búsqueda híbrida nativa: vector denso y vector disperso en el mismo punto, combinados
  en una sola consulta.
- Filtros por metadatos (`section`), panel web para inspección y versión fija de la imagen.
- Alternativas consideradas: pgvector (un servicio menos, pero la búsqueda híbrida habría
  que construirla a mano), Weaviate (válida), Chroma (orientada a prototipos), FAISS
  (librería, no base de datos), Pinecone (no es self-hosted).

  ## ADR-009: Indexación híbrida y primeras pruebas de búsqueda

- **Fecha:** 2026-10-03
- **Estado:** Aceptada.

### Indexación
- Colección `bancolombia_chunks` en Qdrant con dos vectores por punto: `dense`
  (OpenAI, 1.536 dimensiones, distancia coseno) y `bm25` (FastEmbed, español, con IDF
  calculado por Qdrant sobre toda la colección).
- BM25 en español: elimina palabras vacías y reduce las palabras a su raíz (verificado con
  tests: "tarjeta" y "tarjetas" producen el mismo índice).
- Reconstrucción completa de la colección en cada indexación: con 1.625 fragmentos es
  rápida y barata, y evita que queden fragmentos de páginas que ya no existen. La
  indexación incremental queda como mejora futura.
- Índice de payload sobre `section` para filtros futuros.

| Etapa | Resultado |
|---|---|
| Fragmentos indexados | 1.625 |
| Tokens enviados a OpenAI | ~324 mil (~0,7 centavos de dólar) |
| Vectores densos | 19,8 s |
| Vectores BM25 | 2,0 s (local, sin PyTorch) |

### Primeras pruebas de búsqueda (top 3, `scripts/exploration/try_search.py`)
| Pregunta | Semántica | BM25 | Híbrida (RRF) |
|---|---|---|---|
| "¿Cómo abro un CDT?" | Glosario e inscripción de cuentas | Páginas "¿Cómo abro...?" de otros productos | Combinación de ambas; ninguna sobre CDT |
| "¿Cuánto me cobran por tener la tarjeta de crédito?" | Páginas generales de tarjetas | Costo de un avance ("cobran") | Páginas relacionadas, sin la cuota de manejo |

### Hallazgos
- Las palabras de la forma de la pregunta ("cómo", "abro", "cobran") dominan la búsqueda
  BM25 cuando coinciden con títulos de otras páginas.
- El contenido sobre cuota de manejo existe en el corpus (22 páginas de tarjetas), pero
  no llega al top 3.
- Fragmentos con "CDT" en el corpus: <completar>. [Si son pocos: el problema es de
  cobertura, porque el contenido de CDT vive en Valores con poco texto.]
- La misma página puede ocupar varias posiciones del top.

### Consecuencias para la Fase 4
- Reformular la pregunta antes de buscar (expandir siglas, usar términos del sitio).
- Reranker sobre los 20 candidatos de la búsqueda híbrida.
- Medir primero si el fragmento correcto aparece entre los 20 candidatos: si no aparece,
  el reranker no puede rescatarlo.

## ADR-010: Estrategia de recuperación por defecto → híbrida (medida con golden set)

- **Fecha:** 2026-10-03
- **Estado:** Aceptada.

### Método
Golden set de 15 preguntas escritas como las haría un usuario, con la página correcta de
cada una (`eval/golden_set.jsonl`), de distintos tipos: paráfrasis, siglas, términos
exactos, tablas, preguntas frecuentes y definiciones. Se mide la posición de la primera
página correcta entre 20 candidatos (`python -m bbva_rag.evaluation.retrieval`).

### Resultados
| Estrategia | hit@1 | hit@3 | hit@5 | hit@20 | MRR |
|---|---|---|---|---|---|
| Semántica | 47 % | 60 % | 67 % | 87 % | 0,56 |
| BM25 | 40 % | 40 % | 67 % | 87 % | 0,48 |
| Híbrida (RRF) | 53 % | 60 % | 60 % | 93 % | 0,60 |

### Decisión
Se usa la búsqueda **híbrida** por defecto (`RETRIEVAL_STRATEGY=hybrid`):
- Mejor hit@20 (93 %): es la estrategia que más veces trae la página correcta entre los
  candidatos que recibirá el reranker.
- Mejor MRR (0,60) y hit@1 (53 %).
- La semántica y BM25 fallan en preguntas distintas: la semántica no encuentra siglas
  ("DTF") y BM25 no encuentra paráfrasis ("sacar plata en efectivo" frente a "avance").
  La híbrida recupera ambos tipos.

### Hallazgos
- La fusión RRF no siempre ordena mejor que una estrategia individual (hit@5: 60 % frente
  a 67 % de la semántica): es buena para reunir candidatos, no para ordenarlos.
- Brecha entre hit@20 (93 %) y hit@5 (60 %): en 4 de cada 10 preguntas la página correcta
  se recupera, pero no llegaría al LLM sin un reordenamiento. **Justifica el reranker.**
- Pregunta no recuperada por la híbrida: q03 (línea telefónica, dato en tabla).

### Limitaciones
- Con 15 preguntas, cada pregunta equivale a ~7 puntos porcentuales; diferencias de un
  solo valor no son concluyentes. Ampliar el golden set queda como mejora futura.
- La evaluación es a nivel de página, no de fragmento.

## ADR-011: Reranker multilingüe y número de candidatos

- **Fecha:** 2026-10-03
- **Estado:** Aceptada.

### Modelos disponibles en FastEmbed
Solo uno es multilingüe: `jinaai/jina-reranker-v2-base-multilingual` (1,11 GB). Los demás
están entrenados en inglés o en chino e inglés.

### Comparación (20 candidatos de la búsqueda híbrida)
| Configuración | hit@1 | hit@3 | hit@5 | MRR | Tiempo del reranker |
|---|---|---|---|---|---|
| Híbrida, sin reranker | 47 % | 60 % | 60 % | 0,56 | — |
| + `ms-marco-MiniLM-L-12-v2` (inglés) | 40 % | 73 % | 73 % | 0,56 | 3,73 s |
| + `jina-reranker-v2-base-multilingual` | 67 % | 87 % | 93 % | 0,75 | 7,58 s |

- El reranker en inglés mejora unas preguntas y empeora otras (MRR sin cambios): no
  entiende el español y se guía por coincidencias superficiales.
- El multilingüe sube al top 5 todas las páginas correctas que estaban entre los
  candidatos: alcanza el techo posible (hit@5 = hit@20 = 93 %).
- **Techo:** el reranker solo reordena; no puede recuperar páginas que la búsqueda no trajo
  (q03).

### Número de candidatos
| Candidatos | hit@5 | MRR | Tiempo del reranker |
|---|---|---|---|
| 20 | 93 % | 0,75 | 7,58 s |
| **15** | **93 %** | **0,75** | **5,58 s** |
| 10 | 87 % | 0,73 | 3,39 s |

Se eligen **15 candidatos**: misma calidad que 20 con un 26 % menos de latencia. Con 10 se
pierde una pregunta (q04, cuya página estaba en la posición 13). Configurable con
`RETRIEVAL_TOP_K`.

### Limitaciones
- **Licencia:** el modelo es CC-BY-NC-4.0 (uso no comercial). Válido para esta prueba; en
  producción debe reemplazarse por un reranker con licencia comercial (por ejemplo,
  `bge-reranker-v2-m3`, Apache 2.0, o un servicio de reranking por API). La interfaz del
  reranker aísla ese cambio en una sola clase.
- **Latencia:** ~5,6 s por pregunta en CPU de portátil. Mejoras posibles: GPU, modelo
  cuantizado o reranking por API.
- Variabilidad: entre ejecuciones, los embeddings de OpenAI y los empates de RRF pueden
  mover alguna posición; las mejoras del reranker son mucho mayores que esa variación.

  ## ADR-012: Umbral de relevancia del grafo

- **Fecha:** 2026-10-04
- **Estado:** Aceptada.

Se midió el mejor puntaje del reranker en las 15 preguntas del golden set y en 8 preguntas
sobre temas del banco sin respuesta en el corpus (`eval/negative_set.jsonl`,
`python -m bbva_rag.evaluation.threshold`).

| Umbral | Respondibles aceptadas | Sin respuesta rechazadas |
|---|---|---|
| −0,3 | 100 % | 43 % |
| **0,0** | **92 %** | **86 %** |
| 0,3 | 58 % | 86 % |

**Decisión:** `RELEVANCE_THRESHOLD=0.0`. Rechaza la mayoría de los contextos inútiles. La
única pregunta respondible por debajo (q13, −0,26) no se pierde: el grafo la reformula y
busca de nuevo.

**Hallazgo:** algunos contextos sin la página correcta obtienen puntajes altos (q02, q03,
q04), porque contienen páginas parecidas. El umbral no reemplaza las reglas del prompt de
respuesta, que son la segunda línea de defensa contra respuestas inventadas.

**Limitación:** pocas preguntas por grupo (12 y 7 con puntaje); el valor debe revisarse
con un conjunto más grande.


## ADR-013: Historial persistente en PostgreSQL

- **Fecha:** 2026-10-04
- **Estado:** Aceptada.

- **PostgreSQL** (Docker, `postgres:17-alpine`) con dos tablas: `conversations` y
  `messages`. Cada respuesta guarda metadatos para la analítica: intención, resultado
  (`answered`, `no_answer`, `direct_reply`, `error`), pregunta reescrita, mejor puntaje,
  búsquedas, fuentes, tiempos por nodo, latencia total y calificación del usuario.
- **SQLAlchemy 2.0:** tablas tipadas; el mismo código funciona con SQLite en memoria en los
  tests.
- **Patrón Repository** (`ConversationRepository`): único punto de acceso a la base.
  Pregunta y respuesta se guardan en una sola transacción.
- **Patrón Facade** (`ChatService.ask`): oculta el grafo, la memoria y la persistencia
  detrás de una sola llamada, reutilizable por la CLI y la API.
- **Historial de N mensajes** (`HISTORY_MAX_MESSAGES`): se leen solo los N más recientes
  con `LIMIT`, sin cargar la conversación completa.
- **Los errores también se guardan** (`outcome = error`) para medir la tasa de fallos.
- **Limitación:** las tablas se crean con `create_all`; las migraciones con Alembic quedan
  como mejora futura.

  ### Resultados de la prueba
- Una conversación retomada con `--session` respondió correctamente una pregunta de
  seguimiento ("¿y se puede retirar la plata antes de ese plazo?") usando el historial
  guardado en PostgreSQL.
- La calificación del usuario quedó registrada (`feedback = 1`).

### Hallazgos y limitaciones
- Las preguntas sobre la propia conversación ("¿de qué estábamos hablando?") se
  clasificaban como preguntas del banco y terminaban sin respuesta. Corregido en el prompt
  de análisis: se responden directamente con el historial.
- Una pregunta de seguimiento con error de escritura ("que plazoz se tienen?") terminó sin
  respuesta. Pendiente de diagnóstico con la pregunta reescrita guardada en la base.
- Las respuestas `no_answer` tardan 13–16 s, frente a ~9 s de una respuesta normal: es el
  costo del ciclo de reformulación (dos búsquedas y dos pasadas por el reranker).