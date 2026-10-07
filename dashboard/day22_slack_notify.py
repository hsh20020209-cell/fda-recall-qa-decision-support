"""
[선택 기능 · 팀 기본 설계 외] Slack 전송.

day21 설계(app_design_prototype.py)는 "외부 전송은 수행하지 않습니다"를 원칙으로 한다.
이 모듈은 그 원칙을 벗어나는 확장 기능이라 별도 파일로 분리했고, 전송 전에는 반드시
"외부로 데이터가 전송됩니다" 확인창을 거친다.

* Webhook URL 은 **절대 코드/저장소에 넣지 않는다.**
  - 환경변수 SLACK_WEBHOOK_URL, 또는
  - .streamlit/secrets.toml 의 SLACK_WEBHOOK_URL (예: .streamlit/secrets.toml.example 참고)
* 설정이 없으면 전송은 동작하지 않고 안내 메시지만 표시한다.
"""
from __future__ import annotations

import os

import requests

# v1 호환용 상수: 값은 코드에 두지 않고 import 시점의 환경변수만 읽는다.
SLACK_FIXED_WEBHOOK_URL: str = os.environ.get("SLACK_WEBHOOK_URL", "").strip()


def get_webhook_url() -> str:
    url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if url:
        return url
    try:  # Streamlit secrets (로컬 secrets.toml / Streamlit Community Cloud Secrets)
        import streamlit as st
        return str(st.secrets.get("SLACK_WEBHOOK_URL", "")).strip()
    except Exception:
        return ""


def is_configured() -> bool:
    return bool(get_webhook_url())


def send_report(report_text: str, case_label: str = "", webhook_url: str | None = None) -> tuple[bool, str]:
    """QA Summary Report 텍스트를 Slack 채널로 전송. 반환: (성공여부, 사용자 메시지)"""
    webhook_url = (webhook_url or get_webhook_url()).strip()
    if not webhook_url:
        return False, "Slack Webhook이 설정되지 않았습니다. 환경변수 SLACK_WEBHOOK_URL 또는 .streamlit/secrets.toml 을 확인하세요."
    text = report_text if len(report_text) <= 3800 else report_text[:3800] + "\n…(길이 제한으로 일부 생략)"
    header = f"*QA Summary Report* {('· ' + case_label) if case_label else ''}\n"
    payload = {"text": header + "```" + text + "```"}
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code == 200 and resp.text == "ok":
            return True, "Slack 채널로 전송되었습니다."
        return False, f"Slack 전송 실패 (status={resp.status_code}): {resp.text[:200]}"
    except requests.RequestException as exc:
        return False, f"Slack 전송 중 오류가 발생했습니다: {exc}"
