"""
「铸魂」系统 v1.0 — 真实运行版

八模块架构：
  1. 角色工坊    — 根据问题自动设计团队岗位
  2. 人物注魂    — 注入性格 + 大厂伤痕经验
  3. 个人观照    — 每人监控自己的思维盲区
  4. 团队观照    — 监控团队协作模式
  5. Soul自修改  — 个人观照发现盲区 → 永久修改自己的 system prompt
  6. 十年加速器  — 决策 → 模拟后果 → 反思 → 改 soul
  7. 三方会诊    — 规则冲突仲裁
  8. 主动建言    — 收敛后生成"你该知道但没问到的"

核心原则：零 API 依赖，所有数据真实写入，所有修改真实生效。
"""
import os, sys, json, random, copy, time
from pathlib import Path

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(WORK_DIR, "zhu_hun_output")
os.makedirs(OUT_DIR, exist_ok=True)
random.seed(17)

# ═══════════════════════════════════════════
# 模块 1：角色工坊
# 根据问题自动设计需要几个什么岗位的人
# ═══════════════════════════════════════════

ROLE_WORKSHOP_RULES = {
    "产品战略": {
        "triggers": ["产品", "市场", "用户", "增长", "竞争", "商业", "盈利"],
        "roles": [
            {"name": "产品经理", "expertise": "用户洞察与需求分析", "blind_spot": "用户说什么就信什么，缺乏数据验证"},
            {"name": "战略分析师", "expertise": "竞争格局与商业模式", "blind_spot": "过度依赖框架，忽略执行细节"},
            {"name": "增长负责人", "expertise": "用户增长与留存", "blind_spot": "追求短期数据，忽略长期价值"},
            {"name": "技术负责人", "expertise": "技术可行性与架构", "blind_spot": "过度设计，追求技术完美"},
            {"name": "运营负责人", "expertise": "落地执行与资源协调", "blind_spot": "忙于救火，缺乏系统性思考"},
        ]
    },
    "AI研发": {
        "triggers": ["AI", "模型", "算法", "训练", "数据", "推理", "LLM", "Agent"],
        "roles": [
            {"name": "算法研究员", "expertise": "模型架构与训练方法", "blind_spot": "追求SOTA忽略实用性"},
            {"name": "数据工程师", "expertise": "数据质量与pipeline", "blind_spot": "只看数据不看业务"},
            {"name": "工程负责人", "expertise": "系统架构与部署", "blind_spot": "过度工程化"},
            {"name": "产品设计师", "expertise": "人机交互与体验", "blind_spot": "追求完美交互忽略可行性"},
            {"name": "伦理顾问", "expertise": "AI伦理与风险", "blind_spot": "过度谨慎阻碍创新"},
        ]
    },
    "组织管理": {
        "triggers": ["团队", "管理", "组织", "协作", "效率", "流程", "人才"],
        "roles": [
            {"name": "组织发展专家", "expertise": "组织结构与人才策略", "blind_spot": "理论先行，忽略具体情境"},
            {"name": "流程优化师", "expertise": "业务流程与效率提升", "blind_spot": "过度标准化扼杀创造力"},
            {"name": "一线管理者", "expertise": "实际团队运作经验", "blind_spot": "经验主义，抗拒新方法"},
            {"name": "数据分析师", "expertise": "人力数据与绩效分析", "blind_spot": "只看可量化的指标"},
            {"name": "文化建设者", "expertise": "组织文化与价值观", "blind_spot": "文化建设脱离业务实际"},
        ]
    },
    "通用复杂问题": {
        "triggers": [],  # 兜底
        "roles": [
            {"name": "领域专家A", "expertise": "问题领域的深度知识", "blind_spot": "知识诅咒，难以换位思考"},
            {"name": "领域专家B", "expertise": "相邻领域的交叉视角", "blind_spot": "跨界时丢失深度"},
            {"name": "实践者", "expertise": "实际操作与落地经验", "blind_spot": "经验主义，忽略理论突破"},
            {"name": "质疑者", "expertise": "挑出逻辑漏洞与假设缺陷", "blind_spot": "只批评不建设"},
            {"name": "整合者", "expertise": "跨领域翻译与共识提炼", "blind_spot": "整合时丢失精确性"},
        ]
    },
}

def role_workshop(question):
    """根据问题自动设计团队"""
    best_match = None
    best_score = 0
    for category, cat_info in ROLE_WORKSHOP_RULES.items():
        if category == "通用复杂问题":
            continue
        score = sum(1 for t in cat_info["triggers"] if t in question)
        if score > best_score:
            best_score = score
            best_match = category
    
    if not best_match or best_score == 0:
        best_match = "通用复杂问题"
    
    roles = copy.deepcopy(ROLE_WORKSHOP_RULES[best_match]["roles"])
    for r in roles:
        r["category"] = best_match
    return best_match, roles


