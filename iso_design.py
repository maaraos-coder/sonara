"""Pure acoustic-design helpers used by SONARA.

The functions in this module return projected acoustic quantities only.  They
deliberately do not assign ISO/TS 19488 classes: that interpretation belongs to
the student (or the acoustic consultant) using the official standard.
"""

from __future__ import annotations

import numpy as np


THIRD_OCTAVE_50_3150 = np.array(
    [50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
     800, 1000, 1250, 1600, 2000, 2500, 3150],
    dtype=float,
)
THIRD_OCTAVE_100_3150 = THIRD_OCTAVE_50_3150[3:]
OCTAVE_EQUIPMENT = np.array([63, 125, 250, 500, 1000, 2000, 4000], dtype=float)

# ISO 717-1 reference curve (one-third-octave bands, 100 Hz to 3150 Hz).
AIRBORNE_REFERENCE = np.array(
    [33, 36, 39, 42, 45, 48, 51, 52, 53, 54, 55, 56, 56, 56, 56, 56],
    dtype=float,
)

# ISO 717-2 reference curve (one-third-octave bands, 100 Hz to 3150 Hz).
IMPACT_REFERENCE = np.array(
    [62, 62, 62, 62, 62, 62, 61, 60, 59, 58, 57, 54, 51, 48, 45, 42],
    dtype=float,
)

# Normalized spectra used for ISO 717-1 spectrum-adaptation terms.  The first
# three entries extend the calculation down to 50 Hz.
SPECTRUM_C_50_3150 = np.array(
    [-40, -36, -33, -29, -26, -23, -21, -19, -17, -15,
     -13, -12, -11, -10, -9, -9, -9, -9, -9],
    dtype=float,
)
SPECTRUM_CTR_50_3150 = np.array(
    [-25, -23, -21, -20, -20, -18, -16, -15, -14, -13,
     -12, -11, -9, -8, -9, -10, -11, -13, -15],
    dtype=float,
)

A_WEIGHTING_OCTAVE = np.array([-26.2, -16.1, -8.6, -3.2, 0.0, 1.2, 1.0])


def energetic_sum_db(levels, axis=0):
    arr = np.asarray(levels, dtype=float)
    return 10.0 * np.log10(np.maximum(np.sum(10.0 ** (arr / 10.0), axis=axis), 1e-30))


def transmission_average_db(values):
    """Average sound-reduction values through their transmission factors."""
    arr = np.asarray(values, dtype=float)
    return -10.0 * np.log10(np.maximum(np.mean(10.0 ** (-arr / 10.0)), 1e-30))


def compare_predicted_measured(predicted_freqs, predicted_values, measured_freqs, measured_values):
    """Compare an airborne-insulation prediction with a measured spectrum.

    Measured points are retained only inside the predicted frequency range and
    the prediction is interpolated on those exact bands.  The function reports
    signed bias (prediction minus measurement), MAE and RMSE, plus the ISO
    717-1 single-number ratings when the measured data cover 100--3150 Hz.
    It intentionally does not decide compliance or assign a building class.
    """
    pf = np.asarray(predicted_freqs, dtype=float)
    pv = np.asarray(predicted_values, dtype=float)
    mf = np.asarray(measured_freqs, dtype=float)
    mv = np.asarray(measured_values, dtype=float)

    if pf.size != pv.size or mf.size != mv.size:
        raise ValueError("Frecuencias y valores deben tener la misma cantidad de datos.")
    if pf.size < 2 or mf.size < 1:
        raise ValueError("Se requieren al menos dos puntos predichos y un punto medido.")
    if not (np.all(np.isfinite(pf)) and np.all(np.isfinite(pv)) and
            np.all(np.isfinite(mf)) and np.all(np.isfinite(mv))):
        raise ValueError("Los datos de validación deben ser numéricos y finitos.")

    order_p = np.argsort(pf)
    order_m = np.argsort(mf)
    pf, pv = pf[order_p], pv[order_p]
    mf, mv = mf[order_m], mv[order_m]
    if np.any(np.diff(pf) <= 0) or np.any(np.diff(mf) <= 0):
        raise ValueError("Las frecuencias no pueden repetirse.")

    overlap = (mf >= pf[0]) & (mf <= pf[-1])
    if not np.any(overlap):
        raise ValueError("El ensayo y la predicción no comparten bandas de frecuencia.")
    mf, mv = mf[overlap], mv[overlap]
    aligned = np.interp(mf, pf, pv)
    residual = aligned - mv

    result = {
        "freqs": mf,
        "predicted": aligned,
        "measured": mv,
        "residual": residual,
        "bias": float(np.mean(residual)),
        "mae": float(np.mean(np.abs(residual))),
        "rmse": float(np.sqrt(np.mean(residual ** 2))),
        "max_abs_error": float(np.max(np.abs(residual))),
        "predicted_rw": None,
        "measured_rw": None,
        "delta_rw": None,
    }
    required = THIRD_OCTAVE_100_3150
    if mf[0] <= required[0] and mf[-1] >= required[-1]:
        predicted_rw, _, _ = airborne_rating(mf, aligned)
        measured_rw, _, _ = airborne_rating(mf, mv)
        result.update({
            "predicted_rw": predicted_rw,
            "measured_rw": measured_rw,
            "delta_rw": predicted_rw - measured_rw,
        })
    return result


def airborne_rating(freqs, values):
    """Return the ISO 717-1 weighted value and the shifted reference curve."""
    f = np.asarray(freqs, dtype=float)
    curve = np.interp(THIRD_OCTAVE_100_3150, f, np.asarray(values, dtype=float))
    # Search upward and retain the highest integer shift whose sum of
    # unfavourable deviations is not greater than 32 dB.
    best = None
    best_ref = None
    for rating in range(-20, 121):
        shifted = AIRBORNE_REFERENCE + (rating - 52.0)
        deviations = np.maximum(shifted - curve, 0.0)
        if float(np.sum(deviations)) <= 32.0 + 1e-9:
            best = rating
            best_ref = shifted
    if best is None:
        best = -20
        best_ref = AIRBORNE_REFERENCE + (best - 52.0)
    return int(best), THIRD_OCTAVE_100_3150.copy(), best_ref


def spectrum_adaptation_term(freqs, values, weighted_value, spectrum="C", low_frequency=False):
    f = np.asarray(freqs, dtype=float)
    values = np.asarray(values, dtype=float)
    start = 0 if low_frequency else 3
    target_freqs = THIRD_OCTAVE_50_3150[start:]
    if target_freqs[0] < float(np.min(f)):
        raise ValueError("La curva no contiene las bandas bajas necesarias (50, 63 y 80 Hz).")
    target = SPECTRUM_C_50_3150 if spectrum.upper() == "C" else SPECTRUM_CTR_50_3150
    target = target[start:]
    curve = np.interp(target_freqs, f, values)
    value = -10.0 * np.log10(np.sum(10.0 ** ((target - curve) / 10.0)))
    return int(round(value - float(weighted_value)))


def airborne_single_numbers(freqs, values):
    weighted, _, ref = airborne_rating(freqs, values)
    result = {
        "weighted": weighted,
        "c": spectrum_adaptation_term(freqs, values, weighted, "C", False),
        "ctr": spectrum_adaptation_term(freqs, values, weighted, "Ctr", False),
        "reference": ref,
    }
    if float(np.min(freqs)) <= 50.0:
        result["c50_3150"] = spectrum_adaptation_term(freqs, values, weighted, "C", True)
        result["ctr50_3150"] = spectrum_adaptation_term(freqs, values, weighted, "Ctr", True)
    else:
        result["c50_3150"] = None
        result["ctr50_3150"] = None
    return result


