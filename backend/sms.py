import os
import time
import logging
import json
import urllib.request

logger = logging.getLogger(__name__)

# 发送短信走MirageX API（已验证可用）
SMS_PROXY_URL = os.environ.get("SMS_PROXY_URL", "https://api.miragex.agentmj.vip/api/sms")

DEV_MODE = os.environ.get("SMS_DEV_MODE", "0") == "1"

_code_store = {}


def send_verify_code(phone: str) -> dict:
    """发送验证码，通过MirageX短信代理"""
    cached = _code_store.get(phone)
    if cached and time.time() - cached["time"] < 60:
        return {"ok": False, "msg": "发送太频繁，请60秒后重试"}

    if DEV_MODE:
        code = "123456"
        logger.info(f"[DEV MODE] 验证码: {code} -> {phone}")
        _code_store[phone] = {
            "code": code,
            "time": time.time(),
            "verified": False,
            "attempts": 0,
            "dev_mode": True,
        }
        _cleanup_expired()
        return {"ok": True, "msg": "验证码已发送（开发模式：123456）"}

    try:
        # 调用MirageX短信API
        url = f"{SMS_PROXY_URL}/send"
        data = json.dumps({"phone": phone}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())

        if result.get("code") != 0:
            logger.error(f"sms send error: {result}")
            return {"ok": False, "msg": result.get("msg", "短信发送失败")}

        # MirageX不返回验证码（阿里云服务端管理），本地无法比対
        # 验证码校验也走MirageX的/verify接口
        _code_store[phone] = {
            "code": None,  # 服务端管理
            "time": time.time(),
            "verified": False,
            "attempts": 0,
            "dev_mode": False,
        }
        _cleanup_expired()
        return {"ok": True, "msg": "验证码已发送"}

    except Exception as e:
        logger.error(f"sms send exception: {e}")
        return {"ok": False, "msg": "短信发送失败"}


def verify_code(phone: str, code: str) -> dict:
    """验证验证码"""
    cached = _code_store.get(phone)
    if not cached:
        return {"ok": False, "msg": "请先获取验证码"}
    if time.time() - cached["time"] > 300:
        del _code_store[phone]
        return {"ok": False, "msg": "验证码已过期"}
    if cached["attempts"] >= 5:
        del _code_store[phone]
        return {"ok": False, "msg": "验证次数过多，请重新获取"}

    # 本地有code（开发模式）
    stored_code = cached.get("code")
    if stored_code:
        if stored_code != code:
            cached["attempts"] += 1
            return {"ok": False, "msg": "验证码错误"}
    else:
        # 走MirageX验证接口
        try:
            url = f"{SMS_PROXY_URL}/verify"
            data = json.dumps({"phone": phone, "code": code}).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())

            if result.get("code") != 0:
                cached["attempts"] += 1
                return {"ok": False, "msg": result.get("msg", "验证码错误")}
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            logger.error(f"sms verify http error: {e.code} {body}")
            cached["attempts"] += 1
            return {"ok": False, "msg": "验证码错误"}
        except Exception as e:
            logger.error(f"sms verify exception: {e}")
            return {"ok": False, "msg": "验证失败"}

    cached["verified"] = True
    cached.pop("code", None)
    return {"ok": True, "msg": "验证成功"}


def is_phone_verified(phone: str) -> bool:
    cached = _code_store.get(phone)
    return bool(cached and cached["verified"])


def _cleanup_expired():
    now = time.time()
    expired = [k for k, v in _code_store.items() if now - v["time"] > 300]
    for k in expired:
        del _code_store[k]
