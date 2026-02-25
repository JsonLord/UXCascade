from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import uuid
from functools import lru_cache

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class StorageService:
  """
  Service responsible for uploading PNGs to MinIO (S3-compatible) and generating public URLs.

  The bucket is auto-created on first upload, with an anonymous GET policy applied.
  """

  def __init__(
    self,
    endpoint: str,
    access_key: str,
    secret_key: str,
    bucket: str,
    public_url: str,
  ) -> None:
    self._bucket = bucket
    self._public_url = public_url.rstrip("/")
    self._client = boto3.client(
      "s3",
      endpoint_url=endpoint,
      aws_access_key_id=access_key,
      aws_secret_access_key=secret_key,
      config=Config(signature_version="s3v4"),
      region_name="us-east-1",
    )
    self._bucket_ready = False

  # ── Public API ─────────────────────────────────────────────────────────────

  def upload_png(self, key: str, png_bytes: bytes) -> str:
    """Upload PNG bytes to MinIO and return the public URL."""
    self._ensure_bucket()
    self._client.put_object(
      Bucket=self._bucket,
      Key=key,
      Body=png_bytes,
      ContentType="image/png",
    )
    return f"{self._public_url}/{self._bucket}/{key}"

  def save_step_screenshot(self, screenshot_b64: str, elements: list[dict]) -> str:
    """
    Draw bounding boxes on a base64 screenshot, upload to MinIO, and return the URL.

    If elements is empty, the image is uploaded as-is without annotation.
    Returns an empty string on error so the simulation is not interrupted.
    """
    if not screenshot_b64:
      return ""
    try:
      png_bytes = (
        annotate_screenshot(screenshot_b64, elements)
        if elements
        else base64.b64decode(screenshot_b64)
      )
      key = f"steps/{uuid.uuid4()}.png"
      return self.upload_png(key, png_bytes)
    except Exception:
      logger.exception("Failed to save step screenshot")
      return ""

  async def save_step_screenshot_async(
    self,
    screenshot_b64: str,
    elements: list[dict],
  ) -> str:
    """Async wrapper for save_step_screenshot. Runs boto3 synchronous I/O in a thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
      None,
      self.save_step_screenshot,
      screenshot_b64,
      elements,
    )

  # ── Internal helpers ───────────────────────────────────────────────────────

  def _ensure_bucket(self) -> None:
    if self._bucket_ready:
      return
    try:
      self._client.head_bucket(Bucket=self._bucket)
    except ClientError as exc:
      code = exc.response["Error"]["Code"]
      if code in ("404", "NoSuchBucket"):
        self._client.create_bucket(Bucket=self._bucket)
        self._set_bucket_public()
      else:
        raise
    self._bucket_ready = True

  def _set_bucket_public(self) -> None:
    """Apply a policy that allows anonymous GET access to the bucket."""
    policy = {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": {"AWS": ["*"]},
          "Action": ["s3:GetObject"],
          "Resource": [f"arn:aws:s3:::{self._bucket}/*"],
        }
      ],
    }
    self._client.put_bucket_policy(
      Bucket=self._bucket,
      Policy=json.dumps(policy),
    )


@lru_cache(maxsize=1)
def get_storage_service() -> StorageService:
  from app.core.config import settings

  return StorageService(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    bucket=settings.MINIO_BUCKET,
    public_url=settings.MINIO_PUBLIC_URL,
  )


# ── Screenshot annotation ──────────────────────────────────────────────────────

# Prefer Noto CJK font for CJK character rendering
_FONT_CANDIDATES = [
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
  "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
  "/usr/share/fonts/noto-cjk/NotoSansCJKjp-Regular.otf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
  for path in _FONT_CANDIDATES:
    if os.path.exists(path):
      try:
        return ImageFont.truetype(path, size)
      except Exception:
        continue
  return ImageFont.load_default()


# Color palette: color-coded by element type
_TAG_COLORS: dict[str, tuple[int, int, int]] = {
  "button": (59, 130, 246),  # blue
  "a": (16, 185, 129),  # green
  "input": (245, 158, 11),  # amber
  "select": (139, 92, 246),  # purple
  "textarea": (236, 72, 153),  # pink
}
_DEFAULT_COLOR = (100, 116, 139)  # slate


def annotate_screenshot(
  screenshot_b64: str,
  elements: list[dict],
) -> bytes:
  """
  Draw bounding boxes onto a base64-encoded PNG and return the resulting PNG bytes.

  Parameters
  ----------
  screenshot_b64:
      Base64-encoded PNG provided by browser-use
  elements:
      List of elements in [{index, tag, x, y, width, height}, ...] format
  """
  img_bytes = base64.b64decode(screenshot_b64)
  img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

  overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
  draw = ImageDraw.Draw(overlay)

  for elem in elements:
    x, y, w, h = elem["x"], elem["y"], elem["width"], elem["height"]
    if w <= 2 or h <= 2:
      continue

    tag = elem.get("tag", "")
    r, g, b = _TAG_COLORS.get(tag, _DEFAULT_COLOR)

    # Semi-transparent fill
    draw.rectangle(
      [x, y, x + w, y + h],
      fill=(r, g, b, 25),
      outline=(r, g, b, 200),
      width=2,
    )

    # Index label (top-left corner)
    label = str(elem["index"])
    font = _load_font(11)
    label_w = max(len(label) * 7 + 4, 18)
    draw.rectangle([x, y, x + label_w, y + 14], fill=(r, g, b, 220))
    draw.text((x + 2, y + 1), label, fill=(255, 255, 255, 255), font=font)

  result = Image.alpha_composite(img, overlay).convert("RGB")
  out = io.BytesIO()
  result.save(out, format="PNG", optimize=True)
  return out.getvalue()


def upload_annotated_screenshot(
  screenshot_b64: str,
  elements: list[dict],
) -> str:
  """
  Upload an annotated screenshot to MinIO and return its URL.
  Returns an empty string on error so the simulation is not interrupted.
  """
  try:
    png_bytes = (
      annotate_screenshot(screenshot_b64, elements)
      if elements
      else (base64.b64decode(screenshot_b64))
    )
    key = f"steps/{uuid.uuid4()}.png"
    return get_storage_service().upload_png(key, png_bytes)
  except Exception:
    logger.exception("Failed to upload annotated screenshot")
    return ""
