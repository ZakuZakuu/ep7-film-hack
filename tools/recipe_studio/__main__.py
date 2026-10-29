"""python -m tools.recipe_studio: local-only preview, fit and calibration."""
import argparse
import json
import os
from pathlib import Path
from .recipe import calibration, load_json, neutral, validate, vector
from .images import read_image, png_bytes, private_output
from .model import raw_baseline
from .backend import Model, backend_status
from .lut import read_cube, read_hald, apply_lut
from .fit import fit_pair, fit_reference


def write_json(path, obj):
    private_output(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main(argv=None):
    p = argparse.ArgumentParser(description="E-P7 本地配方预览 / 拟合，不连接相机")
    p.add_argument("--model", choices=("workspace", "approximate"), help="优先 Workspace HSL 或显式近似后备")
    p.add_argument("--workspace-qualification", help="本机原生验证生成的私有资格 JSON")
    p.add_argument("--calibration", help="本地校准文件；默认未校准模型")
    commands = p.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="仅监听 127.0.0.1 的浏览器界面")
    serve.add_argument("--port", type=int, default=8765)
    preview = commands.add_parser("preview")
    preview.add_argument("source")
    preview.add_argument("recipe")
    preview.add_argument("--output", required=True)
    fit = commands.add_parser("fit")
    fit.add_argument("source", nargs="?")
    fit.add_argument("--photo", help="LUT-only 可选照片颜色与对比图")
    group = fit.add_mutually_exclusive_group(required=True)
    group.add_argument("--target", help="已对齐的同场景目标照片")
    group.add_argument("--reference", help="不同场景参考，仅匹配分布")
    group.add_argument("--lut", help="sRGB 3D .cube 或 Hald PNG/TIFF")
    fit.add_argument("--initial", help="初始配方 JSON")
    fit.add_argument("--output", required=True)
    fit.add_argument("--report", required=True)
    fit.add_argument("--max-nfev", type=int, default=100)
    fit.add_argument("--samples", type=int, default=768)
    calibrate = commands.add_parser("calibrate", help="仅校准近似后备的效果增益与 RAW 基线")
    calibrate.add_argument("--pairs", required=True)
    calibrate.add_argument("--output", required=True)
    calibrate.add_argument("--report", required=True)
    calibrate.add_argument("--max-nfev", type=int, default=80)
    args = p.parse_args(argv)
    try:
        if args.model: os.environ["EP7_RECIPE_MODEL"] = args.model
        if args.workspace_qualification: os.environ["EP7_WORKSPACE_QUALIFICATION"] = args.workspace_qualification
        cal = calibration(args.calibration)
        if args.command == "serve":
            from .server import create_app
            if not 1024 <= args.port <= 65535:
                raise ValueError("端口需为 1024…65535")
            print(f"本地预览：http://127.0.0.1:{args.port} （无相机连接、无外部上传）", flush=True)
            print(backend_status()["label"], flush=True)
            create_app(cal).run(host="127.0.0.1", port=args.port, debug=False, threaded=True)
            return
        if args.command == "calibrate":
            from .calibrate import calibrate as calibrate_pairs
            updated, report = calibrate_pairs(args.pairs, cal, args.max_nfev)
            write_json(args.output, updated)
            write_json(args.report, report)
        elif args.command == "fit" and args.lut and args.source is None:
            from .lut_fit import fit_lut, wb_apply
            lut = read_cube(Path(args.lut).read_text(encoding="utf-8-sig")) if Path(args.lut).suffix.lower() == ".cube" else read_hald(args.lut)
            photo = None
            if args.photo:
                photo, photo_info = read_image(args.photo, max_side=1024)
                if photo_info["kind"] == "raw": photo = raw_baseline(photo, cal)
            initial = validate(load_json(Path(args.initial).read_text(encoding="utf-8")),cal) if args.initial else None
            recipe, report = fit_lut(lut,cal,photo,initial,args.max_nfev,args.samples)
            write_json(args.output,recipe)
            write_json(args.report,report)
            if photo is not None:
                import numpy as np
                predicted = wb_apply(Model(photo,cal).apply(vector(recipe)),report["wb_shift"])
                comparison = np.concatenate((photo,apply_lut(photo,lut),predicted),axis=1)
                private_output(str(Path(args.output).with_suffix(".compare.png"))).write_bytes(png_bytes(comparison))
        else:
            if not args.source: raise ValueError("此模式需要基准照片；仅 LUT 可省略")
            if getattr(args,"photo",None): raise ValueError("--photo 仅用于不带 source 的 LUT 拟合")
            base, info = read_image(args.source, max_side=1600 if args.command == "preview" else 1024)
            if info["kind"] == "raw":
                base = raw_baseline(base, cal)
            if args.command == "preview":
                recipe = validate(load_json(Path(args.recipe).read_text(encoding="utf-8")), cal)
                private_output(args.output).write_bytes(png_bytes(Model(base, cal).apply(vector(recipe))))
                info["model"] = backend_status()
                print(json.dumps(info, ensure_ascii=False))
                return
            from .images import resize
            initial = validate(load_json(Path(args.initial).read_text(encoding="utf-8")), cal) if args.initial else neutral()
            # Validate alignment at full dimensions, then fit a display-size proxy.
            if args.target:
                target, ti = read_image(args.target, max_side=1024)
                if ti["kind"] == "raw":
                    target = raw_baseline(target, cal)
                if ti["original_shape"] != info["original_shape"] or target.shape != base.shape:
                    raise ValueError("成对图像尺寸不同；请先在本地配准")
                base, target = resize(base, 1024), resize(target, 1024)
            elif args.lut:
                base = resize(base, 1024)
                lut = read_cube(Path(args.lut).read_text(encoding="utf-8-sig")) if Path(args.lut).suffix.lower() == ".cube" else read_hald(args.lut)
                target = apply_lut(base, lut)
            else:
                target, ti = read_image(args.reference, max_side=1024)
                if ti["kind"] == "raw":
                    target = raw_baseline(target, cal)
                base = resize(base, 1024)
            if args.reference:
                recipe, report = fit_reference(base, target, cal, initial, args.max_nfev)
            else:
                recipe, report = fit_pair(base, target, cal, initial, args.max_nfev, args.samples)
                report["mode"] = "lut" if args.lut else "aligned-pair"
            if args.lut:
                report["warnings"].append("LUT 按已显影 sRGB 使用；Log/ACES/厂商专用输入域不受支持")
                if lut["clipped_values"]:
                    report["warnings"].append("LUT 含 0…1 外输出，已裁切到显示域")
            report["source_decode"] = info
            write_json(args.output, recipe)
            write_json(args.report, report)
        print(json.dumps({"result": "完成", "output": args.output, "report": args.report}, ensure_ascii=False))
    except (ValueError, OSError, RuntimeError) as e:
        p.exit(2, f"错误：{e}\n")


if __name__ == "__main__":
    main()