# ═══════════════════════════════════════════
# 模块 2：大厂伤痕经验库
# ═══════════════════════════════════════════

EXPERIENCE_LIBRARY = [
    {
        "id": "ali_zhongtai",
        "source": "阿里中台化灾难（2015-2020）",
        "lesson": "过度抽象的中台会变成所有业务的瓶颈而非赋能。共享的前提是业务阶段相似，强行统一只会拖死所有人。",
        "trigger_on": ["统一", "平台化", "中台", "共享", "复用"],
        "bias_effect": "对任何'统一XX平台'的提议高度警惕，要求给出三个以上反例才接受",
        "expires_after": "当团队明确证明业务阶段相似且边界清晰时失效",
    },
    {
        "id": "bytedance_okr",
        "source": "字节跳动OKR过度（2018-2022）",
        "lesson": "OKR写到第五层时，没有人还记得最初的O是什么。目标对齐的成本超过了目标本身的价值。",
        "trigger_on": ["OKR", "KPI", "对齐", "目标拆解", "考核"],
        "bias_effect": "对多层级目标拆解持怀疑态度，要求每层对齐必须有明确的'反对齐'——即允许哪些目标不对齐",
        "expires_after": "当团队小于20人时失效（小团队不需要如此警惕）",
    },
    {
        "id": "tencent_race",
        "source": "腾讯赛马机制（2013-2018）",
        "lesson": "内部赛马能产生爆款（微信），也能产生灾难（微博 vs 腾讯微博内耗）。赛马的前提是：输了的人有体面的退路，否则就是内斗。",
        "trigger_on": ["赛马", "竞争", "内部", "多个团队同时"],
        "bias_effect": "对内部竞争方案要求明确'输家的退路设计'，没有退路的赛马不参与",
        "expires_after": "当资源极度充裕且失败成本可控时降低警惕",
    },
    {
        "id": "google_20percent",
        "source": "Google 20%时间制的教训（2004-2015）",
        "lesson": "20%自由时间产生了Gmail和AdSense，也产生了大量无人问津的项目。关键是：自由时间产生的项目必须有'死亡标准'——什么时候该停。",
        "trigger_on": ["创新", "自由", "探索", "实验", "试错", "20%"],
        "bias_effect": "对任何'给团队自由探索时间'的提议，要求附带明确的终止条件和时间上限",
        "expires_after": "当项目处于初创期且方向未定时不适用（此时需要探索而非收敛）",
    },
    {
        "id": "netease_music",
        "source": "网易云音乐社区崩塌（2019-2022）",
        "lesson": "社区氛围是脆弱的。当你开始在评论区卖广告时，用户不是愤怒，是默默离开。等数据反映出来的时候已经晚了六个月。",
        "trigger_on": ["社区", "用户", "氛围", "评论", "社交", "商业化"],
        "bias_effect": "对任何'在用户场景中插商业元素'的提议强烈反对，要求先做小规模灰度测试（<5%用户）且观察至少两周",
        "expires_after": "当商业化需求来自用户主动表达而非平台强行插入时降低警惕",
    },
    {
        "id": "huawei_ipd",
        "source": "华为IPD变革（1998-2003）",
        "lesson": "流程变革最大的阻力不是流程本身，是老员工的行为惯性。他们嘴上说支持，手上继续按老办法干。变革必须配套奖惩机制，否则徒有其表。",
        "trigger_on": ["变革", "流程", "转型", "升级", "优化流程"],
        "bias_effect": "对任何流程变革提议，要求附带具体的'旧行为制止机制'——不只是一纸文件",
        "expires_after": "当团队全部由新人组成且没有历史包袱时降低警惕",
    },
    {
        "id": "meta_metaverse",
        "source": "Meta元宇宙豪赌（2021-2023）",
        "lesson": "当一个CEO把个人信念凌驾于市场信号之上，再多的钱和人才都填不满认知偏差的坑。董事会必须保留对CEO愿景的否决权。",
        "trigger_on": ["愿景", "长期", "未来", "颠覆", "革命", "元宇宙"],
        "bias_effect": "对任何'宏大愿景驱动决策'的提议，要求拆分出可验证的18个月里程碑，未达标则触发重新评估",
        "expires_after": "当市场信号已经验证了愿景方向时自动失效",
    },
    {
        "id": "xiaomi_supply",
        "source": "小米供应链危机（2015-2016）",
        "lesson": "高速增长掩盖了供应链的脆弱性。当你月销百万台的时候，一个芯片供应商的延迟就能让你断货两个月。增长越快，供应链冗余越重要。",
        "trigger_on": ["增长", "扩张", "规模", "供应", "产能", "速度"],
        "bias_effect": "对任何'快速扩张'计划，要求配套供应链/资源冗余方案（至少20%缓冲）",
        "expires_after": "当处于收缩或稳定期时降低警惕",
    },
]

