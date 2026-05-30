# 🚀 Guía de Despliegue: PLACCA.CO ERP

Esta guía explica paso a paso cómo desplegar la aplicación ERP en **Streamlit Community Cloud** de forma 100% gratuita.

## 📁 Archivos Necesarios
Asegúrate de tener los siguientes archivos en una misma carpeta:
1. `app.py` (El código principal de la aplicación)
2. `erp_system.db` (La base de datos SQLite ya inicializada con tus datos)
3. `requirements.txt` (Las dependencias del proyecto)

## 🛠️ Paso 1: Subir el código a GitHub
Streamlit Cloud necesita conectarse a un repositorio de GitHub para leer el código.

1. Crea una cuenta gratuita en [GitHub](https://github.com/) si no tienes una.
2. Crea un nuevo repositorio (puede ser privado o público). Nómbralo algo como `placca-erp`.
3. Sube los 3 archivos mencionados arriba (`app.py`, `erp_system.db`, `requirements.txt`) a este nuevo repositorio.

> **Nota sobre la base de datos:** Al subir `erp_system.db` a GitHub y desplegar en Streamlit Cloud, los datos se guardarán en el servidor de Streamlit. Ten en cuenta que si el servidor se reinicia, los datos volverán al estado original del archivo en GitHub. Para un uso a largo plazo en producción, se recomienda conectar Streamlit a una base de datos en la nube (como Supabase o PostgreSQL) en lugar de usar SQLite local.

## 🌐 Paso 2: Desplegar en Streamlit Community Cloud
1. Ve a [Streamlit Community Cloud](https://share.streamlit.io/) e inicia sesión con tu cuenta de GitHub.
2. Haz clic en el botón **"New app"**.
3. Selecciona el repositorio que acabas de crear (`tu-usuario/placca-erp`).
4. En el campo "Branch", déjalo en `main` (o la rama por defecto).
5. En el campo "Main file path", escribe `app.py`.
6. Haz clic en **"Deploy!"**.

¡Listo! En un par de minutos, Streamlit instalará las librerías necesarias y tu aplicación estará disponible en una URL pública que podrás compartir con tu equipo de 3 personas.

## 👥 Usuarios Predefinidos
Para iniciar sesión en la aplicación, puedes usar cualquiera de estos usuarios:

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| `admin` | `admin123` | Administrador |
| `ventas` | `ventas123` | Vendedor |
| `bodega` | `bodega123` | Bodeguero |

*(Recuerda cambiar estas contraseñas en el código si la aplicación será pública).*

## 💡 Opciones Alternativas de Despliegue (Para mantener datos persistentes)
Si necesitas que la base de datos SQLite no se borre al reiniciar el servidor, puedes desplegar la aplicación en **Render.com** usando un "Disk" persistente:

1. Crea una cuenta en [Render](https://render.com/).
2. Crea un nuevo **"Web Service"** conectado a tu repositorio de GitHub.
3. Configura el comando de inicio (`Start Command`): `streamlit run app.py --server.port $PORT`
4. Añade un **"Disk"** en la configuración avanzada y móntalo en la ruta donde se guarda tu base de datos.
