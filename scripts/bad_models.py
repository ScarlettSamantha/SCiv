import sys
import os
from panda3d.core import loadPrcFileData, Filename
from direct.showbase.ShowBase import ShowBase

# Prevent opening a window
loadPrcFileData("", "window-type none")


MODEL_EXTENSIONS = (".bam", ".egg", ".gltf", ".glb")
THRESHOLD = 1e-6
MODELS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/models"))


def find_model_files(root, exts=MODEL_EXTENSIONS):
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(exts):
                yield os.path.join(dirpath, fn)


def check_for_zero_scale_nodes(model_np, model_path, threshold=THRESHOLD):
    found_bad = False
    for node in model_np.find_all_matches("**"):
        scale = node.getScale()
        if abs(scale[0]) < threshold or abs(scale[1]) < threshold or abs(scale[2]) < threshold:
            print(f"[BAD SCALE] {model_path} → Node: {node.getName()} | Scale: {scale}")
            found_bad = True
    return found_bad


class ModelScanApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.models_with_issues = []
        print(f"Scanning for models in: {MODELS_ROOT}")

        for model_path in find_model_files(MODELS_ROOT):
            try:
                model_np = self.loader.loadModel(Filename.fromOsSpecific(model_path))
                if not model_np or model_np.isEmpty():
                    print(f"[SKIP] Could not load: {model_path}")
                    continue
                if check_for_zero_scale_nodes(model_np, model_path):
                    self.models_with_issues.append(model_path)
            except Exception as e:
                print(f"[ERROR] Loading {model_path}: {e}")

        print("\n=== Scan Complete ===")
        if self.models_with_issues:
            print("Models with zero/near-zero scale found:")
            for path in self.models_with_issues:
                print(" -", path)
        else:
            print("No problematic models found.")

        # Exit after scanning
        sys.exit(0)


if __name__ == "__main__":
    ModelScanApp()