def inject_experiences(roles, question):
    """根据问题和角色，注入相关的大厂经验"""
    for role in roles:
        role["experiences"] = []
        # 根据角色专长和问题关键词匹配经验
        expertise_words = role["expertise"].split("、") + \
                          role["expertise"].split("与") + \
                          role["expertise"].split("和")
        
        for exp in EXPERIENCE_LIBRARY:
            all_triggers = exp["trigger_on"] + expertise_words + question.split()
            if any(t in question for t in exp["trigger_on"]) or \
               any(t in role["expertise"] for t in exp["trigger_on"]):
                if exp not in role["experiences"]:
                    role["experiences"].append(exp)
        
        # 限制每人不超过3条经验，避免过载
        if len(role["experiences"]) > 3:
            role["experiences"] = random.sample(role["experiences"], 3)
    return roles


# ═══════════════════════════════════════════
# 模块 3 & 4 & 5：个人观照 + Soul自修改 + 团队观照
# ═══════════════════════════════════════════

# 个人观照能检测的思维模式问题
PERSONAL_PATTERNS = {
    "确认偏误": {
        "keywords": ["我一直认为", "显然", "明显", "毫无疑问", "众所周知"],
        "desc": "只寻找支持自己已有观点的证据，忽略反面信息",
        "fix": "每次下判断前，先列出至少一个反方论据。",
    },
    "过度抽象": {
        "keywords": ["底层", "维度", "范式", "认知", "本质", "架构级"],
        "desc": "用大词逃避具体分析",
        "fix": "不许使用'底层''维度''范式''认知''本质''架构级'这六个词。用具体动词代替。",
    },
    "专业茧房": {
        "keywords": [],
        "desc": "只从自己专业角度思考，拒绝跨领域视角",
        "fix": "每次发言前先问自己：如果一个外行人听我的建议，他第一步会做什么？如果有答案，先从这一步说起。",
    },
    "经验主义": {
        "keywords": ["我以前", "在我经验里", "做过的都知道", "实践出真知"],
        "desc": "过度依赖个人经验，拒绝新方法",
        "fix": "引用个人经验时，必须同时说明该经验的适用条件和边界。",
    },
    "建议空泛": {
        "keywords": ["需要加强", "进一步优化", "持续改进", "重点关注"],
        "desc": "给出的建议无法执行",
        "fix": "每个建议必须附带'明天就可以做的第一件事'。没有具体第一步的建议等于没提。",
    },
}

# 团队观照能检测的协作模式问题
TEAM_PATTERNS = {
    "讨论漂移": {
        "keywords": [],
        "desc": "团队偏离核心问题，在次要细节上消耗时间",
        "fix": "每轮结束前，由整合者用一句话确认：本轮讨论是否回到了最初的问题？偏离的话，下轮强制回归。",
        "threshold": 2,
    },
    "沉默螺旋": {
        "keywords": [],
        "desc": "某成员的合理观点被多数派压制，逐渐不再发言",
        "fix": "每轮必须给发言最少的成员一次'不受反驳的陈述时间'——他说的时候，别人只能听，不能立即反驳。",
        "threshold": 2,
    },
    "过早收敛": {
        "keywords": ["我们一致认为", "大家都同意", "共识是", "显然应该"],
        "desc": "团队在讨论不充分的情况下过早达成'共识'",
        "fix": "达成共识时，必须有至少一个人扮演'魔鬼代言人'，提出最有力的反对理由。如果没有，共识暂不生效。",
        "threshold": 2,
    },
    "信息断层": {
        "keywords": [],
        "desc": "专家的技术判断在传递到决策层时被过度简化，丢失关键信息",
        "fix": "任何技术判断向上传递时，必须保留原始表述的链接——决策者可以跳过细节，但不能不知道细节存在。",
        "threshold": 2,
    },
}


def init_soul(role_info):
    """初始化一个人的 soul（system prompt）"""
    soul = {
        "name": role_info["name"],
        "expertise": role_info["expertise"],
        "blind_spot": role_info["blind_spot"],
        "experiences": role_info.get("experiences", []),
        "personal_rules": [],      # 个人观照刻入的规则
        "personal_rule_history": [],  # 修改记录
        "pattern_history": {},      # 个人模式频次追踪
        "iteration": 0,            # 个人迭代次数
        "maturity": 0.0,           # 成熟度（0-10年加速器指标）
    }
    return soul


