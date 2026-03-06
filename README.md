Organizer Dofus 🛡️ KhyDofus Tabs - Organizador Visual para Dofus La herramienta definitiva para jugadores multicuentas. Gestiona, organiza y cambia entre tus ventanas de Dofus de forma rápida y visual.

🚀 ¿Qué es KhyDofus Tabs? KhyDofus Tabs es una aplicación de escritorio ligera diseñada para mejorar la experiencia de juego ("Quality of Life") de los usuarios que juegan con múltiples cuentas en Dofus.

Permite visualizar el orden de tus personajes mediante sus iconos de clase oficiales, cambiar de ventana rápidamente con atajos de teclado y organizar tu equipo mediante arrastrar y soltar (Drag & Drop).

✅ 100% Seguro: No modifica los archivos del juego ni interactúa con el cliente de Dofus a nivel de código. Funciona exclusivamente a nivel de ventanas de Windows.

✨ Características Principales Detección Automática: Detecta tus ventanas de Dofus abiertas y descarga automáticamente los iconos de clase (Feca, Yopuka, Ocra, etc.) desde la API oficial. Barra Visual Personalizable: Modo Texto: Muestra el nombre y el atajo. Modo Icono: Solo muestra la imagen de la clase. Modo Hover: Muestra el nombre solo al pasar el ratón. Organización Drag & Drop: Arrastra y suelta los personajes para cambiar el orden de la iniciativa en tiempo real. Gestión de Atajos (Hotkeys): Asigna teclas individuales (F1, F2, F3...) a cada personaje. Teclas para "Siguiente Ventana" y "Ventana Anterior". Perfiles de Equipo: Guarda y carga configuraciones de orden para tus distintos equipos (PvM, Koli, Drop, etc.). Smart Hide (Auto-Ocultar): La barra se oculta automáticamente si cambias a otra ventana (Chrome, Discord, etc.) y reaparece al volver al juego. Personalización Total: Cambia el tamaño (Pequeño, Medio, Grande), la orientación (Vertical/Horizontal) y la opacidad de la ventana.

📥 Descarga e Instalación Ve a la sección de Releases de este repositorio. Descarga el archivo KhyDofusTabs.exe. (Opcional) Descarga el archivo icono.ico y ponlo en la misma carpeta para ver el logo en la ventana. ¡Ejecuta el .exe y listo! No requiere instalación.

Nota: Es recomendable ejecutar como Administrador para asegurar que los atajos de teclado globales funcionen correctamente sobre la ventana de Dofus.

🎮 Cómo se usa Abre tus cuentas de Dofus. Ejecuta KhyTrayerTabs. Verás una barra con tus personajes. Haz Clic Derecho en la barra para abrir la Configuración ⚙️. Configura tus teclas (por defecto F1-F8) y el orden de tus personajes.

Atajos Rápidos: Ctrl + Shift + H: Modo Fantasma (Oculta/Muestra la interfaz visual, pero los atajos siguen funcionando).

⚖️ Aviso Legal y Copyright KhyDofus Tabs - Herramienta de Organización Visual

Esta aplicación es una herramienta de terceros gratuita y sin ánimo de lucro. NO modifica los archivos del juego. NO automatiza acciones (no es un bot). NO intercepta paquetes de red.

Simplemente ayuda a cambiar entre ventanas usando atajos de teclado estándar de Windows.

AVISO DE COPYRIGHT: Dofus y Ankama son marcas registradas de Ankama Games. Todas las imágenes, logotipos y nombres de clases son propiedad exclusiva de Ankama Games. Esta aplicación no está afiliada, respaldada ni patrocinada por Ankama Games.

Desarrollado con ❤️ para la comunidad hispana de Dofus. Visita mi canal: Khytrayer Dofus


TÉCNICO ------------------------------------------------------------------------------------------------------

# KhyDofus Tabs (Organizador de ventanas para Dofus)

Overlay de escritorio para Windows (PySide6) pensado para **organizar y cambiar rápidamente entre ventanas de Dofus** mediante un dock/overlay siempre-visible, con estética dark premium y configuración integrada.

> Proyecto de terceros, sin afiliación con Ankama. No modifica archivos del juego.

---

## Características

- **Overlay/dock flotante** (siempre visible) con lista de personajes/ventanas.
- **Cambio de ventana** por click (enfoca la ventana objetivo).
- **Atajos de teclado** (slots y next/prev).
- **Reordenación de ventanas** desde un organizador (drag & drop).
- **Compact Dock** (solo iconos) + tooltips.
- **Smart Hide**: oculta automáticamente el overlay cuando no estás en Dofus.
- **Tema premium dark** (QSS) + pequeñas animaciones.
- **Almanax** integrado en Configuración.

---

## Requisitos

- **Windows 10/11**
- **Python 3.13+** (o 3.12) para ejecutar desde código.

Dependencias principales:
- PySide6
- pygetwindow
- keyboard
- Pillow
- psutil

---

## Instalación (modo desarrollo)

Desde la raíz del proyecto:

```powershell
python -m pip install -r requirements.txt
```

---

## Ejecutar en local

Desde la raíz del proyecto:

```powershell
python main.py
```

Si necesitas ver logs:

```powershell
python -u main.py
```

---

## Configuración y archivo `config.json`

El proyecto guarda la configuración en el perfil del usuario para evitar permisos de administrador:

- `%APPDATA%\KhyDofusTabs\config.json`

Esto permite ejecutar el `.exe` en carpetas normales sin que intente escribir al lado del ejecutable.

---

## Build: crear `.exe` (PyInstaller onefile)

1) Instala PyInstaller:

```powershell
python -m pip install pyinstaller
```

2) Genera el ejecutable **onefile** (sin consola):

```powershell
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "KhyDofusTabs" `
  --icon "icono.ico" `
  --add-data "khy_dofus_tabs\assets\qss\theme.qss;khy_dofus_tabs\assets\qss" `
  --add-data "khy_dofus_tabs\assets\icons\youtube.png;khy_dofus_tabs\assets\icons" `
  --add-data "khy_dofus_tabs\assets\icons\kofi.png;khy_dofus_tabs\assets\icons" `
  main.py
```

Salida:
- `dist\KhyDofusTabs.exe`

---

## Uso rápido

- Click en un personaje/icono para **enfocar** su ventana.
- Click derecho sobre el overlay para abrir el **menú**:
  - Configuración
  - Refrescar
  - Aviso legal
  - Cerrar

En Configuración:
- Ajusta **Escala UI**, **Opacidad**, **Orientación**, **Modo texto**
- Activa **Compact Dock**
- Configura **slots/hotkeys**
- Reordena ventanas desde **Perfiles & Orden**

---

## Aviso legal

Este proyecto es una herramienta de terceros gratuita y sin ánimo de lucro.

- **No modifica** archivos del juego.
- **No automatiza** acciones (no es un bot).
- **No intercepta** paquetes de red.

Dofus y Ankama son marcas registradas de Ankama Games.
Todas las imágenes, logotipos y nombres de clases son propiedad de Ankama Games.

---

## Enlaces

- YouTube: https://www.youtube.com/@KhytrayerDofus
- Ko-fi: https://ko-fi.com/tradexapp
