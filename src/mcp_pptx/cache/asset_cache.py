"""Asset caching for downloaded images and resources."""

import hashlib
import logging
import mimetypes
import time
from pathlib import Path
from typing import Dict, Optional

import httpx
from PIL import Image

logger = logging.getLogger(__name__)


class AssetCache:
    """Manages caching of downloaded assets."""

    def __init__(self, cache_dir: Optional[Path] = None, max_age_hours: int = 24):
        self.cache_dir = cache_dir or Path(".cache/assets")
        self.max_age_hours = max_age_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def download_image(self, url: str) -> Optional[Path]:
        """Download and cache an image."""
        try:
            # Generate cache key from URL
            cache_key = hashlib.sha256(url.encode()).hexdigest()
            
            # Check if already cached
            cached_files = list(self.cache_dir.glob(f"{cache_key}.*"))
            if cached_files:
                cached_file = cached_files[0]
                if self._is_cache_valid(cached_file):
                    logger.debug(f"Using cached image: {cached_file}")
                    return cached_file
                else:
                    cached_file.unlink()  # Remove expired cache
            
            # Download the image
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Determine file extension
                content_type = response.headers.get('content-type', '')
                ext = mimetypes.guess_extension(content_type) or '.png'
                
                # Handle common image extensions
                if ext in ['.jpeg', '.jpe']:
                    ext = '.jpg'
                elif ext not in ['.png', '.jpg', '.gif', '.bmp', '.svg']:
                    ext = '.png'
                
                # Save to cache
                cache_file = self.cache_dir / f"{cache_key}{ext}"
                cache_file.write_bytes(response.content)
                
                # Optimize image if needed
                await self._optimize_image(cache_file)
                
                logger.info(f"Downloaded and cached image: {url} -> {cache_file}")
                return cache_file
                
        except Exception as e:
            logger.error(f"Failed to download image {url}: {e}")
            return None

    async def _optimize_image(self, image_path: Path) -> None:
        """Optimize image size and format."""
        try:
            # Skip SVG files
            if image_path.suffix.lower() == '.svg':
                return
            
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB with white background
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                    img = rgb_img
                
                # Resize if too large
                max_size = (1920, 1080)  # Max HD resolution
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    logger.debug(f"Resized image {image_path} to {img.size}")
                
                # Check file size and compress if needed
                if image_path.stat().st_size > 2 * 1024 * 1024:  # 2MB
                    # Save with lower quality
                    img.save(image_path, optimize=True, quality=85)
                    logger.debug(f"Compressed image {image_path}")
                
        except Exception as e:
            logger.warning(f"Failed to optimize image {image_path}: {e}")

    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cached file is still valid."""
        if not cache_file.exists():
            return False
        
        file_age = time.time() - cache_file.stat().st_mtime
        max_age_seconds = self.max_age_hours * 3600
        
        return file_age < max_age_seconds

    def cleanup_old_assets(self) -> int:
        """Remove expired assets from cache."""
        removed_count = 0
        
        for cache_file in self.cache_dir.iterdir():
            if not self._is_cache_valid(cache_file):
                try:
                    cache_file.unlink()
                    removed_count += 1
                    logger.debug(f"Removed expired cache file: {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove cache file {cache_file}: {e}")
        
        return removed_count

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.iterdir())
        total_files = len(cache_files)
        total_size = sum(f.stat().st_size for f in cache_files if f.is_file())
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }