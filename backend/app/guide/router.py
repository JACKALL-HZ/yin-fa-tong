"""智能导诊 + 语音挂号路由层"""

from fastapi import APIRouter
from app.shared.response import ApiResponse
from app.guide.schemas import GuideRequest, GuideResponse
from app.guide.service import guide_diagnose

router = APIRouter(prefix="/api/guide", tags=["智能服务"])


@router.post("/diagnose", response_model=ApiResponse[GuideResponse])
async def diagnose(req: GuideRequest):
    """AI 智能导诊

    输入症状描述（支持方言/口语），返回：
    - 推荐科室（含置信度和推理理由）
    - OTC 用药参考（Dify AI 模式）
    - 老年患者注意事项
    - 紧急情况警示
    """
    data = await guide_diagnose(req)
    return ApiResponse.ok(data, message="导诊完成")


@router.post("/voice-search")
async def voice_search(voice_text: str = "头疼发烧"):
    """语音挂号：识别语音指令 → 匹配科室/医生 → 返回导航建议

    前端将录制的语音转文字后提交此接口，返回：
    - 推荐科室列表
    - 可直接跳转的挂号链接参数
    """
    from pydantic import BaseModel

    class VoiceResult(BaseModel):
        guided_dept: str | None = None
        search_keyword: str
        suggestion: str

    # 复用导诊引擎（Dify 优先）
    guide_result = await guide_diagnose(GuideRequest(symptom_text=voice_text))
    top_dept = guide_result.results[0].dept_name if guide_result.results else None

    return ApiResponse.ok({
        "guided_dept": top_dept,
        "search_keyword": voice_text,
        "suggestion": f"建议挂【{top_dept}】" if top_dept else "未匹配到科室，请重新描述",
        "navigate_to": f"/reserve?dept={top_dept}" if top_dept else None,
        "emergency_flag": guide_result.emergency_flag,
    })