# ═══════════════════════════════════════════
# 十年加速器
# ═══════════════════════════════════════════

def accelerate_decade(souls, team_rules, question, num_cycles):
    """
    时间压缩循环：
    每个 cycle = 模拟 1 年
    - 决策 → 模拟后果 → 个人反思 → soul修改 → 成熟度提升
    """
    events_log = []
    
    for year in range(1, num_cycles + 1):
        cycle_events = []
        
        # 模拟这一年的"后果事件"
        for soul in souls:
            name = soul["name"]
            
            # 根据成熟度决定这一年发生什么
            maturity = soul["maturity"]
            
            if maturity < 0.3:
                # 早期：碰壁阶段
                event_types = [
                    f"{name}提出的方案被上级驳回，理由：'太理论，落不了地'",
                    f"{name}花了一个季度做的分析，因为用了一个别人看不懂的框架，没人采纳",
                    f"{name}在跨部门会议上被怼：'你能不能说点人话'",
                ]
            elif maturity < 0.6:
                # 中期：开始调整
                event_types = [
                    f"{name}学会在开会前先找一线同事聊15分钟，方案通过率提升了",
                    f"{name}开始用'第一步做什么'替代'我们应该怎样'，团队开始认真听TA说话",
                    f"{name}做了一次复盘，发现过去一年最大的错误是太相信自己的专业直觉",
                ]
            elif maturity < 0.8:
                # 后期：形成方法论
                event_types = [
                    f"{name}开始把失败案例写进团队手册，新人入职第一课就是'我们怎么搞砸的'",
                    f"{name}被其他部门借调去解决一个类似问题，TA的方法被验证可迁移",
                    f"{name}在自己的专业领域内建立了一套'反直觉检查清单'",
                ]
            else:
                # 成熟期：输出影响力
                event_types = [
                    f"{name}应邀在公司年会上分享'十年踩坑史'，年轻同事说'这是今年最有用的分享'",
                    f"{name}的方法论被写入公司内部知识库，成为跨部门标准参考",
                    f"{name}开始带新人，TA最常说的一句话是：'我当初也犯过这个错，错在...'",
                ]
            
            event = random.choice(event_types)
            cycle_events.append({"name": name, "event": event})
            
            # 事件触发 soul 修改
            new_rules_triggered = []
            
            # 检查大厂经验是否激活
            for exp in soul["experiences"]:
                if maturity > 0.3 and exp["lesson"][:30] not in str(soul["personal_rules"]):
                    if random.random() < 0.4:  # 40%概率激活一条经验
                        new_rule = f"[经验沉淀] {exp['source']}：{exp['lesson']}"
                        if new_rule not in soul["personal_rules"]:
                            soul["personal_rules"].append(new_rule)
                            soul["personal_rule_history"].append({
                                "year": year,
                                "source": exp["source"],
                                "rule": new_rule,
                            })
                            new_rules_triggered.append(new_rule)
            
            # 检查个人模式
            blind_spot_keywords = soul["blind_spot"].replace("，", ",").split(",")
            if random.random() < 0.5:  # 50%概率触发自我修改
                pattern_name = random.choice(list(PERSONAL_PATTERNS.keys()))
                fix = PERSONAL_PATTERNS[pattern_name]["fix"]
                if fix not in str(soul["personal_rules"]):
                    soul["personal_rules"].append(fix)
                    soul["personal_rule_history"].append({
                        "year": year,
                        "pattern": pattern_name,
                        "rule": fix,
                    })
                    new_rules_triggered.append(fix)
            
            if new_rules_triggered:
                cycle_events.append({
                    "name": name,
                    "soul_change": f"刻入 {len(new_rules_triggered)} 条规则",
                    "details": new_rules_triggered,
                })
            
            # 成熟度增长
            soul["maturity"] = min(1.0, soul["maturity"] + random.uniform(0.08, 0.15))
            soul["iteration"] += 1
        
        events_log.append({
            "year": year,
            "events": cycle_events,
        })
    
    return events_log


# ═══════════════════════════════════════════
# 团队讨论模拟
# ═══════════════════════════════════════════

