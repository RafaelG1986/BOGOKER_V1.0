Evidencia de Producto: APP Móvil BOGOKER para Android
<img alt="Banner BOGOKER" src="https://i.imgur.com/4YDHCL8.png">
Descripción General
BOGOKER Mobile es una aplicación Android diseñada para complementar el sistema de gestión de leads inmobiliarios BOGOKER V1.0. Esta aplicación permitirá a los asesores inmobiliarios gestionar sus leads, recibir notificaciones en tiempo real y realizar seguimiento a sus clientes desde cualquier lugar.

Índice de Contenidos
Análisis de Requerimientos
Arquitectura de la Aplicación
Diseño de la Interfaz
Implementación de Módulos
Integración con el Backend
Pruebas Unitarias
Generación de APK
Documentación Técnica
1. Análisis de Requerimientos
1.1 Requisitos Funcionales
Autenticación y seguridad

Inicio de sesión con credenciales del sistema web
Mantenimiento de sesión con tokens JWT
Cierre de sesión seguro
Gestión de Leads

Visualización de lista de leads con paginación
Filtrado y búsqueda avanzada
Visualización detallada de cada lead
Creación de nuevos leads desde el móvil
Edición de información de leads existentes
Seguimiento de Clientes

Actualización de estado de leads
Registro de interacciones con clientes
Programación de recordatorios
Notificaciones

Recepción de notificaciones push de nuevos leads
Alertas de recordatorios y seguimientos pendientes
Notificaciones de asignación de leads
Comunicación

Envío de mensajes a clientes vía WhatsApp
Realización de llamadas directas
Envío de correos electrónicos
1.2 Requisitos No Funcionales
Compatibilidad con Android 8.0 (API 26) y versiones superiores
Tiempo de respuesta inferior a 2 segundos para operaciones básicas
Diseño responsive adaptable a diferentes tamaños de pantalla
Funcionamiento offline con sincronización posterior
Consumo eficiente de batería y datos móviles
2. Arquitectura de la Aplicación
2.1 Patrón Arquitectónico
Se implementa la arquitectura MVVM (Model-View-ViewModel) combinada con Clean Architecture para garantizar:

Separación clara de responsabilidades
Testabilidad de componentes
Mantenibilidad del código
Escalabilidad de la aplicación
2.2 Diagrama de Componentes
2.3 Diagrama de Paquetes
3. Diseño de la Interfaz
3.1 Mapa de Navegación
<img alt="Mapa de Navegación" src="https://i.imgur.com/JlE5tPf.png">
3.2 Wireframes Principales
Pantalla de Login

Interfaz de autenticación con campos para usuario y contraseña, botón de ingreso y opción para recordar credenciales.

Dashboard Principal

Vista con tarjetas de resumen mostrando:

Leads totales
Leads nuevos
Leads en seguimiento
Leads convertidos
Listado de Leads

Visualización en tarjetas con información resumida:

Nombre del cliente
Tipo de propiedad
Ubicación
Fecha de contacto
Estado actual
Acciones rápidas
Detalle de Lead

Pantalla con toda la información del lead organizada en pestañas:

Información personal
Datos de la propiedad
Historial de comunicaciones
Notas y seguimiento
Formulario de Nuevo Lead

Interfaz de captura de datos con validación en tiempo real y progreso por pasos.

3.3 Material Design Components
Se implementa la biblioteca de Material Design 3 para mantener consistencia visual y experiencia de usuario actualizada.

4. Implementación de Módulos
4.1 Módulo de Autenticación
4.2 Módulo de Gestión de Leads
4.3 Módulo de Notificaciones
4.4 Módulo de Comunicaciones
5. Integración con el Backend
5.1 Configuración Retrofit
5.2 Implementación de Repositorios
5.3 Almacenamiento Local con Room
5.4 Trabajador en segundo plano para sincronización
6. Pruebas Unitarias
6.1 Pruebas de ViewModels
6.2 Pruebas de Casos de Uso
6.3 Pruebas de Repositorios
6.4 Pruebas de Integración
7. Generación de APK
7.1 Configuración del archivo build.gradle
7.2 Comandos para generar APK
Generar APK de debug
Generar APK de release firmada
Verificar APK generada
7.3 Proceso de firma de APK
Crear keystore para firma (una vez)
Configurar local.properties (para desarrollo local)
Configurar en CI/CD (para integración continua)
8. Documentación Técnica
8.1 Configuración del Entorno de Desarrollo
Requisitos previos
Android Studio (versión Arctic Fox o superior)
JDK 17
Kotlin 1.8.0+
Gradle 8.0+
Android SDK 34
Android Build Tools 34.0.0
Configuración del proyecto
Abrir en Android Studio
Abrir Android Studio
Seleccionar "Open an existing project"
Navegar hasta la carpeta del proyecto y seleccionarla
Ejecutar la aplicación
Conectar un dispositivo Android o usar el emulador
Seleccionar "Run 'app'" en Android Studio
8.2 Arquitectura Detallada
MVVM con Clean Architecture

Capa de Datos (Data Layer)

Implementaciones concretas de repositorios
Fuentes de datos: API y Base de datos local
Modelos de datos: DTOs y entidades de Room
Capa de Dominio (Domain Layer)

Entidades de negocio
Casos de uso: acciones que puede realizar el usuario
Interfaces de repositorios (contratos)
Capa de Presentación (Presentation Layer)

Activities y Fragments
ViewModels
States: modelos que representan el estado de la UI
Adapters: para RecyclerViews
8.3 Patrones de Diseño Aplicados
Repository Pattern

Para abstraer las fuentes de datos y proporcionar una API limpia
Factory Pattern

Para crear objetos complejos, especialmente en la inyección de dependencias
Observer Pattern

Implementado con Kotlin Flow para observar cambios en los datos
Adapter Pattern

Para adaptar datos a formatos específicos de UI en RecyclerViews
Strategy Pattern

Para implementar diferentes estrategias de comunicación
Builder Pattern

Para construcción de objetos complejos como solicitudes de red
8.4 Guía de Código
Convenciones de nomenclatura

Nombres de clases: PascalCase
Nombres de funciones y variables: camelCase
Constantes: SNAKE_CASE_CAPS
Archivos: Snake_case_caps para recursos, PascalCase para Kotlin
Estructura de paquetes

Las clases están organizadas por característica y luego por capa
Ejemplo: com.bogoker.mobile.auth.presentation
Guía de estilo

Seguimos las convenciones de codificación de Kotlin
Utilizamos ktlint para asegurar consistencia
Esta implementación de la aplicación móvil BOGOKER proporciona una solución completa y robusta para la gestión de leads inmobiliarios desde dispositivos Android, complementando perfectamente la versión web existente y mejorando la productividad de los asesores inmobiliarios al permitirles gestionar su trabajo desde cualquier lugar.

El código está cuidadosamente estructurado siguiendo los principios de Clean Architecture y MVVM, lo que facilita su mantenimiento, escalabilidad y la realización de pruebas unitarias.

La APK generada está optimizada para rendimiento y tamaño, asegurando una experiencia de usuario fluida incluso en dispositivos con recursos limitados.

Aplicación desarrollada por Rafael González
Fecha: 28 de abril de 2025