"""
El boletín de la corrida (spec PANTALLAS_VER_APRENDER, decisiones 14 y 15): los datos de la pantalla
final, sin dibujar nada, y su texto para la consola. También el formato de los números (decisión 8)
y la escala de los gráficos (decisión 10), que usan las pantallas.

Sin pygame y sin azar: todo sale del registro de la corrida (src/analytics/registro.py).
"""

import math

from config import SimulationConfig
from .registro import PASOS, COLUMNAS_DE_PASOS

MENOS = "−"  # El signo menos, no el guion
RAYA = "—"   # Un cambio que no se puede medir: el valor de la generación 1 es 0

NOMBRES_DE_MODOS = {"guiado": "guiado", "autonomo": "autónomo"}
TITULOS_DE_HITOS = ("¡Primera llave roja!", "¡Primera puerta abierta!", "¡Primera llave dorada!",
                    "¡Puerta de hierro abierta!", "¡Cofre abierto!")

ULTIMAS = 5  # Los cuatro números comparan la generación 1 contra el promedio de las últimas 5
# Título, columna del CSV, decimales, cómo se mide el cambio, qué es, y si se alarga con la generación
CUATRO_NUMEROS = (
    ("FITNESS PROMEDIO", "fitness_prom", 1, "porcentaje", None, False),
    ("MANZANAS POR AGENTE", "manzanas_prom", 2, "veces", None, False),
    ("EDAD PROMEDIO", "edad_prom", 0, "porcentaje", "ticks vividos", True),
    ("RECORRIDO PROMEDIO", "distancia_prom", 0, "veces", "píxeles", True),
)

PIE_CON_EVOLUCION = ("¿Aprendieron de verdad? Se mide contra la línea base sin evolución: "
                     "python experimento.py")
PIE_LINEA_BASE = "Esta corrida es la línea base: cada generación arranca con cerebros al azar"


# --- Formato de los números (decisión 8) ---

def numero(valor, decimales=0):
    """31,2 · 2.220 · −3,5: coma decimal, punto de miles y el signo menos de verdad."""
    texto = f"{abs(valor):,.{decimales}f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    return (MENOS if round(valor, decimales) < 0 else "") + texto


def con_signo(valor, decimales=0):
    """+1,1 · −0,4: una diferencia, siempre con su signo."""
    return ("+" if round(valor, decimales) >= 0 else "") + numero(valor, decimales)


def porcentaje(valor):
    """+73 %: el cambio en porcentaje, entero y con espacio."""
    return f"{con_signo(valor)} %"


def veces(valor):
    """×1,9: cuántas veces el valor de la generación 1."""
    return f"×{numero(valor, 1)}"


def nombre_de_las_ayudas(acercarse, curriculo, deslizar=False):
    """Las ayudas prendidas: "acercarse", "currículo", "deslizar" o varias con " + "; "" si ninguna
    (spec PUZZLE_APRENDIBLE, decisión 11). El panel las pone en un renglón propio."""
    ayudas = (("acercarse", acercarse), ("currículo", curriculo), ("deslizar", deslizar))
    return " + ".join(nombre for nombre, prendida in ayudas if prendida)


def nombre_del_modo(modo, acercarse, curriculo=False, deslizar=False):
    """El modo, y las ayudas prendidas: "autónomo + acercarse + currículo". Lo usa el encabezado del
    boletín."""
    nombre = NOMBRES_DE_MODOS.get(modo, modo)
    ayudas = nombre_de_las_ayudas(acercarse, curriculo, deslizar)
    return f"{nombre} + {ayudas}" if ayudas else nombre


def minutos_simulados(ticks_totales):
    """Los ticks de todas las generaciones, a 60 por segundo, en minutos (DIAG-15)."""
    return ticks_totales / 60 / 60


# --- Escala de los gráficos (decisión 10) ---

_BASES = (1, 2, 2.5, 5)
_DIVISIONES = 5
_TOLERANCIA = 1e-9  # 0,1 + 0,2 da 0,30000000000000004: sin tolerancia, el eje subiría un paso de más


