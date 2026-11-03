# Tech DNA 🧬
Plataforma de evaluación técnica y gestión de talento para candidatos y evaluadores en el ecosistema de desarrollo de software.

## 📸
- logged in `/`
<img width="1035" height="853" alt="Screenshot 2026-10-19 111656" src="https://github.com/user-attachments/assets/b25b3a65-ce4c-4d3c-ab85-7e75c84055e8" />


- `accounts/profile/edit/`

<img width="802" height="918" alt="Screenshot 2026-10-09 132449" src="https://github.com/user-attachments/assets/bc1e2bf2-e3d7-4279-9de9-75001667f09a" />

- `accounts/profile/`

<img width="513" height="719" alt="Screenshot 2026-10-09 132630" src="https://github.com/user-attachments/assets/5d7734f8-9a4a-4deb-8b4d-baaf3139c3bc" />

- `assessments/create`
<img width="938" height="882" alt="Screenshot 2026-10-19 111708" src="https://github.com/user-attachments/assets/9adcf6c0-dba8-471c-bc88-499cd59a614e" />

- `assessments/`
<img width="980" height="800" alt="Screenshot 2026-10-19 111717" src="https://github.com/user-attachments/assets/6b708d4c-960d-40a6-9a50-c38f7b08f333" />

- `assessments/1/evaluacion-de-prueba`
<img width="1011" height="730" alt="Screenshot 2026-10-19 111726" src="https://github.com/user-attachments/assets/3432ce44-c62b-4119-84c3-ff1bf175c391" />

- sesión 8: documentación `api/docs/`
<img width="1836" height="907" alt="Screenshot 2026-10-26 155147" src="https://github.com/user-attachments/assets/1d2bb0ab-0225-49e5-9dee-f3a1001e11d4" />







## 📋 Progreso del Proyecto (Sesiones 1 - 8)

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
- **Sesión 4 — Módulo de Evaluaciones (CRUD Base)**
    - Implementación del modelo `Assessment` y `Favorite` con relaciones hacia `User`, `Technology` y `Role`.
    - Generación automática y segura de URLs amigables mediante slugs canónicos (`slugify`).
    - Vistas de listado, creación (`create`), actualización (`update`) y eliminación (`delete`).
- **Sesión 5 — Búsqueda, Filtros y Optimización de Consultas**
    - Implementación de búsqueda por términos (`q`) y filtrado por tecnología, rol o propietario.
    - Optimización de consultas a la base de datos utilizando `select_related` y `prefetch_related` para evitar problemas N+1.
    - Paginación de listados e interfaz de filtrado avanzada.
- **Sesión 6 — Funcionalidades Avanzadas y Suite de Tests**
    - Contador de visitas atómico en la vista de detalle utilizando expresiones `F()` (`views_count`).
    - Sistema de marcación de favoritos (`toggle_favorite`) con restricción anti-autofavorito para propietarios.
    - Subida de archivos multimedia adjuntos en formularios de evaluación (`multipart/form-data`).
    - Ajustes de diseño CSS para prevenir desbordamientos (`overflow-wrap: anywhere`).
    - Autorización estricta mediante `OwnerRequiredMixin` retornando `HttpResponseForbidden` (403).
    - Suite completa de 30 pruebas unitarias verificadas y superadas en `assessments/tests.py`.
- **Sesión 7 — API REST Base y Django REST Framework (DRF)**
    - Creación de la aplicación `api` y configuración de Django REST Framework.
    - Registro de routers principales bajo `/api/v1/`.
    - Implementación de endpoints de solo lectura para `technologies` y `roles`.
- **Sesión 8 — API REST Avanzada: Serializers, Permisos, Filtros y Testing**
    - Implementación de `AssessmentSerializer` con serializers públicos anidados (`UserPublicSerializer`, `TechnologySerializer`, `RoleSerializer`) y asignación automática del usuario solicitante como propietario.
    - Creación del permiso personalizado `IsOwnerOrReadOnly` para restringir la modificación y eliminación únicamente al propietario del recurso.
    - Filtrado dinámico REST mediante `django-filters` (`AssessmentFilter`) por tecnología y rol, complementado con búsqueda textual (`search_fields`) y ordenamiento por fecha y favoritos.
    - Acción personalizada `@action` para marcar/desmarcar evaluaciones como favoritas desde la API (`POST /api/v1/assessments/<pk>/favorite/`).
    - Suite completa de 6 pruebas unitarias automatizadas (`APITestCase`) validando autenticación, permisos, CRUD y filtros.
