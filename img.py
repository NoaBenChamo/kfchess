from __future__ import annotations

import pathlib

import cv2
import numpy as np

class Img:
    def __init__(self):
        self.img = None

    def read(self, path: str | pathlib.Path,
             size: tuple[int, int] | None = None,
             keep_aspect: bool = False,
             interpolation: int = cv2.INTER_AREA) -> "Img":
        """
        Load `path` into self.img and **optionally resize**.

        Parameters
        ----------
        path : str | Path
            Image file to load.
        size : (width, height) | None
            Target size in pixels.  If None, keep original.
        keep_aspect : bool
            • False  → resize exactly to `size`
            • True   → shrink so the *longer* side fits `size` while
                       preserving aspect ratio (no cropping).
        interpolation : OpenCV flag
            E.g.  `cv2.INTER_AREA` for shrink, `cv2.INTER_LINEAR` for enlarge.

        Returns
        -------
        Img
            `self`, so you can chain:  `sprite = Img().read("foo.png", (64,64))`
        """
        path = str(path)
        self.img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if self.img is None:
            raise FileNotFoundError(f"Cannot load image: {path}")

        if size is not None:
            target_w, target_h = size
            h, w = self.img.shape[:2]

            if keep_aspect:
                scale = min(target_w / w, target_h / h)
                new_w, new_h = int(w * scale), int(h * scale)
            else:
                new_w, new_h = target_w, target_h

            self.img = cv2.resize(self.img, (new_w, new_h), interpolation=interpolation)

        return self

    def draw_on(self, other_img, x, y):
        if self.img is None or other_img.img is None:
            raise ValueError("Both images must be loaded before drawing.")

        src = self.img
        if src.shape[2] != other_img.img.shape[2]:
            if src.shape[2] == 3 and other_img.img.shape[2] == 4:
                src = cv2.cvtColor(src, cv2.COLOR_BGR2BGRA)
            elif src.shape[2] == 4 and other_img.img.shape[2] == 3:
                src = cv2.cvtColor(src, cv2.COLOR_BGRA2BGR)

        h, w = src.shape[:2]
        H, W = other_img.img.shape[:2]

        x1, y1 = max(x, 0), max(y, 0)
        x2, y2 = min(x + w, W), min(y + h, H)
        sx1, sy1 = x1 - x, y1 - y
        sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)
        if x2 <= x1 or y2 <= y1:
            return

        roi = other_img.img[y1:y2, x1:x2]
        sprite = src[sy1:sy2, sx1:sx2]

        if sprite.shape[2] == 4:
            b, g, r, a = cv2.split(sprite)
            mask = a / 255.0
            for c in range(3):
                roi[..., c] = (1 - mask) * roi[..., c] + mask * sprite[..., c]
        else:
            other_img.img[y1:y2, x1:x2] = sprite

    def put_text(self, txt, x, y, font_size, color=(255, 255, 255, 255), thickness=1):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.putText(self.img, txt, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                    color, thickness, cv2.LINE_AA)

    def show(self, window_name="KFChess"):
        if self.img is None:
            raise ValueError("Image not loaded.")
        display = cv2.cvtColor(self.img, cv2.COLOR_BGRA2BGR) if self.img.shape[2] == 4 else self.img
        cv2.imshow(window_name, display)
