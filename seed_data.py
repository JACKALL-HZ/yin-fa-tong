"""种子数据脚本 - 为银发通项目填充医院/科室/医生/排班/志愿者数据"""
import requests
import random
from datetime import date, timedelta

BASE = "http://localhost:8000/api"
HEADERS = {"Content-Type": "application/json"}

# ======== 1. 管理员登录 ========
def login():
    # 尝试登录已存在的 admin
    r = requests.post(f"{BASE}/auth/login", json={"username": "admin_yft", "password": "123456"})
    if r.status_code == 200:
        print("[OK] 管理员登录成功")
        return r.json()["data"]["access_token"]
    # 注册新管理员
    r = requests.post(f"{BASE}/auth/register", json={"username": "admin_yft", "password": "123456", "user_type": 3})
    if r.status_code == 200:
        print("[OK] 管理员注册+登录成功")
        return r.json()["data"]["access_token"]
    raise Exception(f"登录失败: {r.text}")

token = login()
AUTH = {**HEADERS, "Authorization": f"Bearer {token}"}

# ======== 2. 医院数据 ========
hospitals = [
    {"hospital_name": "北京协和医院", "hospital_level": "三级甲等", "address": "北京市东城区帅府园一号", "phone": "010-69156114"},
    {"hospital_name": "北京大学第三医院", "hospital_level": "三级甲等", "address": "北京市海淀区花园北路49号", "phone": "010-82266699"},
    {"hospital_name": "北京安贞医院", "hospital_level": "三级甲等", "address": "北京市朝阳区安贞路2号", "phone": "010-64412431"},
    {"hospital_name": "上海市第六人民医院", "hospital_level": "三级甲等", "address": "上海市徐汇区宜山路600号", "phone": "021-64369181"},
    {"hospital_name": "中山大学附属第一医院", "hospital_level": "三级甲等", "address": "广州市越秀区中山二路58号", "phone": "020-87755766"},
    {"hospital_name": "杭州市第一人民医院", "hospital_level": "二级甲等", "address": "杭州市上城区浣纱路261号", "phone": "0571-87065701"},
    {"hospital_name": "南京市鼓楼医院", "hospital_level": "二级甲等", "address": "南京市鼓楼区中山路321号", "phone": "025-83106666"},
    {"hospital_name": "银发通社区合作医院", "hospital_level": "一级", "address": "社区就近服务网点", "phone": "400-888-0001"},
]
hospital_ids = []
for h in hospitals:
    r = requests.post(f"{BASE}/hospitals", json=h, headers=AUTH)
    if r.status_code == 200:
        hid = r.json()["data"]["id"]
        hospital_ids.append(hid)
        print(f"  [OK] 医院: {h['hospital_name']} (id={hid})")
    else:
        print(f"  [!] 医院创建失败 {h['hospital_name']}: {r.text}")

