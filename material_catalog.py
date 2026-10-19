"""Access to SONARA's normalized acoustic material catalogue."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import lzma
import os
from pathlib import Path
import sqlite3
import tempfile

import pandas as pd


ROOT = Path(__file__).resolve().parent
CATALOG_DB = ROOT / "data" / "acoustic_catalog.sqlite"
CATALOG_PART_PATTERN = "acoustic_catalog.sqlite.xz.part-*"
CATALOG_SHA256 = "c4c29e0c7104e002e33ef09f6d4ed14e7cf94c7f90dc30cb9961a15dc57cb9a9"
DERIVED_MATERIALS_CSV = ROOT / "data" / "acoustic_materials.csv"


def _catalog_parts() -> list[Path]:
    return sorted((ROOT / "data").glob(CATALOG_PART_PATTERN))


@lru_cache(maxsize=1)
def catalog_database_path() -> Path:
    """Return the SQLite path, reconstructing the versioned XZ parts if needed."""
    if CATALOG_DB.exists():
        return CATALOG_DB
    parts = _catalog_parts()
    if not parts:
        raise FileNotFoundError("No se encontró el catálogo acústico de SONARA.")
    runtime_dir = Path(tempfile.gettempdir()) / "sonara-acoustic-catalog"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    target = runtime_dir / "acoustic_catalog.sqlite"
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == CATALOG_SHA256:
        return target
    temporary = runtime_dir / "acoustic_catalog.sqlite.tmp"
    decompressor = lzma.LZMADecompressor()
    digest = hashlib.sha256()
    with temporary.open("wb") as output:
        for part in parts:
            decoded = decompressor.decompress(part.read_bytes())
            output.write(decoded)
            digest.update(decoded)
    if not decompressor.eof or digest.hexdigest() != CATALOG_SHA256:
        temporary.unlink(missing_ok=True)
        raise ValueError("El catálogo acústico no superó la verificación de integridad.")
    os.replace(temporary, target)
    return target


def catalog_available() -> bool:
    return (CATALOG_DB.exists() or bool(_catalog_parts())) and DERIVED_MATERIALS_CSV.exists()


@lru_cache(maxsize=1)
def derived_materials_dataframe() -> pd.DataFrame:
    if not DERIVED_MATERIALS_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(DERIVED_MATERIALS_CSV)


def _display_name(row: pd.Series) -> str:
    name = str(row.get("name", "")).strip() or "Material sin nombre"
    manufacturer = str(row.get("manufacturer", "")).strip()
    if manufacturer and manufacturer.lower() not in {"empty", "generic", "nan"}:
        return f"{name} · {manufacturer}"
    guid = str(row.get("guid", "")).strip("{}")
    return f"{name} · {guid[:8]}" if guid else name


@lru_cache(maxsize=1)
def calculation_materials() -> dict[str, dict]:
    """Return every isotropic material with complete calculation properties."""
    frame = derived_materials_dataframe()
    if frame.empty:
        return {}
    flags = frame["quality_flags"].fillna("").astype(str).str.strip()
    usable = frame[(frame["model_type"] == "Isotropic") & (flags == "")].copy()
    materials: dict[str, dict] = {}
    for _, row in usable.iterrows():
        label = _display_name(row)
        if label in materials:
            label = f"{label} · ID {int(row['entity_id'])}"
        is_glass = str(row.get("dataset")) == "Glazing"
        materials[label] = {
            "nombre": label,
            "nombre_catalogo": str(row.get("name", "")),
            "tipo": "vidrio" if is_glass else "placa",
            "grupo": "vidrio" if is_glass else "panel",
            "espesor": float(row["thickness_m"]) * 1000.0,
            "dens": float(row["density_kg_m3"]),
            "E": float(row["youngs_modulus_pa"]),
            "eta": float(row.get("loss_factor", 0.0) or 0.0),
            "poisson": float(row.get("poisson_ratio", 0.30)),
            "anisotropia": 1.0,
            "color": "#5DADE2" if is_glass else "#9CA3AF",
            "unidad": "m²",
            "precio": 0.0,
            "proveedor": str(row.get("manufacturer", "")),
            "activo": True,
            "catalog_entity_id": int(row["entity_id"]),
            "catalog_guid": str(row.get("guid", "")),
            "model_type": "Isotropic",
            "source": "SONARA acoustic catalogue",
        }
    return materials


def catalog_summary() -> pd.DataFrame:
    if not catalog_available():
        return pd.DataFrame(columns=["dataset", "records"])
    database = catalog_database_path()
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        return pd.read_sql_query(
            """
            SELECT dataset, COUNT(*) AS records
            FROM canonical_entities
            GROUP BY dataset
            ORDER BY dataset
            """,
            connection,
        )


def browse_catalog(
    dataset: str | None = None,
    search: str = "",
    chile_only: bool = False,
    limit: int = 2000,
) -> pd.DataFrame:
    """Browse canonical catalogue records without loading the entire database."""
    if not catalog_available():
        return pd.DataFrame()
    clauses = []
    params: list[object] = []
    if dataset and dataset != "Todos":
        clauses.append("e.dataset = ?")
        params.append(dataset)
    query = str(search or "").strip()
    if query:
        clauses.append("(e.name LIKE ? OR e.manufacturer LIKE ? OR e.model_type LIKE ?)")
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard])
    if chile_only:
        clauses.append(
            "EXISTS (SELECT 1 FROM regions r WHERE r.entity_id=e.entity_id "
            "AND lower(r.region)='chile' AND r.enabled=1)"
        )
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    sql = f"""
        SELECT e.entity_id, e.dataset, e.name, e.manufacturer, e.model_type,
               e.category, e.guid, e.remarks_technical
        FROM canonical_entities e
        {where}
        ORDER BY e.dataset, e.name
        LIMIT ?
    """
    params.append(max(1, min(int(limit), 5000)))
    database = catalog_database_path()
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        return pd.read_sql_query(sql, connection, params=params)