def escala(*series):
    """El eje de un gráfico: (inferior, superior, paso). Las series comparten eje.

    El paso es el más chico de la forma {1; 2; 2,5; 5} × 10ᵏ que cubre de mín(0, mínimo) a
    máx(0, máximo) en 5 divisiones o menos. Si todo vale 0, el eje va de 0 a 1.
    """
    valores = [valor for serie in series for valor in serie]
    bajo, alto = min([0.0, *valores]), max([0.0, *valores])
    if bajo == alto:
        return 0.0, 1.0, 0.2
    exponente = math.floor(math.log10((alto - bajo) / _DIVISIONES)) - 1
    while True:
        for base in _BASES:
            paso = base * 10.0 ** exponente
            abajo = math.floor(bajo / paso + _TOLERANCIA)
            arriba = math.ceil(alto / paso - _TOLERANCIA)
            if arriba - abajo <= _DIVISIONES:
                return round(abajo * paso, 10), round(arriba * paso, 10), round(paso, 10)
        exponente += 1


# --- El boletín (decisiones 14 y 15) ---

def linea_de_hito(hito):
    """La línea de consola de un hito (decisión 5)."""
    return (f"🏆 {TITULOS_DE_HITOS[hito['paso'] - 1]} Agente {hito['agente']}, generación "
            f"{hito['generacion']}, segundo {hito['tick'] / 60:.1f}")


def _primera_generacion(historia, paso, columna):
    """La primera generación en que algún agente dio ese paso, o None (decisión 4). Una generación que
    nació con el paso dado no cuenta (spec PUZZLE_APRENDIBLE, decisión 10)."""
    return next((fila["generacion"] for fila in historia
                 if fila[columna] > 0 and fila["etapa_inicial"] < paso), None)


def _cuatro_numeros(historia):
    """Fitness, manzanas, edad y recorrido: la generación 1 contra el promedio de las últimas K."""
    primera = historia[0]
    cantidad = min(ULTIMAS, len(historia) - 1)
    ultimas = historia[-cantidad:] if cantidad else []
    se_alargan = any(fila["ticks_max"] > primera["ticks_max"] for fila in ultimas)
    desde = "gen 1 → gen 2" if cantidad == 1 else f"gen 1 → promedio de las últimas {cantidad}"

    numeros = []
    for titulo, columna, decimales, medida, que_es, crece_con_el_tiempo in CUATRO_NUMEROS:
        inicio = primera[columna]
        if not ultimas:
            numeros.append({"titulo": titulo, "valor": numero(inicio, decimales), "cambio": None,
                            "sube": None, "nota": "una sola generación"})
            continue
        final = sum(fila[columna] for fila in ultimas) / cantidad
        if inicio == 0:
            cambio = RAYA
        elif medida == "porcentaje":
            cambio = porcentaje((final - inicio) / inicio * 100)
        else:
            cambio = veces(final / inicio)
        sube = None if inicio == 0 or final == inicio else final > inicio
        nota = [que_es] if que_es else []
        nota.append(desde)
        if crece_con_el_tiempo and se_alargan:
            nota.append("sube también porque las generaciones se alargan")
        numeros.append({"titulo": titulo,
                        "valor": f"{numero(inicio, decimales)} → {numero(final, decimales)}",
                        "cambio": cambio, "sube": sube, "nota": "; ".join(nota)})
    return numeros