# ======== 3. 科室数据 ========
dept_templates = [
    "心血管内科", "呼吸内科", "消化内科", "神经内科",
    "骨科", "普通外科", "泌尿外科",
    "妇产科", "儿科", "眼科", "耳鼻喉科",
    "皮肤科", "内分泌科", "中医科", "口腔科",
]
# 为每个科室定义一个"擅长领域"描述，后续给医生生成用
dept_specialty_map = {
    "心血管内科": ["冠心病介入治疗", "心律失常射频消融", "高血压综合管理", "心力衰竭诊治", "心脏起搏器植入"],
    "呼吸内科": ["慢性阻塞性肺病", "支气管哮喘", "肺部肿瘤早期诊断", "睡眠呼吸障碍", "间质性肺病"],
    "消化内科": ["胃食管反流病", "幽门螺杆菌根除", "肝硬化门脉高压", "炎症性肠病", "消化道早癌筛查"],
    "神经内科": ["脑血管病急性期治疗", "帕金森病综合管理", "癫痫精准用药", "阿尔茨海默病", "头痛眩晕专病"],
    "骨科": ["关节置换术", "脊柱微创手术", "运动损伤康复", "骨折创伤修复", "骨质疏松综合治疗"],
    "普通外科": ["腹腔镜胆囊切除术", "疝气无张力修补", "甲状腺癌根治术", "胃癌D2根治术", "结直肠癌腹腔镜手术"],
    "泌尿外科": ["经尿道前列腺电切", "输尿管软镜碎石", "肾癌保留肾单位手术", "膀胱肿瘤电切", "前列腺癌根治术"],
    "妇产科": ["高危妊娠管理", "无痛分娩", "宫腔镜子宫肌瘤切除", "宫颈癌筛查", "更年期综合管理"],
    "儿科": ["小儿哮喘防治", "新生儿黄疸诊治", "儿童生长发育评估", "小儿先天性心脏病", "过敏性疾病"],
    "眼科": ["白内障超声乳化", "青光眼微创手术", "近视激光矫正", "糖尿病视网膜病变", "干眼症综合治疗"],
    "耳鼻喉科": ["鼻内镜鼻窦手术", "中耳炎显微手术", "声带息肉微创", "过敏性鼻炎免疫治疗", "OSAS综合治疗"],
    "皮肤科": ["银屑病生物制剂治疗", "痤疮综合治疗", "特应性皮炎", "皮肤美容激光", "皮肤肿瘤切除"],
    "内分泌科": ["2型糖尿病综合管理", "甲状腺结节消融", "肥胖症代谢手术评估", "骨质疏松防治", "痛风规范化治疗"],
    "中医科": ["脾胃病针灸调理", "颈腰椎病正骨", "失眠中药治疗", "肿瘤术后扶正", "妇科月经不调"],
    "口腔科": ["种植牙修复", "隐形正畸", "牙周病系统治疗", "儿童龋齿防治", "口腔颌面外科"],
}
dept_ids = {}  # {(hospital_id, dept_name): dept_id}
for hid in hospital_ids:
    # 每个医院随机选 10-15 个科室
    n = random.randint(10, 15)
    chosen = random.sample(dept_templates, n)
    for dn in chosen:
        r = requests.post(f"{BASE}/departments", json={"hospital_id": hid, "dept_name": dn}, headers=AUTH)
        if r.status_code == 200:
            did = r.json()["data"]["id"]
            dept_ids[(hid, dn)] = did
        else:
            print(f"  [!] 科室创建失败 hid={hid} {dn}: {r.status_code}")
print(f"  [OK] 总共创建 {len(dept_ids)} 个科室")

# ======== 4. 医生数据 ========
titles = ["主任医师", "副主任医师", "主治医师", "主治医师", "住院医师"]
title_weights = [1, 2, 4, 4, 3]  # 住院医师和主治医师偏多

# 中文姓名库
surnames = ["王", "李", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴", "徐", "孙", "马", "朱", "胡", "郭", "何", "高", "林", "郑"]
given_names = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "洋", "涛", "军", "杰", "秀英", "建国", "志强", "文博", "浩然", "雨桐", "思远", "晓明"]

all_doctor_ids = []
for (hid, dn), did in dept_ids.items():
    n_doctors = random.randint(1, 4)
    specialties = dept_specialty_map.get(dn, ["全科诊疗"])
    for _ in range(n_doctors):
        name = random.choice(surnames) + random.choice(given_names)
        title = random.choices(titles, weights=title_weights, k=1)[0]
        specialty = random.choice(specialties)
        fee = {"主任医师": 50, "副主任医师": 30, "主治医师": 20, "住院医师": 10}.get(title, 15)
        r = requests.post(f"{BASE}/doctors", json={
            "dept_id": did,
            "doctor_name": name,
            "doctor_title": title,
            "specialty": specialty,
            "register_fee": fee,
        }, headers=AUTH)
        if r.status_code == 200:
            all_doctor_ids.append(r.json()["data"]["id"])
        else:
            print(f"  [!] 医生创建失败: {r.status_code}")
