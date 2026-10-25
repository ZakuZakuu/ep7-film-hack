"""Loopback-only, token-protected local studio; images stay in bounded RAM."""
from concurrent.futures import ThreadPoolExecutor
import copy
import io
import secrets
import threading
from urllib.parse import urlsplit
from flask import Flask, jsonify, request, Response, abort
from .images import read_image, resize, png_bytes
from .recipe import calibration, validate, vector, load_json
from .model import Model, raw_baseline
from .lut import read_cube, read_hald, apply_lut
from .fit import fit_pair, fit_reference


def create_app(cal=None):
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024
    app.config["STUDIO_TOKEN"] = secrets.token_urlsafe(32)
    cal = copy.deepcopy(cal or calibration())
    lock = threading.Lock()
    state = {"images": {}, "lut": None, "revision": 0, "job": None, "progress": {}}
    worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="local-recipe-fit")

    @app.before_request
    def local_only():
        # Prevent DNS rebinding and cross-origin uploads, including local websites.
        if request.host.split(":")[0] not in ("127.0.0.1", "localhost"):
            abort(403)
        if request.method != "GET":
            if not secrets.compare_digest(request.headers.get("X-Studio-Token", ""), app.config["STUDIO_TOKEN"]):
                abort(403)
            origin = request.headers.get("Origin")
            if origin and urlsplit(origin).netloc != request.host:
                abort(403)

    @app.after_request
    def private_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' blob:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
        return response

    @app.errorhandler(ValueError)
    @app.errorhandler(OSError)
    @app.errorhandler(RuntimeError)
    def invalid(error):
        # No tracebacks, file paths or EXIF in browser responses.
        return jsonify(error=str(error)), 400

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/config")
    def config():
        return jsonify(token=app.config["STUDIO_TOKEN"], calibration=cal)

    @app.post("/api/upload/<role>")
    def upload(role):
        if role not in ("base", "target", "reference", "lut") or "file" not in request.files:
            raise ValueError("请选择文件与有效角色")
        f = request.files["file"]
        data = f.read()
        if role == "lut":
            lut = read_cube(data.decode("utf-8-sig")) if f.filename.lower().endswith(".cube") else read_hald(io.BytesIO(data))
            with lock:
                state["lut"] = lut
                state["revision"] += 1
            return jsonify(result="LUT 已在本机内存中载入", size=lut["grid"].shape[0])
        rgb, info = read_image(data, name=f.filename, max_side=1024)
        if info["kind"] == "raw":
            rgb = raw_baseline(rgb, cal)
        with lock:
            state["images"][role] = (rgb, info)
            state["revision"] += 1
            revision = state["revision"]
        return jsonify(info=info, revision=revision)

    def base():
        with lock:
            if "base" not in state["images"]:
                raise ValueError("先载入基准照片")
            return state["images"]["base"][0]

    @app.get("/api/base.png")
    def base_png():
        return Response(png_bytes(resize(base(), 900)), mimetype="image/png")

    @app.post("/api/preview")
    def preview():
        recipe = validate(load_json(request.get_data(as_text=True)), cal)
        rgb = resize(base(), 900)
        return Response(png_bytes(Model(rgb, cal).apply(vector(recipe))), mimetype="image/png")

    @app.post("/api/validate")
    def validate_recipe():
        return jsonify(validate(load_json(request.get_data(as_text=True)), cal))

    @app.post("/api/fit")
    def start_fit():
        obj = load_json(request.get_data(as_text=True))
        if not isinstance(obj, dict) or obj.get("mode") not in ("target", "reference", "lut"):
            raise ValueError("请选择同场景、异场景或 LUT")
        initial = validate(obj.get("recipe"), cal)
        mode = obj["mode"]
        with lock:
            if state["job"] is not None and not state["job"].done():
                return jsonify(error="已有拟合在运行，请等待"), 409
            if "base" not in state["images"]:
                raise ValueError("先载入基准照片")
            rgb, base_info = state["images"]["base"]
            if mode == "lut":
                if state["lut"] is None:
                    raise ValueError("先载入 LUT")
                lut = state["lut"]
                target = apply_lut(rgb, lut)
            else:
                if mode not in state["images"]:
                    raise ValueError("先载入目标/参考照片")
                target, target_info = state["images"][mode]
                if mode == "target" and target_info["original_shape"] != base_info["original_shape"]:
                    raise ValueError("成对照片原始尺寸不同；请先配准，不能靠预览缩小掩盖差异")
            state["progress"] = {"status": "running", "evaluations": 0}
            revision = state["revision"]

            def progress(update):
                with lock:
                    state["progress"].update(update)

            def run():
                if mode == "reference":
                    result, report = fit_reference(rgb, target, cal, initial, progress=progress)
                else:
                    result, report = fit_pair(rgb, target, cal, initial, progress=progress)
                    report["mode"] = "lut" if mode == "lut" else "aligned-pair"
                report["source_decode"] = base_info
                if mode == "lut":
                    report["warnings"].append("LUT 必须以已显影 sRGB 为输入；不支持 Log/ACES/shaper 域")
                    if lut["clipped_values"]:
                        report["warnings"].append("LUT 具有超出显示域的值，已裁切")
                return {"status": "done", "recipe": result, "report": report, "revision": revision}

            state["job"] = worker.submit(run)
        return jsonify(status="running")

    @app.get("/api/fit")
    def fit_status():
        with lock:
            job = state["job"]
            if job is None:
                return jsonify(status="idle")
            if not job.done():
                return jsonify(state["progress"])
            try:
                result = job.result()
                result["stale_input"] = result["revision"] != state["revision"]
                return jsonify(result)
            except ValueError as e:
                return jsonify(status="error", error=str(e))
            except Exception:
                # Never expose private traceback/file details through the HTTP service.
                return jsonify(status="error", error="拟合失败；请检查图像、色区覆盖与对齐条件")

    return app