def armar_boletin(registro):
    """Los datos del boletín, como textos listos para mostrar. Espera al menos una generación terminada."""
    historia = registro.historia
    primera, ultima = historia[0], historia[-1]
    generaciones = len(historia)
    evolucion = bool(primera["evolucion"])
    poblacion = SimulationConfig.POPULATION_SIZE

    minutos = minutos_simulados(sum(fila["ticks"] for fila in historia))
    # Deslizar no va en el CSV: se lee del switch, que main() pisa con --deslizar
    modo = nombre_del_modo(primera['modo'], primera['acercarse'], primera['etapa_inicial'] > 0,
                           SimulationConfig.DESLIZAR)
    subtitulo = " · ".join([
        f"Modo {modo}",
        "con evolución" if evolucion else "sin evolución (línea base)",
        f"semilla {primera['semilla']}",
        f"{generaciones} generación" if generaciones == 1 else f"{generaciones} generaciones",
        f"{numero(minutos, 1)} min simulados",
    ])

    # El embudo: cuántos de la última generación llegaron a cada paso, y la primera vez en la corrida
    embudo = []
    for paso, (nombre, columna) in enumerate(zip(PASOS, COLUMNAS_DE_PASOS), start=1):
        agentes, primera_vez = ultima[columna], _primera_generacion(historia, paso, columna)
        if primera_vez is not None:
            texto = f"{agentes} de {poblacion} · 1ª vez: gen {primera_vez}"
        elif agentes:  # Nadie lo dio, pero la última generación nació con él: la llave del currículo
            texto = f"{agentes} de {poblacion} · dada al nacer"
        else:
            texto = "nadie, en ninguna generación"
        embudo.append({"paso": paso, "nombre": nombre.capitalize(), "agentes": agentes,
                       "fraccion": agentes / poblacion, "primera_vez": primera_vez, "texto": texto})

    alcanzados = [fila for fila in embudo if fila["primera_vez"] is not None]
    hasta_donde = PASOS[alcanzados[-1]["paso"] - 1] if alcanzados else "nadie agarró la llave roja"

    # La única frase sobre el cofre (decisión 14 a)
    primera_vez_cofre = embudo[-1]["primera_vez"]
    if primera_vez_cofre is None:
        cofre = "el cofre no se abrió"
    else:
        # Cada agente abre el cofre una sola vez: la suma de la columna es cuántos lo abrieron
        abrieron = sum(fila["agentes_cofre"] for fila in historia)
        quienes = "lo abrió 1 agente" if abrieron == 1 else f"lo abrieron {abrieron} agentes"
        cofre = f"el cofre se abrió por primera vez en la generación {primera_vez_cofre}; {quienes} en la corrida"

    murieron_todos = None
    if ultima["vivos"] == 0:
        murieron_todos = (f"La generación {ultima['generacion']} terminó en el tick "
                          f"{numero(ultima['ticks'])} de {numero(ultima['ticks_max'])}: murieron todos")

    mejor = registro.mejor
    manzanas = "1 manzana" if mejor["manzanas"] == 1 else f"{numero(mejor['manzanas'])} manzanas"
    # Hasta dónde llegó él: lo que se le dio al nacer no cuenta (spec PUZZLE_APRENDIBLE, decisión 10)
    if mejor["etapa"] > mejor["etapa_inicial"]:
        llego_a = PASOS[mejor["etapa"] - 1]
    elif mejor["etapa_inicial"]:
        llego_a = f"ningún paso (nació con la {PASOS[mejor['etapa_inicial'] - 1]})"
    else:
        llego_a = "ningún paso del puzzle"

    mapas = [registro.calor_gen1] + ([registro.calor_ultima] if generaciones > 1 else [])

    return {
        "titulo": "Corrida terminada",
        "subtitulo": subtitulo,
        "hasta_donde": hasta_donde,
        "cofre": cofre,
        "numeros": _cuatro_numeros(historia),
        "embudo": embudo,
        "murieron_todos": murieron_todos,
        "mejor": {
            "id": mejor["id"],
            "titulo": f"#{mejor['id']} · generación {mejor['generacion']}",
            "renglones": [f"Fitness {numero(mejor['fitness'], 1)}",
                          f"{manzanas} · {numero(mejor['recorrido'])} px de recorrido",
                          f"vivió {numero(mejor['ticks_vividos'])} ticks",
                          f"llegó a: {llego_a}"],
        },
        "mapas": [{"generacion": mapa["generacion"],
                   "texto": f"Generación {mapa['generacion']} · {numero(registro.cobertura(mapa))} % del mapa"}
                  for mapa in mapas],
        "pie": PIE_CON_EVOLUCION if evolucion else PIE_LINEA_BASE,
    }


def texto_de_consola(boletin):
    """El boletín en texto, para el log de la corrida (decisión 15)."""
    renglones = [
        f"📋 {boletin['titulo']}",
        boletin["subtitulo"],
        f"Hasta dónde llegaron: {boletin['hasta_donde']} · {boletin['cofre']}",
        "",
    ]
    for dato in boletin["numeros"]:
        cambio = f" ({dato['cambio']})" if dato["cambio"] else ""
        renglones.append(f"{dato['titulo'].capitalize()}: {dato['valor']}{cambio} · {dato['nota']}")
    renglones += ["", "Puzzle, cuántos llegaron a cada paso en la última generación:"]
    renglones += [f"  {fila['nombre']}: {fila['texto']}" for fila in boletin["embudo"]]
    if boletin["murieron_todos"]:
        renglones.append(boletin["murieron_todos"])
    mejor = boletin["mejor"]
    renglones += [
        "",
        f"Mejor agente de la corrida: {mejor['titulo']}",
        "  " + " · ".join(mejor["renglones"]),
        "",
        "Por dónde caminaron: " + "; ".join(mapa["texto"] for mapa in boletin["mapas"]),
        "",
        boletin["pie"],
    ]
    return "\n".join(renglones)
