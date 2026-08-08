# Pipeline de Análisis de Exámenes con IA

*Documento de referencia en español para el Trabajo de Fin de Grado. La documentación técnica completa, orientada a la navegación por agentes de IA, se mantiene en `README.md` y `PROJECT_BRIEF.md` (inglés).*

---

## 1. Qué es este proyecto

Un sistema de estudio para exámenes universitarios de Informática, construido en dos capas:

1. **Pipeline CLI** (`pipeline/pipeline.py`) — decide *qué* estudiar. Procesa exámenes de años anteriores, extrae las preguntas, las clasifica por tema y calcula una puntuación de prioridad (ROI) por tema.
2. **Tutor conversacional** (`tutor/`) — enseña los temas ya priorizados mediante recuperación activa, dificultad progresiva y repetición espaciada.

Este documento se centra en la capa 1 (el pipeline), que es la parte con lógica de software propiamente dicha y la relevante para la discusión de arquitectura del TFG. La capa 2 es un conjunto de prompts e instrucciones para un agente conversacional, no código ejecutable.

## 2. Qué hace el pipeline

Dado uno o varios exámenes pasados (texto o PDF), el pipeline:

1. Extrae cada pregunta con su puntuación y su tipo de formato (opción múltiple, respuesta corta, explicación/derivación, código o demostración).
2. Etiqueta cada pregunta con una etiqueta canónica de tema, reutilizando las etiquetas existentes y creando nuevas solo cuando es necesario.
3. Estima, una única vez por tema nuevo, dos parámetros cualitativos: dificultad (D, 1–6) y conectividad (C, 1–3, cuántos otros temas dependen de él).
4. Agrega de forma puramente programática, sin IA, tres variables por tema a partir de todos los exámenes: F (frecuencia de aparición), G (fracción media de puntos) y Fmt (profundidad de formato).
5. Calcula `Priority = 100 × (F × G × C) / (D × Fmt)` y escribe `Exam_ROI_Pipeline.xlsx` con el ranking resultante.

Es importante para la discusión de arquitectura distinguir qué hace el modelo de lenguaje y qué hace código determinista:

| Tarea | Quién la hace |
|---|---|
| Extraer preguntas de un PDF/texto | LLM |
| Etiquetar cada pregunta con un tema | LLM |
| Estimar D y C **solo para temas nuevos** | LLM |
| Calcular F, G, Fmt y el ranking final | Python puro |
| Generar el Excel | Python puro (openpyxl) |

El LLM nunca recalcula D/C para un tema ya conocido, y nunca toca la aritmética de agregación. Esto no es solo una decisión de coste: acota el papel del modelo a juicios cualitativos difíciles de programar (clasificación semántica, estimación de dificultad), dejando todo lo verificable y determinista fuera de su alcance.

## 3. Uso actual: Claude (Anthropic)

Por defecto, el pipeline usa la API de Claude (Anthropic) en dos llamadas por examen:

- **Etapa 1** (`stage1_extract`): un modelo pequeño y rápido (Claude Haiku) extrae las preguntas.
- **Etapa 2** (`stage2_tag_score`): un modelo más capaz (Claude Sonnet) etiqueta los temas y estima D/C para los temas nuevos, en lotes para exámenes largos.

Esta elección se debe al contexto original del proyecto (herramientas de Anthropic ya integradas en el flujo de trabajo del autor), no a una dependencia estructural del pipeline respecto a un proveedor concreto — ver la siguiente sección.

## 4. Independencia respecto al proveedor de IA

Esta es la pregunta central para el TFG: **¿cuánto del diseño depende de Anthropic/Claude?** Muy poco, y de forma acotada a un punto concreto del código.

### 4.1 Dónde vive el acoplamiento

Todo el pipeline — lectura de PDF, construcción de prompts, parseo de JSON, matemática de agregación, generación del Excel — es agnóstico al proveedor: son cadenas de texto y estructuras de datos, no tipos específicos de un SDK. El único punto de acoplamiento real está en dos funciones de `pipeline.py`:

- `_client()` — instancia el cliente del SDK correspondiente.
- `call_llm()` — envía el prompt (sistema + usuario) y devuelve texto plano, detectando si la respuesta fue truncada por el límite de tokens.

Todo lo demás en el pipeline llama a `call_llm(system, user, model=...)` y trata el resultado como una cadena de texto, sin saber ni importarle qué proveedor la generó.

### 4.2 Diseño implementado: selección de proveedor en tiempo de ejecución

El pipeline implementa una capa de abstracción mínima (`PROVIDERS`, en `pipeline.py`) que permite elegir el proveedor sin tocar código, mediante la variable de entorno `LLM_PROVIDER`:

