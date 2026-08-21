"""变量加密 + 动态表达式计算。
加密用 Fernet(对称),密钥从 Django SECRET_KEY 派生。
动态变量表达式用受限命名空间 eval,只暴露 datetime/random/uuid/time。
"""
import base64
import hashlib
import logging
import random
import time
import uuid
from datetime import datetime

from django.conf import settings

logger = logging.getLogger(__name__)

# ponytail: 从 SECRET_KEY 派生 Fernet key,32字节 SHA256 后 base64
_KEY = base64.urlsafe_b64encode(
    hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
)

try:
    from cryptography.fernet import Fernet
    _FERNET = Fernet(_KEY)
except ImportError:
    _FERNET = None
    logger.warning("cryptography not installed, encryption disabled")


def encrypt_value(plain: str) -> str:
    if not plain or _FERNET is None:
        return plain
    return _FERNET.encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_value(cipher: str) -> str:
    if not cipher or _FERNET is None:
        return cipher
    try:
        return _FERNET.decrypt(cipher.encode("utf-8")).decode("utf-8")
    except Exception:
        # 不是合法密文或密钥变了,原样返回
        return cipher


# 动态变量表达式命名空间
_DYNAMIC_NS = {
    "datetime": datetime,
    "random": random,
    "uuid": uuid,
    "time": time,
}


def eval_dynamic(expr: str):
    """受限 eval,只允许 datetime/random/uuid/time。
    ponytail: 用 eval 是最简方案,要更严格可换 ast 解析。
    """
    if not expr:
        return ""
    try:
        return eval(expr, {"__builtins__": {}}, dict(_DYNAMIC_NS))
    except Exception as e:
        logger.warning("dynamic expr eval failed: %s -> %s", expr, e)
        return ""
