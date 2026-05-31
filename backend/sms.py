import os
import time
import logging
import random

logger = logging.getLogger(__name__)

SMS_ACCESS_KEY_ID = os.environ.get("SMS_ACCESS_KEY_ID", "")
SMS_ACCESS_KEY_SECRET = os.environ.get("SMS_ACCESS_KEY_SECRET", "")
SMS_SIGN_NAME = "速通互联验证码"
SMS_TEMPLATE_CODE = "100001"
DEV_MODE = os.environ.get("SMS_DEV_MODE", "1") == "1"

_code_store = {}


def send_verify_code(phone: str) -> dict:
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
        from alibabacloud_dypnsapi20170525.client import Client
        from alibabacloud_openapi_client import OpenApiClient
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_dypnsapi20170525 import models as sms_models

        config = open_api_models.Config(
            access_key_id=SMS_ACCESS_KEY_ID,
            access_key_secret=SMS_ACCESS_KEY_SECRET,
        )
        config.endpoint = "dypnsapi.aliyuncs.com"
        client = Client(config)

        req = sms_models.SendSmsVerifyCodeRequest(
            phone_number=phone,
            sign_name=SMS_SIGN_NAME,
            template_code=SMS_TEMPLATE_CODE,
            code_length=6,
            valid_time=300,
            interval=60,
        )
        resp = client.send_sms_verify_code(req)
        body = resp.body
        if body.code != "OK":
            logger.error(f"sms send error: {body.code} {body.message}")
            return {"ok": False, "msg": "短信发送失败，请稍后重试"}

        verify_code = None
        if hasattr(body, "model") and body.model:
            verify_code = getattr(body.model, "verify_code", None)

        _code_store[phone] = {
            "code": verify_code,
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
    cached = _code_store.get(phone)
    if not cached:
        return {"ok": False, "msg": "请先获取验证码"}
    if time.time() - cached["time"] > 300:
        del _code_store[phone]
        return {"ok": False, "msg": "验证码已过期"}
    if cached["attempts"] >= 5:
        del _code_store[phone]
        return {"ok": False, "msg": "验证次数过多，请重新获取"}

    stored_code = cached.get("code")
    if stored_code:
        if stored_code != code:
            cached["attempts"] += 1
            return {"ok": False, "msg": "验证码错误"}
    elif not cached.get("dev_mode", False):
        try:
            from alibabacloud_dypnsapi20170525.client import Client
            from alibabacloud_openapi_client import OpenApiClient
            from alibabacloud_tea_openapi import models as open_api_models
            from alibabacloud_dypnsapi20170525 import models as sms_models

            config = open_api_models.Config(
                access_key_id=SMS_ACCESS_KEY_ID,
                access_key_secret=SMS_ACCESS_KEY_SECRET,
            )
            config.endpoint = "dypnsapi.aliyuncs.com"
            client = Client(config)

            req = sms_models.CheckSmsVerifyCodeRequest(
                phone_number=phone,
                verify_code=code,
            )
            resp = client.check_sms_verify_code(req)
            if resp.body.code != "OK":
                cached["attempts"] += 1
                return {"ok": False, "msg": "验证码错误"}
        except Exception as e:
            logger.error(f"sms check exception: {e}")
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
