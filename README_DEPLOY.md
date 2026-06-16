# SONARA 1.0 Comercial — Deploy

## Estructura
- `app.py`: aplicación principal.
- `requirements.txt`: dependencias Python.
- `Dockerfile`: contenedor para despliegue comercial.
- `render.yaml`: blueprint para Render.
- `.streamlit/config.toml`: configuración de Streamlit.
- `data/`: archivos iniciales de usuarios/licencias/materiales/proyectos.

## Probar local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Probar con Docker
```bash
docker build -t sonara .
docker run -p 8501:8501 sonara
```

Abrir:
```text
http://localhost:8501
```

## Deploy comercial recomendado en Render
1. Crear cuenta en GitHub.
2. Crear repositorio `sonara`.
3. Subir todos estos archivos.
4. Crear cuenta en Render.
5. New > Web Service.
6. Conectar el repositorio GitHub.
7. Elegir Docker.
8. Deploy.

## Dominio .cl
En Render:
- Settings > Custom Domains.
- Agregar `sonaraapp.cl` o `www.sonaraapp.cl`.
- Render entregará registros DNS.
- Esos registros se agregan en NIC.cl o en el proveedor DNS.

## Importante para versión comercial real
La versión actual guarda usuarios/proyectos en archivos CSV/JSON dentro del servidor.
Para producción con muchos usuarios conviene migrar a:
- PostgreSQL para usuarios/proyectos.
- almacenamiento persistente o base de datos.
- integración de pago Stripe/Mercado Pago/Webpay.