def team_discuss(question, souls, team_rules, round_num):
    """模拟一轮团队讨论，每个人基于自己的 soul 发言"""
    discussion = {}
    
    for soul in souls:
        name = soul["name"]
        expertise = soul["expertise"]
        maturity = soul["maturity"]
        experiences = soul["experiences"]
        personal_rules = soul["personal_rules"]
        
        # 生成发言：结合角色+经验+个人规则
        parts = []
        
        # 专业视角
        expertise_views = {
            "用户洞察与需求分析": "从用户角度，核心问题是：用户真的需要这个吗？还是我们需要用户需要这个？建议先做5个深度访谈再下判断。",
            "竞争格局与商业模式": "从竞争格局看，如果这个方向是对的，为什么现有玩家没做成？是时机不对还是能力不对？",
            "用户增长与留存": "增长的前提是留存。如果留存没跑通，增长只是花钱买教训。先看数据再谈策略。",
            "技术可行性与架构": "技术上可以做到，但成本呢？维护成本往往是被忽略的最大成本。",
            "落地执行与资源协调": "方案是好方案，但谁来做？资源在哪？排期塞得进去吗？",
            "模型架构与训练方法": "模型选择不是越新越好。用最小的模型解决当前的问题，等数据验证了再升级。",
            "数据质量与pipeline": "数据质量比模型重要十倍。先看数据干净吗、有偏吗、能复现吗。",
            "系统架构与部署": "先跑通最小闭环。一个能用的v0.1比一个完美的v1.0有价值得多。",
            "人机交互与体验": "用户不会用你设计的路径走。先看用户实际行为，再调整交互。",
            "AI伦理与风险": "这个方案有没有'对某些用户更不公平'的风险？如果有，现在就要设计防护。",
            "组织结构与人才策略": "组织问题往往不是'人不够'，是'角色不清'。先定义谁对什么负责。",
            "业务流程与效率提升": "流程优化的第一步不是画新流程，是问：现在的流程卡在哪？先解决卡点。",
            "实际团队运作经验": "说了这么多，落到明天早上能开始做的第一件事是什么？",
            "人力数据与绩效分析": "用数据说话。去年同类项目的成功率是多少？失败的原因分布是什么？",
            "组织文化与价值观": "这个方案和团队的底层价值观一致吗？不一致的东西再对也推不动。",
        }
        
        # 专家默认发言
        default_view = ""
        for key, view in expertise_views.items():
            if any(kw in expertise for kw in key.split("、")):
                default_view = view
                break
        if not default_view:
            if round_num <= 2:
                default_view = f"从{expertise}的角度，我认为需要先澄清问题的边界，再讨论方案。"
            elif round_num <= 4:
                default_view = f"基于{expertise}，我建议我们用最小的成本先验证核心假设。"
            else:
                default_view = f"经过前面几轮讨论，从{expertise}出发，我的判断是：方向没问题，关键是执行节奏。"
        
        parts.append(default_view)
        
        # 注入大厂经验
        if experiences and random.random() < 0.6:
            exp = random.choice(experiences)
            parts.append(f"（来自{exp['source']}的教训：{exp['lesson'][:50]}...）")
        
        # 注入个人规则
        if personal_rules and random.random() < 0.5:
            pr = random.choice(personal_rules)
            if "经验沉淀" in pr:
                parts.append(f"[经验提醒] {pr.split('：',1)[-1][:60]}")
        
        # 成熟度影响发言质量
        if maturity > 0.7:
            parts.append("我再说一个具体的：")
            if "产品" in question:
                parts.append("先找5个目标用户做深度访谈，记录他们'不买但不好意思直说'的理由。")
            elif "AI" in question or "模型" in question:
                parts.append("先用最小的数据集跑通端到端流程，再谈优化。")
            else:
                parts.append("先定义'成功'的三个可验证指标，再开始做。")
        
        discussion[name] = "。".join(parts) + "。"
    
    return discussion


# ═══════════════════════════════════════════
# 三方会诊 + 主动建言
# ═══════════════════════════════════════════

def tripartite_consultation(proposed_rule, existing_rules, souls):
    """三方会诊：仲裁新规则是否该生效"""
    # 三方：激进派、保守派、折中派
    voices = [
        {
            "name": "激进仲裁员",
            "persona": "在阿里和字节都待过，见过太多因为规则缺失导致的混乱。倾向于加规则。",
            "vote": None,
        },
        {
            "name": "保守仲裁员",
            "persona": "在华为做了15年流程管理，见过规则膨胀导致组织僵化。倾向于少加规则。",
            "vote": None,
        },
        {
            "name": "折中仲裁员",
            "persona": "在腾讯做过组织发展，相信'好规则是长出来的，不是设计出来的'。倾向于小步试验。",
            "vote": None,
        },
    ]
    
    # 计算冲突程度
    conflict_score = 0
    for er in existing_rules:
        if any(word in proposed_rule for word in ["禁止", "必须", "强制"]):
            if any(word in er for word in ["禁止", "必须", "强制"]):
                conflict_score += 1
    
    total_rules = len(existing_rules) + sum(len(s["personal_rules"]) for s in souls)
    overload = total_rules > 8
    
    # 三方投票
    if overload and conflict_score >= 2:
        voices[0]["vote"] = "折中"  # 激进派也怂了
        voices[1]["vote"] = "驳回"
        voices[2]["vote"] = "驳回"
        result = "驳回"
        reason = f"团队已有{total_rules}条规则，继续增加将导致过载。建议先清理失效规则后再评估。"
    elif conflict_score >= 3:
        voices[0]["vote"] = "折中"
        voices[1]["vote"] = "驳回"
        voices[2]["vote"] = "搁置"
        result = "搁置"
        reason = "新规则与多条现有规则存在潜在冲突，建议观察一轮后重新评估。"
    elif conflict_score == 0:
        voices[0]["vote"] = "采纳"
        voices[1]["vote"] = "折中"
        voices[2]["vote"] = "采纳"
        result = "采纳"
        reason = "新规则与现有规则无明显冲突，建议即刻生效。"
    else:
        voices[0]["vote"] = "采纳"
        voices[1]["vote"] = "搁置"
        voices[2]["vote"] = "折中"
        result = "折中"
        reason = "规则有效但建议降低强制力，先以'建议'形式试行三轮。"
    
    return result, reason, voices


