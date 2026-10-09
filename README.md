# Tech DNA 🧬
Plataforma de evaluación técnica y gestión de talento para candidatos y evaluadores en el ecosistema de desarrollo de software.

## 📸
`/`
<img width="1004" height="863" alt="Screenshot 2026-10-09 132205" src="https://github.com/user-attachments/assets/4dfaca6e-ec2a-4116-843c-d3fd804cfcf9" />

<img width="867" height="578" alt="Screenshot 2026-10-09 132352" src="https://github.com/user-attachments/assets/56a77d07-5eb5-4ea5-9a80-c1f595030341" />

`accounts/profile/edit/`

<img width="802" height="918" alt="Screenshot 2026-10-09 132449" src="https://github.com/user-attachments/assets/bc1e2bf2-e3d7-4279-9de9-75001667f09a" />

`accounts/profile/`

<img width="513" height="719" alt="Screenshot 2026-10-09 132630" src="https://github.com/user-attachments/assets/5d7734f8-9a4a-4deb-8b4d-baaf3139c3bc" />




## 📋 Progreso del Proyecto (Sesiones 1 - 3)

- Sesión 1 — Arquitectura Base y Setup Inicial
    - Inicialización del proyecto Django con configuración modular (`settings/base.py`).
    - Configuración de variables de entorno con `.env` y sistema de plantillas base heredable (`base.html`).
    - Creación de la aplicación `core` y diseño visual responsivo con CSS nativo.
- Sesión 2 — Modelado y Estructura de Aplicaciones
    - Creación y registro de las aplicaciones base: `accounts`, `skills` y `assessments`.
    - Enrutamiento global (`ROOT_URLCONF`) y diseño de la interfaz de navegación superior.
    - Configuración del modelo de datos inicial y migraciones base.
- Sesión 3 — Autenticación, Perfiles y Manejo de Medios
    - Implementación del modelo personalizado `accounts.User` (`AbstractUser`) con campos técnicos (`role`, `primary_track`, `avatar`, redes).
    - Flujo completo de autenticación: registro con validación de email único, login, logout y auto-login tras registrarse.
    - Vistas y formularios de perfil (`profile`, `profile_edit`) con subida de imágenes mediante `Pillow` y configuración de `MEDIA_URL` / `MEDIA_ROOT`.
    - Suite de 4 pruebas unitarias superadas en `accounts/tests.py`.

-------------------------

## 🛠️ Stack Tecnológico

Lenguaje: Python 3.12

Framework Web: Django 6.1.2

Base de Datos: SQLite3 (entorno de desarrollo)

Gestión de Imágenes: Pillow

Frontend: HTML5, CSS3 nativo (variables CSS, diseño responsivo)

## 📁 Estructura del Proyecto

```text
TechDNApp/
└── _TechDna_/
    ├── accounts/                 # Aplicación de autenticación y perfiles
    │   ├── migrations/           # Migraciones de base de datos
    │   ├── forms.py              # Formularios (RegisterForm, ProfileForm)
    │   ├── models.py             # Modelo User extendido
    │   ├── tests.py              # Tests unitarios de autenticación
    │   ├── urls.py               # Enrutamiento de cuentas
    │   └── views.py              # Vistas de registro y perfil
    ├── core/                     # Vistas globales y páginas base
    ├── media/                    # Almacenamiento local de avatares subidos
    │   └── avatars/
    ├── static/                   # Hojas de estilo y recursos estáticos
    │   └── css/
    │       └── styles.css
    ├── techDna/                  # Configuración modular del proyecto
    │   ├── settings/
    │   │   ├── base.py           # Configuración base del proyecto
    │   │   └── ...
    │   ├── urls.py               # Enrutador principal
    │   └── wsgi.py
    ├── templates/                # Plantillas HTML
    │   ├── accounts/
    │   │   ├── login.html
    │   │   ├── register.html
    │   │   ├── profile.html
    │   │   └── profile_edit.html
    │   └── base.html
    ├── manage.py
    └── requirements.txt

```

## ⚙️ Instalación y Puesta en Marcha

1. Clonar el repositorio y entrar al directorio
```bash
git clone https://github.com/TechDNApp/TechDNApp.git
cd TechDNApp\_TechDna_
```

2. Configurar el entorno virtual
```bash
python -m venv .venv
.venv\Scripts\Activate
```

3. Instalar dependencias
```bash
pip install -r requirements.txt
```

4. Variables de entorno

Crea un archivo `.env` en la raíz del proyecto (`_TechDna_`) con las variables mínimas requeridas:

```python
DJANGO_SECRET_KEY=tu_clave_secreta_aqui
DEBUG=True
```
5. Ejecutar migraciones
```bash
python manage.py makemigrations accounts
python manage.py migrate
```

6. Iniciar el servidor de desarrollo
```bash
python manage.py runserver
```

Accede a la aplicación en **http://localhost:8000/**.

## 🧪 Ejecución de Tests

Para validar la suite completa de pruebas unitarias de la app accounts:
```bash
python manage.py test accounts
```

## 📌 Rutas Principales de Autenticación

| Método | Ruta | Nombre de URL (`name`) | Descripción | Acceso |
| :--- | :--- | :--- | :--- | :--- |
| `GET`, `POST` | `/accounts/login/` | `accounts:login` | Formulario e inicio de sesión de usuario | Público |
| `POST` | `/accounts/logout/` | `accounts:logout` | Cierre de sesión e invalidación de token de sesión | Autenticado |
| `GET`, `POST` | `/accounts/register/` | `accounts:register` | Formulario de registro y auto-login | Público |
| `GET` | `/accounts/profile/` | `accounts:profile` | Vista de detalle del perfil técnico y avatar | Autenticado |
| `GET`, `POST` | `/accounts/profile/edit/` | `accounts:profile_edit` | Edición de datos personales, enlaces y avatar (`multipart`) | Autenticado |



## 👥 Equipo de Desarrollo

| Nombre | Rol / Track | GitHub | LinkedIn |
| :--- | :--- | :--- | :--- |
| **Angelo** | Full Stack Developer | [github](https://github.com/) | [linkedin](https://linkedin.com/) |
| **Maite** | Full Stack Developer | [github](https://github.com/) | [linkedin](https://linkedin.com/) |
| **Mio** | Full Stack Developer | [github](https://github.com/miaryl) | [linkedin](https://linkedin.com/in/mio-ogura) |





