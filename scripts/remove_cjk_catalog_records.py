#!/usr/bin/env python3
"""Remove catalogue records whose visible identity contains CJK characters."""

from __future__ import annotations

import csv
import hashlib
import lzma
import os
from pathlib import Path
import re
import sqlite3
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PART_GLOB = "acoustic_catalog.sqlite.xz.part-*"
MATERIALS_CSV = DATA_DIR / "acoustic_materials.csv"
PART_SIZE = 400_000
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
CHILD_TABLES = (
    "connection_properties",
    "fields",
    "floor_cover_properties",
    "layers",
    "profiles",
    "regions",
    "spectra",
)


def contains_cjk(value: object) -> bool:
    return bool(CJK.search(str(value or "")))


def reconstruct_database(target: Path) -> None:
    parts = sorted(DATA_DIR.glob(PART_GLOB))
    if not parts:
        raise FileNotFoundError("No se encontraron las partes del catálogo comprimido.")
    decoder = lzma.LZMADecompressor()
    with target.open("wb") as output:
        for part in parts:
            output.write(decoder.decompress(part.read_bytes()))
    if not decoder.eof:
        raise ValueError("El catálogo comprimido está incompleto.")


def delete_entities(database: Path) -> tuple[int, dict[str, int]]:
    with sqlite3.connect(database) as connection:
        rows = connection.execute(
            "SELECT entity_id, dataset, name, manufacturer FROM entities"
        ).fetchall()
        matches = [
            row for row in rows if contains_cjk(row[2]) or contains_cjk(row[3])
        ]
        identifiers = [int(row[0]) for row in matches]
        by_dataset: dict[str, int] = {}
        for _, dataset, _, _ in matches:
            by_dataset[str(dataset)] = by_dataset.get(str(dataset), 0) + 1

        for offset in range(0, len(identifiers), 800):
            batch = identifiers[offset : offset + 800]
            placeholders = ",".join("?" for _ in batch)
            for table in CHILD_TABLES:
                connection.execute(
                    f"DELETE FROM {table} WHERE entity_id IN ({placeholders})", batch
                )
            connection.execute(
                f"DELETE FROM entities WHERE entity_id IN ({placeholders})", batch
            )

        connection.execute(
            """
            UPDATE source_files
            SET record_count = (
                SELECT COUNT(*) FROM entities WHERE entities.source_id=source_files.source_id
            )
            """
        )
        connection.commit()
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise ValueError(f"El catálogo quedó con referencias inválidas: {violations[:3]}")
        connection.execute("VACUUM")
    return len(identifiers), by_dataset


def filter_materials_csv() -> int:
    with MATERIALS_CSV.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("El CSV de materiales no tiene encabezados.")
        rows = list(reader)
    kept = [
        row
        for row in rows
        if not contains_cjk(row.get("name"))
        and not contains_cjk(row.get("manufacturer"))
    ]
    temporary = MATERIALS_CSV.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)
    os.replace(temporary, MATERIALS_CSV)
    return len(rows) - len(kept)


def replace_compressed_parts(database: Path) -> tuple[str, int]:
    raw = database.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    compressed = lzma.compress(raw, format=lzma.FORMAT_XZ, preset=9)
    old_paths = sorted(
        path for path in DATA_DIR.glob(PART_GLOB) if not path.name.endswith(".new")
    )
    new_paths: list[Path] = []
    for index, offset in enumerate(range(0, len(compressed), PART_SIZE)):
        path = DATA_DIR / f"acoustic_catalog.sqlite.xz.part-{index:02d}.new"
        path.write_bytes(compressed[offset : offset + PART_SIZE])
        new_paths.append(path)
    for old_path in old_paths:
        old_path.unlink()
    for new_path in new_paths:
        os.replace(new_path, new_path.with_suffix(""))
    return digest, len(new_paths)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sonara-cjk-clean-") as folder:
        database = Path(folder) / "acoustic_catalog.sqlite"
        reconstruct_database(database)
        deleted, by_dataset = delete_entities(database)
        csv_deleted = filter_materials_csv()
        digest, part_count = replace_compressed_parts(database)
    print(f"deleted_entities={deleted}")
    print(f"deleted_by_dataset={by_dataset}")
    print(f"deleted_csv_rows={csv_deleted}")
    print(f"catalog_sha256={digest}")
    print(f"compressed_parts={part_count}")


if __name__ == "__main__":
    main()