- **Sesión 9 — Módulo de Notificaciones y Tiempo Real**
    - Creación de la aplicación notifications con modelos y señales (signals.py) para avisos automáticos ante eventos en la plataforma.
    - Endpoints API dedicados para la gestión, listado y marcado de notificaciones de usuario (/api/v1/notifications/).
    - Integración de infraestructura de mensajería y colas de tareas mediante Redis ejecutado vía contenedores Docker (redis-techdna).
- **Sesión 10 — Módulo de Chat Educativo (Estudiante / Instructor)**
    - Implementación de la aplicación chat con los modelos Conversation y Message orientados al ecosistema educativo (student e instructor).
    - Creación de servicios transaccionales protegidos (services.py) para la obtención/creación segura de conversaciones atadas a evaluaciones (assessment_id) y envío de mensajes con validación de participantes.
    - Vistas web tradicionales y endpoints API en DRF para listar conversaciones, iniciar chats, enviar mensajes (/chat/api/conversations/...) y marcar mensajes como leídos.
    - Restricción de permisos personalizada (IsConversationParticipant) para asegurar la privacidad de los mensajes.
- **Sesión 11 — Refactorización de Dominio, UI y Endpoints API**
   - Migración completa del modelo comercial heredado (buyer/seller) al modelo educativo (student/instructor) en serializers, servicios, permisos y señales de notificación.
   - Ajuste de vistas web y plantillas (conversation_list.html, chat_detail.html) con enrutamiento namespaced correcto (chat:detail).
   - Resolución de errores de deserialización y excepciones ImproperlyConfigured / AttributeError, asegurando una integración robusta entre el frontend y la API REST del chat.
- **Sesión 12 — Geolocalización, PostGIS y Búsquedas por Proximidad**
   - Extensión espacial PostGIS en PostgreSQL e integración de GeoDjango (`django.contrib.gis`, motor `postgis`).
   - Campos `location` (`PointField`, WGS84 / SRID 4326, `geography=True`) y `location_name` en `accounts.User`, editables desde el perfil (latitud/longitud) y el admin.
   - Servicio `accounts.services.get_candidates_nearby()`: candidatos dentro de un radio en km, anotados y ordenados por distancia (`Distance`, `D(km=...)`).
   - Endpoint `GET /api/v1/candidates/?lat=...&lng=...&distance_km=10` (autenticado) con `distance_km` en la respuesta, validación de parámetros (400) y coordenadas redondeadas a ~1 km por privacidad.
   - Suite de tests espaciales en `accounts/test_geo.py` (servicio, API y formulario de perfil).

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
    ├── assessments/              # Aplicación de evaluaciones técnicas
    │   ├── migrations/           # Migraciones del modelo Assessment y Favorite
    │   ├── forms.py              # Formularios de creación y edición
    │   ├── models.py             # Modelos Assessment y Favorite
    │   ├── tests.py              # Suite de 30 pruebas unitarias
    │   ├── urls.py               # Rutas CRUD, búsqueda y favoritos
    │   └── views.py              # Vistas basadas en clases y funciones
    ├── core/                     # Vistas globales y páginas base
    ├── media/                    # Almacenamiento local de avatares y archivos
    │   └── avatars/
    ├── skills/                   # Aplicación de competencias, tecnologías y roles
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
    │   ├── assessments/          # Plantillas de listado, detalle, formularios
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
```bash
python manage.py test assessments
```

Para validar todas las aplicaciones del proyecto:

```bash
python manage.py test 
```

## 🌍 PostGIS y GeoDjango (Sesión 12)
GeoDjango necesita las librerías nativas GDAL/GEOS/PROJ y la extensión PostGIS en la base de datos.

1. Instalar PostGIS (en macOS con Homebrew instala también GDAL, GEOS y PROJ):

```bash
brew install postgis
```

2. Activar la extensión con el superusuario de PostgreSQL (en Homebrew, tu usuario de macOS). Se crea también en `template1` para que la BD de tests (`test_techdna`) la herede sin dar permisos de superusuario al usuario de la app:

```bash
psql -d techdna -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

```bash
psql -d template1 -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

3. Los tests ya no usan SQLite en memoria (no soporta campos espaciales): corren sobre PostgreSQL/PostGIS.

4. Si Django no encuentra GDAL/GEOS, añade al `.env` `GDAL_LIBRARY_PATH` y `GEOS_LIBRARY_PATH` (ver `.env.example`).

5. Migrar y probar:

```bash
python manage.py migrate
python manage.py test accounts.test_geo
```

## 🐳 Configuración de Entorno con Docker (Redis)
Para el correcto funcionamiento del sistema de colas, tareas en segundo plano y notificaciones en tiempo real, el proyecto utiliza un contenedor de Redis.

**Comandos útiles para la gestión de Docker:**
1. Verificar estado de los contenedores:

```Bash
docker ps -a
```

