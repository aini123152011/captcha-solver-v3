"""任务处理器 - 验证码求解"""

from typing import Any
from uuid import UUID

from loguru import logger

from captcha_solver.application.services.task_service import TaskService
from captcha_solver.config import settings
from captcha_solver.domain.value_objects import TaskStatus, TaskType
from captcha_solver.infrastructure.browser.pool import get_browser_pool
from captcha_solver.infrastructure.database.connection import async_session_maker


async def solve_captcha_task(
    ctx: dict[str, Any],
    task_id: str,
) -> dict[str, Any]:
    """
    验证码求解任务

    由 arq Worker 执行
    """
    logger.info(f"Processing task {task_id}")

    async with async_session_maker() as session:
        task_service = TaskService(session)

        try:
            # 获取任务
            task = await task_service.get_task_by_id(UUID(task_id))

            # 更新状态为处理中
            await task_service.start_processing(UUID(task_id))

            # 获取浏览器池
            browser_pool = await get_browser_pool()

            # 执行求解
            async with browser_pool.new_context() as context:
                page = await context.new_page()

                try:
                    # 导入求解器
                    from captcha_solver.infrastructure.browser.solver import RecaptchaV2Solver

                    solver = RecaptchaV2Solver()

                    # 获取域名
                    domain = task.get_domain()
                    if not domain:
                        raise ValueError("No domain available for task")

                    # 求解
                    result = await solver.solve(
                        page=page,
                        website_key=task.website_key,
                        website_domain=domain,
                        is_enterprise=task.is_enterprise,
                    )

                    if result.success and result.token:
                        # 成功 - 完成任务并扣费
                        await task_service.complete_task(UUID(task_id), result.token)
                        logger.info(f"Task {task_id} completed successfully")
                        return {"status": "success", "token": result.token}
                    else:
                        # 失败
                        await task_service.fail_task(
                            UUID(task_id),
                            result.error_code or "CAPTCHA_UNSOLVABLE",
                            result.error_desc or "Failed to solve captcha",
                        )
                        logger.warning(f"Task {task_id} failed: {result.error_code}")
                        return {"status": "failed", "error": result.error_code}

                finally:
                    await page.close()

        except Exception as e:
            logger.exception(f"Task {task_id} error: {e}")

            # 标记任务失败
            try:
                await task_service.fail_task(
                    UUID(task_id),
                    "INTERNAL_ERROR",
                    str(e)[:500],  # 截断错误信息
                )
            except Exception:
                pass

            return {"status": "failed", "error": str(e)}
