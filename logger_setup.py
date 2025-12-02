import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Optional
from pathlib import Path
from datetime import datetime
from shutil import copy2

from config import LogConfig


def setup_logging(name: str = "fauna") -> logging.Logger:
    """Configure and return the app logger.
    - Writes to rotating file handler (buffered by OS) to reduce stdout overhead
    - Level controlled by LogConfig
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        # Already configured
        return logger

    level = getattr(logging, (LogConfig.level or "INFO").upper(), logging.INFO)
    logger.setLevel(level)

    if LogConfig.enable:
        # 确保日志文件夹存在
        log_path = Path(LogConfig.file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用按分钟轮转的处理器，保留若干快照副本
        # 基础日志固定使用 logs/fauna.log，保证文件名不变
        fh = TimedRotatingFileHandler(
            filename=str(log_path),
            when="S",  # 秒级轮转
            interval=getattr(LogConfig, "snapshot_seconds", 30),  # 默认30秒
            backupCount=getattr(LogConfig, "snapshot_backup_count", 120),
            encoding="utf-8",
            utc=False,
            delay=True,
        )
        # 轮转后的文件名后缀（加入时间，便于定位），形如：logs/fauna.log.20251202_1531
        # 这种命名能被 TimedRotatingFileHandler 正确清理，并保持基础文件名为 fauna.log
        fh.suffix = "%Y%m%d_%H%M%S.log"

        # 仅复制快照，不移动/删除基础日志文件，确保 tail 不中断
        def _rotator(source: str, dest: str) -> None:
            try:
                copy2(source, dest)
            except Exception:
                # 安静失败，避免影响主程序
                pass
        fh.rotator = _rotator

        fmt = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(fmt)
        fh.setLevel(level)
        logger.addHandler(fh)

    # Disable propagation to avoid duplicate logs on root
    logger.propagate = False
    return logger