def dnt_from_apparent_curve(r_apparent, volume, separating_area, t0=0.5):
    """Convert apparent reduction index R' to standardized level difference.

    Using Sabine's relation, DnT = R' + 10 log10(0.16 V / (T0 S)).
    The measured reverberation time cancels because R' is already normalized to
    equivalent absorption area.
    """
    v = max(float(volume), 1e-9)
    s = max(float(separating_area), 1e-9)
    t0 = max(float(t0), 1e-9)
    correction = 10.0 * np.log10(0.16 * v / (t0 * s))
    return np.asarray(r_apparent, dtype=float) + correction


def impact_rating(freqs, levels):
    """ISO 717-2 one-third-octave rating plus CI and CI,50-2500."""
    f = np.asarray(freqs, dtype=float)
    levels = np.asarray(levels, dtype=float)
    curve = np.interp(THIRD_OCTAVE_100_3150, f, levels)
    best = None
    best_ref = None
    # For impact sound, unfavourable deviations are measured values above the
    # reference curve.  The selected reference value at 500 Hz is as low as
    # possible while keeping their sum no greater than 32 dB.
    for rating in range(120, -21, -1):
        shifted = IMPACT_REFERENCE + (rating - 60.0)
        deviations = np.maximum(curve - shifted, 0.0)
        if float(np.sum(deviations)) <= 32.0 + 1e-9:
            best = rating
            best_ref = shifted
    if best is None:
        best = 120
        best_ref = IMPACT_REFERENCE + (best - 60.0)

    mask = (f >= 100) & (f <= 2500)
    l_sum = float(energetic_sum_db(levels[mask], axis=0))
    ci = int(round(l_sum - 15.0 - best))
    ci50 = None
    if float(np.min(f)) <= 50.0:
        mask50 = (f >= 50) & (f <= 2500)
        l_sum50 = float(energetic_sum_db(levels[mask50], axis=0))
        ci50 = int(round(l_sum50 - 15.0 - best))
    return {"weighted": int(best), "ci": ci, "ci50_2500": ci50, "reference": best_ref}


def composite_single_number(parts, descriptor="rw"):
    """Area-weighted composite insulation from component single-number values."""
    if not parts:
        raise ValueError("Se requiere al menos un componente.")
    areas = np.array([max(float(p["area"]), 0.0) for p in parts], dtype=float)
    if float(np.sum(areas)) <= 0:
        raise ValueError("La superficie total debe ser mayor que cero.")
    vals = np.array([float(p[descriptor]) for p in parts], dtype=float)
    tau = np.sum(areas * 10.0 ** (-vals / 10.0)) / np.sum(areas)
    return float(-10.0 * np.log10(max(tau, 1e-30)))


def facade_single_numbers(parts, volume, facade_area, shape_correction=0.0, lden=None):
    """Simplified EN 12354-3 design estimate for a composite facade.

    Each part needs ``area``, ``rw`` and ``ctr``.  The output is the projected
    standardized A-weighted level difference for traffic noise.
    """
    ratr_parts = [dict(p, ratr=float(p["rw"]) + float(p.get("ctr", 0.0))) for p in parts]
    rw_comp = composite_single_number(parts, "rw")
    ratr_comp = composite_single_number(ratr_parts, "ratr")
    correction = 10.0 * np.log10(0.32 * max(float(volume), 1e-9) / max(float(facade_area), 1e-9))
    dnt_atr = ratr_comp + float(shape_correction) + correction
    return {
        "rw_composite": rw_comp,
        "ratr_composite": ratr_comp,
        "geometry_correction": correction,
        "dnt_a_tr": dnt_atr,
        "indoor_from_lden": None if lden is None else float(lden) - dnt_atr,
    }


def a_weighted_level(freqs, levels):
    curve = np.interp(OCTAVE_EQUIPMENT, np.asarray(freqs, dtype=float), np.asarray(levels, dtype=float))
    return float(energetic_sum_db(curve + A_WEIGHTING_OCTAVE, axis=0))


