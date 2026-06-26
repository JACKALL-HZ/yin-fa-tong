"""体检指标解读模板引擎（规则引擎，非大模型）"""

# ---------- 单指标判定规则 ----------

def _judge_blood_pressure(systolic: float | None, diastolic: float | None) -> str:
    """血压解读（单位 mmHg）"""
    if systolic is None or diastolic is None:
        return ""
    if systolic < 90 or diastolic < 60:
        return f"血压偏低（{systolic}/{diastolic} mmHg），建议适当补充营养，起身时动作放慢，避免头晕跌倒。"
    if systolic <= 120 and diastolic <= 80:
        return f"血压正常（{systolic}/{diastolic} mmHg），继续保持健康生活方式。"
    if systolic <= 140 and diastolic <= 90:
        return f"血压正常高值（{systolic}/{diastolic} mmHg），建议减少盐摄入，适量运动，定期监测。"
    if systolic <= 160 or diastolic <= 100:
        return f"血压偏高（{systolic}/{diastolic} mmHg），建议尽早就医评估，低盐饮食，遵医嘱服药。"
    return f"血压明显升高（{systolic}/{diastolic} mmHg），请尽快就医，切勿拖延。"


def _judge_glucose(glucose: float | None) -> str:
    """空腹血糖解读（单位 mmol/L）"""
    if glucose is None:
        return ""
    if glucose < 3.9:
        return f"空腹血糖偏低（{glucose} mmol/L），可能出现心慌、出冷汗，建议随身带糖果，及时进食。"
    if glucose <= 6.1:
        return f"空腹血糖正常（{glucose} mmol/L），继续保持。"
    if glucose < 7.0:
        return f"空腹血糖偏高（{glucose} mmol/L），属于糖尿病前期，建议控制饮食、增加运动、定期复查。"
    return f"空腹血糖明显升高（{glucose} mmol/L），可能已患糖尿病，请尽早就医，严格控制饮食。"


def _judge_lipids(tc: float | None, tg: float | None, hdl: float | None, ldl: float | None) -> str:
    """血脂解读"""
    parts = []
    if tc is not None:
        if tc < 5.2:
            parts.append(f"总胆固醇正常（{tc} mmol/L）")
        elif tc < 6.2:
            parts.append(f"总胆固醇偏高（{tc} mmol/L），建议低脂饮食、增加运动")
        else:
            parts.append(f"总胆固醇明显升高（{tc} mmol/L），建议就医评估，可能需要药物治疗")
    if tg is not None:
        if tg < 1.7:
            parts.append(f"甘油三酯正常（{tg} mmol/L）")
        elif tg < 2.3:
            parts.append(f"甘油三酯偏高（{tg} mmol/L），减少油腻食物和甜食")
        else:
            parts.append(f"甘油三酯明显升高（{tg} mmol/L），建议就医评估")
    if hdl is not None:
        if hdl >= 1.0:
            parts.append(f"高密度脂蛋白（好胆固醇）正常（{hdl} mmol/L）")
        else:
            parts.append(f"高密度脂蛋白偏低（{hdl} mmol/L），建议增加有氧运动")
    if ldl is not None:
        if ldl < 3.4:
            parts.append(f"低密度脂蛋白（坏胆固醇）正常（{ldl} mmol/L）")
        elif ldl < 4.1:
            parts.append(f"低密度脂蛋白偏高（{ldl} mmol/L），注意饮食控制")
        else:
            parts.append(f"低密度脂蛋白明显升高（{ldl} mmol/L），建议就医评估")
    return "；".join(parts) if parts else ""


def _judge_uric_acid(ua: float | None) -> str:
    if ua is None:
        return ""
    if ua <= 420:
        return f"尿酸正常（{ua} μmol/L）"
    if ua <= 540:
        return f"尿酸偏高（{ua} μmol/L），建议多喝水、少吃海鲜内脏、少喝啤酒"
    return f"尿酸明显升高（{ua} μmol/L），有痛风风险，建议就医"


def _judge_creatinine(creatinine: float | None) -> str:
    """血肌酐解读（单位 μmol/L）"""
    if creatinine is None:
        return ""
    if 44 <= creatinine <= 133:
        return f"血肌酐正常（{creatinine} μmol/L），肾功能良好。"
    if creatinine < 44:
        return f"血肌酐偏低（{creatinine} μmol/L），可能与营养不良或肌肉量不足有关，建议加强营养。"
    if creatinine <= 177:
        return f"血肌酐偏高（{creatinine} μmol/L），建议多喝水、减少高蛋白饮食，定期复查肾功能。"
    return f"血肌酐明显升高（{creatinine} μmol/L），提示肾功能受损，请尽快就医。"


