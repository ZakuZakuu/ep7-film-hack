# T9 · Source and private image-metadata reproduction

[Capability/workflow report](../research/e142-native-style-workflows.md) · [Issue #29](https://github.com/ZakuZakuu/ep7-film-hack/issues/29). Public documents and legitimately published images only; no owner's files, camera transport or OEM firmware analysis. Public commit contains original prose, selected facts and these commands, **no photo/manual/source redistribution or complete EXIF/MakerNote export**.

## Sources and tool scope

- Official [E-P7 manual](https://my.omsystem.com/consumer/manuals/cameras/E-P7_MANUAL_EN.pdf):200pages,16862659bytes, SHA-256 `54b139500c2f4192bc678b10427309d1ead22c8455550b6d235d467c2eea83f8`. Retrieved with ordinary public HTTPS after the web viewer's size limit; text via Poppler25.03.0 `pdftotext -layout`. Read printed pp46–53,70–73,89–96,103–113,129–130,137–138,145–146 and relevant defaults/menu lists. Numbers are manual pages, **not firmware addresses**.
- Official [specs](https://jp.omsystem.com/product/dslr/pen/ep7/spec.html)/[E-P7 Q&A](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/products/ep7/) and FAQ [006722](https://digital-faq.jp.omsystem.com/faq/public/app/servlet/qadoc?QID=006722), [007407](https://digital-faq.jp.omsystem.com/faq/public/app/servlet/qadoc?QID=007407), [007489](https://digital-faq.jp.omsystem.com/faq/public/app/servlet/qadoc?QID=007489): current public content reviewed2026-10-12. FAQ text uses CP932; a UTF-8-only read failed and was corrected from cached bytes. Browser/standard HTTP-client access sometimes differ;200 alone is not evidence.
- ExifTool13.59 at **`2200871d9cef988051d2a99d67df3bda6cbb30a8`**: [Olympus.pm](https://github.com/exiftool/exiftool/blob/2200871d9cef988051d2a99d67df3bda6cbb30a8/lib/Image/ExifTool/Olympus.pm),157893bytes, SHA-256 `f974dc7c82b5e187148e0defc8d733734445df2121175097f001fe551ae08651`. [README license](https://github.com/exiftool/exiftool/blob/2200871d9cef988051d2a99d67df3bda6cbb30a8/README): Phil Harvey/Perl Artistic or GPL. Mature read-only CLI reused; original private scripts only orchestrate bounded downloads/allowlisted reads. No parser or camera API implemented.

For an external ignored checkout, select `lib` plus the CLI/README and record the pinned revision; no test-photo archive is needed. A sparse checkout may need network permission to fetch missing blobs. Do not clone/copy source into tracked tools.

```bash
perl work/t9/exiftool/exiftool -ver
git -C work/t9/exiftool rev-parse HEAD
sha256sum work/t9/exiftool/lib/Image/ExifTool/Olympus.pm
```

**No ExifTool write options:** no tag assignments, `-tagsFromFile`, overwrite switches or XMP generation. File-level Writable annotations do not establish camera ingress. `AFFineTune`/`AFFineTuneAdj` describe autofocus, not the ART slider. Global Olympus dictionaries/array names do not prove E-P7 active settings or complete UI mapping.

## Private sample identities and source controls

Ordinary public JPEG downloads were capped at16MiB each. Original copies/selected JSON kept in **`/tmp/ep7-style-metadata/` mode0700**, files0600. No serial, GPS, dates, author or user account queried/exported; originals were never rewritten. These published samples are not the private1.1 firmware or an owner-camera session.

| Source / local role | Bytes / SHA-256 | What the check actually supports |
| --- | --- | --- |
| [Official Natural sample](https://jp.omsystem.com/cms/images/goods/e-p7/content/000115036.jpg) / `natural.jpg` |802097 /`fc805de1865edd0a311b705aa5059a5c8dbc1a7317eadb08c02d482aec78a14e`|Workspace1.5W marker; retained E-P7 metadata, **processed** |
| [Official COLOR-captioned sample](https://jp.omsystem.com/cms/images/goods/e-p7/content/000115038.jpg) / `color.jpg` |1603680 /`52e4a44d06b1bb943410b18292c5518df5664f2f9bb3222befc2030d5f3d73b5`|Workspace1.32M, Natural token; caption not a reliable active-profile assertion |
| [Official MONO3-captioned sample](https://jp.omsystem.com/cms/images/goods/e-p7/content/000115032.jpg) / `mono3.jpg` |2464421 /`b246b070fe3e997e8b2be44af8228f3ba6eb614da8c2d33998d7486f3a002f3a`|Workspace1.4M, Monochrome Profile2 token; WB namespace conflict. Not a direct-camera profile control |
| [Author's Download Original](https://img.photographyblog.com/reviews/olympus_e_p7/sample_images/olympus_e_p7_11.jpg) / `review-original.jpg`, from [review](https://www.photographyblog.com/reviews/olympus_e_p7_review) |12907659 /`c8f588af48909a8abc23e410f20b71155d03f075e7f210e4a4410dccd8c9b109`|E-P7/SoftwareVersion1.0; caption-compatible exposure, credible original-source JPEG, **no independent camera/authenticity test** |

Source pages supplied actual links; no invented photo URL or user photo needed. A normal HTTP client received403 on the review page; the browser source yielded the Download Original link, and its public image was retrieved successfully. The viewer could not open that image because of its size. No login, camera, private account or access-control bypass. Images were not used for subjective film-fit scoring or exported as fixtures.

## Allowlisted read and counterchecks

After obtaining those exact public sample copies, run from repository root. Keep all output private. The first two source guards are original data-independent countercontrols, not fabricated E-P7 captures. A separate original2×2 JPEG without EXIF was also checked: no Model/PictureMode fields, so it cannot establish a camera recipe.

```bash
umask 077
python3 - <<'PY'
from pathlib import Path
import hashlib, json, subprocess

def admissible(info):
    # Weak necessary checks only: not an authenticity proof or firmware-version test.
    return info.get('IFD0:Model') == 'E-P7' and not any(
        marker in info.get('IFD0:Software', '') for marker in ['Workspace', 'Photoshop'])

assert not admissible({'IFD0:Model': 'other-model', 'IFD0:Software': 'Version 1.0'})
assert not admissible({'IFD0:Model': 'E-P7', 'IFD0:Software': 'Workspace'})
assert not admissible({})

path = Path('/tmp/ep7-style-metadata/review-original.jpg')
expected = 'c8f588af48909a8abc23e410f20b71155d03f075e7f210e4a4410dccd8c9b109'
assert path.stat().st_size == 12907659
assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
tags = ['Make', 'Model', 'Software', 'ImageWidth', 'ImageHeight', 'PictureMode',
        'PictureModeSaturation', 'PictureModeContrast', 'PictureModeSharpness',
        'PictureModeBWFilter', 'PictureModeTone', 'Gradation', 'ArtFilter',
        'ArtFilterEffect', 'ToneLevel', 'ColorCreatorEffect', 'ColorProfileSettings',
        'MonochromeProfileSettings', 'MonochromeVignetting', 'MonochromeColor',
        'FilmGrainEffect', 'WhiteBalance', 'WhiteBalance2', 'WhiteBalanceTemperature',
        'WhiteBalanceBracket', 'ColorSpace', 'NoiseFilter', 'NoiseReduction',
        'ShadingCompensation', 'ISO', 'ExposureTime', 'FNumber', 'ExposureProgram',
        'ExposureCompensation', 'ExposureMode', 'MeteringMode']
result = subprocess.run(['perl', 'work/t9/exiftool/exiftool', '-G1', '-s', '-j'] +
                        ['-' + tag for tag in tags] + [str(path)],
                        capture_output=True, text=True, check=True)
info = json.loads(result.stdout)[0]
assert all(k == 'SourceFile' or k.rsplit(':', 1)[-1] in tags for k in info)
assert admissible(info) and info['IFD0:Software'] == 'Version 1.0'
assert info['Olympus:PictureMode'].startswith('Natural;')
assert (info['ExifIFD:ISO'], info['ExifIFD:ExposureTime'], info['ExifIFD:FNumber']) == (200, '1/1250', 3.5)
counts = {}
for tag, count in [('ColorProfileSettings', 14), ('MonochromeProfileSettings', 6),
                   ('ArtFilterEffect', 20), ('ToneLevel', 28)]:
    counts[tag] = len(info['Olympus:' + tag].split(';'))
    assert counts[tag] == count
assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
print(json.dumps({'sample_identity_guards': True, 'selected_structure_counts': counts,
                  'input_unchanged': True, 'complete_recipe_recovery': 'unproved'}))
PY
```

Counts describe selected serialized structures, not number of camera slots or complete decode. The Natural original has inactive COLOR/MONO default fields; this is a **presence-versus-activation negative control**. Do not promote14COLOR words to14profiles, or20ART words to20freely composable operators. Some values/names are cross-model mappings. No active original COLOR4/nondefault MONO/ART slider or full WB-memory state was tested. Snapshot crop/exposure is not camera configuration/auto-policy restoration.

Public-safe conclusions are the report's chosen facts/counts; the procedure deliberately does not print full metadata values. Verify before/after hashes, local Markdown links and changed-file allowlist. The existing synthetic CI validates tooling only; no new runtime feature, pytest fixture or camera test is introduced. T7's pending binary consumer and G4/G5 blockers are untouched.
