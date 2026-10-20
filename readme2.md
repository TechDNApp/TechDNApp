🚀 Guía de Configuración del Entorno de Desarrollo con PostgreSQL
Esta guía contiene los pasos necesarios para que todo el equipo configure el entorno local de desarrollo con PostgreSQL y lo conecte correctamente con el proyecto Django.

📋 Requisitos Previos
Tener instalado Python 3.12 o superior.

Tener instalado PostgreSQL (versión 17 o superior recomendada).

🛠️ Pasos de Configuración
1. Clonar el repositorio y activar el entorno virtual
Abre tu terminal (PowerShell o Git Bash) y ejecuta:

PowerShell
# Clonar el repositorio (si aplica)
git clone <URL_DEL_REPOSITORIO>
cd TechDNApp\_TechDna_

# Crear el entorno virtual
python -m venv venv

# Activar el entorno virtual (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# En caso de usar Mac / Linux:
# source venv/bin/activate
2. Instalar dependencias
Instala las librerías necesarias, incluyendo el conector de PostgreSQL (psycopg[binary]):

PowerShell
pip install -r requirements.txt
3. Crear la Base de Datos en PostgreSQL
Abre la consola de PostgreSQL (psql) o tu cliente gráfico (pgAdmin, DBeaver, etc.) y crea la base de datos para el proyecto:

SQL
CREATE DATABASE techdna_db;
4. Configurar las Variables de Entorno (.env)
Crea un archivo .env en la raíz del proyecto (junto a manage.py) con la configuración de tu entorno local:

Fragmento de código
DEBUG=True
SECRET_KEY=tu_clave_secreta_local
DB_NAME=techdna_db
DB_USER=postgres
DB_PASSWORD=tu_contraseña_local
DB_HOST=localhost
DB_PORT=5432
Nota: Sustituye tu_contraseña_local por la clave asignada a tu usuario de PostgreSQL durante la instalación.

5. Aplicar las Migraciones
Ejecuta las migraciones para estructurar las tablas e índices en la base de datos:

PowerShell
python manage.py makemigrations
python manage.py migrate
6. Verificar la Conexión y Servidor
Arranca el servidor de desarrollo de Django:

PowerShell
python manage.py runserver
Abre tu navegador en [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Si la página carga correctamente y sin errores en la terminal, ¡el entorno está listo para trabajar!