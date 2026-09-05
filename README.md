# VERDI · Control de Estacionamientos

Aplicación para registrar entradas, salidas y retornos de vehículos en el acceso del Edificio VERDI.

## Flujo operativo
- **Vehículos dentro:** lista viva con botón `SALIÓ` de un toque.
- **Salieron recientemente:** panel desplegable con botón `ENTRÓ` de un toque para registrar retornos sin volver a escribir la placa.
- Los movimientos pueden intercalarse libremente: A sale, B sale, A entra, C sale, B entra, etc.
- Búsqueda por placa o departamento.
- Placa normalizada automáticamente a seis caracteres alfanuméricos con formato `ABC-123`.
- Una placa nueva puede registrarse y marcarse como `ENTRÓ` en el mismo paso.
- Cada permanencia conserva su entrada y salida; un retorno genera una nueva permanencia.
- Bicicletas: siempre asociadas a un Dpto., con cochera opcional.
- Cocheras alquiladas: responsable externo sin Dpto.; se identifica por número de cochera y nivel de sótano.

## Infraestructura
147 espacios: S1 1–43, S2 44–89, S3 90–136, S4 137–147.

La asignación exacta de cada cochera a cada Dpto. queda pendiente de la relación oficial de la administración; el sistema no inventa asignaciones.
