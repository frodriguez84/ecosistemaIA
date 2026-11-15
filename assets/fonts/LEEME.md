# Fuentes de las pantallas

Las usan el panel, los avisos y la pantalla final (spec
[Pantallas para ver aprender](../../docs/specs/active/PANTALLAS_VER_APRENDER.md), decisión 13):
Pixelify Sans para los títulos e Inter para el resto. Las carga `src/ui/fuentes.py`; si falta una,
`main.py` con ventana se corta al arrancar con el nombre del archivo.

Son TTF **estáticos**, un archivo por peso: pygame 2.6 no elige el peso de una fuente variable.

| Archivo | Familia y peso | Versión | De dónde salió |
|---------|----------------|---------|----------------|
| `pixelify-sans/PixelifySans-Bold.ttf` | Pixelify Sans Bold (700) | 1.000 | Repo de la autora, [eifetx/Pixelify-Sans](https://github.com/eifetx/Pixelify-Sans), `fonts/ttf/`, commit `39df74aba80df8157546034b878e8be1eb565ced` |
| `inter/Inter-Regular.ttf` | Inter Regular (400) | 4.001 (release v4.1) | [rsms/inter, release v4.1](https://github.com/rsms/inter/releases/tag/v4.1), `Inter-4.1.zip` → `extras/ttf/` |
| `inter/Inter-SemiBold.ttf` | Inter SemiBold (600) | 4.001 (release v4.1) | Ídem |
| `inter/Inter-Bold.ttf` | Inter Bold (700) | 4.001 (release v4.1) | Ídem |

Bajadas el 2026-11-15, sin modificar.

## Licencia

Las dos familias tienen la **SIL Open Font License 1.1**, cuyo texto está en el `OFL.txt` de cada
carpeta (el de Inter es su `LICENSE.txt`, con otro nombre). El código del proyecto es MIT
([LICENSE](../../LICENSE)); las fuentes, no.

## Qué caracteres tienen

A Pixelify Sans le falta la `→`: por eso ningún título la lleva. Inter tiene todos los de las
pantallas (`→`, `×`, `−`, `·`, `¡`, `ª` y las tildes). Lo verifica `tests/test_fuentes.py`.