2. Iniciar el contenedor de Redis (redis-techdna):

```Bash
docker start redis-techdna
```
3. Detener el contenedor de Redis:

```Bash
docker stop redis-techdna
```

## 📌 Rutas Principales de Autenticación
***Autenticación y Cuentas (accounts)***
| Método | Ruta | Nombre de URL (`name`) | Descripción | Acceso |
| :--- | :--- | :--- | :--- | :--- |
| `GET`, `POST` | `/accounts/login/` | `accounts:login` | Formulario e inicio de sesión de usuario | Público |
| `POST` | `/accounts/logout/` | `accounts:logout` | Cierre de sesión e invalidación de token de sesión | Autenticado |
| `GET`, `POST` | `/accounts/register/` | `accounts:register` | Formulario de registro y auto-login | Público |
| `GET` | `/accounts/profile/` | `accounts:profile` | Vista de detalle del perfil técnico y avatar | Autenticado |
| `GET`, `POST` | `/accounts/profile/edit/` | `accounts:profile_edit` | Edición de datos personales, enlaces y avatar (`multipart`) | Autenticado |

***Evaluaciones Técnicas (assessments)***
| Método | Ruta | Nombre de URL (`name`) | Descripción | Acceso |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/assessments/` | `assessments:list` | Listado público de evaluaciones con filtros y búsqueda | Público |
| `GET`, `POST` | `/assessments/create/` | `assessments:create` | Crear una nueva evaluación técnica | Autenticado |
| `GET` | `/assessments/mine/` | `assessments:mine` | Mis evaluaciones creadas (incluidas inactivas) | Autenticado |
| `GET` | `/assessments/technology/<slug>/` | `assessments:by_technology` | Filtrar evaluaciones por tecnología | Público |
| `GET` | `/assessments/owner/<username>/` | `assessments:by_owner` | Evaluaciones públicas de un usuario | Público |
| `POST` | `/assessments/<pk>/favorite/` | `assessments:toggle_favorite` | Añadir o quitar de favoritos | Autenticado (no propietario) |
| `GET`, `POST` | `/assessments/<pk>/edit/` | `assessments:update` | Editar evaluación propia | Propietario (403 si no) |
| `GET`, `POST` | `/assessments/<pk>/delete/` | `assessments:delete` | Eliminar evaluación propia | Propietario (403 si no) |
| `GET` | `/assessments/<pk>/<slug>/` | `assessments:detail` | Vista de detalle de la evaluación (incrementa visitas) | Público |

***Chat y Mensajería Educativa (chat)***
| Método | Ruta | Nombre de URL (`name`) | Descripción | Acceso |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/chat/` | `chat:list` | Bandeja de entrada de conversaciones del usuario | Autenticado |
| `GET` | `/chat/<int:pk>/` | `chat:detail` | Vista de detalle de una conversación y panel de mensajes | Autenticado |
| `POST` | `/chat/api/conversations/start/` | API / DRF | Mis evaluaciones creadas (incluidas inactivas) | Autenticado |
| `POST` | `/chat/api/conversations/<int:pk>/send/` |  API / DRF |Envía un mensaje dentro de una conversación activa | Autenticado |
| `POST` | `/chat/api/conversations/<int:pk>/read/` | API / DRF | Marca los mensajes pendientes como leídos en la conversación | Autenticado |

***API REST y Notificaciones (api/v1/)***
| Método | Ruta | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/technologies/`| Listado de tecnologías disponibles | Público / Autenticado |
| `GET` | `/api/v1/roles/` | Listado de roles profesionales disponibles | Público / Autenticado |
| `GET`, `POST` | `/api/v1/assessments/` |Listado, filtrado y creación de evaluaciones vía AP | Público (GET) / Autenticado (POST) |
| `GET`, `POST`, `DELETE` | `/api/v1/assessments/<pk>/` | Detalle, actualización y borrado de evaluaciones | Propietario o Lectura |
| `POST` | `/api/v1/assessments/<pk>/favorite/` | Alternar favorito en una evaluación vía API | Autenticado |
| `GET` | `/api/v1/notifications/` | Listado de notificaciones del usuario autenticadoI | Autenticado |



## 👥 Equipo de Desarrollo

| Nombre | Rol / Track | GitHub | LinkedIn |
| :--- | :--- | :--- | :--- |
| **Angelo** | Full Stack Developer | [github](https://github.com/) | [linkedin](https://linkedin.com/) |
| **Maite** | Full Stack Developer | [github](https://github.com/) | [linkedin](https://linkedin.com/) |
| **Mio** |  Sprint 4 Scrum Master & Dev| [github](https://github.com/miaryl) | [linkedin](https://linkedin.com/in/mio-ogura) |




