"""EOP能力开放平台网关客户端"""

import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional, Type, TypeVar

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EopGatewayClient:
    """EOP统一网关客户端，封装鉴权、重试、熔断"""

    def __init__(self):
        self.base_url = settings.eop_gateway_url
        self.app_key = settings.eop_app_key
        self.app_secret = settings.eop_app_secret
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=50)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.timeout = 30
        return session

    def _build_headers(self, api_code: str) -> Dict[str, str]:
        """构造EOP请求头"""
        timestamp = str(int(time.time() * 1000))
        nonce = uuid.uuid4().hex[:16]
        sign_str = f"{self.app_key}{timestamp}{nonce}{api_code}"
        signature = hmac.new(
            self.app_secret.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return {
            "Content-Type": "application/json",
            "X-EOP-AppKey": self.app_key,
            "X-EOP-Timestamp": timestamp,
            "X-EOP-Nonce": nonce,
            "X-EOP-Signature": signature,
            "X-EOP-ApiCode": api_code,
        }

    def invoke(
        self,
        api_code: str,
        request_body: Optional[Dict[str, Any]] = None,
        method: str = "POST",
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """调用EOP接口"""
        url = f"{self.base_url}/{api_code}"
        headers = self._build_headers(api_code)
        request_id = uuid.uuid4().hex[:12]

        logger.info(
            "EOP invoke start | api=%s | request_id=%s | body=%s",
            api_code,
            request_id,
            json.dumps(request_body, ensure_ascii=False)[:200],
        )

        try:
            if method.upper() == "GET":
                resp = self._session.get(url, headers=headers, params=request_body, timeout=timeout)
            else:
                resp = self._session.post(url, headers=headers, json=request_body, timeout=timeout)

            resp.raise_for_status()
            result = resp.json()

            logger.info(
                "EOP invoke success | api=%s | request_id=%s | cost=%.2fms",
                api_code,
                request_id,
                (time.time() - int(headers["X-EOP-Timestamp"]) / 1000) * 1000,
            )
            return result

        except requests.exceptions.RequestException as e:
            logger.error(
                "EOP invoke failed | api=%s | request_id=%s | error=%s",
                api_code,
                request_id,
                str(e),
            )
            raise

    def get_api_detail(self, api_code: str) -> Dict[str, Any]:
        """查询API详情（接口16）"""
        return self.invoke("api/detail", {"api_code": api_code})

    def query_data_source(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """查询数据源（接口1）"""
        return self.invoke("data-source/query", params)

    def sync_metadata(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """同步元数据（接口10/12）"""
        return self.invoke("metadata/sync", params)

    def get_master_data_code(self, sys_group_id: str) -> Dict[str, Any]:
        """获取主数据编码"""
        return self.invoke("mdm/getMasterDataCode", {"sys_group_id": sys_group_id})


# 全局单例
eop_client = EopGatewayClient()
