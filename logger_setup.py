import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Optional
from pathlib import Path
from datetime import datetime

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
        fh = TimedRotatingFileHandler(
            filename=str(log_path),
            when="M",
            interval=getattr(LogConfig, "snapshot_minutes", 1),
            backupCount=getattr(LogConfig, "snapshot_backup_count", 120),
            encoding="utf-8",
            utc=False,
            delay=True,
        )
        # 轮转后的文件名后缀（加入时间，便于定位），并确保以 .log 结尾
        fh.suffix = "%Y%m%d_%H%M"

        # 自定义命名：将默认的 "fauna.log.20251202_1531" 改为 "fauna_20251202_1531.log"
        def _make_rotated_namer(base: Path):
            def _namer(default_name: str) -> str:
                dn = Path(default_name)
                # 提取最后一段时间戳
                stamp = dn.name.split(".")[-1]
                final = base.with_name(f"{base.stem}_{stamp}{base.suffix}")
                return str(final)
            return _namer

        fh.namer = _make_rotated_namer(log_path)
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
