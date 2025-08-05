# Herramienta de Etiquetado de Imágenes para YOLOv8

Una aplicación de escritorio intuitiva y eficiente, desarrollada en Python con PySide6, para crear anotaciones de detección de objetos en el formato requerido por YOLOv8.

### 🎥 Demostración

![Demostración de la Herramienta de Etiquetado](https://github.com/viccorari/Data-Labeling-Software/blob/main/software%20de%20etiquetado.gif)

---

## 📋 Descripción

Esta herramienta simplifica el proceso de etiquetado de imágenes para entrenar modelos de detección de objetos. Permite a los usuarios dibujar cuadros delimitadores (*bounding boxes*) sobre las imágenes, asignarles una clase predefinida y guardar las anotaciones automáticamente en archivos `.txt` con el formato YOLOv8.

El flujo de trabajo está optimizado para la velocidad, permitiendo la preselección de etiquetas para etiquetar rápidamente múltiples objetos de la misma clase.

## ✨ Características Principales

* **Interfaz Gráfica Intuitiva:** Diseño limpio y moderno con paneles dedicados para una navegación fluida.
* **Formato YOLOv8 Nativo:** Guarda las anotaciones (`<class_id> <x_center> <y_center> <width> <height>`) en archivos `.txt`, listos para ser usados en el entrenamiento.
* **Gestión de Clases:** Permite añadir, editar y eliminar tus propias clases de objetos.
* **Flujo de Etiquetado Rápido:** Preselecciona una etiqueta y dibuja múltiples cuadros delimitadores sin interrupciones.
* **Visualización y Edición:**
    * Lista de todas las etiquetas en la imagen actual.
    * Resaltado del cuadro delimitador seleccionado para una fácil identificación.
    * Eliminación de etiquetas con un solo clic.
* **Organización Automática:** Todas las etiquetas `.txt` se guardan ordenadamente en una subcarpeta `Yolov8/`.

---

## 🛠️ Requisitos

Para ejecutar esta aplicación, solo necesitas tener Python y la biblioteca PySide6 instalados.

* **Python 3.6+**
* **PySide6**

Puedes instalar PySide6 usando pip:
```bash
pip install PySide6
```

---

## 🚀 Cómo Usarlo

Sigue estos pasos para empezar a etiquetar tus imágenes:

1.  **Clona o descarga el repositorio.**
2.  **Abre una terminal** en el directorio del proyecto.
3.  **Ejecuta la aplicación:**
    ```bash
    python etiquetador.py
    ```
4.  **Selecciona tu Carpeta:** Haz clic en el botón **"Seleccionar Carpeta"** y elige el directorio que contiene tus imágenes (`.jpg`, `.png`).
    * La aplicación creará automáticamente una subcarpeta llamada `Yolov8` para guardar los archivos de etiquetas y un `classes.csv` si no existen.

5.  **Gestiona tus Etiquetas (Opcional):**
    * Haz clic en **"Gestionar Etiquetas"** para añadir, editar o eliminar las clases de objetos. Por defecto, se incluyen "persona" y "pez".

6.  **Etiqueta tus Imágenes:**
    * **Preselecciona una clase:** En el panel derecho superior, haz clic en la etiqueta que deseas usar (ej. "persona").
    * **Dibuja el cuadro:** En la imagen, haz clic y arrastra el ratón para dibujar un cuadro delimitador sobre el objeto.
    * Al soltar el clic, la etiqueta se guardará automáticamente.
    * **Navega** entre imágenes con los botones `<< Anterior` y `Siguiente >>`.

7.  **Edita las Etiquetas Creadas:**
    * En el panel derecho inferior, verás una lista de todas las etiquetas de la imagen actual.
    * **Haz clic en una etiqueta** de la lista para resaltarla en amarillo en la imagen.
    * Con la etiqueta seleccionada, haz clic en **"Eliminar Etiqueta Seleccionada"** para borrarla.

---

## 📁 Estructura de Archivos Creada

Al seleccionar una carpeta, la aplicación generará la siguiente estructura:

```
tu_carpeta_de_imagenes/
├── imagen1.jpg
├── imagen2.png
├── classes.csv         <-- Archivo con los IDs y nombres de tus clases.
└── Yolov8/             <-- Carpeta para todas las anotaciones.
    ├── imagen1.txt
    └── imagen2.txt
```

* **`classes.csv`**: Almacena el mapeo de tus etiquetas. Puedes editarlo manualmente si lo deseas.
* **`Yolov8/`**: Contiene un archivo `.txt` por cada imagen etiquetada, con las anotaciones en formato YOLOv8.

