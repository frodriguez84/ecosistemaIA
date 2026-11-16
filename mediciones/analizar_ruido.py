"""El ruido del fitness: cuánto del ranking de una generación es del cerebro y cuánto es suerte, a partir
de los agentes_*.csv de medir_puerta.py con congelar=G (docs/qa/AnalisisQA.md#ruido-fitness).

Los episodios son las generaciones después de la G: los mismos cerebros (columna cerebro), con mapa,
lugar de nacimiento, rumbo y orden en la lista nuevos. Por corrida (una semilla) y en conjunto, por G:
- Spearman entre pares de episodios (promedio de los pares) e ICC(1) (ANOVA de una vía, el cerebro como
  grupo) del fitness, de sus términos y de la sensibilidad a la brújula y a la comida (el control
  positivo: es del cerebro). Y cuánto ruido mete cada término en puntos de fitness: el desvío dentro
  del cerebro (raíz de MSW).
- El pool (en_pool, con el desempate de evolve): de los que quedan en un episodio, qué fracción queda en
  otro (azar: la fracción del pool). La élite: si el mejor de un episodio es el mejor en otro, si queda
  en el pool, y su lugar mediano.
- Informativo: la correlación sensibilidad a la brújula ↔ fitness en un episodio (mediana) y con el
  promedio de los episodios; Spearman-Brown para 2, 3 y 5 evaluaciones; el orden en la lista contra el
  fitness; ICC(C,1) (sin lo que cambia de un episodio a otro para todos, que no cambia el ranking); los
  clones (mismo pesos_hash): qué parte de la varianza del fitness dentro de un episodio es entre clones,
  o sea suerte; y, como robustez, el Spearman del fitness con la G como un episodio más.

Uso: python mediciones/analizar_ruido.py SALIDA [SALIDA ...]
"""
import csv
import glob
import itertools
import os
import statistics as st
import sys

import numpy as np
from scipy.stats import spearmanr

VARIABLES = ("fitness", "f_comida", "f_acercarse", "f_supervivencia", "f_puzzle", "sens_brujula", "sens_comida")
CORTES = (0.3, 0.6)  # el criterio de lectura, fijado antes de medir


def valor(f, v):
    if v.startswith("sens_"):  # sumada por tick: el promedio por agente
        t = int(f["sens_ticks"] or 0)
        return float(f[v]) / t if t else np.nan
    return float(f[v])


def spearman(x, y):
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        return np.nan  # constante: sin ranking
    return spearmanr(x, y)[0]


def spearman_pares(m):
    pares = [spearman(m[:, i], m[:, j]) for i, j in itertools.combinations(range(m.shape[1]), 2)]
    return np.nan if all(np.isnan(pares)) else float(np.nanmean(pares))


def icc(m):
    """ICC(1), ICC(C,1) y MSW, con m de cerebros × episodios."""
    n, k = m.shape
    medias = m.mean(axis=1)
    msb = k * ((medias - m.mean()) ** 2).sum() / (n - 1)
    msw = ((m - medias[:, None]) ** 2).sum() / (n * (k - 1))
    icc1 = (msb - msw) / (msb + (k - 1) * msw) if msb + msw > 0 else np.nan
    resid = m - medias[:, None] - m.mean(axis=0)[None, :] + m.mean()
    mse = (resid ** 2).sum() / ((n - 1) * (k - 1))
    iccc = (msb - mse) / (msb + (k - 1) * mse) if msb + mse > 0 else np.nan
    return icc1, iccc, msw


def clones(filas_ep):
    """Parte de la varianza del fitness de un episodio que queda entre clones (suerte), y cuántos agentes
    tienen al menos un clon. None si no hay clones."""
    grupos = {}
    for f in filas_ep:
        grupos.setdefault(f["pesos_hash"], []).append(float(f["fitness"]))
    con_clon = [g for g in grupos.values() if len(g) > 1]
    if not con_clon:
        return None
    ss = sum(((np.array(g) - np.mean(g)) ** 2).sum() for g in con_clon)
    gl = sum(len(g) - 1 for g in con_clon)
    total = np.var([float(f["fitness"]) for f in filas_ep], ddof=1)
    return (ss / gl) / total, sum(len(g) for g in con_clon)


