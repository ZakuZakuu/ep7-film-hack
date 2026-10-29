"""Original fixed-point reconstruction of the qualified Workspace HSL stage.

Vendor data is read at runtime, never shipped. Evidence: Acacia DLL 1.0.3.1 from Workspace 2.3.0.22;
shared table identity reference fishcu/oly_fw_analysis@539fcf1 HSL_TABLES.md.
"""

import hashlib
from pathlib import Path
import struct
from .workspace_polar import PolarKernel


def clamp(v, lo, hi):
    return min(hi, max(lo, v))


def truncdiv(v, d):
    return v // d if v >= 0 else -((-v) // d)


def signed7(v):
    return (v & 127) - (128 if v & 64 else 0)


class WorkspaceHSL:
    def __init__(self, path, expected_sha256):
        data = Path(path).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected_sha256:
            raise ValueError("Workspace DLL fingerprint mismatch")
        pe = struct.unpack_from("<I", data, 60)[0]
        if (
            data[:2] != b"MZ"
            or data[pe : pe + 4] != b"PE\0\0"
            or struct.unpack_from("<H", data, pe + 4)[0] != 0x8664
        ):
            raise ValueError("expected qualified x64 PE")
        count = struct.unpack_from("<H", data, pe + 6)[0]
        section = pe + 24 + struct.unpack_from("<H", data, pe + 20)[0]

        def read(rva, size):
            for i in range(count):
                _, start, rawsize, offset = struct.unpack_from(
                    "<IIII", data, section + 40 * i + 8
                )
                delta = rva - start
                if 0 <= delta and delta + size <= rawsize:
                    return data[offset + delta : offset + delta + size]
            raise ValueError("unmapped vendor data range")

        table = read(0xD8380, 3028)
        if (
            hashlib.sha256(table).hexdigest()
            != "a33d64bdb78ac41ba24ccbff820380f563211a095ac08a12a7c37a51b5c00531"
        ):
            raise ValueError("COLOR table identity mismatch")
        self.records = [table[i * 28 : (i + 1) * 28] for i in range(12)]
        self.mask = struct.unpack_from("<H", table, 3024)[0]
        self.polar = PolarKernel.from_dll(path, expected_sha256)
        self.trig = struct.unpack("<16Q", read(0xD6570, 128))
        self.hue = struct.unpack("<15h", read(0xD2FAE - 14, 30))
        self.light = struct.unpack("<15h", read(0xC739E - 14, 30))
        self.constants = {
            r: struct.unpack("<d", read(r, 8))[0] for r in range(0xDCA88, 0xDCB58, 8)
        }
        # Packed streams contain signed seven-bit bases and slopes. These
        # source/destination offsets are qualified by native unpacker xrefs.
        streams = [
            (0x1490, 4, [0x1F14, 0x1F74, 0x1FD4, 0x2034]),
            (0x19D0, 4, [0x2454, 0x24B4, 0x2514, 0x2574]),
            (0x1610, 4, [0x2214, 0x2274, 0x22D4, 0x2334]),
            (0x1790, 2, [0x2154, 0x21B4]),
            (0x1B50, 4, [0x2754, 0x27B4, 0x2814, 0x2874]),
            (0x1CD0, 2, [0x2694, 0x26F4]),
            (0x1850, 2, [0x2394, 0x23F4]),
            (0x1D90, 2, [0x28D4, 0x2934]),
            (0x1910, 2, [0x2094, 0x20F4]),
            (0x1E50, 2, [0x25D4, 0x2634]),
        ]
        banks = {}
        for src, width, destinations in streams:
            words = struct.unpack(
                "<" + ("I" if width == 4 else "H") * 96,
                table[src - 0x1340 : src - 0x1340 + 96 * width],
            )
            for j, dest in enumerate(destinations):
                shift = 8 * (width - j - 1)
                banks[dest] = [signed7(v >> shift) for v in words]
        starts = [
            0x1F14,
            0x1FD4,
            0x2154,
            0x2214,
            0x22D4,
            0x2394,
            0x2454,
            0x2514,
            0x2694,
            0x2754,
            0x2814,
            0x28D4,
            0x2094,
            0x25D4,
        ]
        self.curves = [(banks[start], banks[start + 96]) for start in starts]

    def coefficients(self, values):
        if len(values) != 36 or any(
            type(x) is not int or not -7 <= x <= 7 for x in values
        ):
            raise ValueError("HSL requires 36 integer steps in -7..7")
        # Ratios are arithmetic immediates in the desktop slider conversion,
        # not the camera's differently rounded saturation builder.
        negative = [
            (77, 256),
            (77, 256),
            (79, 256),
            (493, 1280),
            (513, 1280),
            (79, 256),
            (77, 256),
            (77, 256),
            (79, 256),
            (79, 256),
            (79, 256),
            (79, 256),
        ]
        positive = [
            (48, 256),
            (48, 256),
            (48, 256),
            (256, 1280),
            (369, 1280),
            (328, 1280),
            (382, 1280),
            (382, 1280),
            (60, 256),
            (123, 256),
            (80, 256),
            (656, 1280),
        ]
        # Camera recipe H uses the opposite sign to the hidden desktop setter.
        output = []
        for record in range(12):
            wheel = record * 2 if record < 6 else (record - 6) * 2 + 1
            h, s, l = values[wheel], values[12 + wheel], values[24 + wheel]
            factor = struct.unpack_from("<h", self.records[record], 14)[0]
            n, d = (negative if s < 0 else positive)[wheel]
            output.append(
                (self.hue[7 - h], truncdiv(factor * s * n, d), self.light[l + 7])
            )
        return output

    def curve(self, selector, record, coordinate):
        if coordinate > 256:
            return 63
        if not 0 <= record < 12:
            return 0
        cell = (record % 6) * 16 + min(coordinate >> 4, 15)
        base, slope = self.curves[selector - 1]
        return clamp(
            base[cell]
            + ((slope[cell] * (coordinate - min(coordinate >> 4, 15) * 16) + 8) >> 4),
            -63,
            63,
        )

    def group(self, angle, radius, luminance, second, coefficients):
        coords = [0, 0, 0]
        found = [False] * 3
        raw_angle = 0
        record = 14
        for r in range(6 * second, 6 + 6 * second):
            if not self.mask & (1 << r):
                continue
            geometry = struct.unpack_from("<6H", self.records[r])
            meta = self.records[r][20:26]
            raw_angle = (angle - geometry[0]) % 32768
            deltas = [raw_angle, radius - geometry[2], luminance - geometry[4]]
            for axis in range(3):
                delta = deltas[axis]
                if axis == 2 and geometry[4:6] == (0, 0):
                    coords[axis] = 258
                    found[axis] = True
                elif 0 <= delta <= geometry[axis * 2 + 1]:
                    coords[axis] = min(
                        256,
                        (
                            (1 << ((meta[axis * 2 + 1] + 7) & 31))
                            + delta * meta[axis * 2] * 256
                        )
                        >> ((meta[axis * 2 + 1] + 8) & 31),
                    )
                    found[axis] = True
            if all(found):
                record = r
                break
        if record == 14:
            # Native sentinel 15 contributes zero deltas; never index past
            # the twelve real records in our reconstruction.
            return 0, 0, 0
        first = [self.curve(k + 6 * second, record, coords[0]) for k in (1, 2)]
        radial = [self.curve(k + 6 * second, record, coords[1]) for k in (3, 4, 5)]
        lightgate = self.curve(6 + 6 * second, record, coords[2])

        def combine(a, b, gain):
            return (
                clamp(
                    (lightgate * clamp((a * b + 32) >> 6, -64, 63) + 32) >> 6, -64, 63
                )
                * gain
                + 32
            ) >> 6

        hc, sc, lc = coefficients[record]
        dh = combine(first[0], radial[0], hc)
        ds = combine(first[1], radial[1], sc)
        meta = self.records[record][20:22]
        adjusted = clamp(
            ((raw_angle + dh) * meta[0] * 256 + (1 << ((meta[1] + 7) & 31)))
            >> ((meta[1] + 8) & 31),
            0,
            256,
        )
        dl = combine(self.curve(13 + second, record, adjusted), radial[2], lc)
        return dh, ds, dl

    def yuv(self, pixel, coefficients):
        y, cb, cr = pixel
        Y = y * 1023 // 255
        angle, radius = self.polar.convert(
            clamp(truncdiv((cb - 128) * 1023, 255), -512, 511),
            clamp(truncdiv((cr - 128) * 1023, 255), -512, 511),
        )
        changes = [self.group(angle, radius, Y, g, coefficients) for g in (0, 1)]
        angle = clamp((angle + changes[0][0] + changes[1][0]) % 32768, 0, 32767)
        radius = clamp(radius + changes[0][1] + changes[1][1], 0, 1023)
        Y = clamp(Y + changes[0][2] + changes[1][2], 0, 1023)
        word = self.trig[(angle >> 9) & 15]
        fraction = (angle >> 2) & 127
        rising = ((word >> 17) & 1023) * 128 + ((word >> 27) & 127) * fraction
        falling = ((word & 1023) * 128 if word & 1023 else 131072) - (
            (word >> 10) & 127
        ) * fraction
        quadrant = angle & 24576
        sine = rising if quadrant in (0, 16384) else falling
        cosine = rising if quadrant in (8192, 24576) else falling
        if quadrant in (16384, 24576):
            sine = -sine
        if quadrant in (8192, 16384):
            cosine = -cosine
        return (
            Y * 255 // 1023,
            clamp((cosine * radius + 262144) >> 19, -128, 127) + 128,
            clamp((sine * radius + 262144) >> 19, -128, 127) + 128,
        )

    def pixels8(self, pixels, values, rgb=True):
        """Vectorized, byte-exact stage; source/output byte triplets retain order."""
        import numpy as np

        a = np.asarray(pixels)
        if a.ndim < 1 or a.dtype != np.uint8 or a.shape[-1] != 3:
            raise ValueError("stage input must be uint8 triplets")
        shape = a.shape
        a = a.reshape(-1, 3)
        if rgb:
            q = a.astype(float)
            r, g, b = q.T
            c = self.constants
            yy = np.clip(
                g * c[0xDCB00] + r * c[0xDCAD8] + b * c[0xDCAC0], 0, c[0xDCB50]
            ).astype(np.int64)
            cb = np.clip(
                (b * c[0xDCAF8] + c[0xDCB48]) - (g * c[0xDCAE0] + r * c[0xDCAC8]),
                0,
                c[0xDCB50],
            ).astype(np.int64)
            cr = np.clip(
                (r * c[0xDCAF8] - g * c[0xDCAF0]) + (c[0xDCB48] - b * c[0xDCAB8]),
                0,
                c[0xDCB50],
            ).astype(np.int64)
        else:
            yy, cb, cr = a.astype(np.int64).T
        if not hasattr(self, "_polar256"):
            signed = [
                clamp(truncdiv((v - 128) * 1023, 255), -512, 511) for v in range(256)
            ]
            self._polar256 = np.array(
                [[self.polar.convert(x, y) for y in signed] for x in signed],
                dtype=np.int64,
            )
        angle, radius = self._polar256[cb, cr].T
        lum = yy * 1023 // 255
        coef = np.vstack(
            (np.array(self.coefficients(values), dtype=np.int64), [0, 0, 0])
        )
        geometry = np.array(
            [struct.unpack_from("<6H", r) for r in self.records], dtype=np.int64
        )
        metadata = np.array([list(r[20:26]) for r in self.records], dtype=np.int64)

        def curve(selector, record, coordinate):
            cell = (record % 6) * 16 + np.minimum(coordinate >> 4, 15)
            base, slope = self.curves[selector - 1]
            k = np.clip(cell, 0, 95)
            result = np.clip(
                np.array(base)[k]
                + (
                    (
                        np.array(slope)[k]
                        * (coordinate - np.minimum(coordinate >> 4, 15) * 16)
                        + 8
                    )
                    >> 4
                ),
                -63,
                63,
            )
            return np.where(coordinate > 256, 63, np.where(record < 12, result, 0))

        changes = []
        for group in (0, 1):
            coords = np.zeros((3, len(a)), dtype=np.int64)
            found = np.zeros((3, len(a)), bool)
            done = np.zeros(len(a), bool)
            record = np.full(len(a), 12, dtype=np.int64)
            rawangle = np.zeros(len(a), dtype=np.int64)
            for rr in range(group * 6, group * 6 + 6):
                if not self.mask & (1 << rr):
                    continue
                active = ~done
                geom = geometry[rr]
                meta = metadata[rr]
                rawangle = np.where(active, (angle - geom[0]) % 32768, rawangle)
                delta = [rawangle, radius - geom[2], lum - geom[4]]
                for axis in range(3):
                    if axis == 2 and geom[4] == geom[5] == 0:
                        coords[axis, active] = 258
                        found[axis, active] = True
                    else:
                        good = (
                            active
                            & (delta[axis] >= 0)
                            & (delta[axis] <= geom[2 * axis + 1])
                        )
                        scaled = np.minimum(
                            256,
                            (
                                (1 << ((int(meta[2 * axis + 1]) + 7) & 31))
                                + delta[axis] * meta[2 * axis] * 256
                            )
                            >> ((int(meta[2 * axis + 1]) + 8) & 31),
                        )
                        coords[axis, good] = scaled[good]
                        found[axis, good] = True
                completed = active & found.all(axis=0)
                record[completed] = rr
                done |= completed
            angular = [curve(k + 6 * group, record, coords[0]) for k in (1, 2)]
            radial = [curve(k + 6 * group, record, coords[1]) for k in (3, 4, 5)]
            gate = curve(6 + 6 * group, record, coords[2])

            def combine(left, right, gain):
                return (
                    np.clip(
                        (gate * np.clip((left * right + 32) >> 6, -64, 63) + 32) >> 6,
                        -64,
                        63,
                    )
                    * gain
                    + 32
                ) >> 6

            dh = combine(angular[0], radial[0], coef[record, 0])
            ds = combine(angular[1], radial[1], coef[record, 1])
            meta = metadata[np.minimum(record, 11)]
            shifted = np.clip(
                ((rawangle + dh) * meta[:, 0] * 256 + (1 << ((meta[:, 1] + 7) & 31)))
                >> ((meta[:, 1] + 8) & 31),
                0,
                256,
            )
            dl = combine(curve(13 + group, record, shifted), radial[2], coef[record, 2])
            changes.append((dh, ds, dl))
        angle = (angle + changes[0][0] + changes[1][0]) % 32768
        radius = np.clip(radius + changes[0][1] + changes[1][1], 0, 1023)
        lum = np.clip(lum + changes[0][2] + changes[1][2], 0, 1023) * 255 // 1023
        words = np.asarray(self.trig, dtype=np.uint64)[(angle >> 9) & 15].astype(
            np.int64
        )
        fraction = (angle >> 2) & 127
        rising = ((words >> 17) & 1023) * 128 + ((words >> 27) & 127) * fraction
        falling = (
            np.where(words & 1023, (words & 1023) * 128, 131072)
            - ((words >> 10) & 127) * fraction
        )
        quadrant = angle & 24576
        sine = np.where((quadrant == 0) | (quadrant == 16384), rising, falling)
        cosine = np.where((quadrant == 8192) | (quadrant == 24576), rising, falling)
        sine = np.where((quadrant == 16384) | (quadrant == 24576), -sine, sine)
        cosine = np.where((quadrant == 8192) | (quadrant == 16384), -cosine, cosine)
        cb = np.clip((cosine * radius + 262144) >> 19, -128, 127)
        cr = np.clip((sine * radius + 262144) >> 19, -128, 127)
        if not rgb:
            return (
                np.stack((lum, cb + 128, cr + 128), axis=-1)
                .astype(np.uint8)
                .reshape(shape)
            )
        c = self.constants
        out = np.stack(
            (
                (lum - cb * c[0xDCA90]) + cr * c[0xDCB18],
                (lum - cb * c[0xDCAE8]) - cr * c[0xDCB08],
                (cb * c[0xDCB20] + lum) - cr * c[0xDCA88],
            ),
            axis=-1,
        )
        return np.clip(out, 0, c[0xDCB50]).astype(np.uint8).reshape(shape)
