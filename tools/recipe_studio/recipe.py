"""Strict, versioned interchange in wheel order, with no device addresses."""
import copy
import json
import math
from pathlib import Path

FORMAT = "ep7-film-recipe-v1"
SECTORS = ("yellow", "orange", "red", "rose", "magenta", "violet",
           "blue", "azure", "cyan", "teal", "green", "lime")


def load_json(text):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError(f"重复 JSON 字段：{key}")
            obj[key] = value
        return obj

    def invalid(value):
        raise ValueError(f"非法 JSON 数字：{value}")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def neutral(name="新配方"):
    return {"format": FORMAT, "name": name, "description": "",
            "settings": {"hue": [0] * 12, "saturation": [0] * 12,
                         "lightness": [0] * 12,
                         "tone": {"shadows": 0, "midtones": 0, "highlights": 0},
                         "shading": 0},
            "recommendations": {"white_balance": "", "wb_shift": "",
                                "exposure_compensation": ""}}


def integer(value, limit, label):
    if type(value) is not int or not -limit <= value <= limit:
        raise ValueError(f"{label} 必须是 {-limit}…{limit} 的整数")


def validate(recipe, calibration):
    expected = set(neutral())
    if not isinstance(recipe, dict) or set(recipe) != expected or recipe["format"] != FORMAT:
        raise ValueError(f"需要完整的 {FORMAT}；拒绝未知、缺失或旧版本字段")
    for key in ("name", "description"):
        if not isinstance(recipe[key], str) or len(recipe[key]) > 2000:
            raise ValueError(f"{key} 必须是最多 2000 字符的文字")
    if not recipe["name"].strip():
        raise ValueError("配方名称不能为空")
    settings = recipe["settings"]
    if not isinstance(settings, dict) or set(settings) != set(neutral()["settings"]):
        raise ValueError("settings 必须完整且不能包含未知字段")
    for axis in ("hue", "saturation", "lightness"):
        values = settings[axis]
        if not isinstance(values, list) or len(values) != 12:
            raise ValueError(f"{axis} 必须有 12 项，按轮盘顺序排列")
        for value in values:
            integer(value, calibration["limits"][axis], axis)
    tone = settings["tone"]
    if not isinstance(tone, dict) or set(tone) != {"shadows", "midtones", "highlights"}:
        raise ValueError("tone 必须包含 shadows、midtones、highlights")
    for key, value in tone.items():
        integer(value, calibration["limits"]["tone"], key)
    integer(settings["shading"], calibration["limits"]["shading"], "shading")
    rec = recipe["recommendations"]
    if (not isinstance(rec, dict) or set(rec) != set(neutral()["recommendations"]) or
            any(not isinstance(v, str) or len(v) > 2000 for v in rec.values())):
        raise ValueError("recommendations 只允许完整的三个文字建议字段")
    return copy.deepcopy(recipe)


def calibration(path=None):
    default = load_json(Path(__file__).with_name("calibration.json").read_text())
    if path is None:
        return default
    obj = load_json(Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or set(obj) != set(default):
        raise ValueError("校准文件字段不完整或未知")
    if obj["format"] != default["format"] or obj["space"] != default["space"]:
        raise ValueError("不支持的校准格式或色彩空间")
    if obj["status"] not in ("uncalibrated", "locally-fitted"):
        raise ValueError("未知的校准状态")
    if (not isinstance(obj["id"], str) or not 1 <= len(obj["id"]) <= 200 or
            not isinstance(obj["provenance"], dict) or set(obj["provenance"]) != set(default["provenance"]) or
            any(not isinstance(v, str) for v in obj["provenance"].values())):
        raise ValueError("校准标识和来源必须为文字")
    for key, value in default.items():
        if type(value) in (int, float) or isinstance(value, list):
            vals = obj[key] if isinstance(value, list) else [obj[key]]
            if isinstance(value, list) and (not isinstance(vals, list) or len(vals) != len(value)):
                raise ValueError(f"校准数组长度错误：{key}")
            if any(type(v) not in (int, float) or not math.isfinite(v) for v in vals):
                raise ValueError(f"校准数值必须有限：{key}")
    if (not isinstance(obj["limits"], dict) or set(obj["limits"]) != set(default["limits"]) or
            obj["limits"] != {**default["limits"], "saturation": obj["limits"].get("saturation")} or
            type(obj["limits"]["saturation"]) is not int or obj["limits"]["saturation"] not in (5, 7)):
        raise ValueError("仅允许把 saturation 范围从 5 配置到 7；其他范围固定")
    if (not 30 <= obj["sector_width_degrees"] <= 90 or
            not 0.001 <= obj["neutral_chroma_threshold"] <= 1 or
            not 0.01 <= obj["shading_extent"] <= 4 or
            not 0 <= obj["shading_start"] <= 1 or
            not 0 <= obj["shading_gain"] <= 1 or
            not 0.2 <= obj["raw_gamma"] <= 5 or
            any(not 0.1 <= g <= 5 for g in obj["raw_rgb_gain"])):
        raise ValueError("校准几何、增益或 gamma 超出安全范围")
    for key, lo, hi in (("hue_degrees_per_step", -15, -0.01),
                        ("saturation_log_gain_per_step", 0.001, 0.5),
                        ("lightness_gain", 0.01, 3), ("tone_gain_per_step", 0.001, 0.1)):
        if not lo <= obj[key] <= hi:
            raise ValueError(f"校准增益范围错误：{key}")
    if (len(set(obj["sector_centers_degrees"])) != 12 or
            any(not 0 <= x < 360 for x in obj["sector_centers_degrees"]) or
            obj["lightness_native"][7] != 0 or
            any(not -1000 <= x <= 1000 for x in obj["lightness_native"]) or
            any(b <= a for a, b in zip(obj["lightness_native"], obj["lightness_native"][1:])) or
            obj["shading_coordinate_words"][0] != 0 or
            any(not 1 <= x <= 2048 for x in obj["shading_coordinate_words"][1:])):
        raise ValueError("色区、L 换算或暗角坐标错误")
    for key in ("quality_mean_delta_e", "quality_p95_delta_e"):
        if not 0 < obj[key][0] < obj[key][1] <= 100:
            raise ValueError("质量阈值必须正值递增")
    return obj


def vector(recipe):
    s = recipe["settings"]
    return (s["hue"] + s["saturation"] + s["lightness"] +
            [s["tone"][k] for k in ("shadows", "midtones", "highlights")] + [s["shading"]])


def from_vector(values, template=None, rounded=True):
    obj = copy.deepcopy(template or neutral())
    v = [int(round(float(x))) if rounded else float(x) for x in values]
    obj["settings"] = {"hue": v[:12], "saturation": v[12:24], "lightness": v[24:36],
                       "tone": dict(zip(("shadows", "midtones", "highlights"), v[36:39])),
                       "shading": v[39]}
    return obj
