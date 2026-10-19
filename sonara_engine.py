"""Motor acústico físico principal de SONARA.

El módulo concentra las propiedades de placas, la predicción espectral de
aislamiento aéreo y las resonancias masa-aire-masa. Las expresiones que fueron
transcritas de forma cerrada se mantienen separadas de los auxiliares físicos
que todavía deberán contrastarse con casos de referencia.

Las funciones trabajan en unidades SI y no asignan clases de vivienda: esa
interpretación corresponde al alumno usando la norma aplicable.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

import numpy as np


C0 = 343.0
RHO0 = 1.2
Z0 = RHO0 * C0
ENGINE_ID = "SONARA-PHYSICS-1"


@dataclass(frozen=True)
class PlateProperties:
    surface_mass: float
    bending_stiffness: float
    loss_factor: float
    critical_frequency: float
    shear_stiffness: float


def plate_properties(
    density_kg_m3: float,
    thickness_m: float,
    youngs_modulus_pa: float,
    poisson_ratio: float,
    loss_factor: float = 0.0,
) -> PlateProperties:
    """Return the verified isotropic thin-plate properties in SI units."""
    rho = float(density_kg_m3)
    h = float(thickness_m)
    young = float(youngs_modulus_pa)
    nu = float(poisson_ratio)
    eta = max(float(loss_factor), 0.0)
    if rho <= 0 or h <= 0 or young <= 0:
        raise ValueError("Densidad, espesor y módulo de Young deben ser positivos.")
    if not -1.0 < nu < 0.5:
        raise ValueError("El coeficiente de Poisson debe estar entre -1 y 0,5.")
    mass = rho * h
    stiffness = young * h**3 / (12.0 * (1.0 - nu**2))
    critical = C0**2 / (2.0 * math.pi) * math.sqrt(mass / stiffness)
    # Rama isótropa identificada: G_s = E h / 3,64.
    shear = young * h / 3.64
    return PlateProperties(mass, stiffness, eta, critical, shear)


def combine_bonded_layers(layers: Sequence[dict]) -> PlateProperties:
    """Combine bonded layers using the equivalent plate used by SONARA.

    Each layer contains ``material`` and ``espesor`` in millimetres. A layer
    density override can be supplied as ``densidad``.
    """
    if not layers:
        raise ValueError("Se requiere al menos una capa.")
    props: list[PlateProperties] = []
    for layer in layers:
        material = layer["material"]
        thickness = max(float(layer.get("espesor", material.get("espesor", 0.0))) * 1e-3, 1e-9)
        density = layer.get("densidad")
        if density in (None, "", 0, 0.0):
            density = material.get("dens", 0.0)
        props.append(
            plate_properties(
                density,
                thickness,
                material.get("E", 0.0),
                material.get("poisson", 0.30),
                material.get("eta", 0.0),
            )
        )
    mass = float(sum(p.surface_mass for p in props))
    stiffness = float(sum(p.bending_stiffness for p in props))
    # Native resonant loss is mass weighted; retain that physical weighting.
    eta = float(sum(p.surface_mass * p.loss_factor for p in props) / mass)
    critical = C0**2 / (2.0 * math.pi) * math.sqrt(mass / stiffness)
    shear = float(sum(p.shear_stiffness for p in props))
    return PlateProperties(mass, stiffness, eta, critical, shear)


def non_resonant_tl(
    surface_mass: float,
    bending_stiffness: float,
    loss_factor: float,
    frequencies: Iterable[float],
    angle_limit_deg: float = 80.0,
    angle_points: int = 720,
) -> np.ndarray:
    """Diffuse-field non-resonant transmission from angular integration."""
    m = max(float(surface_mass), 1e-12)
    bending = max(float(bending_stiffness), 1e-18)
    eta = max(float(loss_factor), 0.0)
    theta = np.linspace(0.0, math.radians(float(angle_limit_deg)), max(int(angle_points), 64))
    sin_t = np.sin(theta)
    cos_t = np.cos(theta)
    result = []
    for frequency in np.asarray(list(frequencies), dtype=float):
        f = max(float(frequency), 1e-9)
        omega = 2.0 * math.pi * f
        impedance = omega * m * cos_t / (2.0 * Z0)
        bending_ratio = omega**2 * bending * sin_t**4 / (m * C0**4)
        denominator = (1.0 + eta * impedance * bending_ratio) ** 2
        denominator += (impedance * (1.0 - bending_ratio)) ** 2
        integral = float(np.trapezoid(cos_t * sin_t / denominator, theta))
        # Normalization for the 0--80 degree diffuse incidence interval.
        tau = max(2.0 * integral / max(math.sin(theta[-1]) ** 2, 1e-12), 1e-12)
        result.append(-10.0 * math.log10(tau))
    return np.asarray(result, dtype=float)


def radiation_efficiency(frequency_hz: float, critical_frequency_hz: float) -> float:
    """Finite-plate radiation helper used until comparative calibration.

    It is continuous, bounded and exposes the coincidence transition instead
    of hiding it in a fitted correction.
    """
    ratio = max(float(frequency_hz), 1e-9) / max(float(critical_frequency_hz), 1e-9)
    if ratio < 1.0:
        return max(0.02, min(1.0, math.sqrt(ratio)))
    return min(2.0, 1.0 + 0.15 * math.log10(max(ratio, 1.0)))


def modal_density(surface_mass: float, bending_stiffness: float, area_m2: float) -> float:
    """Asymptotic modal density of a thin rectangular plate (modes/Hz)."""
    area = max(float(area_m2), 1e-6)
    return max(area / (4.0 * math.pi) * math.sqrt(surface_mass / bending_stiffness), 1e-12)


def radiation_loss_factor(
    frequency_hz: float,
    surface_mass: float,
    sigma: float,
    regime_factor: float = 1.0,
) -> float:
    return (
        float(regime_factor)
        * Z0
        * float(sigma)
        / (2.0 * math.pi * float(frequency_hz) * float(surface_mass))
    )


def resonant_tl_2022(
    frequency_hz: float,
    plate: PlateProperties,
    panel_width_m: float = 3.0,
    panel_height_m: float = 2.4,
) -> float:
    """Closed resonant-path expression reconstructed for the 2022 branch."""
    f = max(float(frequency_hz), 1e-9)
    area = max(float(panel_width_m) * float(panel_height_m), 1e-6)
    sigma = radiation_efficiency(f, plate.critical_frequency)
    n_modal = modal_density(plate.surface_mass, plate.bending_stiffness, area)
    regime = 2.0 if f < plate.critical_frequency else 1.0
    eta_rad = radiation_loss_factor(f, plate.surface_mass, sigma, regime)
    eta_total = max(plate.loss_factor + 2.0 * eta_rad, 1e-9)
    impedance = 20.0 * math.log10(math.pi * f * plate.surface_mass / Z0)
    finite = 10.0 * math.log10(
        2.0 * eta_total * area * f / (sigma**2 * C0**2)
    )
    modal = 10.0 * math.log10(1.0 / n_modal)
    return impedance + finite + modal


def energetic_parallel_paths(*reductions_db: float) -> float:
    valid = [float(value) for value in reductions_db if math.isfinite(float(value))]
    if not valid:
        raise ValueError("Se requiere al menos un camino acústico finito.")
    return -10.0 * math.log10(sum(10.0 ** (-value / 10.0) for value in valid))


def shear_wave_correction(frequency_hz: float, plate: PlateProperties, thickness_m: float) -> float:
    q_s = float(thickness_m) ** 2 / (2.0 * math.pi) * math.sqrt(
        plate.surface_mass / plate.bending_stiffness
    )
    if q_s / 2.0 > frequency_hz:
        return 0.0
    return 10.0 * math.sqrt(q_s / (2.0 * max(float(frequency_hz), 1e-9)))


def single_leaf_tl(
    layers: Sequence[dict],
    frequencies: Iterable[float],
    panel_width_m: float = 3.0,
    panel_height_m: float = 2.4,
) -> tuple[np.ndarray, PlateProperties]:
    """Main SONARA airborne engine for a bonded single leaf."""
    freqs = np.asarray(list(frequencies), dtype=float)
    plate = combine_bonded_layers(layers)
    non_resonant = non_resonant_tl(
        plate.surface_mass, plate.bending_stiffness, plate.loss_factor, freqs
    )
    resonant = np.asarray(
        [resonant_tl_2022(f, plate, panel_width_m, panel_height_m) for f in freqs],
        dtype=float,
    )
    combined = np.asarray(
        [energetic_parallel_paths(nr, rr) for nr, rr in zip(non_resonant, resonant)],
        dtype=float,
    )
    thickness = sum(float(layer.get("espesor", 0.0)) for layer in layers) * 1e-3
    corrections = np.asarray([shear_wave_correction(f, plate, thickness) for f in freqs])
    return np.maximum(combined + corrections, 0.0), plate


def mam_resonance_frequencies(
    surface_masses: Sequence[float], cavity_depths_m: Sequence[float]
) -> np.ndarray:
    """Solve the generalized mass-air-mass eigenproblem for N leaves."""
    masses = np.asarray(surface_masses, dtype=float)
    depths = np.asarray(cavity_depths_m, dtype=float)
    if masses.ndim != 1 or masses.size < 2 or np.any(masses <= 0):
        raise ValueError("Se requieren al menos dos masas superficiales positivas.")
    if depths.size != masses.size - 1 or np.any(depths <= 0):
        raise ValueError("Debe existir una profundidad positiva por cavidad.")
    stiffness = np.zeros((masses.size, masses.size), dtype=float)
    for index, depth in enumerate(depths):
        spring = RHO0 * C0**2 / depth
        stiffness[index, index] += spring
        stiffness[index + 1, index + 1] += spring
        stiffness[index, index + 1] -= spring
        stiffness[index + 1, index] -= spring
    dynamic = np.diag(1.0 / np.sqrt(masses)) @ stiffness @ np.diag(1.0 / np.sqrt(masses))
    eigenvalues = np.linalg.eigvalsh(dynamic)
    positive = eigenvalues[eigenvalues > 1e-8]
    return np.sqrt(positive) / (2.0 * math.pi)


def double_leaf_tl(
    layers_left: Sequence[dict],
    layers_right: Sequence[dict],
    cavity_mm: float,
    frequencies: Iterable[float],
    configuration: str = "Montante simple",
    absorbent: str = "Sin absorbente",
    fastener_spacing_mm: float = 600.0,
) -> tuple[np.ndarray, PlateProperties, PlateProperties, np.ndarray, float]:
    """Main two-leaf prediction using the physical MAM resonance solver."""
    freqs = np.asarray(list(frequencies), dtype=float)
    left_tl, left = single_leaf_tl(layers_left, freqs)
    right_tl, right = single_leaf_tl(layers_right, freqs)
    depth = max(float(cavity_mm) * 1e-3, 1e-4)
    resonances = mam_resonance_frequencies(
        [left.surface_mass, right.surface_mass], [depth]
    )
    f0 = float(resonances[0])
    upper = C0 / (2.0 * math.pi * depth)
    absorbent_gain = {
        "Sin absorbente": 0.0,
        "Lana mineral 40 kg/m³": 1.5,
        "Lana mineral 60 kg/m³": 3.0,
        "Lana mineral 80 kg/m³": 4.5,
    }.get(absorbent, 0.0)
    frame_gain = {
        "Montante simple": -2.0,
        "Montantes independientes": 1.5,
        "Doble estructura": 3.0,
    }.get(configuration, 0.0)
    spacing_penalty = 0.0
    if configuration == "Montante simple":
        spacing_penalty = -max(0.0, 600.0 - float(fastener_spacing_mm)) / 300.0

    equivalent = PlateProperties(
        left.surface_mass + right.surface_mass,
        left.bending_stiffness + right.bending_stiffness,
        (left.loss_factor * left.surface_mass + right.loss_factor * right.surface_mass)
        / (left.surface_mass + right.surface_mass),
        min(left.critical_frequency, right.critical_frequency),
        left.shear_stiffness + right.shear_stiffness,
    )
    low = non_resonant_tl(
        equivalent.surface_mass,
        equivalent.bending_stiffness,
        equivalent.loss_factor,
        freqs,
    )
    result = np.empty_like(freqs)
    for index, frequency in enumerate(freqs):
        if frequency < f0:
            value = low[index]
        elif frequency < upper:
            value = left_tl[index] + right_tl[index] + 20.0 * math.log10(max(frequency * depth, 1e-12)) - 29.0
            value += absorbent_gain
        else:
            value = left_tl[index] + right_tl[index] + 6.0 + 0.35 * absorbent_gain
        # Broad physical dip around the first MAM mode.
        distance = math.log2(max(frequency, 1e-9) / f0)
        value -= 6.0 * math.exp(-0.5 * (distance / 0.35) ** 2)
        result[index] = value + frame_gain + spacing_penalty
    return np.maximum(result, 0.0), left, right, resonances, upper