```bash
# Claude (Anthropic) — por defecto
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# DeepSeek
pip install openai
export LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY=sk-...

# OpenAI
pip install openai
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```

Esto funciona sin cambios de código para DeepSeek y OpenAI porque ambos exponen una API de *chat completions* compatible con el SDK de OpenAI — es la misma forma de petición y de respuesta, solo cambia la URL base y la clave. Añadir cualquier otro proveedor compatible (Groq, un modelo local servido con vLLM u Ollama, etc.) requiere únicamente una entrada nueva en el diccionario `PROVIDERS`; no hace falta tocar la lógica del pipeline.

### 4.3 Qué sí cambiaría al cambiar de proveedor

Para ser honestos en el análisis, no todo es gratis:

- **Fiabilidad del formato JSON.** Los prompts de las etapas 1 y 2 piden JSON estricto. `parse_json_from()` ya tolera que el modelo envuelva la respuesta en bloques de código Markdown, pero distintos modelos difieren en su disciplina para seguir instrucciones de formato; un modelo más débil en *instruction following* puede necesitar reglas de prompting más estrictas o reintentos adicionales.
- **Calidad del juicio cualitativo.** Las estimaciones de dificultad (D) y conectividad (C) son subjetivas por naturaleza. Modelos distintos producirán estimaciones distintas para el mismo tema — esto no es un fallo de portabilidad, es inherente a delegar un juicio en un LLM.
- **Streaming vs. no streaming.** La implementación actual usa streaming para Anthropic porque el SDK de Anthropic rechaza peticiones no-streaming con presupuestos de tokens de salida grandes (los presupuestos aquí son de 32k). La familia OpenAI-compatible no tiene esa restricción, por lo que usa una petición estándar; esta diferencia está aislada dentro de `call_llm()` y no se propaga al resto del pipeline.

### 4.4 Conclusión para el TFG

El acoplamiento a Anthropic es de **adaptador, no de arquitectura**: dos funciones, sustituibles por una entrada de configuración. El diseño resultante — separar "qué necesito de un LLM" (texto de entrada, texto de salida, señal de truncamiento) de "cómo se lo pido a este proveedor concreto" — es el patrón habitual para no acoplar un sistema a un único proveedor de IA, y es el que se ha adoptado aquí.

## 5. Instalación y uso rápido

```bash
cd pipeline

# 1. Elegir proveedor e instalar su SDK (ver sección 4.2)
pip install -r ../requirements.txt

# 2. Procesar un examen
python pipeline.py add exam_2023.pdf --year 2023 --total-marks 100

# 3. Procesar una carpeta entera de exámenes
python pipeline.py add-folder ../exams/computer_vision

# 4. Reconstruir el Excel sin volver a llamar al LLM
python pipeline.py rebuild

# 5. Ver el estado actual
python pipeline.py status

# 6. Corregir manualmente una estimación de D/C
python pipeline.py edit-topic "Big-O Notation" --d 2 --c 3
```

Documentación completa de comandos y esquemas de datos: `pipeline/docs/pipeline_docs.md`.

## 6. Estructura del repositorio (resumen)

```
.
├── pipeline/        ← el CLI: pipeline.py, taxonomy.json, exámenes ya procesados, el Excel de salida
├── tutor/           ← prompts del tutor conversacional y estado de progreso (capa 2, no es código)
├── loci/            ← infraestructura del palacio de memoria (compartida entre asignaturas)
├── exams/           ← PDFs de exámenes de años anteriores, organizados por asignatura
├── docs/            ← informes de análisis, separados en abiertos / consolidados / archivados
└── assets/          ← diagramas y visualizaciones auxiliares
```

El mapa completo, con la convención de organización y las reglas de versionado de archivos, está en `README.md`.

## 7. Limitaciones y trabajo futuro

Para que la memoria del TFG sea honesta sobre el estado del sistema:

- La estimación de D y C mediante LLM no tiene validación cuantitativa contra resultados reales de examen; es una heurística razonada, no calibrada empíricamente.
- La capa de tutor (capa 2) está actualmente especializada para una asignatura concreta; su generalización a cualquier curso está identificada como problema de diseño abierto (ver `PROJECT_BRIEF.md`, sección de problemas abiertos).
- La integración del método de loci (palacio de memoria) está parcialmente implementada; el esquema de codificación y su evaluación siguen en diseño.
- No existe todavía una evaluación comparativa (Claude vs. DeepSeek vs. otros) de la calidad de extracción y etiquetado sobre el mismo conjunto de exámenes — sería la validación empírica natural de la sección 4 y un experimento con encaje directo en la memoria.
