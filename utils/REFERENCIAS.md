# Configuración de Rutas

Este archivo documenta cómo obtener las rutas locales de los ejecutables.

## Windows

### PuTTY

**Ubicación por defecto:**
```
C:\Program Files\PuTTY\putty.exe
```

**Cómo encontrar la ruta exacta:**
1. Abrir Explorador de archivos
2. Navegar a `C:\Program Files\PuTTY\`
3. Verificar que `putty.exe` existe
4. Copiar la ruta completa

**Si PuTTY está en otra ubicación:**
- Buscar en: `C:\Program Files (x86)\PuTTY\`
- O buscar en: `%LOCALAPPDATA%\Programs\PuTTY\`

### MobaXterm

**Ubicación por defecto:**
```
C:\Program Files (x86)\Mobatek\MobaXterm\MobaXterm.exe
```

### Finding Executables

En PowerShell, buscar ejecutables:
```powershell
Get-ChildItem -Path "C:\" -Filter "putty.exe" -Recurse -ErrorAction SilentlyContinue
```

## Linux

### PuTTY
```bash
which putty
# Typical: /usr/bin/putty
```

### screen/tio
```bash
which screen
which tio
```

## macOS

### PuTTY (via Homebrew)
```bash
which putty
# Typical: /usr/local/bin/putty
```

---

## Crear config.ini

Copiar `config.example.ini` a `config.ini` y ajustar las rutas:

```ini
[putty]
path = TU_RUTA_A_PUTTY_EXE

[mobaxterm]
path = TU_RUTA_A_MOBAXTERM_EXE
```

---

**Nota:** El archivo `config.ini` NO está incluido en el repositorio git (está en .gitignore) para proteger rutas locales.