def analizar(ruta):
    filas = list(csv.DictReader(open(ruta, encoding="utf-8")))
    g0 = int(filas[0]["congelar"])
    por_gen = {}
    for f in filas:
        if int(f["generacion"]) >= g0:
            por_gen.setdefault(int(f["generacion"]), {})[int(f["cerebro"])] = f
    eps = sorted(g for g in por_gen if g > g0)
    cerebros = sorted(por_gen[g0])
    if any(sorted(por_gen[g]) != cerebros for g in eps):
        sys.exit(f"{ruta}: los episodios no tienen los mismos cerebros")
    r = dict(semilla=int(filas[0]["semilla"]), g0=g0, episodios=len(eps), n=len(cerebros),
             distintos=len({por_gen[g0][c]["pesos_hash"] for c in cerebros}))
    mat = {}
    for v in VARIABLES:
        m = np.array([[valor(por_gen[g][c], v) for g in eps] for c in cerebros])
        m = m[~np.isnan(m).any(axis=1)]
        mat[v] = m
        r[v + "_sp"] = spearman_pares(m)
        r[v + "_icc"], r[v + "_iccc"], msw = icc(m)
        r[v + "_ruido"] = float(np.sqrt(msw))
    con6 = np.array([[float(por_gen[g][c]["fitness"]) for g in [g0] + eps] for c in cerebros])
    r["fitness_sp_con_g"] = spearman_pares(con6)
    # El pool y la élite, con el desempate de evolve
    pool = {g: {c for c in cerebros if por_gen[g][c]["en_pool"] == "1"} for g in eps}
    r["pool"] = np.mean([len(pool[i] & pool[j]) / len(pool[i]) for i, j in itertools.combinations(eps, 2)])
    r["pool_azar"] = len(pool[eps[0]]) / len(cerebros)
    mejor = {g: next(c for c in cerebros if por_gen[g][c]["lugar"] == "1") for g in eps}
    lugares = [int(por_gen[j][mejor[i]]["lugar"]) for i, j in itertools.permutations(eps, 2)]
    r["elite_1"] = np.mean([x == 1 for x in lugares])
    r["elite_pool"] = np.mean([por_gen[j][mejor[i]]["en_pool"] == "1" for i, j in itertools.permutations(eps, 2)])
    r["elite_lugar"] = float(np.median(lugares))
    # Informativo
    fit, sens = mat["fitness"], mat["sens_brujula"]
    r["sens_fit_1"] = float(np.median([spearman(sens[:, e], fit[:, e]) for e in range(fit.shape[1])]))
    r["sens_fit_prom"] = spearman(sens.mean(axis=1), fit.mean(axis=1))
    r["orden_fit"] = np.mean([spearman(np.array([float(por_gen[g][c]["orden"]) for c in cerebros]),
                                       np.array([float(por_gen[g][c]["fitness"]) for c in cerebros])) for g in eps])
    cl = [clones(list(por_gen[g].values())) for g in eps]
    cl = [x for x in cl if x is not None]
    r["clones_suerte"] = float(np.mean([x[0] for x in cl])) if cl else np.nan
    r["clones_n"] = float(np.mean([x[1] for x in cl])) if cl else 0
    return r


def resumen(nombre, rs, clave):
    vals = [x[clave] for x in rs]
    if all(np.isnan(v) for v in vals):
        return f"{nombre:<48} —"
    pocos = " ".join(f"{v:+.3f}" for v in vals)
    desvio = np.nanstd(vals, ddof=1) if len(vals) > 1 else np.nan
    return f"{nombre:<48} {pocos} | prom {np.nanmean(vals):+.3f} desvío {desvio:.3f}"


def banda(x):
    return "< 0,3" if x < CORTES[0] else ("≥ 0,6" if x >= CORTES[1] else "0,3-0,6")


def main(carpetas):
    rutas = sorted({r for c in carpetas for r in glob.glob(os.path.join(c, "agentes_*congelar*.csv"))})
    por_g = {}
    for ruta in rutas:
        r = analizar(ruta)
        por_g.setdefault(r["g0"], []).append(r)
    for g0, rs in sorted(por_g.items()):
        rs.sort(key=lambda x: x["semilla"])
        print(f"\n=== Cerebros de la generación {g0}: {len(rs)} semillas ({', '.join(str(x['semilla']) for x in rs)}), "
              f"{rs[0]['episodios']} episodios, {rs[0]['n']} cerebros; distintos por peso: "
              f"{', '.join(str(x['distintos']) for x in rs)}")
        print("Por semilla, y promedio y desvío de las semillas")
        for v in VARIABLES:
            print(resumen(f"Spearman entre episodios, {v}", rs, v + "_sp"))
        for v in VARIABLES:
            print(resumen(f"ICC(1), {v}", rs, v + "_icc"))
        for v in VARIABLES:
            print(resumen(f"ICC(C,1), {v}", rs, v + "_iccc"))
        for v in VARIABLES[:5]:
            print(resumen(f"Ruido dentro del cerebro, {v}", rs, v + "_ruido"))
        print(resumen("Pool: se repite (azar abajo)", rs, "pool"))
        print(resumen("Pool: azar", rs, "pool_azar"))
        print(resumen("Élite: el mejor sigue primero", rs, "elite_1"))
        print(resumen("Élite: el mejor queda en el pool", rs, "elite_pool"))
        print(resumen("Élite: lugar mediano del mejor en otro episodio", rs, "elite_lugar"))
        print(resumen("Sensibilidad ↔ fitness, un episodio (mediana)", rs, "sens_fit_1"))
        print(resumen("Sensibilidad ↔ fitness, promedio de los episodios", rs, "sens_fit_prom"))
        print(resumen("Orden en la lista ↔ fitness", rs, "orden_fit"))
        print(resumen("Clones: suerte / varianza del episodio", rs, "clones_suerte"))
        print(resumen("Clones: agentes con al menos un clon", rs, "clones_n"))
        print(resumen("Robustez: Spearman del fitness con la G", rs, "fitness_sp_con_g"))
        sp = [x["fitness_sp"] for x in rs]
        prom = float(np.mean(sp))
        print(f"\nCriterio: Spearman del fitness, promedio {prom:.3f} ({banda(prom)}); por semilla: "
              + ", ".join(f"{x['semilla']}: {x['fitness_sp']:.3f} ({banda(x['fitness_sp'])})" for x in rs))
        positivo = sum(x["sens_brujula_sp"] > x["fitness_sp"] for x in rs)
        print(f"Control positivo: la sensibilidad a la brújula se repite más que el fitness en {positivo} de {len(rs)}")
        for k in (2, 3, 5):
            rk = k * prom / (1 + (k - 1) * prom)
            print(f"Spearman-Brown, {k} evaluaciones: {rk:.3f} (con el valor del cerebro, ~{np.sqrt(rk):.2f}; "
                  f"con una, ~{np.sqrt(prom):.2f})")


if __name__ == "__main__":
    main(sys.argv[1:] or ["."])