def service_equipment_airborne(
    lw_bands,
    distance,
    directivity,
    source_absorption,
    receiver_absorption,
    separating_area=None,
    reduction_bands=None,
    receiver_t=0.5,
    t0=0.5,
    extra_attenuation=None,
):
    """Educational EN 12354-5 airborne-path estimate by octave bands.

    If ``reduction_bands`` is omitted the source is in the receiving room.  If
    provided, a diffuse source room and transmission through a separating
    element are modelled.  Structural paths must be supplied separately and
    energetically added by the caller.
    """
    lw = np.asarray(lw_bands, dtype=float)
    if lw.size != OCTAVE_EQUIPMENT.size:
        raise ValueError("Se requieren siete bandas de octava entre 63 Hz y 4 kHz.")
    r = max(float(distance), 0.1)
    q = max(float(directivity), 0.01)
    a_src = max(float(source_absorption), 0.01)
    a_rec = max(float(receiver_absorption), 0.01)
    if reduction_bands is None:
        transfer = 10.0 * np.log10(q / (4.0 * np.pi * r * r) + 4.0 / a_rec)
        lp = lw + transfer
    else:
        red = np.asarray(reduction_bands, dtype=float)
        if red.size != lw.size:
            raise ValueError("La curva de aislamiento debe tener siete bandas.")
        s = max(float(separating_area or 0.0), 0.01)
        lp_source = lw + 10.0 * np.log10(4.0 / a_src)
        lp = lp_source - red + 10.0 * np.log10(s / a_rec)
    if extra_attenuation is not None:
        att = np.asarray(extra_attenuation, dtype=float)
        if att.size != lw.size:
            raise ValueError("La atenuación adicional debe tener siete bandas.")
        lp = lp - att
    normalized = lp - 10.0 * np.log10(max(float(receiver_t), 0.05) / max(float(t0), 0.05))
    return {
        "freqs": OCTAVE_EQUIPMENT.copy(),
        "lp": lp,
        "lp_normalized": normalized,
        "la_normalized": a_weighted_level(OCTAVE_EQUIPMENT, normalized),
    }


def reverberation_prediction(volume, floor_area, surfaces, object_absorption=None, method="Sabine"):
    """Predict octave-band equivalent absorption and reverberation time."""
    v = max(float(volume), 1e-9)
    sfloor = max(float(floor_area), 1e-9)
    if not surfaces:
        raise ValueError("Se requiere al menos una superficie.")
    total_surface = 0.0
    absorption = np.zeros(6, dtype=float)
    for item in surfaces:
        area = max(float(item["area"]), 0.0)
        alpha = np.clip(np.asarray(item["alpha"], dtype=float), 0.0, 0.999)
        if alpha.size != 6:
            raise ValueError("Cada material requiere seis coeficientes entre 125 Hz y 4 kHz.")
        total_surface += area
        absorption += area * alpha
    if object_absorption is not None:
        obj = np.asarray(object_absorption, dtype=float)
        if obj.size != 6:
            raise ValueError("La absorción de objetos requiere seis bandas.")
        absorption += np.maximum(obj, 0.0)
    if method.lower().startswith("eyring"):
        alpha_mean = np.clip(absorption / max(total_surface, 1e-9), 0.0, 0.999)
        equivalent = -total_surface * np.log(1.0 - alpha_mean)
        t = 0.161 * v / np.maximum(equivalent, 1e-9)
    else:
        equivalent = absorption
        t = 0.161 * v / np.maximum(absorption, 1e-9)
    bands = np.array([125, 250, 500, 1000, 2000, 4000], dtype=float)
    mid = (bands >= 250) & (bands <= 2000)
    return {
        "freqs": bands,
        "absorption": absorption,
        "equivalent_absorption": equivalent,
        "reverberation_time": t,
        "t_250_2000": float(np.mean(t[mid])),
        "a_over_sfloor_250_2000": float(np.mean(absorption[mid]) / sfloor),
    }
