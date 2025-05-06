# HL7 Forwarder

## Descripción

Esta aplicación web está diseñada para recibir, procesar y reenviar mensajes **HL7** a un **endpoint Mirth Connect** configurable. Además, proporciona trazabilidad de los mensajes, mostrando su estado y respuesta, y ofrece una interfaz de usuario (UI) donde se pueden ver los logs, configuraciones y estadísticas de los eventos.

La aplicación está construida en **Python (Flask)** y utiliza **Docker**. También está equipada con un frontend en **Bootstrap** y una API de backend para manejar los mensajes, configuraciones y logs.

## Características

- **Recepción de mensajes HL7** a través de la API `POST /hl7`.
- **Reenvío de mensajes a Mirth Connect**.
- **Trazabilidad de mensajes** guardada en una base de datos SQLite.
- **Visualización de logs, configuración y estadísticas** desde una interfaz web.
- **Configuración mTLS** para una conexión segura con Mirth Connect.
- **Dockerización** completa con soporte para Nginx.

## Requisitos mínimos

Docker Engine 24 o superior
Docker Compose v2 Incluido en Docker
Python ≥ 3.11

### Dependencias
El archivo `requirements.txt` incluye las dependencias necesarias para inicializar el proyecto.

## Configuración inicial paso a paso

### 1. Clonar y preparar el proyecto 

```bash
git clone 
cd hl7_forwarder
python -m venv venv         
source venv/bin/activate 
pip install -r requirements.txt

### 2. Inicializar el proyecto con Docker

```bash
docker-compose up --build # hl7_app en :8000  |  nginx TLS en :443