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

        # 按分钟轮转：基础文件固定 logs/fauna.log，额外生成快照副本
        fh = TimedRotatingFileHandler(
            filename=str(log_path),
            when="M",  # 分钟级轮转
            interval=getattr(LogConfig, "snapshot_minutes", 1),
            # 这里 backupCount 对我们自定义 rotator 基本无效，设 0 防止默认删除
            backupCount=0,
            encoding="utf-8",
            utc=False,
            delay=True,
        )

        # 自定义 rotator：复制出快照文件，并只保留最近 1 个
        def _rotator(source: str, dest: str) -> None:
            try:
                # 1. 生成当前快照文件名
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                snap_name = f"fauna_{ts}.log"
                snap_path = log_path.parent / snap_name

                # 2. 复制当前主日志到快照
                copy2(source, snap_path)

                # 3. 清理旧快照：只保留最新 1 个
                snapshots = sorted(
                    log_path.parent.glob("fauna_*.log"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                # snapshots[0] 是最新的，其余全部删除
                n = LogConfig.snapshot_backup_count or 1
                snapshots = snapshots[n:]
                for old in snapshots[1:]:
                    try:
                        old.unlink()
                    except Exception:
                        # 删除失败就算了，避免影响正常写日志
                        pass

            except Exception:
                # rotator 里绝不能抛异常，否则会影响 handler 正常工作
                pass

        fh.rotator = _rotator
        # dest 参数我们不使用，只是满足 TimedRotatingFileHandler 调用签名

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