print(f"  [OK] 总共创建 {len(all_doctor_ids)} 位医生")

# ======== 5. 排班数据（未来7天） ========
today = date.today()
schedule_count = 0
for doc_id in all_doctor_ids:
    # 每位医生随机排 2-5 天
    days = random.randint(2, 5)
    work_dates = random.sample([today + timedelta(days=i) for i in range(1, 8)], days)
    for wd in work_dates:
        period = random.choice(["AM", "PM", "ALL"])
        normal_num = random.randint(20, 50)
        elder_num = random.randint(5, 15)
        r = requests.post(f"{BASE}/schedules", json={
            "doctor_id": doc_id,
            "work_date": wd.isoformat(),
            "time_period": period,
            "normal_num": normal_num,
            "elder_priority_num": elder_num,
        }, headers=AUTH)
        if r.status_code == 200:
            schedule_count += 1
        else:
            print(f"  [!] 排班创建失败: doc={doc_id} date={wd} status={r.status_code}")
print(f"  [OK] 总共创建 {schedule_count} 条排班")

# ======== 6. 志愿者数据 ========
volunteers = [
    {"vol_name": "张阿姨", "vol_phone": "13900001001", "service_dept": "心血管内科", "service_desc": "退休护士，有30年护理经验，熟悉医院流程，热情细心。", "status": 1},
    {"vol_name": "李义工", "vol_phone": "13900001002", "service_dept": "骨科", "service_desc": "大学生志愿者，参加过多次敬老公益活动，能帮助推轮椅和挂号。", "status": 1},
    {"vol_name": "王大姐", "vol_phone": "13900001003", "service_dept": "眼科", "service_desc": "社区志愿者，擅长为视力不便的长辈读报告和引导就诊。", "status": 1},
    {"vol_name": "刘同学", "vol_phone": "13900001004", "service_dept": "儿科", "service_desc": "医学院大四学生，可协助长辈完成挂号、取药等流程。", "status": 1},
    {"vol_name": "赵老师", "vol_phone": "13900001005", "service_dept": "妇产科", "service_desc": "退休教师，性格温和，擅长沟通，7年陪诊经验。", "status": 1},
    {"vol_name": "陈阿姨", "vol_phone": "13900001006", "service_dept": "中医科", "service_desc": "熟悉常见老年慢性病管理，能协助长辈与医生有效沟通病史。", "status": 1},
    {"vol_name": "孙义工", "vol_phone": "13900001007", "service_dept": "神经内科", "service_desc": "耐心细致，长期服务阿尔茨海默病老人，有专业护理知识。", "status": 1},
    {"vol_name": "周大哥", "vol_phone": "13900001008", "service_dept": "消化内科", "service_desc": "退役军人，体力好，可协助行动不便的长辈上下楼。", "status": 1},
]
vol_count = 0
for v in volunteers:
    r = requests.post(f"{BASE}/volunteers", json=v, headers=AUTH)
    if r.status_code == 200:
        vol_count += 1
    else:
        print(f"  [!] 志愿者创建失败 {v['vol_name']}: {r.status_code}")
print(f"  [OK] 总共创建 {vol_count} 位志愿者")

# ======== 7. 汇总 ========
print()
print("=" * 50)
print(f"  种子数据填充完成！")
print(f"  医院: {len(hospital_ids)} 家")
print(f"  科室: {len(dept_ids)} 个")
print(f"  医生: {len(all_doctor_ids)} 位")
print(f"  排班: {schedule_count} 条")
print(f"  志愿者: {vol_count} 位")
print("=" * 50)
print(f"  挂号可用日期: {today + timedelta(days=1)} ~ {today + timedelta(days=7)}")
print(f"  管理员: admin_yft / 123456")
print(f"  前端: http://localhost")
print("=" * 50)
