"""reCAPTCHA v2 求解器"""

import asyncio
import base64
import io
import random
import re
import tempfile
from pathlib import Path
from typing import Protocol

import httpx
from loguru import logger
from playwright.async_api import Page
from pydub import AudioSegment

from captcha_solver.config import settings
from captcha_solver.domain.interfaces.browser import SolveResult


class IAudioTranscriber(Protocol):
    """音频转文字接口"""

    async def transcribe(self, audio_path: str) -> str | None:
        ...


class WhisperTranscriber:
    """Whisper ASR 转录器"""

    async def transcribe(self, audio_path: str) -> str | None:
        try:
            import whisper

            model = whisper.load_model("base")
            result = model.transcribe(audio_path, language="en")
            return result.get("text", "").strip()
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return None


class RecaptchaV2Solver:
    """reCAPTCHA v2 求解器 - 音频模式"""

    def __init__(self, transcriber: IAudioTranscriber | None = None):
        self._transcriber = transcriber or WhisperTranscriber()

    async def solve(
        self,
        page: Page,
        website_url: str | None = None,
        website_key: str | None = None,
        website_domain: str | None = None,
        is_enterprise: bool = False,
    ) -> SolveResult:
        """求解 reCAPTCHA v2"""
        try:
            # 构建目标 URL
            target_url = self._build_target_url(
                website_domain=website_domain,
                website_key=website_key,
                is_enterprise=is_enterprise,
            )

            # 导航到页面
            await page.goto(target_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(random.uniform(1, 2))

            # 点击 checkbox
            checkbox_clicked = await self._click_checkbox(page)
            if not checkbox_clicked:
                return SolveResult(
                    success=False,
                    error_code="CHECKBOX_NOT_FOUND",
                    error_desc="Could not find reCAPTCHA checkbox",
                )

            await asyncio.sleep(random.uniform(1, 2))

            # 检查是否直接通过
            token = await self._get_token(page)
            if token:
                return SolveResult(success=True, token=token)

            # 切换到音频挑战
            audio_switched = await self._switch_to_audio(page)
            if not audio_switched:
                return SolveResult(
                    success=False,
                    error_code="AUDIO_SWITCH_FAILED",
                    error_desc="Could not switch to audio challenge",
                )

            # 尝试音频求解 (最多3次)
            for attempt in range(3):
                result = await self._solve_audio_challenge(page)
                if result.success:
                    return result
                if result.error_code == "CAPTCHA_BLOCKED":
                    break
                await asyncio.sleep(random.uniform(1, 2))

            return SolveResult(
                success=False,
                error_code="CAPTCHA_UNSOLVABLE",
                error_desc="Failed to solve after multiple attempts",
            )

        except Exception as e:
            logger.exception(f"Solve error: {e}")
            return SolveResult(
                success=False,
                error_code="INTERNAL_ERROR",
                error_desc=str(e)[:200],
            )

    def _build_target_url(
        self,
        website_domain: str | None,
        website_key: str | None,
        is_enterprise: bool,
    ) -> str:
        """构建目标 URL"""
        base = "https://www.google.com/recaptcha"
        api = "enterprise" if is_enterprise else "api2"
        # 版本号需要定期更新，可通过 https://www.google.com/recaptcha/api.js 获取
        version = "7gg7H51Q-naNfhmCP3_R47ho"
        return (
            f"{base}/{api}/anchor?"
            f"ar=1&k={website_key}&co={self._encode_domain(website_domain)}"
            f"&hl=en&v={version}&size=normal"
        )

    def _encode_domain(self, domain: str | None) -> str:
        """编码域名"""
        if not domain:
            return ""
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        return base64.b64encode(domain.encode()).decode().rstrip("=")

    async def _click_checkbox(self, page: Page) -> bool:
        """点击 checkbox"""
        try:
            checkbox = page.locator("#recaptcha-anchor")
            await checkbox.wait_for(state="visible", timeout=10000)
            await checkbox.click()
            return True
        except Exception as e:
            logger.warning(f"Checkbox click failed: {e}")
            return False

    async def _get_token(self, page: Page) -> str | None:
        """获取 token"""
        try:
            textarea = page.locator("#g-recaptcha-response, #recaptcha-token")
            value = await textarea.input_value(timeout=5000)
            return value if value else None
        except Exception:
            return None

    async def _switch_to_audio(self, page: Page) -> bool:
        """切换到音频挑战"""
        try:
            # 等待 bframe 出现
            bframe = page.frame_locator("iframe[src*='bframe']")
            audio_btn = bframe.locator("#recaptcha-audio-button")
            await audio_btn.wait_for(state="visible", timeout=10000)
            await audio_btn.click()
            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.warning(f"Switch to audio failed: {e}")
            return False

    async def _solve_audio_challenge(self, page: Page) -> SolveResult:
        """求解音频挑战"""
        try:
            bframe = page.frame_locator("iframe[src*='bframe']")

            # 检查是否被阻止
            blocked = bframe.locator(".rc-doscaptcha-header-text")
            if await blocked.count() > 0:
                return SolveResult(
                    success=False,
                    error_code="CAPTCHA_BLOCKED",
                    error_desc="reCAPTCHA blocked automated queries",
                )

            # 获取音频 URL
            download_link = bframe.locator(".rc-audiochallenge-tdownload-link")
            await download_link.wait_for(state="visible", timeout=10000)
            audio_url = await download_link.get_attribute("href")

            if not audio_url:
                return SolveResult(
                    success=False,
                    error_code="AUDIO_URL_NOT_FOUND",
                    error_desc="Could not find audio download URL",
                )

            # 下载并转录音频
            text = await self._transcribe_audio(audio_url)
            if not text:
                return SolveResult(
                    success=False,
                    error_code="TRANSCRIPTION_FAILED",
                    error_desc="Could not transcribe audio",
                )

            # 输入答案
            input_field = bframe.locator("#audio-response")
            await input_field.fill(text)
            await asyncio.sleep(random.uniform(0.5, 1))

            # 点击验证
            verify_btn = bframe.locator("#recaptcha-verify-button")
            await verify_btn.click()
            await asyncio.sleep(2)

            # 获取 token
            token = await self._get_token(page)
            if token:
                return SolveResult(success=True, token=token)

            return SolveResult(
                success=False,
                error_code="VERIFICATION_FAILED",
                error_desc="Answer verification failed",
            )

        except Exception as e:
            logger.warning(f"Audio challenge failed: {e}")
            return SolveResult(
                success=False,
                error_code="AUDIO_CHALLENGE_ERROR",
                error_desc=str(e)[:200],
            )

    async def _transcribe_audio(self, audio_url: str) -> str | None:
        """下载并转录音频"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(audio_url)
                resp.raise_for_status()

            # 转换为 wav
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as mp3_file:
                mp3_file.write(resp.content)
                mp3_path = mp3_file.name

            wav_path = mp3_path.replace(".mp3", ".wav")
            audio = AudioSegment.from_mp3(mp3_path)
            audio.export(wav_path, format="wav")

            # 转录
            text = await self._transcriber.transcribe(wav_path)

            # 清理
            Path(mp3_path).unlink(missing_ok=True)
            Path(wav_path).unlink(missing_ok=True)

            return text

        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return None
