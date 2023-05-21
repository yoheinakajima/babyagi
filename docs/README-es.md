<h1 align="center"> 
babyagi 

</h1>

# Objetivo

Este script de Python es un ejemplo de un sistema de gestión de tareas impulsado por inteligencia artificial. El sistema utiliza las API de OpenAI y Pinecone para crear, priorizar y ejecutar tareas. La idea principal detrás de este sistema es que crea tareas basadas en el resultado de tareas anteriores y un objetivo predefinido. Luego, el script utiliza las capacidades de procesamiento del lenguaje natural (NLP) de OpenAI para crear nuevas tareas basadas en el objetivo, y Pinecone para almacenar y recuperar los resultados de las tareas para el contexto. Esta es una versión simplificada del original [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28 de marzo de 2023).

Este README cubrirá lo siguiente:

- [Cómo funciona el script](#como-funciona)

- [Cómo utilizar el script](#como-utilizar)

- [Modelos compatibles](#modelos-compatibles)

- [Advertencia sobre la ejecución continua del script](#advertencia-script-continuo)

# Cómo funciona<a name="como-funciona"></a>

El script funciona ejecutando un bucle infinito que realiza los siguientes pasos:

1. Extrae la primera tarea de la lista de tareas.
2. Envía la tarea al agente de ejecución, que utiliza la API de OpenAI para completar la tarea según el contexto.
3. Enriquece el resultado y lo almacena en Pinecone.
4. Crea nuevas tareas y prioriza la lista de tareas en función del objetivo y el resultado de la tarea anterior.
</br>

La función execution_agent() es donde se utiliza la API de OpenAI. Esta toma dos parámetros: el objetivo y la tarea. Luego envía una solicitud a la API de OpenAI, que devuelve el resultado de la tarea. La solicitud consta de una descripción de la tarea del sistema de IA, el objetivo y la tarea en sí. Luego se devuelve el resultado como una cadena.
</br>
La función task_creation_agent() es donde se utiliza la API de OpenAI para crear nuevas tareas basadas en el objetivo y el resultado de la tarea anterior. La función toma cuatro parámetros: el objetivo, el resultado de la tarea anterior, la descripción de la tarea y la lista de tareas actual. Luego envía una solicitud a la API de OpenAI, que devuelve una lista de nuevas tareas como strings. Luego, la función devuelve las nuevas tareas como una lista de diccionarios, donde cada diccionario contiene el nombre de la tarea.
</br>
La función prioritization_agent() es donde se utiliza la API de OpenAI para priorizar la lista de tareas. La función toma un parámetro, el ID de la tarea actual. Luego envía una solicitud a la API de OpenAI, que devuelve la lista de tareas repriorizadas como una lista numerada.

Finalmente, el script utiliza Pinecone para almacenar y recuperar los resultados de las tareas para el contexto. El script crea un índice Pinecone basado en el nombre de la tabla especificado en la variable YOUR_TABLE_NAME. Luego, Pinecone se utiliza para almacenar los resultados de la tarea en el índice, junto con el nombre de la tarea y cualquier metadato adicional.

# Cómo utilizar el script<a name="como-utilizar"></a>

Para utilizar el script, deberá seguir estos pasos:

1. Clonar el repositorio a través de `git clone https://github.com/yoheinakajima/babyagi.git` y `cd` en el repositorio clonado.
2. Instalar los paquetes requeridos: `pip install -r requirements.txt`
3. Copiar el archivo .env.example a .env: `cp .env.example .env`. Aquí es donde establecerá las siguientes variables.
4. Establezca sus claves de API de OpenAI y Pinecone en las variables OPENAI_API_KEY, OPENAPI_API_MODEL y PINECONE_API_KEY.
5. Establezca el entorno de Pinecone en la variable PINECONE_ENVIRONMENT.
6. Establezca el nombre de la tabla donde se almacenarán los resultados de la tareas en la variable TABLE_NAME.
7. (Opcional) Establezca el objetivo del sistema de gestión de tareas en la variable OBJECTIVE.
8. (Opcional) Establezca la primera tarea del sistema en la variable INITIAL_TASK.
9. Ejecute el script.

Todos los valores opcionales anteriores también se pueden especificar en la línea de comando.

# Modelos compatibles<a name="modelos-compatibles"></a>

Este script funciona con todos los modelos de OpenAI, así como con Llama a través de Llama.cpp. El modelo predeterminado es **gpt-3.5-turbo**. Para utilizar un modelo diferente, especifíquelo a través de OPENAI_API_MODEL o utilice la línea de comando.

## Llama

Descargue la última versión de [Llama.cpp](https://github.com/ggerganov/llama.cpp) y siga las instrucciones para compilarla. También necesitará los pesos del modelo Llama.

- **Bajo ninguna circunstancia comparta enlaces IPFS, enlaces magnet o cualquier otro enlace para descargar modelos en cualquier lugar de este repositorio, incluyendo propuestas (issues), debates (discussions) o solicitudes de extracción (pull requests). Serán eliminados de inmediato.**

Después de eso, enlace `llama/main` a llama.cpp/main y `models` a la carpeta donde tenga los pesos del modelo Llama. Luego ejecute el script con `OPENAI_API_MODEL=llama` o el argumento `-l`.

# Advertencia<a name="advertencia-script-continuo"></a>

Este script está diseñado para ser ejecutado continuamente como parte de un sistema de gestión de tareas. La ejecución continua de este script puede resultar en un alto uso de la API, así que úselo responsablemente. Además, el script requiere que las APIs de OpenAI y Pinecone estén configuradas correctamente, así que asegúrese de haber configurado las APIs antes de ejecutar el script.

# Contribución

Como es obvio, BabyAGI todavía está en su infancia y, por lo tanto, todavía estamos determinando su dirección y los pasos a seguir. Actualmente, un objetivo de diseño clave para BabyAGI es ser _simple_ para que sea fácil de entender y construir sobre ella. Para mantener esta simplicidad, solicitamos amablemente que se adhiera a las siguientes pautas al enviar solicitudes de extracción (PR):

- Enfóquese en modificaciones pequeñas y modulares en lugar de refactorizaciones extensas.
- Al introducir nuevas funciones, proporcione una descripción detallada del caso de uso específico que está abordando.

Una nota de @yoheinakajima (5 de abril de 2023):

> I know there are a growing number of PRs, appreciate your patience - as I am both new to GitHub/OpenSource, and did not plan my time availability accordingly this week. Re:direction, I've been torn on keeping it simple vs expanding - currently leaning towards keeping a core Baby AGI simple, and using this as a platform to support and promote different approaches to expanding this (eg. BabyAGIxLangchain as one direction). I believe there are various opinionated approaches that are worth exploring, and I see value in having a central place to compare and discuss. More updates coming shortly.

Soy nuevo en GitHub y en código abierto, así que por favor tenga paciencia mientras aprendo a administrar este proyecto adecuadamente. Dirijo una empresa de capital de riesgo durante el día, por lo que generalmente revisaré las solicitudes de extracción y los problemas por la noche después de acostar a mis hijos, lo que puede no ser todas las noches. Estoy abierto a la idea de traer soporte y actualizaré esta sección pronto (expectativas, visiones, etc). Estoy hablando con muchas personas y aprendiendo, ¡esperen actualizaciones pronto!

# Antecedentes

BabyAGI es una versión simplificada de [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28 de marzo de 2023) compartido en Twitter. Esta versión se ha reducido a 140 líneas: 13 comentarios, 22 líneas en blanco y 105 líneas de código. El nombre del repositorio surgió como reacción al agente autónomo original, y el autor no pretende implicar que esto sea AGI.

Hecho con amor por [@yoheinakajima](https://twitter.com/yoheinakajima), que casualmente es un VC (¡me encantaría ver lo que estás construyendo!).