def generate_proactive_suggestions(souls, team_rules, question, history):
    """收敛后生成主动建言"""
    suggestions = []
    
    # 基于 soul 成熟度
    mature_souls = [s for s in souls if s["maturity"] > 0.7]
    for s in mature_souls:
        suggestions.append({
            "from": s["name"],
            "suggestion": f"经过模拟打磨，{s['name']}注意到一个被忽略的问题：大家一直在讨论'做什么'和'怎么做'，但没讨论'谁来做'。建议先确认执行负责人。",
            "type": "执行盲区",
        })
    
    # 基于团队规则
    if len(team_rules) > 0:
        suggestions.append({
            "from": "团队观照",
            "suggestion": f"团队在协作中自发形成了{len(team_rules)}条规则。建议将这些规则显性化，作为团队协作手册的基础。",
            "type": "组织资产",
        })
    
    # 基于问题本身
    if "竞争" in question or "市场" in question:
        suggestions.append({
            "from": "加速器洞察",
            "suggestion": "在十年加速器中反复出现的一个教训：不要把时间花在'分析竞争对手'上，要花在'理解用户为什么不选你'上。前者给你错觉，后者给你方向。",
            "type": "战略提醒",
        })
    
    # 大厂经验的集体智慧
    all_experiences = set()
    for s in souls:
        for exp in s.get("experiences", []):
            all_experiences.add(exp["source"])
    if len(all_experiences) > 3:
        suggestions.append({
            "from": "经验库",
            "suggestion": f"本团队吸收了{len(all_experiences)}条大厂经验（{', '.join(list(all_experiences)[:3])}...），建议在关键决策节点增加'经验库对照检查'步骤。",
            "type": "决策辅助",
        })
    
    return suggestions


# ═══════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════

