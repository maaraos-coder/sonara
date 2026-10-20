"""Detailed, auditable building-acoustics calculation paths for SONARA.

The module keeps the calculation layer independent from Streamlit.  It uses
measured spectra whenever they are available and exposes every path so that a
student can inspect the energetic sum.  Local application documents and the
official standards remain the authority for contractual work.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


THIRD_OCTAVE = np.array(
    [50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
     800, 1000, 1250, 1600, 2000, 2500, 3150], dtype=float,
)
OCTAVE = np.array([63, 125, 250, 500, 1000, 2000, 4000], dtype=float)
A_WEIGHTING_OCTAVE = np.array([-26.2, -16.1, -8.6, -3.2, 0.0, 1.2, 1.0])
THIRD_OCTAVE_A_WEIGHTING = np.array(
    [-30.2, -26.2, -22.5, -19.1, -16.1, -13.4, -10.9, -8.6, -6.6,
     -4.8, -3.2, -1.9, -0.8, 0.0, 0.6, 1.0, 1.2, 1.3, 1.2], dtype=float,
)
REFERENCE_AREA = 10.0
REFERENCE_LENGTH = 1.0
REFERENCE_POWER = 1e-12
AIR_DENSITY = 1.2
SPEED_OF_SOUND = 343.0


@dataclass(frozen=True)
class EngineMetadata:
    engine: str = "SONARA-ISO12354-RAIN-1"
    frequency_resolution: str = "tercio de octava"
    status: str = "prediccion de proyecto"


METADATA = EngineMetadata()


def _curve(values, frequencies, target):
    values = np.asarray(values, dtype=float)
    frequencies = np.asarray(frequencies, dtype=float)
    target = np.asarray(target, dtype=float)
    if values.size != frequencies.size or values.size < 2:
        raise ValueError("Cada espectro requiere frecuencias y valores compatibles.")
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(frequencies)):
        raise ValueError("Los espectros deben contener sólo valores finitos.")
    if np.any(np.diff(frequencies) <= 0.0):
        raise ValueError("Las frecuencias deben ser únicas y estrictamente crecientes.")
    return np.interp(target, frequencies, values)


def energetic_levels(levels):
    data = np.asarray(levels, dtype=float)
    if data.size == 0:
        raise ValueError("Se requiere al menos un camino acústico.")
    return 10.0 * np.log10(np.maximum(np.sum(10.0 ** (data / 10.0), axis=0), 1e-30))


def a_weighted_total(levels, weighting):
    levels = np.asarray(levels, dtype=float)
    weighting = np.asarray(weighting, dtype=float)
    if levels.shape != weighting.shape:
        raise ValueError("La ponderación A debe coincidir con el espectro.")
    return float(10.0 * np.log10(np.sum(10.0 ** ((levels + weighting) / 10.0))))


def energetic_reduction(paths):
    data = np.asarray(paths, dtype=float)
    if data.size == 0:
        raise ValueError("Se requiere al menos un camino acústico.")
    return -10.0 * np.log10(np.maximum(np.sum(10.0 ** (-data / 10.0), axis=0), 1e-30))


def junction_kij(junction_type, mass_i, mass_j, measured=None, elastic_improvement=0.0):
    """Return a transparent engineering estimate of the vibration index Kij.

    A measured Kij always has priority.  The analytical presets use the mass
    ratio M=log10(mj/mi); their purpose is to populate the detailed workflow
    when junction test data are unavailable.
    """
    if measured is not None:
        return float(measured)
    mi = max(float(mass_i), 0.1)
    mj = max(float(mass_j), 0.1)
    m = np.log10(mj / mi)
    label = str(junction_type).lower()
    if "independ" in label or "separada" in label or "doble estructura" in label:
        base = 25.0
    elif "elást" in label or "resilien" in label:
        base = 15.0 + 5.7 * m * m
    elif "semi-rígida" in label or "semi rígida" in label:
        base = 12.0 + 5.7 * m * m
    elif "rígida pesada" in label:
        base = 8.7 + 5.7 * m * m
    elif "rígida liviana" in label or "montante simple" in label:
        base = 5.7 + 5.7 * m * m
    elif "cruz" in label or "x" == label.strip():
        base = 8.7 + 5.7 * m * m
    elif "t" in label:
        base = 5.7 + 5.7 * m * m
    elif "esquina" in label or "l" == label.strip():
        base = 3.0 + 5.7 * m * m
    else:
        base = 5.0 + 5.7 * m * m
    return float(max(base + float(elastic_improvement), 0.0))


def airborne_path_reduction(curve_i, curve_j, kij, separating_area, junction_length,
                            delta_i=0.0, delta_j=0.0):
    geometry = 10.0 * np.log10(
        max(float(separating_area), 1e-9) /
        max(float(junction_length) * REFERENCE_LENGTH, 1e-9)
    )
    return (
        0.5 * (np.asarray(curve_i, dtype=float) + np.asarray(curve_j, dtype=float))
        + float(kij) + geometry + np.asarray(delta_i) + np.asarray(delta_j)
    )


def airborne_detailed(direct_curve, frequencies, separating_area, volume,
                      junctions=None, t0=0.5):
    """Detailed ISO 12354-1 path sum (Dd plus Df, Fd and Ff per junction)."""
    target = THIRD_OCTAVE.copy()
    direct = _curve(direct_curve, frequencies, target)
    paths = [{"name": "Dd", "curve": direct}]
    for index, junction in enumerate(junctions or [], start=1):
        if not junction.get("active", True):
            continue
        source = _curve(
            junction["source_curve"],
            junction.get("source_frequencies", junction.get("frequencies", frequencies)), target,
        )
        receiver = _curve(
            junction["receiver_curve"],
            junction.get("receiver_frequencies", junction.get("frequencies", frequencies)), target,
        )
        kij = junction_kij(
            junction.get("junction_type", "T"),
            junction.get("mass_source", 100.0),
            junction.get("mass_receiver", 100.0),
            measured=junction.get("kij"),
            elastic_improvement=junction.get("elastic_improvement", 0.0),
        )
        length = junction.get("length", 3.0)
        delta_source = junction.get("delta_source", 0.0)
        delta_receiver = junction.get("delta_receiver", 0.0)
        label = junction.get("name", f"Unión {index}")
        paths.extend([
            {"name": f"Df · {label}", "curve": airborne_path_reduction(
                direct, receiver, kij, separating_area, length, 0.0, delta_receiver)},
            {"name": f"Fd · {label}", "curve": airborne_path_reduction(
                source, direct, kij, separating_area, length, delta_source, 0.0)},
            {"name": f"Ff · {label}", "curve": airborne_path_reduction(
                source, receiver, kij, separating_area, length, delta_source, delta_receiver)},
        ])
    apparent = energetic_reduction([path["curve"] for path in paths])
    correction = 10.0 * np.log10(
        0.16 * max(float(volume), 1e-9) /
        (max(float(t0), 1e-9) * max(float(separating_area), 1e-9))
    )
    return {
        "metadata": METADATA,
        "frequencies": target,
        "paths": paths,
        "apparent_curve": apparent,
        "dnt_curve": apparent + correction,
        "geometry_correction": correction,
    }


def impact_flanking_curve(direct_level, r_source, r_receiver, kij,
                          separating_area, junction_length, delta_receiver=0.0):
    geometry = 10.0 * np.log10(
        max(float(separating_area), 1e-9) /
        max(float(junction_length) * REFERENCE_LENGTH, 1e-9)
    )
    return (
        np.asarray(direct_level, dtype=float)
        + 0.5 * (np.asarray(r_source, dtype=float) - np.asarray(r_receiver, dtype=float))
        - float(kij) - geometry - np.asarray(delta_receiver)
    )


def impact_detailed(base_level, frequencies, floor_improvement=None,
                    ceiling_improvement=None, separating_area=10.0,
                    receiver_t=0.5, junctions=None, t0=0.5):
    """ISO 12354-2 direct and structural flanking paths by frequency band."""
    target = THIRD_OCTAVE.copy()
    base = _curve(base_level, frequencies, target)
    floor_delta = np.zeros_like(target) if floor_improvement is None else _curve(
        floor_improvement, frequencies, target)
    ceiling_delta = np.zeros_like(target) if ceiling_improvement is None else _curve(
        ceiling_improvement, frequencies, target)
    direct = base - floor_delta - ceiling_delta
    paths = [{"name": "Directo", "curve": direct}]
    for index, junction in enumerate(junctions or [], start=1):
        if not junction.get("active", True):
            continue
        source_r = _curve(
            junction["source_curve"],
            junction.get("source_frequencies", junction.get("frequencies", frequencies)), target,
        )
        receiver_r = _curve(
            junction["receiver_curve"],
            junction.get("receiver_frequencies", junction.get("frequencies", frequencies)), target,
        )
        kij = junction_kij(
            junction.get("junction_type", "T"),
            junction.get("mass_source", 100.0),
            junction.get("mass_receiver", 100.0),
            measured=junction.get("kij"),
            elastic_improvement=junction.get("elastic_improvement", 0.0),
        )
        curve = impact_flanking_curve(
            direct, source_r, receiver_r, kij, separating_area,
            junction.get("length", 3.0), junction.get("delta_receiver", 0.0),
        )
        paths.append({"name": junction.get("name", f"Flanco {index}"), "curve": curve})
    total = energetic_levels([path["curve"] for path in paths])
    normalized = total - 10.0 * np.log10(
        max(float(receiver_t), 0.05) / max(float(t0), 0.05)
    )
    return {
        "metadata": METADATA,
        "frequencies": target,
        "paths": paths,
        "direct_curve": direct,
        "total_curve": total,
        "normalized_curve": normalized,
    }


def facade_detailed(large_elements, volume, facade_area, shape_correction=0.0,
                    small_elements=None, joints=None, exterior_level=None):
    """ISO 12354-3 facade sum including elements, Dn,e paths and joints."""
    target = THIRD_OCTAVE[3:].copy()
    area_total = max(float(facade_area), 1e-9)
    tau_terms = np.zeros_like(target)
    path_rows = []
    for element in large_elements or []:
        area = max(float(element.get("area", 0.0)), 0.0)
        curve = _curve(element["curve"], element.get("frequencies", target), target)
        equivalent = area / area_total * 10.0 ** (-curve / 10.0)
        tau_terms += equivalent
        path_rows.append({"name": element.get("name", "Elemento"), "kind": "Elemento", "curve": curve})
    for element in small_elements or []:
        dne = _curve(element["dne_curve"], element.get("frequencies", target), target)
        count = max(float(element.get("count", 1.0)), 0.0)
        tau_terms += count * REFERENCE_AREA / area_total * 10.0 ** (-dne / 10.0)
        path_rows.append({"name": element.get("name", "Elemento pequeño"), "kind": "Dn,e", "curve": dne})
    for joint in joints or []:
        rs = _curve(joint["rs_curve"], joint.get("frequencies", target), target)
        length = max(float(joint.get("length", 0.0)), 0.0)
        tau_terms += length * REFERENCE_LENGTH / area_total * 10.0 ** (-rs / 10.0)
        path_rows.append({"name": joint.get("name", "Junta"), "kind": "Junta", "curve": rs})
    if not np.any(tau_terms > 0.0):
        raise ValueError("La fachada requiere al menos una vía de transmisión activa.")
    apparent = -10.0 * np.log10(np.maximum(tau_terms, 1e-30))
    correction = 10.0 * np.log10(0.32 * max(float(volume), 1e-9) / area_total)
    d2mnt = apparent + float(shape_correction) + correction
    return {
        "metadata": METADATA,
        "frequencies": target,
        "paths": path_rows,
        "apparent_curve": apparent,
        "d2mnt_curve": d2mnt,
        "geometry_correction": correction,
        "interior_curve": None if exterior_level is None else _curve(
            exterior_level, target, target) - d2mnt,
    }


def service_equipment_detailed(paths, receiver_absorption, receiver_t=0.5, t0=0.5):
    """EN 12354-5 path framework for airborne, duct and structure-borne sources.

    Airborne and duct paths use sound power. Structure-borne paths use a
    source spectrum plus the measured/calculated installed transfer function
    to the receiving room. All paths are returned separately.
    """
    absorption = max(float(receiver_absorption), 0.01)
    contributions = []
    for index, path in enumerate(paths or [], start=1):
        kind = str(path.get("kind", "airborne_same_room"))
        source = _curve(path["source_curve"], path.get("frequencies", OCTAVE), OCTAVE)
        attenuation = _curve(
            path.get("attenuation_curve", np.zeros_like(OCTAVE)),
            path.get("frequencies", OCTAVE), OCTAVE,
        )
        if kind in {"airborne_same_room", "duct_outlet"}:
            distance = max(float(path.get("distance", 2.0)), 0.1)
            directivity = max(float(path.get("directivity", 2.0)), 0.01)
            transfer = 10.0 * np.log10(
                directivity / (4.0 * np.pi * distance * distance) + 4.0 / absorption
            )
            level = source + transfer - attenuation
        elif kind == "airborne_adjacent":
            reduction = _curve(path["reduction_curve"], path.get("frequencies", OCTAVE), OCTAVE)
            source_absorption = max(float(path.get("source_absorption", 20.0)), 0.01)
            separating_area = max(float(path.get("separating_area", 10.0)), 0.01)
            level = (
                source + 10.0 * np.log10(4.0 / source_absorption)
                - reduction + 10.0 * np.log10(separating_area / absorption)
                - attenuation
            )
        elif kind == "structure_borne":
            transfer = _curve(path["transfer_curve"], path.get("frequencies", OCTAVE), OCTAVE)
            level = source + transfer - attenuation
        else:
            raise ValueError(f"Tipo de camino de instalaciones no reconocido: {kind}")
        contributions.append({"name": path.get("name", f"Camino {index}"), "kind": kind, "curve": level})
    total = energetic_levels([item["curve"] for item in contributions])
    normalized = total - 10.0 * np.log10(
        max(float(receiver_t), 0.05) / max(float(t0), 0.05)
    )
    la = a_weighted_total(normalized, A_WEIGHTING_OCTAVE)
    return {
        "metadata": METADATA,
        "frequencies": OCTAVE.copy(),
        "paths": contributions,
        "total_curve": total,
        "normalized_curve": normalized,
        "la_normalized": la,
    }


def outdoor_sound_power_detailed(indoor_level, frequencies, elements,
                                 diffuse_field_correction=-6.0):
    """ISO 12354-4 indoor-to-outdoor sound power, resolved by element.

    Each element provides area and a reduction spectrum. Optional adaptation
    terms account for openings, mounting and directivity without hiding them in
    a single correction. The result is sound power radiated by the envelope.
    """
    target = THIRD_OCTAVE[3:].copy()
    lp = _curve(indoor_level, frequencies, target)
    paths = []
    for index, element in enumerate(elements or [], start=1):
        if not element.get("active", True):
            continue
        area = max(float(element.get("area", 0.0)), 0.0)
        if area <= 0.0:
            continue
        reduction = _curve(
            element["curve"], element.get("frequencies", frequencies), target
        )
        correction = float(element.get("correction", 0.0))
        directivity = float(element.get("directivity_correction", 0.0))
        lw = (
            lp + float(diffuse_field_correction) - reduction
            + 10.0 * np.log10(area / 1.0) + correction + directivity
        )
        paths.append({
            "name": element.get("name", f"Elemento {index}"),
            "area": area,
            "curve": lw,
        })
    if not paths:
        raise ValueError("Se requiere al menos un elemento exterior activo con área positiva.")
    total = energetic_levels([path["curve"] for path in paths])
    return {
        "metadata": METADATA,
        "frequencies": target,
        "paths": paths,
        "sound_power_curve": total,
        "lwa": a_weighted_total(total, np.interp(target, THIRD_OCTAVE, THIRD_OCTAVE_A_WEIGHTING)),
        "diffuse_field_correction": float(diffuse_field_correction),
    }


def room_absorption_detailed(volume, surfaces, method="sabine", air_absorption=None):
    """EN 12354-6 equivalent absorption area and reverberation time."""
    target = OCTAVE[1:].copy()  # 125--4000 Hz
    total_surface = 0.0
    equivalent = np.zeros_like(target)
    eyring_log = np.zeros_like(target)
    rows = []
    for index, surface in enumerate(surfaces or [], start=1):
        area = max(float(surface.get("area", 0.0)), 0.0)
        if area <= 0.0:
            continue
        alpha = np.clip(
            _curve(surface["alpha"], surface.get("frequencies", target), target),
            0.0, 0.999999,
        )
        total_surface += area
        equivalent += area * alpha
        eyring_log += area * np.log(np.maximum(1.0 - alpha, 1e-9))
        rows.append({"name": surface.get("name", f"Superficie {index}"), "area": area, "alpha": alpha})
    if total_surface <= 0.0:
        raise ValueError("La superficie total del recinto debe ser positiva.")
    if air_absorption is None:
        air = np.zeros_like(target)
    else:
        air = _curve(air_absorption, target, target)
    air_term = 4.0 * np.maximum(air, 0.0) * max(float(volume), 0.01)
    label = str(method).strip().lower()
    if label == "eyring":
        absorption = -eyring_log + air_term
    elif label == "sabine":
        absorption = equivalent + air_term
    else:
        raise ValueError("El método debe ser 'sabine' o 'eyring'.")
    reverberation = 0.161 * max(float(volume), 0.01) / np.maximum(absorption, 1e-9)
    return {
        "metadata": METADATA,
        "frequencies": target,
        "surfaces": rows,
        "equivalent_absorption": absorption,
        "reverberation_time": reverberation,
        "total_surface": total_surface,
        "method": label,
    }


RAIN_PRESETS = {
    "Moderada": {"intensity_mm_h": 4.0, "drop_diameter_mm": 1.0, "velocity_m_s": 4.5},
    "Intensa": {"intensity_mm_h": 15.0, "drop_diameter_mm": 2.0, "velocity_m_s": 6.5},
    "Fuerte": {"intensity_mm_h": 40.0, "drop_diameter_mm": 3.0, "velocity_m_s": 8.0},
    "Chaparrón": {"intensity_mm_h": 100.0, "drop_diameter_mm": 4.0, "velocity_m_s": 9.0},
}


def terminal_drop_velocity(diameter_mm):
    """Stable terminal-velocity approximation for 0.1--6 mm rain drops."""
    diameter = float(np.clip(diameter_mm, 0.1, 6.0))
    return float(9.65 - 10.3 * math.exp(-0.6 * diameter))


def rain_excitation(intensity_mm_h, drop_diameter_mm, velocity_m_s=None,
                    area_m2=1.0, slope_degrees=0.0):
    """TRain/TDrop equivalent: flow, drop rate and normal kinetic power."""
    intensity = max(float(intensity_mm_h), 0.0)
    diameter = float(np.clip(drop_diameter_mm, 0.1, 6.0)) * 1e-3
    velocity = terminal_drop_velocity(diameter * 1e3) if velocity_m_s is None else max(float(velocity_m_s), 0.1)
    projected_area = max(float(area_m2), 1e-6) * max(math.cos(math.radians(float(slope_degrees))), 0.05)
    water_flow = intensity * 1e-3 / 3600.0 * projected_area
    drop_volume = math.pi * diameter**3 / 6.0
    drop_mass = 1000.0 * drop_volume
    drops_per_second = water_flow / max(drop_volume, 1e-18)
    normal_velocity = velocity * max(math.cos(math.radians(float(slope_degrees))), 0.05)
    energy_per_drop = 0.5 * drop_mass * normal_velocity**2
    return {
        "intensity_mm_h": intensity,
        "drop_diameter_mm": diameter * 1e3,
        "velocity_m_s": velocity,
        "normal_velocity_m_s": normal_velocity,
        "projected_area_m2": projected_area,
        "drop_mass_kg": drop_mass,
        "drops_per_second": drops_per_second,
        "kinetic_power_w": energy_per_drop * drops_per_second,
    }


def _rain_force_weights(frequencies, contact_time, critical_frequency):
    omega = 2.0 * np.pi * np.asarray(frequencies, dtype=float)
    impulse = np.sinc(omega * float(contact_time) / (2.0 * np.pi)) ** 2
    radiation = np.clip(np.sqrt(np.asarray(frequencies) / max(float(critical_frequency), 1.0)), 0.02, 1.0)
    weights = np.maximum(impulse * radiation, 1e-12)
    return weights / np.sum(weights)


def rainfall_material_spectrum(density, thickness, youngs_modulus, poisson,
                               loss_factor, intensity_mm_h, slope_degrees=30.0,
                               roof_area=1.0, drop_diameter_mm=2.0,
                               velocity_m_s=None, edge_damping=0.0,
                               joist_spacing=0.6):
    """Research-mode plate response driven by the kinetic rain-energy flux.

    Extracted material properties drive mass, bending stiffness, coincidence
    and damping. The output is a prediction, never labelled as measured data.
    """
    rho = max(float(density), 1.0)
    h = max(float(thickness), 1e-5)
    e = max(float(youngs_modulus), 1e5)
    nu = float(np.clip(0.30 if poisson is None else poisson, 0.0, 0.49))
    eta = max(float(0.02 if loss_factor is None else loss_factor), 0.001)
    surface_mass = rho * h
    bending = e * h ** 3 / (12.0 * (1.0 - nu ** 2))
    critical = 343.0 ** 2 / (2.0 * np.pi) * np.sqrt(surface_mass / max(bending, 1e-20))
    excitation = rain_excitation(
        intensity_mm_h, drop_diameter_mm, velocity_m_s, roof_area, slope_degrees
    )
    contact_time = max(drop_diameter_mm * 1e-3 / excitation["normal_velocity_m_s"], 1e-5)
    weights = _rain_force_weights(THIRD_OCTAVE, contact_time, critical)
    span_factor = np.clip(float(joist_spacing) / 0.6, 0.25, 4.0)
    mass_control = 1.0 / (1.0 + (surface_mass / 12.0) ** 1.6)
    damping_total = eta + max(float(edge_damping), 0.0)
    damping_control = np.clip(np.sqrt(0.02 / damping_total), 0.15, 5.0)
    total_efficiency = np.clip(0.002 * mass_control * damping_control * span_factor, 1e-8, 0.05)
    band_power = np.maximum(excitation["kinetic_power_w"] * total_efficiency * weights, 1e-20)
    radiating_area = max(float(roof_area), 1e-9)
    intensity = band_power / radiating_area
    lw = 10.0 * np.log10(band_power / REFERENCE_POWER)
    li = 10.0 * np.log10(intensity / 1e-12)
    return {
        "metadata": METADATA,
        "frequencies": THIRD_OCTAVE.copy(),
        "li_curve": li,
        "sound_power_curve": lw,
        "radiated_band_power_w": band_power,
        "surface_mass": surface_mass,
        "bending_stiffness": bending,
        "critical_frequency": critical,
        "excitation": excitation,
        "kinetic_power": excitation["kinetic_power_w"],
        "acoustic_efficiency": total_efficiency,
        "calculation_trace": [
            "TRainCalcParameters", "TDrop/DropIteration", "TRain",
            "TRoof.calculateRain", "NearFieldDropsRadiation",
        ],
    }


def double_roof_rain_spectrum(outer_result, inner_density, inner_thickness,
                              cavity_depth, inner_youngs_modulus,
                              inner_poisson=0.30, inner_loss_factor=0.02,
                              cavity_absorption=0.0):
    """TRoofDoublePanel/two-port equivalent for a double rain roof.

    The outer-leaf rain intensity is transferred through the air spring and
    both plate impedances. It exposes the MAM resonance and the transfer curve
    used, allowing independent comparison with measured data.
    """
    freqs = np.asarray(outer_result["frequencies"], dtype=float)
    m1 = max(float(outer_result["surface_mass"]), 0.01)
    m2 = max(float(inner_density) * float(inner_thickness), 0.01)
    inner_poisson = float(np.clip(0.30 if inner_poisson is None else inner_poisson, 0.0, 0.49))
    inner_youngs_modulus = max(float(inner_youngs_modulus), 1e5)
    depth = max(float(cavity_depth), 0.005)
    f_mam = 1.0 / (2.0 * np.pi) * np.sqrt(
        AIR_DENSITY * SPEED_OF_SOUND**2 / depth * (1.0 / m1 + 1.0 / m2)
    )
    omega = 2.0 * np.pi * freqs
    air_stiffness = AIR_DENSITY * SPEED_OF_SOUND**2 / depth
    z1 = omega * m1
    z2 = omega * m2
    eta = max(float(inner_loss_factor), 0.001) + max(float(cavity_absorption), 0.0)
    resonance = 1.0 / np.sqrt((1.0 - (freqs / f_mam) ** 2) ** 2 + (2.0 * eta * freqs / f_mam) ** 2)
    impedance_transfer = air_stiffness / np.sqrt((z1 * z2) ** 2 + air_stiffness**2 * (z1 + z2) ** 2)
    transfer = np.clip(impedance_transfer * resonance * SPEED_OF_SOUND * AIR_DENSITY, 1e-8, 1.0)
    reduction = -10.0 * np.log10(transfer)
    inner_critical = SPEED_OF_SOUND**2 / (2.0 * np.pi) * np.sqrt(
        m2 / max(inner_youngs_modulus * inner_thickness**3 / (12.0 * (1.0 - inner_poisson**2)), 1e-20)
    )
    radiation = np.clip(np.sqrt(freqs / max(inner_critical, 1.0)), 0.03, 1.0)
    radiation_correction = 10.0 * np.log10(radiation)
    inner_li = np.asarray(outer_result["li_curve"], dtype=float) - reduction + radiation_correction
    inner_lw = np.asarray(outer_result["sound_power_curve"], dtype=float) - reduction + radiation_correction
    return {
        "metadata": METADATA,
        "frequencies": freqs,
        "li_curve": inner_li,
        "sound_power_curve": inner_lw,
        "outer_li_curve": np.asarray(outer_result["li_curve"], dtype=float),
        "transfer_reduction": reduction,
        "mam_frequency": float(f_mam),
        "inner_surface_mass": m2,
        "inner_critical_frequency": float(inner_critical),
        "calculation_trace": list(outer_result.get("calculation_trace", [])) + [
            "TRoofDoublePanel.InitRoof", "calcISPLTwoPort", "MAM correction",
        ],
    }


def rainfall_indoor_level(li_curve, frequencies, roof_area, volume,
                          reverberation_time, ceiling_reduction=None):
    """Convert measured or predicted rain intensity Li(f) to indoor Lp(f)."""
    target = THIRD_OCTAVE.copy()
    li = _curve(li_curve, frequencies, target)
    area = max(float(roof_area), 0.01)
    absorption = 0.16 * max(float(volume), 0.01) / max(float(reverberation_time), 0.05)
    ceiling = np.zeros_like(target) if ceiling_reduction is None else _curve(
        ceiling_reduction, frequencies, target)
    lp = li + 10.0 * np.log10(area) + 10.0 * np.log10(4.0 / absorption) - ceiling
    a_weight = THIRD_OCTAVE_A_WEIGHTING
    la = a_weighted_total(lp, a_weight)
    return {
        "metadata": METADATA,
        "frequencies": target,
        "li_curve": li,
        "lp_curve": lp,
        "la_indoor": la,
        "equivalent_absorption": absorption,
    }