def _judge_blood_routine(wbc: float | None, hgb: float | None, plt: float | None) -> str:
    """血常规解读：白细胞(WBC)×10⁹/L、血红蛋白(HGB)g/L、血小板(PLT)×10⁹/L"""
    parts = []
    if wbc is not None:
        if 4.0 <= wbc <= 10.0:
            parts.append(f"白细胞正常（{wbc}×10⁹/L）")
        elif wbc < 4.0:
            parts.append(f"白细胞偏低（{wbc}×10⁹/L），免疫力可能下降，注意防感染")
        else:
            parts.append(f"白细胞偏高（{wbc}×10⁹/L），可能有感染或炎症，建议就医排查")
    if hgb is not None:
        if hgb >= 120:
            parts.append(f"血红蛋白正常（{hgb} g/L）")
        elif hgb >= 90:
            parts.append(f"血红蛋白轻度偏低（{hgb} g/L），建议多吃红肉、动物肝脏等含铁食物")
        else:
            parts.append(f"血红蛋白明显偏低（{hgb} g/L），提示贫血，请就医进一步检查")
    if plt is not None:
        if 100 <= plt <= 300:
            parts.append(f"血小板正常（{plt}×10⁹/L）")
        elif plt < 100:
            parts.append(f"血小板偏低（{plt}×10⁹/L），凝血功能可能受影响，建议就医")
        else:
            parts.append(f"血小板偏高（{plt}×10⁹/L），建议就医排查原因")
    return "；".join(parts) if parts else ""


def _judge_liver(alt: float | None, ast: float | None) -> str:
    parts = []
    if alt is not None:
        if alt <= 40:
            parts.append(f"谷丙转氨酶正常（{alt} U/L）")
        elif alt <= 80:
            parts.append(f"谷丙转氨酶轻度升高（{alt} U/L），注意休息，避免饮酒")
        else:
            parts.append(f"谷丙转氨酶明显升高（{alt} U/L），提示肝细胞损伤，建议就医")
    if ast is not None:
        if ast <= 40:
            parts.append(f"谷草转氨酶正常（{ast} U/L）")
        elif ast <= 80:
            parts.append(f"谷草转氨酶轻度升高（{ast} U/L），注意休息")
        else:
            parts.append(f"谷草转氨酶明显升高（{ast} U/L），建议就医")
    return "；".join(parts) if parts else ""


# ---------- 综合解读 ----------

def interpret(indicators: dict) -> str:
    """
    对 OCR 提取的指标字典进行通俗化解读
    返回适合老年用户阅读的通俗文字
    """
    if not indicators:
        return "未能从报告中识别出体检指标，请确认图片清晰度或手动输入指标数值。"

    sections = []

    bp = _judge_blood_pressure(indicators.get("收缩压"), indicators.get("舒张压"))
    if bp:
        sections.append(bp)

    glu = _judge_glucose(indicators.get("空腹血糖"))
    if glu:
        sections.append(glu)

    lipids = _judge_lipids(
        indicators.get("总胆固醇"), indicators.get("甘油三酯"),
        indicators.get("高密度脂蛋白"), indicators.get("低密度脂蛋白"),
    )
    if lipids:
        sections.append(lipids)

    ua = _judge_uric_acid(indicators.get("尿酸"))
    if ua:
        sections.append(ua)

    liver = _judge_liver(indicators.get("谷丙转氨酶"), indicators.get("谷草转氨酶"))
    if liver:
        sections.append(liver)

    cr = _judge_creatinine(indicators.get("肌酐"))
    if cr:
        sections.append(cr)

    blood = _judge_blood_routine(indicators.get("白细胞"), indicators.get("血红蛋白"), indicators.get("血小板"))
    if blood:
        sections.append(blood)

    if not sections:
        sections.append("识别到的指标均在正常范围内，请继续保持健康生活方式。")

    # 添加免责声明
    disclaimer = "\n\n【免责声明】以上解读仅供参考，不构成医疗诊断。如有不适，请及时就医。"
    return "\n\n".join(sections) + disclaimer
