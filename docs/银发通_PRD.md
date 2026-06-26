5. # 银发通（Silver Hair Connect）产品需求文档

  ------

  ## 文档信息

  | 项目         | 内容                                        |
  | ------------ | ------------------------------------------- |
  | **文档名称** | 银发通 PRD（Product Requirements Document） |
  | **文档版本** | v1.0                                        |
  | **创建日期** | 202X-XX-XX                                  |
  | **项目名称** | 银发通——适老化智慧就医服务平台              |
  | **产品定位** | 面向老年群体的轻量化便民就医辅助系统        |
  | **文档状态** | 初稿 / 待评审                               |

  ------

  ## 目录

  1. [项目概述](https://www.yuque.com/jackal-uhpvg/mng24m/eyfarlg0wq2vrubk#1-项目概述)
  2. [整体技术架构说明](https://www.yuque.com/jackal-uhpvg/mng24m/eyfarlg0wq2vrubk#2-整体技术架构说明)
  3. [功能需求](https://www.yuque.com/jackal-uhpvg/mng24m/eyfarlg0wq2vrubk#3-功能需求)
  4. [数据库设计](https://www.yuque.com/jackal-uhpvg/mng24m/eyfarlg0wq2vrubk#4-数据库设计)
  5. [项目数据模拟说明](https://www.yuque.com/jackal-uhpvg/mng24m/eyfarlg0wq2vrubk#5-项目数据模拟说明)
  6. [非功能性需求](https://www.yuque.com/jackal-uhpvg/mng24m/eyfarlg0wq2vrubk#6-非功能性需求)
  7. [风险评估与对策](https://www.yuque.com/jackal-uhpvg/mng24m/eyfarlg0wq2vrubk#7-风险评估与对策)
  8. [项目验收标准](https://www.yuque.com/jackal-uhpvg/mng24m/eyfarlg0wq2vrubk#8-项目验收标准)
  9. [项目总结](https://www.yuque.com/jackal-uhpvg/mng24m/eyfarlg0wq2vrubk#9-项目总结)

  ------

  ## 1. 项目概述

  ### 1.1 项目背景

  当前数字化医疗全面普及，但老年群体普遍存在数字鸿沟，线下就医痛点突出：老年人不会自主线上挂号缴费、线下就医排队耗时久、无法精准描述病症匹配科室、无法自主查看候诊叫号进度，异地子女也无法便捷陪同代办就医业务。

  国家卫健委持续推进医疗机构适老化线上就医服务建设，要求就医平台配备长者极简界面、亲友代办、语音交互、老年专属号源等普惠便民功能。

  本项目基于 Vue3+TS、FastAPI、MySQL、Redis、Elasticsearch、Python 全套Python技术栈搭建银发通——适老化智慧就医服务平台，精简冗余架构，由FastAPI承载全部业务+定时任务能力，聚焦社区合作医院轻量化就医场景，锚定三大核心主打业务：

  - 线上预约挂号+智能候诊提醒
  - AI本地化智能导诊
  - 公益志愿者一对一陪诊（项目核心创新点）

  专项解决老年群体就医难、分诊难、无人陪护就医痛点，兼顾子女远程代办、医院后台简易运维能力，打通智能分诊、分时挂号、排队提醒、线上缴费、陪诊预约、消息通知全便民流程。项目摒弃大型互联网医院繁重业务，业务体量适配本科毕业设计开发、答辩评审标准。

  ### 1.2 核心痛点分析

  #### 1.2.1 老年患者端

  1. 常规就医软件字体偏小、功能繁杂、操作链路长，老年人学习使用成本极高；
  2. 线下人工窗口挂号、缴费排队时长较长，老年人体力不足，就医便捷度低；
  3. 老年人病症表述能力有限，盲目自选科室挂号，极易出现挂错科室、就医低效问题；
  4. 无标准化候诊编号，无法实时查看排队进度，只能长时间在诊室门口等候；
  5. 子女异地生活，无法代为挂号分诊、陪同就诊，高龄失能老人无专属陪护人员就医，市面就医平台缺少轻量化公益陪诊预约渠道。

  #### 1.2.2 子女代办端

  1. 无专属入口统一绑定多位长辈信息，长辈挂号、体检代办流程繁琐；
  2. 无法协助老人精准分诊挂号、实时接收候诊进度，无正规平台可预约线下陪护人员陪同就医。

  #### 1.2.3 医院运营端

  1. 线下人工窗口客流集中，医院人力运营成本偏高；
  2. 老年优先号源无系统化管控，号源并发预约易超卖、丢失，且无异常回滚补救机制；
  3. 缺少可视化数据看板，无法统计就诊高峰、号源使用、陪诊订单核心运营数据；
  4. 医院、科室、医生无标准化关联架构，人员、排班业务管理混乱。

  ### 1.3 项目目标

  #### 1.3.1 业务目标（四级功能分层）

  本次项目严格按照开发优先级、答辩权重，划分为四大层级：P0核心必做功能、P1增强加分功能、P2特色亮点功能、后台管理功能，层级边界清晰，可直接拆分AI开发任务，答辩层级逻辑直观易懂。

  | 功能层级           | 模块数量 | 核心目标                                             |
  | ------------------ | -------- | ---------------------------------------------------- |
  | **P0核心必做功能** | 13个     | 搭建就医基础闭环，覆盖挂号、缴费、候诊、消息核心链路 |
  | **P1增强加分功能** | 4个      | 优化适老就医体验，提升产品易用性                     |
  | **P2特色亮点功能** | 3个      | 打造项目差异化创新点，突出毕设竞争力                 |
  | **后台管理功能**   | 7个      | 支撑平台简易运维，保障业务正常运转                   |

  **P0核心必做功能核心落地目标：**

  1. 搭建长者模式+子女标准版双UI界面，适配老人自主操作、子女远程代办分诊挂号双场景；
  2. 打造核心业务一：分时线上预约挂号+全流程候诊提醒，配置20%老年专属优先号源，新增Redis号源异常回滚机制；
  3. 打造核心业务二：本地化AI智能导诊服务，适配方言口语问诊，辅助老人自主匹配科室；
  4. 打造核心创新业务三：线上公益陪诊申请报备，用户自主挑选适配科室志愿者提交就医陪诊申请；
  5. 搭建医院管理后台，统一运维号源、志愿者、排班、就诊全量数据。

  #### 1.3.2 技术目标

  1. 体检报告本地AI大白话通俗解读，联动陪诊业务完成后续健康答疑；
  2. 志愿者服务评价体系，优化核心陪诊业务服务质量；
  3. Redis缓存管控号源，搭载原子扣减+业务异常自动回滚机制，高并发挂号无号源超卖、丢失，接口响应≤200ms；
  4. Elasticsearch仅同步四类数据，实现方言、模糊语义检索，精简索引冗余；
  5. 优化RabbitMQ架构，仅保留Direct直连、Delay延迟双交换机，适配毕设体量；
  6. 整合后端架构，FastAPI统一承载全部业务接口、后台定时任务；
  7. 实现首页一键切换双UI模式，适配不同人群操作习惯；
  8. 优化密码加密体系，统一使用bcrypt加密算法，符合后端安全开发规范。

  ### 1.4 目标用户画像

  | 角色               | 描述                                   | 核心诉求                                                     |
  | ------------------ | -------------------------------------- | ------------------------------------------------------------ |
  | **老年患者**       | 60岁及以上老年群体，移动端操作能力薄弱 | 大字体、高对比配色、语音操控、极简按钮；双登录方式降低门槛；便捷挂号/候诊 |
  | **子女代办用户**   | 中青年异地子女                         | 绑定多名长辈信息，远程完成挂号、缴费、候诊查看、报告查询全代办操作 |
  | **医院运营管理员** | 医院后台工作人员                       | 基础信息维护、号源排班配置、数据运营查看；后台白名单准入保障安全 |

  ------

  ## 2. 整体技术架构说明

  ### 2.1 分层闭环架构

  ```plain
  银发通平台
  ├── 前端层 (Vue3 + TypeScript + Element Plus)
  │   ├── H5就医用户端（长者模式/子女标准版双UI）
  │   └── PC医院管理端（数据可视化、简易运维）
  ├── 后端层 (FastAPI 一站式服务)
  │   ├── 业务接口（用户/挂号/缴费/导诊/陪诊/后台管理）
  │   ├── 定时任务（APScheduler：号源同步/超时回收/健康提醒）
  │   └── 中间件集成（Redis/MQ/ES/语音识别）
  ├── 数据层
  │   ├── MySQL（结构化业务数据持久化）
  │   ├── Redis（号源/候诊/Token缓存，Lua原子操作）
  │   ├── Elasticsearch（四类基础数据检索）
  │   └── RabbitMQ（双交换机：Direct/Delay）
  └── 部署层 (Docker + Docker Compose)
      ├── 容器化打包所有组件
      ├── Nginx反向代理（HTTPS配置）
      └── 阿里云ECS部署
  ```

  ### 2.2 核心中间件用途

  | 中间件            | 核心用途                                                     | 优化策略                             |
  | ----------------- | ------------------------------------------------------------ | ------------------------------------ |
  | **Redis**         | 缓存号源/候诊数据/Token；接口限流；Lua原子扣减号源           | 仅缓存核心业务数据，异常自动回滚     |
  | **Elasticsearch** | 医院/科室/医生/症状词库模糊/方言检索                         | 仅同步四类基础数据，降低检索压力     |
  | **RabbitMQ**      | 消息推送（挂号/候诊/陪诊提醒）；延时任务（超时取消/健康提醒） | 仅保留Direct/Delay双交换机，剔除冗余 |

  ------

  ## 3. 功能需求

  ### 3.1 功能全景图

  ```plain
  银发通平台
  ├── 前端用户端 (H5)
  │   ├── 通用模块
  │   │   ├── 用户登录注册（账号密码/模拟微信授权）
  │   │   ├── 长辈绑定（增删改查长辈就医信息）
  │   │   ├── 双模式界面切换（长者极简/子女标准）
  │   │   └── 消息中心（全平台提醒落库查看）
  │   ├── P0核心模块
  │   │   ├── 医院-科室-医生-排班四级查询
  │   │   ├── 挂号预约（自主/老年优先/子女代办）
  │   │   ├── 预约订单管理（多状态筛选/取消）
  │   │   ├── 在线缴费（挂号/检查/医药费用）
  │   │   ├── 候诊排队（实时叫号/排队进度）
  │   │   └── 就诊提醒（挂号/候诊/到号通知）
  │   ├── P1增强模块
  │   │   ├── AI智能导诊（文字/方言症状匹配科室）
  │   │   ├── 语音挂号（语音指令检索/挂号）
  │   │   ├── 健康提醒（用药/复诊/体检定时提醒）
  │   │   └── 运营数据查看（仅管理员可见）
  │   └── P2特色模块
  │       ├── 体检报告AI解读（OCR识别+通俗解读）
  │       ├── 志愿者信息查看（资质/评分/服务科室）
  │       └── 陪诊预约申请（自选志愿者+提交报备）
  └── 后台管理端 (PC)
      ├── 基础信息管理（医院/科室/医生）
      ├── 排班号源管理（出诊时段/老年号配置）
      ├── 志愿者管理（信息录入/状态管控）
      ├── 订单管理（挂号/陪诊订单核销/审核）
      ├── 用户管理（账号查看/权限管控）
      └── 数据统计看板（挂号量/号源占比/科室热度）
  
  ```
  ### 3.2 后端项目结构（Feature-First）
  
  本系统采用 Feature-First（按业务领域划分）分包方式，将挂号预约、候诊排队、陪诊服务、健康提醒等核心业务独立封装为模块。每个模块内部包含 Router、Service、Repository、Schema、Model 等组件，实现高内聚、低耦合设计，便于后续功能扩展和团队协作开发。
  
  ```text
  backend/
  ├── app/
  │
  ├── main.py                         # FastAPI应用入口
  ├── config.py                       # 系统配置
  ├── dependencies.py                 # 全局依赖注入
  │
  ├── middleware/
  │   ├── cors.py                     # 跨域配置
  │   ├── request_id.py               # 请求追踪
  │   └── logging.py                  # 请求日志
  │
  ├── exception/
  │   ├── base.py                     # 自定义异常
  │   └── handler.py                  # 全局异常处理
  │
  ├── shared/
  │   ├── database.py                 # MySQL连接管理
  │   ├── redis.py                    # Redis客户端
  │   ├── rabbitmq.py                 # RabbitMQ客户端
  │   ├── elasticsearch.py            # Elasticsearch客户端
  │   ├── pagination.py               # 分页工具
  │   └── response.py                 # 统一响应结构
  │
  ├── auth/                           # 认证授权模块
  │   ├── router.py
  │   ├── service.py
  │   ├── schemas.py
  │   ├── models.py
  │   ├── repository.py
  │   └── utils.py
  │
  ├── user/                           # 用户中心模块
  │   ├── router.py
  │   ├── service.py
  │   ├── schemas.py
  │   ├── models.py
  │   └── repository.py
  │
  ├── hospital/                       # 医院管理模块
  │   ├── router.py
  │   ├── service.py
  │   ├── schemas.py
  │   ├── models.py
  │   └── repository.py
  │
  ├── department/                     # 科室管理模块
  │
  ├── doctor/                         # 医生管理模块
  │
  ├── schedule/                       # 排班管理模块
  │
  ├── reserve/                        # 挂号预约模块
  │   ├── router.py
  │   ├── service.py
  │   ├── schemas.py
  │   ├── models.py
  │   ├── repository.py
  │   ├── cache/
  │   │   └── source_cache.py
  │   └── mq/
  │       ├── producer.py
  │       └── consumer.py
  │
  ├── queue/                          # 候诊排队模块
  │
  ├── payment/                        # 在线缴费模块
  │
  ├── guide/                          # 智能导诊模块
  │   ├── symptom_dict/
  │   └── service.py
  │
  ├── search/                         # 搜索模块（ES）
  │   ├── document/
  │   ├── sync/
  │   └── service.py
  │
  ├── reminder/                       # 健康提醒模块
  │   ├── router.py
  │   ├── service.py
  │   ├── scheduler/
  │   └── mq/
  │
  ├── message/                        # 消息中心模块
  │
  ├── accompany/                      # 陪诊服务模块
  │   ├── volunteer/
  │   ├── order/
  │   └── review/
  │
  ├── report/                         # 体检报告模块
  │   ├── ocr/
  │   ├── template/
  │   └── service.py
  │
  ├── statistics/                     # 数据统计模块
  │   ├── dashboard.py
  │   └── service.py
  │
  ├── alembic/                        # 数据库迁移
  │
  ├── tests/                          # 单元测试
  │
  ├── Dockerfile
  ├── requirements.txt
  └── .env.example
  ```
  
  ---
  
  ### 3.3 前端项目结构
  
  前端采用 Vue3 + TypeScript + Pinia + Vue Router 技术栈，按照业务功能进行模块化划分，实现页面、状态管理、接口调用与业务逻辑解耦，提高项目可维护性和扩展性。
  
  ```text
  frontend/
  ├── src/
  │
  ├── main.ts                         # 应用入口
  ├── App.vue                         # 根组件
  │
  ├── router/
  │   ├── index.ts
  │   ├── modules/
  │   │   ├── user.ts
  │   │   ├── reserve.ts
  │   │   ├── accompany.ts
  │   │   └── admin.ts
  │   └── guards.ts
  │
  ├── stores/
  │   ├── user.ts
  │   ├── reserve.ts
  │   ├── message.ts
  │   └── app.ts
  │
  ├── api/
  │   ├── auth.ts
  │   ├── user.ts
  │   ├── hospital.ts
  │   ├── department.ts
  │   ├── doctor.ts
  │   ├── schedule.ts
  │   ├── reserve.ts
  │   ├── payment.ts
  │   ├── queue.ts
  │   ├── guide.ts
  │   ├── accompany.ts
  │   ├── reminder.ts
  │   ├── report.ts
  │   └── statistics.ts
  │
  ├── views/
  │
  │   ├── login/
  │
  │   ├── home/
  │
  │   ├── hospital/
  │
  │   ├── reserve/
  │   │   ├── ReserveView.vue
  │   │   ├── MyReserveView.vue
  │   │   └── QueueView.vue
  │
  │   ├── reminder/
  │
  │   ├── accompany/
  │   │   ├── VolunteerList.vue
  │   │   ├── VolunteerDetail.vue
  │   │   ├── ApplyView.vue
  │   │   └── ReviewView.vue
  │
  │   ├── report/
  │
  │   ├── message/
  │
  │   └── admin/
  │       ├── hospital/
  │       ├── doctor/
  │       ├── schedule/
  │       ├── reserve/
  │       ├── accompany/
  │       ├── user/
  │       └── dashboard/
  │
  ├── components/
  │   ├── common/
  │   ├── layout/
  │   └── business/
  │
  ├── composables/
  │
  ├── utils/
  │
  ├── types/
  │
  └── assets/
  │
  ├── public/
  ├── vite.config.ts
  ├── tsconfig.json
  ├── package.json
  └── .env.example
  ```
  
  ### 分包设计说明
  
  本系统采用前后端分离架构，并遵循 Feature-First 分包原则。后端按照业务领域划分为用户中心、医院管理、挂号预约、陪诊服务、健康提醒等多个独立模块，每个模块拥有完整的控制层、业务层和数据访问层结构。前端则按照业务页面划分目录，实现路由、状态管理和接口层的模块化管理。
  
  这种设计方式能够有效降低模块间耦合度，提高代码复用率，便于后续功能扩展和系统维护，同时符合现代互联网项目及企业级项目开发规范。
  ### 3.4 核心业务流程

  #### 3.4.1 挂号预约主流程

  ```plain
  用户登录 → 选择模式（长者/子女）
      → （子女模式）绑定/选择长辈 → 医院-科室-医生-排班查询
      → 选择号源（老年优先/普通）→ 提交预约订单
      → 在线缴费 → 生成候诊编号 → 实时查看候诊进度
      → 接收候诊提醒 → 就诊完成
      → （超时未支付）Delay交换机自动取消订单 → 号源回收
  ```

  #### 3.4.2 陪诊预约主流程（核心创新点）

  ```plain
  子女登录 → 绑定长辈 → 查看在岗志愿者列表（资质/评分/科室）
      → 自选志愿者 → 填写陪诊日期/科室 → 提交陪诊申请
      → 后端生成待审核订单 → Direct交换机推送管理员通知
      → 管理员审核订单 → 订单流转至待服务
      → 志愿者履约陪护 → 服务完结 → 用户评价 → 更新志愿者评分/服务次数
  ```

  ### 3.5 功能详细设计

  #### 3.5.1 P0核心功能详细设计

  | 模块             | 业务场景                       | 核心流程/规则                                                |
  | ---------------- | ------------------------------ | ------------------------------------------------------------ |
  | **用户登录注册** | 三类角色登录，规避微信资质限制 | 1. 手机号+密码注册（bcrypt加密） 2. 账号密码/模拟微信授权登录 3. JWT鉴权+Redis缓存状态 4. 管理员白名单准入后台 |
  | **长辈绑定**     | 子女代办核心前置功能           | 1. 增删改查长辈信息（姓名/医保/生日/电话） 2. 绑定后可代长辈完成全流程就医操作 |
  | **双模式界面**   | 适配不同用户操作习惯           | 【长者模式】：超大字体+高对比配色+四大核心入口 【子女模式】：全功能入口，支持代办全操作 |
  | **四级查询**     | 挂号前置基础功能               | 医院→科室→医生→排班四级联动；展示号源剩余数量（普通/老年）   |
  | **挂号预约**     | 核心就医业务                   | 1. 自主挂号/老年优先挂号（60岁自动匹配） 2. 子女代挂号（绑定长辈信息） 3. Redis Lua原子扣减号源，异常回滚 |
  | **订单+缴费**    | 挂号闭环收尾                   | 1. 订单状态：待支付/已预约/已完成/已取消 2. 模拟三类费用支付，生成缴费核验记录 |
  | **候诊+提醒**    | 提升就医体验核心               | 1. 缴费后生成NK开头候诊编号 2. 前端无感刷新叫号/排队人数/预估时长 3. RabbitMQ推送三级提醒（挂号成功/顺位候诊/即将到号） |

  #### 3.5.2 P1增强功能详细设计

  | 模块             | 业务场景             | 核心实现                                                     |
  | ---------------- | -------------------- | ------------------------------------------------------------ |
  | **AI智能导诊**   | 解决老人分诊失误问题 | 自研医疗症状词库；文字/方言输入病症→匹配最优科室；无第三方大模型依赖 |
  | **语音挂号**     | 适配操作能力薄弱老人 | 语音识别解析指令→检索科室/医生→跳转挂号页面                  |
  | **健康提醒**     | 慢病/复诊老人刚需    | 录入用药/复诊/体检信息→Delay交换机定时推送提醒；消息落库可查 |
  | **运营数据看板** | 医院运维决策支撑     | ECharts可视化展示：挂号总量/号源占比/科室热度TOP10           |

  #### 3.5.3 P2特色亮点功能详细设计

  | 模块               | 业务场景               | 核心实现                                                     |
  | ------------------ | ---------------------- | ------------------------------------------------------------ |
  | **体检报告AI解读** | 解决老人看不懂报告问题 | 1. 上传报告图片→OpenCV OCR识别指标 2. 规则引擎+模板输出通俗解读（非大模型生成） 3. 输出健康建议，无医疗诊断风险 |
  | **志愿者陪诊预约** | 独居老人陪护核心创新点 | 1. 前端展示志愿者信息（头像/评分/服务科室） 2. 用户自选志愿者→提交申请→生成待审核订单 3. RabbitMQ推送管理员审核通知 4. 订单状态：待审核→待服务→服务中→已完成→已取消 5. 服务完结后用户评价，更新志愿者评分 |

  #### 3.5.4 后台管理功能详细设计

  | 模块             | 核心功能               | 简化策略                     |
  | ---------------- | ---------------------- | ---------------------------- |
  | **基础信息管理** | 医院/科室/医生档案维护 | 仅保留增删改查，无复杂配置   |
  | **排班号源管理** | 出诊时段/老年号配置    | 简化批量排班，仅满足基础演示 |
  | **志愿者管理**   | 信息录入/状态管控      | 仅开关接单状态，无精细化考核 |
  | **订单管理**     | 挂号/陪诊订单核销/审核 | 仅基础订单操作，无复杂售后   |
  | **用户管理**     | 账号查看/权限管控      | 仅白名单准入，无细粒度权限   |

  ------

  ## 4. 数据库设计

  ### 4.1 数据库设计规范

  1. 搭建医院→科室→医生→排班四级外键关联架构，业务归属闭环；
  2. 候诊叫号、排队实时数据存入Redis，Lua脚本原子控号；
  3. 全表统一配置create_time、update_time、is_deleted审计字段；
  4. 全表字段注释完整，关联外键合规，共计12张核心业务表。

  ### 4.2 核心数据表清单

  | 表名               | 核心用途                     | 关键字段                                    |
  | ------------------ | ---------------------------- | ------------------------------------------- |
  | tb_hospital        | 合作医院信息存储             | 医院名称/等级/地址                          |
  | tb_user            | 平台用户（老人/子女/管理员） | 账号/密码(bcrypt)/用户类型                  |
  | tb_elder_bind      | 子女-长辈绑定关系            | 长辈姓名/身份证/医保/生日（年龄判定）       |
  | tb_department      | 科室信息                     | 医院ID/科室名称                             |
  | tb_doctor          | 医生信息                     | 科室ID/职称/擅长/挂号费                     |
  | tb_schedule        | 医生排班号源                 | 医生ID/出诊日期/时段/普通/老年号数量        |
  | tb_reserve         | 挂号预约订单                 | 用户ID/排班ID/候诊编号/支付/订单状态        |
  | tb_pay_record      | 缴费记录                     | 预约单ID/缴费金额                           |
  | tb_physical_report | 体检报告                     | 长辈ID/报告图片地址                         |
  | tb_volunteer       | 志愿者信息                   | 姓名/电话/服务科室/评分/服务次数/状态       |
  | tb_accompany_order | 陪诊订单                     | 用户ID/长辈ID/志愿者ID/陪诊日期/5态订单状态 |
  | tb_message         | 消息通知                     | 用户ID/消息类型/内容/读取状态               |

  ### 4.3 核心建表SQL语句

  ```sql
  -- 全局说明：全表统一新增审计字段 create_time、update_time、is_deleted，默认逻辑删除
  
  -- 1.合作医院主表
  CREATE TABLE `tb_hospital` (
    `id` bigint NOT NULL AUTO_INCREMENT COMMENT '医院主键',
    `hospital_name` varchar(50) NOT NULL COMMENT '医院名称',
    `hospital_level` varchar(20) DEFAULT NULL COMMENT '医院等级',
    `address` varchar(200) DEFAULT NULL COMMENT '医院地址',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint NOT NULL DEFAULT 0 COMMENT '0未删除 1已删除',
    PRIMARY KEY (`id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  
  -- 2.平台用户表（角色修正：区分三类业务角色）
  CREATE TABLE `tb_user` (
    `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
    `wx_openid` varchar(128) DEFAULT NULL COMMENT '模拟微信唯一标识',
    `username` varchar(32) DEFAULT NULL COMMENT '登录账号',
    `password` varchar(64) NOT NULL COMMENT 'bcrypt加密登录密码',
    `nickname` varchar(64) NOT NULL COMMENT '用户昵称',
    `user_type` tinyint NOT NULL DEFAULT 1 COMMENT '1老年用户 2子女用户 3管理员',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint NOT NULL DEFAULT 0 COMMENT '0未删除 1已删除',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_openid` (`wx_openid`),
    UNIQUE KEY `uk_username` (`username`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  
  -- 3.子女长辈绑定表（补齐全部需求字段，支撑年龄自动判定老年号）
  CREATE TABLE `tb_elder_bind` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `child_uid` bigint NOT NULL COMMENT '子女用户ID',
    `elder_name` varchar(32) NOT NULL COMMENT '长辈姓名',
    `elder_id_card` varchar(20) DEFAULT NULL COMMENT '长辈身份证号',
    `elder_phone` varchar(20) DEFAULT NULL COMMENT '长辈联系电话',
    `gender` tinyint DEFAULT 1 COMMENT '1男 2女',
    `birthday` date DEFAULT NULL COMMENT '长辈出生日期，用于自动核算年龄',
    `medical_card` varchar(50) NOT NULL COMMENT '医保卡编号',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint NOT NULL DEFAULT 0 COMMENT '0未删除 1已删除',
    PRIMARY KEY (`id`),
    KEY `idx_child` (`child_uid`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  
  -- 4.科室关联表
  CREATE TABLE `tb_department` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `hospital_id` bigint NOT NULL COMMENT '所属医院ID',
    `dept_name` varchar(50) NOT NULL COMMENT '科室名称',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint NOT NULL DEFAULT 0 COMMENT '0未删除 1已删除',
    PRIMARY KEY (`id`),
    KEY `idx_hospital` (`hospital_id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  
  -- 5.医生信息表（补齐职称、擅长、挂号费、头像业务字段）
  CREATE TABLE `tb_doctor` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `dept_id` bigint NOT NULL COMMENT '所属科室ID',
    `doctor_name` varchar(32) NOT NULL COMMENT '医生姓名',
    `doctor_title` varchar(20) DEFAULT NULL COMMENT '医生职称：医师/主治医师/副主任医师/主任医师',
    `specialty` varchar(200) DEFAULT NULL COMMENT '擅长诊疗病症',
    `register_fee` decimal(8,2) NOT NULL DEFAULT 0 COMMENT '单次挂号资费',
    `doctor_avatar` varchar(255) DEFAULT NULL COMMENT '医生头像存储地址',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint NOT NULL DEFAULT 0 COMMENT '0未删除 1已删除',
    PRIMARY KEY (`id`),
    KEY `idx_dept` (`dept_id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  
  -- 6.排班号源表（新增时段字段，区分上下午出诊）
  CREATE TABLE `tb_schedule` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `doctor_id` bigint NOT NULL COMMENT '医生ID',
    `work_date` date NOT NULL COMMENT '出诊日期',
    `time_period` varchar(10) NOT NULL DEFAULT 'AM' COMMENT 'AM上午 PM下午 ALL全天',
    `normal_num` int NOT NULL DEFAULT 0 COMMENT '普通号数量',
    `elder_priority_num` int NOT NULL DEFAULT 0 COMMENT '老年优先号',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint NOT NULL DEFAULT 0 COMMENT '0未删除 1已删除',
    PRIMARY KEY (`id`),
    KEY `idx_doctor` (`doctor_id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  
  -- 7.挂号预约订单表（拆分支付/订单双状态，新增候诊状态）
  CREATE TABLE `tb_reserve` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `user_id` bigint NOT NULL COMMENT '预约用户',
    `schedule_id` bigint NOT NULL COMMENT '排班ID',
    `elder_bind_id` bigint DEFAULT NULL COMMENT '代办长辈ID',
    `queue_code` varchar(20) DEFAULT NULL COMMENT '候诊排队编号',
    `queue_status` tinyint DEFAULT 1 COMMENT '候诊状态：1等待中 2就诊中 3已完成',
    `pay_status` tinyint NOT NULL DEFAULT 1 COMMENT '1待支付 2已支付 3超时取消',
    `order_status` tinyint NOT NULL DEFAULT 1 COMMENT '订单状态：1待支付 2已预约 3已就诊 4已取消',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint NOT NULL DEFAULT 0 COMMENT '0未删除 1已删除',
    PRIMARY KEY (`id`),
    KEY `idx_user` (`user_id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  
  -- 8.缴费记录表
  CREATE TABLE `tb_pay_record` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `reserve_id` bigint NOT NULL COMMENT '关联预约单ID',
    `pay_money` decimal(10,2) NOT NULL COMMENT '缴费金额',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint NOT NULL DEFAULT 0 COMMENT '0未删除 1已删除',
    PRIMARY KEY (`id`),
    KEY `idx_reserve` (`reserve_id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  
  -- 9.体检报告表
  CREATE TABLE `tb_physical_report` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `elder_bind_id` bigint NOT NULL COMMENT '绑定长辈ID',
    `report_url` varchar(255) NOT NULL COMMENT '报告图片地址',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint NOT NULL DEFAULT 0 COMMENT '0未删除 1已删除',
    PRIMARY KEY (`id`),
    KEY `idx_elder` (`elder_bind_id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  
  -- 10.志愿者信息表（新增头像、服务简介、评分、服务次数，适配用户自主选人）
  CREATE TABLE `tb_volunteer` (
    `id` bigint NOT NULL AUTO_INCREMENT COMMENT '志愿者主键',
    `vol_name` varchar(32) NOT NULL COMMENT '志愿者姓名',
    `vol_phone` varchar(20) NOT NULL COMMENT '联系电话',
    `service_dept` varchar(100) DEFAULT NULL COMMENT '可服务科室',
    `avatar` varchar(255) DEFAULT NULL COMMENT '志愿者头像地址',
    `service_desc` varchar(255) DEFAULT NULL COMMENT '陪诊服务简介、从业经验',
    `service_score` decimal(2,1) NOT NULL DEFAULT 5.0 COMMENT '综合服务评分1-5分',
    `service_count` int NOT NULL DEFAULT 0 COMMENT '累计完成陪诊次数',
    `status` tinyint NOT NULL DEFAULT 1 COMMENT '1可预约 0不可预约',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint NOT NULL DEFAULT 0 COMMENT '0未删除 1已删除',
    PRIMARY KEY (`id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  
  -- 11.陪诊订单表（新版5态订单，适配自选志愿者+审核履约流程）
  CREATE TABLE `tb_accompany_order` (
    `id` bigint NOT NULL AUTO_INCREMENT COMMENT '陪诊订单主键',
    `user_id` bigint NOT NULL COMMENT '下单子女用户ID',
    `elder_bind_id` bigint NOT NULL COMMENT '陪同长辈ID',
    `volunteer_id` bigint NOT NULL COMMENT '用户自主选定志愿者ID',
    `accompany_date` date NOT NULL COMMENT '陪诊日期',
    `order_status` tinyint NOT NULL DEFAULT 1 COMMENT '1待审核 2待服务 3服务中 4已完成 5已取消',
    `service_score` tinyint DEFAULT NULL COMMENT '用户评价打分1-5分',
    `service_comment` varchar(200) DEFAULT NULL COMMENT '陪诊文字评价',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint NOT NULL DEFAULT 0 COMMENT '0未删除 1已删除',
    PRIMARY KEY (`id`),
    KEY `idx_user` (`user_id`),
    KEY `idx_vol` (`volunteer_id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  
  -- 12.平台消息通知表（适配全平台提醒落库，前端消息中心查看）
  CREATE TABLE `tb_message` (
    `id` bigint NOT NULL AUTO_INCREMENT COMMENT '消息主键',
    `user_id` bigint NOT NULL COMMENT '接收用户ID',
    `msg_type` tinyint NOT NULL DEFAULT 1 COMMENT '1系统通知 2挂号通知 3候诊通知 4健康提醒 5陪诊通知',
    `msg_content` varchar(255) NOT NULL COMMENT '消息内容',
    `read_status` tinyint NOT NULL DEFAULT 0 COMMENT '0未读 1已读',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint NOT NULL DEFAULT 0 COMMENT '0未删除 1已删除',
    PRIMARY KEY (`id`),
    KEY `idx_uid` (`user_id`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
  ```

  ------

  ## 5. 项目数据模拟说明

  ### 5.1 项目整体定位

  《银发通 —— 适老化线上就医服务平台》是面向老年群体及其子女打造的轻量化便民就医辅助系统，不替代医院院内 HIS 诊疗系统，专注解决老年人线下就医全流程痛点，聚焦线上前置服务与配套帮扶能力，填补传统挂号平台缺少老年陪护、适老交互、分诊引导的空白。

  ### 5.2 挂号模块模拟实现细则

  #### 5.2.1 后台模拟数据维护

  - 管理员后台自主录入医院、科室、医生全套模拟数据，搭建四级业务架构，无需第三方医疗接口；
  - 预设科室：内科、外科、骨科、神经内科、心血管科、消化科、眼科、耳鼻喉科、老年病科、中医科；
  - 每个科室配置3-5名虚构执业医生，完善职称、擅长慢病、挂号费用基础信息。

  #### 5.2.2 号源流转模拟逻辑

  ```plain
  MySQL（持久存号） ← 每日凌晨定时任务 → Redis（缓存控号）
      ↓（用户挂号）
  Redis Lua原子扣减号源 → 异常自动回滚
      ↓（15分钟未支付）
  Delay交换机 → 自动取消订单 → 号源回收
  ```

  ------

  ## 6. 非功能性需求

  ### 6.1 RabbitMQ中间件规范

  | 交换机类型       | 适用业务场景                  | 核心规则                                 |
  | ---------------- | ----------------------------- | ---------------------------------------- |
  | Direct直连交换机 | 挂号成功通知推送              | 路由键精准匹配，一对一推送，用户消息隔离 |
  | Direct直连交换机 | 候诊顺位/到号提醒推送         | 消息持久化，服务重启不丢失               |
  | Direct直连交换机 | 陪诊申请后台通知推送          | 消息同步落库tb_message表                 |
  | Delay延迟交换机  | 挂号订单超时自动取消/号源回收 | 15分钟超时触发，原子回收号源             |
  | Delay延迟交换机  | 定点服药提醒推送              | 按用户设定时间精准推送                   |
  | Delay延迟交换机  | 复诊/体检到期提醒推送         | 周期触发，消息落库可查                   |

  ### 6.2 Docker部署规范

  1. 前端、后端、数据库、中间件全部容器打包，Docker Compose一键启停；
  2. Nginx反向代理配置HTTPS域名，适配模拟微信授权访问；
  3. 数据卷持久挂载，容器重启业务数据不丢失，支持全天候公网访问。

  ### 6.3 性能安全指标

  1. 挂号核心接口响应时间≤500ms，高并发无号源超卖/丢失；
  2. AI语义导诊仅辅助推荐科室，不作为专业医疗诊断依据，无误诊合规风险；
  3. 候诊数据Redis缓存，前端页面无感刷新，无卡顿延迟；
  4. 安全防护：密码bcrypt加密、信息脱敏、后台白名单、接口限流。

  ------

  ## 7. 风险评估与对策

  | 风险点                        | 解决方案                                                     |
  | ----------------------------- | ------------------------------------------------------------ |
  | ES数据冗余、检索卡顿          | 限定仅四类基础数据同步索引，隔离订单/用户业务数据            |
  | 微信登录企业资质门槛高        | 自研模拟微信授权登录，完全脱离官方开放平台                   |
  | 高峰挂号号源超卖/丢失         | Redis Lua脚本原子扣减号源，异常自动回滚；接口限流防刷        |
  | 老年用户操作难度大            | 默认进入长者模式，全流程语音引导，简化操作步骤               |
  | 第三方大模型导诊误诊/付费风险 | 自研本地化AI语义导诊，绑定医疗专属词库，零第三方接口依赖     |
  | 用户恶意占用老年号源          | Delay交换机定时作废未支付订单，自动回收优先号源              |
  | 双后端分工混乱，答辩架构不清  | 剔除Node.js服务，FastAPI一站式承载业务+定时任务，统一Python技术栈 |

  ------

  ## 8. 项目验收标准

  1. 医院-科室-医生-排班四级架构关联完整，候诊编号生成、叫号全流程闭环；
  2. Redis号源扣减异常自动回滚，并发场景无号源丢失、超卖；
  3. 用户隐私信息前端脱敏，密码bcrypt加密存储，后台白名单准入生效；
  4. RabbitMQ双交换机业务运行正常，挂号超时、服药提醒业务无误；
  5. 长者/标准版界面一键切换，长者模式功能极简、字体适配老年使用；
  6. 双登录方式可用，用户角色权限划分精准；
  7. ES限定数据检索，检索精准高效（响应≤1s）；
  8. 项目可Docker容器化部署阿里云ECS，公网全功能稳定运行。

  ------

  ## 9. 项目总结

  ### 9.1 核心价值

  本项目落地银发通——适老化智慧就医服务平台，紧扣老年就医数字鸿沟民生痛点，贴合医疗适老化国家政策，核心聚焦三大差异化业务：

  - AI方言智能导诊：解决老人分诊失误问题；
  - 线上预约挂号+候诊全流程提醒：免去线下排队值守；
  - 线上志愿者公益陪诊：填补独居老人无陪护就医缺口。

  ### 9.2 架构优化

  1. 剔除冗余Node.js服务，后端统一Python技术栈，Vue3+FastAPI闭环架构；
  2. 精简RabbitMQ至Direct/Delay双交换机，APScheduler管控全平台定时任务；
  3. Redis Lua脚本原子控号+异常回滚，根治号源超卖问题；
  4. 收紧ES同步范围，优化检索性能；
  5. 统一使用bcrypt加密，全表新增标准审计字段，贴合企业开发规范。

  ### 9.3 业务优化

  1. 聚焦三大核心业务深度打磨，后台功能轻量化简化设计；
  2. 自研模拟微信登录，规避第三方资质风险；
  3. 陪诊模块优化为「用户自选志愿者+MQ推送+管理员审核」单向闭环，降低开发量，提升答辩易懂性；
  4. 划分功能优先级，全力聚焦用户端核心业务，后台仅做基础运维配套。

  ### 9.4 不足与展望

  - 现阶段为模拟就医系统，未对接线下医院官方接口；
  - 后续可优化方向：对接合规医疗接口、提升方言导诊识别精度、接入合规第三方支付、完善全就医闭环。
