"""Comparación de alternativas mediante descriptores acústicos finales.

Este módulo no asigna clases normativas. El usuario introduce el objetivo que
corresponde a su encargo y SONARA compara las prestaciones calculadas.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


def _norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", text.lower().replace("′", "'").replace("₂", "2"))


ALIASES = {
    "rw": ("rw",),
    "rw_c": ("rwc", "ra"),
    "rw_ctr": ("rwctr", "ratr"),
    "dntw": ("dntw",),
    "dnt_a": ("dnta",),
    "dnt_atr": ("dntatr",),
    "lntw": ("lntw", "l'ntw"),
    "lnw": ("lnw",),
    "d2mntw": ("d2mntw",),
    "d2mnt_atr": ("d2mntatr", "d2mnta,tr"),
    "laeq_nt": ("laeq", "laeqnt", "laeqntproyectado"),
    "lafmax_nt": ("lafmax", "lafmaxnt", "lafmaxntproyectado"),
}


def canonical_descriptor(label: object) -> str:
    normalized = _norm(label)
    for key, aliases in ALIASES.items():
        if normalized == _norm(key) or any(normalized == _norm(alias) for alias in aliases):
            return key
    return normalized or "rw"


def descriptor_family(label: object) -> str:
    key = canonical_descriptor(label)
    if key.startswith("d2m"):
        return "Fachada"
    if key in {"lntw", "lnw"}:
        return "Impacto"
    if key.startswith("laeq") or key.startswith("lafmax"):
        return "Instalaciones"
    return "Aéreo"


def default_direction(label: object) -> str:
    return "<=" if descriptor_family(label) in {"Impacto", "Instalaciones"} else ">="


def descriptor_value(solution: dict, label: object):
    if not isinstance(solution, dict):
        return None
    key = canonical_descriptor(label)
    candidates = [key, *ALIASES.get(key, ())]
    containers = [solution]
    if isinstance(solution.get("descriptores"), dict):
        containers.append(solution["descriptores"])
    for container in containers:
        normalized = {_norm(k): v for k, v in container.items()}
        for candidate in candidates:
            value = normalized.get(_norm(candidate))
            if value not in (None, ""):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    pass
    # Los módulos de fachada e instalaciones guardan también un valor genérico.
    calc = _norm(solution.get("tipo_calculo", ""))
    if ((key.startswith("d2m") and "fachada" in calc)
            or ((key.startswith("laeq") or key.startswith("lafmax")) and "instalaciones" in calc)):
        try:
            return float(solution.get("valor"))
        except (TypeError, ValueError):
            return None
    return None


@dataclass(frozen=True)
class Evaluation:
    value: float
    target: float
    direction: str
    margin: float
    complies: bool


def evaluate(value: float, target: float, direction: str) -> Evaluation:
    direction = "<=" if str(direction).strip() == "<=" else ">="
    value, target = float(value), float(target)
    margin = target - value if direction == "<=" else value - target
    return Evaluation(value, target, direction, margin, margin >= -1e-9)


def rank_solutions(solutions, descriptor, target, direction=None, priority="Mayor desempeño"):
    direction = direction or default_direction(descriptor)
    rows = []
    for index, solution in enumerate(solutions or []):
        value = descriptor_value(solution, descriptor)
        if value is None:
            continue
        ev = evaluate(value, target, direction)
        rows.append({
            "index": index,
            "solution": solution,
            "name": solution.get("nombre", f"Alternativa {index + 1}"),
            "descriptor": canonical_descriptor(descriptor),
            "value": ev.value,
            "target": ev.target,
            "direction": ev.direction,
            "margin": ev.margin,
            "complies": ev.complies,
            "cost": float(solution.get("costo_estimado", solution.get("costo", 0)) or 0),
            "mass": float(solution.get("masa", 0) or 0),
            "thickness": float(solution.get("espesor", 0) or 0),
        })

    def key(row):
        compliance = 0 if row["complies"] else 1
        if priority == "Menor costo":
            return compliance, row["cost"], -row["margin"]
        if priority == "Menor espesor":
            return compliance, row["thickness"], -row["margin"]
        if priority == "Menor masa":
            return compliance, row["mass"], -row["margin"]
        return compliance, -row["margin"], row["cost"]

    return sorted(rows, key=key)
