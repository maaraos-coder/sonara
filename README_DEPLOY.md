# SONARA 1.0 Comercial — Deploy

## Estructura
- `app.py`: aplicación principal.
- `sonara_engine.py`: motor físico principal para placas y sistemas masa-aire-masa.
- `material_catalog.py`: acceso al catálogo acústico normalizado.
- `iso_design.py`: motor verificable de descriptores acústicos de proyecto.
- `data/acoustic_catalog.sqlite.xz.part-*`: catálogo completo de 3.646 registros,
  comprimido y reconstruido automáticamente al iniciar.
- `data/acoustic_materials.csv`: propiedades auditadas de materiales y vidrios.
- `tests/`: pruebas unitarias del motor, catálogo, descriptores y acceso Academy.
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

## Alcance acústico docente

La calculadora entrega valores proyectados de aislamiento aéreo, impacto,
fachada, ruido de instalaciones y reverberación. No asigna automáticamente
clases ISO/TS 19488:2021; la consulta de las tablas, clasificación y
justificación corresponden al estudiante.

`SONARA-PHYSICS-1` es el motor principal de ruido aéreo. Calcula propiedades
de placa isótropa, caminos resonante/no resonante y sistemas masa-aire-masa;
ISO 717 e ISO 12354 consumen las curvas obtenidas. Hasta completar el banco de
comparación, los resultados conservan carácter de proyecto y docencia.

Ejecutar las pruebas del motor con:

```bash
python -m unittest discover -s tests -v
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

### Acceso Academy del Diplomado

SONARA reconoce como `academy` indefinida toda cuenta creada con un correo
activo en `authorized_students` del Supabase del Diplomado. Configure en Render
estas variables privadas:

- `SONARA_ACADEMY_SUPABASE_URL`
- `SONARA_ACADEMY_SUPABASE_SERVICE_ROLE_KEY`

La clave debe ser `service_role`/`secret`, nunca `anon` ni `publishable`. Los
alumnos eligen su propia contraseña de SONARA; el RUT no se copia ni se usa
como contraseña. Una cuenta trial previa se convierte automáticamente en
Academy al volver a ingresar con el correo autorizado.

Las credenciales hash, el perfil y el tipo de licencia se guardan en la tabla
privada `sonara_accounts`, con RLS habilitado y sin permisos para `anon` ni
`authenticated`. Esto mantiene las cuentas entre reinicios aunque Render use
el plan gratuito. El SQL reproducible está en `supabase/sonara_accounts.sql`.

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