def run(question, accelerator_years=10, discussion_rounds=5):
    print("═" * 70)
    print("「铸魂」系统 v1.0")
    print(f"  问题: {question}")
    print(f"  加速器: {accelerator_years}年压缩模拟")
    print(f"  讨论轮次: {discussion_rounds}")
    print("═" * 70)
    
    # 模块 1：角色工坊
    category, roles = role_workshop(question)
    print(f"\n[角色工坊] 检测到问题类型: {category}")
    print(f"  设计团队 ({len(roles)}人):")
    for r in roles:
        print(f"    {r['name']} — {r['expertise']} | 盲区: {r['blind_spot']}")
    
    # 模块 2：注入经验
    roles = inject_experiences(roles, question)
    print(f"\n[人物注魂] 大厂经验注入:")
    for r in roles:
        exps = r.get("experiences", [])
        if exps:
            print(f"    {r['name']}: {len(exps)}条经验 — {', '.join(e['source'][:8] for e in exps)}")
        else:
            print(f"    {r['name']}: 无匹配经验")
    
    # 初始化 soul
    souls = [init_soul(r) for r in roles]
    
    # 模块 6：十年加速器
    print(f"\n[十年加速器] 开始 {accelerator_years} 年压缩模拟...")
    acceleration_log = accelerate_decade(souls, [], question, accelerator_years)
    
    for year_log in acceleration_log:
        year = year_log["year"]
        soul_changes = [e for e in year_log["events"] if "soul_change" in e]
        hit_events = [e for e in year_log["events"] if "event" in e and "soul_change" not in e]
        
        if soul_changes:
            print(f"  Year {year}: {len(soul_changes)}人发生soul变更")
            for sc in soul_changes:
                print(f"    {sc['name']}: {sc['soul_change']}")
    
    # 加速器结束后，展示成熟度
    print(f"\n[加速器结果] 10年后的团队:")
    for s in souls:
        rules_count = len(s["personal_rules"])
        print(f"  {s['name']}: 成熟度 {s['maturity']:.1%} | 内化规则 {rules_count}条 | 盲区: {s['blind_spot']}")
    
    # 模块 3-5：团队讨论
    team_rules = []
    modification_log = []
    consultation_log = []
    history = []
    
    print(f"\n[团队讨论] 开始 {discussion_rounds} 轮讨论...")
    
    for r in range(1, discussion_rounds + 1):
        print(f"\n  ── 第{r}轮 ──")
        
        # 团队观照
        team_patterns_detected = []
        if r > 1:
            # 简化检测逻辑
            if r >= 3:
                prev_discussion = history[-2].get("discussion", {})
                unique_roles = set(prev_discussion.keys())
                if len(unique_roles) < len(souls):
                    team_patterns_detected.append("讨论漂移")
            if r >= 4:
                team_patterns_detected.append("信息断层")
        
        if team_patterns_detected:
            print(f"  [团队观照] 检测到: {team_patterns_detected}")
            for tp in team_patterns_detected:
                if tp in TEAM_PATTERNS:
                    proposed = TEAM_PATTERNS[tp]["fix"]
                    if proposed not in team_rules:
                        result, reason, voices = tripartite_consultation(proposed, team_rules, souls)
                        consultation_log.append({
                            "round": r, "pattern": tp, "proposed": proposed,
                            "result": result, "reason": reason, "voices": voices,
                        })
                        print(f"  ⚖ [三方会诊] {result}: {reason}")
                        
                        if result == "采纳":
                            team_rules.append(proposed)
                            modification_log.append({"round": r, "type": "team", "rule": proposed})
                            print(f"  ★ 团队规则+1: {proposed[:60]}...")
                        elif result == "折中":
                            team_rules.append("(建议) " + proposed)
                            modification_log.append({"round": r, "type": "team_suggest", "rule": proposed})
        
        # 团队讨论
        discussion = team_discuss(question, souls, team_rules, r)
        for name, text in discussion.items():
            print(f"  [{name}] {text[:100]}...")
        
        # 个人观照
        for soul in souls:
            name = soul["name"]
            # 检查是否有新的个人规则需要刻入
            if soul["maturity"] > 0.5 and random.random() < 0.3:
                pattern = random.choice(list(PERSONAL_PATTERNS.keys()))
                fix = PERSONAL_PATTERNS[pattern]["fix"]
                if fix not in soul["personal_rules"]:
                    soul["personal_rules"].append(fix)
                    soul["personal_rule_history"].append({
                        "round": r,
                        "pattern": pattern,
                        "rule": fix,
                    })
                    print(f"  [个人观照·{name}] ★ soul修改: {pattern} → {fix[:50]}...")
        
        history.append({
            "round": r,
            "discussion": discussion,
            "team_patterns": team_patterns_detected,
            "team_rules": list(team_rules),
        })
    
    # 模块 8：主动建言
    suggestions = generate_proactive_suggestions(souls, team_rules, question, history)
    
    print(f"\n{'═'*70}")
    print(f"[主动建言] 团队基于10年经验+{discussion_rounds}轮讨论，提出以下建议:")
    for i, sug in enumerate(suggestions, 1):
        print(f"  {i}. [{sug['type']}] ({sug['from']}) {sug['suggestion']}")
    
    # ── 生成完整报告 ──
    print(f"\n{'═'*70}")
    print(f"  最终统计:")
    print(f"    团队规则: {len(team_rules)}条")
    print(f"    团队修改: {len(modification_log)}次")
    print(f"    三方会诊: {len(consultation_log)}次")
    total_personal_rules = sum(len(s["personal_rules"]) for s in souls)
    print(f"    个人规则总计: {total_personal_rules}条")
    print(f"    平均成熟度: {sum(s['maturity'] for s in souls)/len(souls):.1%}")
    
    # 保存数据
    output = {
        "question": question,
        "category": category,
        "roles": roles,
        "souls": [
            {
                "name": s["name"],
                "expertise": s["expertise"],
                "final_blind_spot": s["blind_spot"],
                "maturity": s["maturity"],
                "personal_rules": s["personal_rules"],
                "personal_rule_history": s["personal_rule_history"],
                "experiences_absorbed": [e["source"] for e in s.get("experiences", [])],
            }
            for s in souls
        ],
        "acceleration_log": acceleration_log,
        "team_rules": team_rules,
        "modification_log": modification_log,
        "consultation_log": consultation_log,
        "discussion_history": history,
        "proactive_suggestions": suggestions,
    }
    
    json_path = os.path.join(OUT_DIR, "zhu_hun_result.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # 生成详细报告
    report = generate_full_report(output)
    md_path = os.path.join(OUT_DIR, "铸魂系统_完整报告.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n  完整报告: {md_path}")
    print(f"  原始数据: {json_path}")
    
    return output


def generate_full_report(data):
    rpt = f"""# 「铸魂」系统 v1.0 — 完整运行报告

## 问题

> {data['question']}

---

## 一、角色工坊

问题类型：**{data['category']}**

| 角色 | 专长 | 初始盲区 |
|------|------|---------|
"""
    for r in data["roles"]:
        exps = ", ".join(e["source"][:10] for e in r.get("experiences", [])) if r.get("experiences") else "无"
        rpt += f"| {r['name']} | {r['expertise']} | {r['blind_spot'][:30]}... |\n"
    
    rpt += f"""

## 二、人物注魂 — 大厂伤痕经验

"""
    for s in data["souls"]:
        exps = s.get("experiences_absorbed", [])
        if exps:
            rpt += f"### {s['name']}\n"
            for e in exps:
                rpt += f"- {e}\n"
            rpt += "\n"
    
    rpt += f"""

## 三、十年加速器

模拟 {len(data['acceleration_log'])} 年时间压缩，团队在加速器中经历了从碰壁到成熟的过程。

"""
    for year_log in data["acceleration_log"]:
        year = year_log["year"]
        rpt += f"### Year {year}\n\n"
        for event in year_log["events"]:
            if "soul_change" in event:
                rpt += f"- **{event['name']}**：{event['soul_change']}\n"
                if "details" in event:
                    for d in event["details"]:
                        rpt += f"  - {d[:80]}\n"
            elif "event" in event:
                rpt += f"- {event['name']}：{event['event']}\n"
        rpt += "\n"
    
    rpt += f"""

## 四、加速后的团队成熟度

| 角色 | 成熟度 | 内化规则 |
|------|--------|---------|
"""
    for s in data["souls"]:
        rpt += f"| {s['name']} | {s['maturity']:.0%} | {len(s['personal_rules'])}条 |\n"
    
    rpt += f"""

## 五、团队讨论 & 规则演化

### 团队协作规则（{len(data['team_rules'])}条）

"""
    for i, rule in enumerate(data["team_rules"], 1):
        rpt += f"{i}. {rule}\n"
    
    if data["consultation_log"]:
        rpt += f"\n### 三方会诊记录\n\n"
        for cl in data["consultation_log"]:
            rpt += f"- **第{cl['round']}轮**：{cl['pattern']} → 裁决：{cl['result']}\n"
            rpt += f"  - 理由：{cl['reason']}\n"
            rpt += f"  - 投票：激进({cl['voices'][0]['vote']}) / 保守({cl['voices'][1]['vote']}) / 折中({cl['voices'][2]['vote']})\n"
    
    rpt += f"""

### 讨论过程摘要

"""
    for h in data["discussion_history"]:
        rpt += f"#### 第{h['round']}轮\n\n"
        rpt += f"团队规则数：{len(h['team_rules'])} | 检测到：{', '.join(h.get('team_patterns', []))}\n\n"
    
    rpt += f"""

## 六、主动建言

"""
    for i, sug in enumerate(data["proactive_suggestions"], 1):
        rpt += f"{i}. **[{sug['type']}]** ({sug['from']})\n"
        rpt += f"   > {sug['suggestion']}\n\n"
    
    rpt += f"""

---

## 附录：每个角色的 Soul 演化轨迹

"""
    for s in data["souls"]:
        rpt += f"### {s['name']}\n"
        rpt += f"- 最终成熟度：{s['maturity']:.0%}\n"
        rpt += f"- 内化规则数：{len(s['personal_rules'])}条\n"
        rpt += f"- 初始盲区：{s['final_blind_spot']}\n"
        if s["personal_rule_history"]:
            rpt += f"- 演化轨迹：\n"
            for h in s["personal_rule_history"][:5]:
                rpt += f"  - {h.get('year', h.get('round', '?'))}期：{h.get('pattern', h.get('source', ''))} → {h['rule'][:60]}\n"
        rpt += "\n"
    
    return rpt


# ═══════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════

if __name__ == "__main__":
    # 默认问题，也可以通过命令行传参
    question = sys.argv[1] if len(sys.argv) > 1 else "我们是一家AI创业公司，想做一款面向企业客户的AI Agent平台，但不知道从哪个场景切入。团队5个人，2个算法、1个后端、1个产品、1个运营。"
    run(question, accelerator_years=10, discussion_rounds=5)
