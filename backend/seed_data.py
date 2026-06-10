import sys,os
sys.path.insert(0,os.getcwd())
from app.database import SessionLocal
from app.models import *

db = SessionLocal()
try:
    for t in [AssetHandoverLog,MetadataCompleteLog,UploadMultimodalUnstructured,UploadAssetProduct,UploadAssetApi,UploadAssetIndicator,UploadAssetLabel,UploadResourceField,UploadResourceTable,UploadResourceDatabase,UploadResourceSystem,AuditResult,AuditRule,UploadMultimodalDataset,DatasetQuality,DatasetMetadata,DatasetCatalog,MetaFieldConfig,UploadMidField,UploadMidTable,UploadMidDatabase,UploadMidSystem,MidFieldGenRule,MetadataFieldMapping,MidFieldModifyLog,UploadOperationLog,UploadResultTable,ClassifyMid,MetadataCompleteTask]:
        db.query(t).delete()
    db.commit()
    print("[OK] cleared")

    # --- Catalog ---
    cat_items = [
        ("YW-YWWH","云网运营领域",None,1,"领域",1),
        ("KH-KHFW","客户服务领域",None,1,"领域",2),
        ("SC-QQ","全渠道领域",None,1,"领域",3),
        ("SC-SC","市场领域",None,1,"领域",4),
        ("WL-WXA","网信安领域",None,1,"领域",5),
        ("CG-CG","采供领域",None,1,"领域",6),
        ("YW-YXWH","运行维护","YW-YWWH",2,"场景",1),
        ("YW-YWAQ","云网安全","YW-YWWH",2,"场景",2),
        ("YW-YJFW","应急服务","YW-YWWH",2,"场景",3),
        ("KH-FWGL","服务管理","KH-KHFW",2,"场景",1),
        ("KH-KHGX","客户关系","KH-KHFW",2,"场景",2),
        ("KH-ZLJD","质量监督","KH-KHFW",2,"场景",3),
        ("YW-YXWH-ZSK","知识库","YW-YXWH",3,"细类",1),
        ("YW-YXWH-YL","语料","YW-YXWH",3,"细类",2),
        ("KH-FWGL-YL","语料","KH-FWGL",3,"细类",1),
    ]
    for cid,name,pid,lv,ct,ord in cat_items:
        db.add(DatasetCatalog(catalog_id=cid,catalog_name=name,parent_id=pid,catalog_level=lv,catalog_type=ct,sort_order=ord))
    db.commit()
    print("[OK] catalog:",len(cat_items))

    # --- Datasets ---
    now="20260511000000"
    ds=[]
    def D(**kw): return DatasetMetadata(**kw)
    ds.append(D(dataset_id="JT-KF-HWXJ-RGHWXJLJ-0001",dataset_name="网络故障处理知识库-知识库数据集",dataset_type="知识库",biz_owner="张明",biz_owner_phone="133****1100",contact_name="李华",contact_phone="139****2211",org_unit="集团",org_dept="云网运营部",biz_scene="运行维护",biz_sub_scene="故障处理",application="网络故障AI助手",work_order_no="WO-2025-001",expected_size="500GB",actual_size="320GB",storage_location="/data/lake/network/kb/fault/",is_in_lake="是",resource_pool="内蒙",network_type="CN2-1124",host_ip="10.0.1.10",dataset_format="txt,csv,json",source_system="智能运维平台",update_freq="日",is_sensitive="否",share_requirement="全集团",use_structured="是",data_level="场景化层",kb_type="技术知识库",kb_modality="文本",kb_expected_scale="500GB",kb_actual_scale="320GB",create_time="20250115",update_time="20260511",version="v2.3.0",status="在用",build_unit="云网运营部AI组",build_target="构建网络故障处理知识库",dataset_desc="汇聚全网故障处理案例",scene_online_time="25年3月",oper_type="0",oper_time=now))
    ds.append(D(dataset_id="JT-KF-KHFW-CJWTK-0002",dataset_name="客户服务FAQ知识库-知识库数据集",dataset_type="知识库",biz_owner="王芳",biz_owner_phone="133****2200",contact_name="赵强",contact_phone="139****3322",org_unit="集团",org_dept="客户服务部",biz_scene="服务管理",biz_sub_scene="客户咨询",application="智能客服机器人",work_order_no="WO-2025-002",expected_size="200GB",actual_size="180GB",storage_location="/data/lake/customer/kb/faq/",is_in_lake="是",resource_pool="南京",network_type="CN2-BIGDATA",host_ip="10.1.1.10",dataset_format="json,csv",source_system="客服知识管理系统",update_freq="周",is_sensitive="否",share_requirement="全集团",use_structured="是",data_level="场景化层",kb_type="业务知识库",kb_modality="文本",kb_expected_scale="200GB",kb_actual_scale="180GB",create_time="20250301",update_time="20260510",version="v1.5.0",status="在用",build_unit="客户服务部AI组",build_target="构建统一FAQ知识库",dataset_desc="涵盖宽带移网IPTV业务FAQ问答对",scene_online_time="25年5月",oper_type="0",oper_time=now))
    ds.append(D(dataset_id="JT-KF-YWWH-YWDH-0003",dataset_name="云网运维对话语料-语料数据集",dataset_type="语料",biz_owner="刘伟",biz_owner_phone="133****3300",contact_name="陈晨",contact_phone="139****4433",org_unit="集团",org_dept="云网运营部",biz_scene="运行维护",biz_sub_scene="运维调度",application="运维调度大模型",work_order_no="WO-2025-003",expected_size="1TB",actual_size="780GB",storage_location="/data/lake/network/corpus/dialogue/",is_in_lake="是",resource_pool="内蒙",network_type="CN2-1124",host_ip="10.0.2.10",dataset_format="json,txt",source_system="运维工单系统",update_freq="日",is_sensitive="否",share_requirement="业务条线",use_structured="否",data_level="预处理层",corpus_type="对话语料",corpus_modality="文本",corpus_expected_scale="1TB",corpus_actual_scale="780GB",is_annotated="是",annotation_labels="意图|槽位|情感",annotation_method="人工标注",annotator_type="运维专家",create_time="20250201",update_time="20260511",version="v3.0.0",status="回流",build_unit="云网运营部",build_target="构建运维领域对话语料",dataset_desc="运维人员与调度系统对话记录含标注",scene_online_time="25年6月",oper_type="0",oper_time=now))
    ds.append(D(dataset_id="JT-KF-KHZL-KEZH-0004",dataset_name="客服质检标注语料-语料数据集",dataset_type="语料",biz_owner="孙丽",biz_owner_phone="133****4400",contact_name="周杰",contact_phone="139****5544",org_unit="X省公司",org_dept="客户服务部",biz_scene="质量监督",biz_sub_scene="服务质检",application="智能质检系统",work_order_no="WO-2025-004",expected_size="300GB",actual_size="250GB",storage_location="/data/lake/customer/quality/corpus/",is_in_lake="是",resource_pool="南京",network_type="CN2-BIGDATA",host_ip="10.2.1.10",dataset_format="json",source_system="客服录音系统",update_freq="周",is_sensitive="是",sensitive_info="客户手机号身份证号",share_requirement="业务条线",use_structured="否",data_level="预处理层",corpus_type="质检语料",corpus_modality="文本+音频",corpus_expected_scale="300GB",corpus_actual_scale="250GB",is_annotated="是",annotation_labels="服务态度|解决率",annotation_method="人工+AI辅助",annotator_type="质检专员",create_time="20250401",update_time="20260509",version="v1.2.0",status="在用",build_unit="X省公司客服部",build_target="建设客服质检语料",dataset_desc="客服通话转写文本及其质检标注",scene_online_time="25年7月",oper_type="0",oper_time=now))
    ds.append(D(dataset_id="JT-KF-YWWH-YWZSS-0005",dataset_name="网络运维助手提示词集-提示词数据集",dataset_type="提示词",biz_owner="赵岩",biz_owner_phone="133****5500",contact_name="马超",contact_phone="139****6655",org_unit="集团",org_dept="云网运营部",biz_scene="运行维护",biz_sub_scene="故障处理",application="运维助手Prompt管理",work_order_no="WO-2025-005",expected_size="10MB",actual_size="8MB",storage_location="/data/lake/network/prompt/",is_in_lake="否",not_in_lake_reason="文件较小挂载共享存储",resource_pool="天翼云",network_type="CN2-1124",host_ip="10.0.3.10",dataset_format="json,md",source_system="Prompt管理平台",update_freq="不定时",is_sensitive="否",share_requirement="业务条线",use_structured="是",data_level="场景化层",prompt_expected_scale="10MB",prompt_actual_scale="8MB",prompt_target_model="Claude-4",prompt_task="故障诊断工单生成",prompt_app_sys="运维助手Agent",create_time="20260101",update_time="20260510",version="v1.8.0",status="在用",build_unit="云网运营部AI组",build_target="构建标准化Prompt模板",dataset_desc="网络运维场景系统提示词和少样本示例",scene_online_time="25年4月",oper_type="0",oper_time=now))
    ds.append(D(dataset_id="JT-KF-YWWH-JZGJ-0006",dataset_name="基站告警原始数据-原始数据集",dataset_type="原始数据",biz_owner="钱峰",biz_owner_phone="133****6600",contact_name="吴涛",contact_phone="139****7766",org_unit="集团",org_dept="云网运营部",biz_scene="运行维护",biz_sub_scene="告警管理",application="告警分析平台",work_order_no="WO-2025-006",expected_size="2TB",actual_size="1.5TB",storage_location="/data/lake/network/raw/alarm/",is_in_lake="是",resource_pool="内蒙",network_type="CN2-1124",host_ip="10.0.4.10",dataset_format="json,csv",source_system="网管系统",update_freq="实时",is_sensitive="是",sensitive_info="基站IP设备序列号",share_requirement="业务条线",use_structured="是",data_level="原始数据层",create_time="20240101",update_time="20260511",version="v4.5.0",status="在用",build_unit="云网运营部",build_target="全量采集基站告警原始数据",dataset_desc="全国基站设备实时告警数据",scene_online_time="24年12月",oper_type="0",oper_time=now))
    ds.append(D(dataset_id="JT-KF-KHFW-YHTGD-0007",dataset_name="用户投诉工单原始数据-原始数据集",dataset_type="原始数据",biz_owner="周婷",biz_owner_phone="133****7700",contact_name="郑凯",contact_phone="139****8877",org_unit="X省公司",org_dept="客户服务部",biz_scene="服务管理",biz_sub_scene="投诉处理",application="投诉分析系统",work_order_no="WO-2025-007",expected_size="100GB",actual_size="85GB",storage_location="/data/lake/customer/raw/complaint/",is_in_lake="是",resource_pool="南京",network_type="CN2-BIGDATA",host_ip="10.2.2.10",dataset_format="json,xlsx",source_system="CRM系统",update_freq="日",is_sensitive="是",sensitive_info="客户姓名手机号身份证号地址",share_requirement="业务条线",use_structured="是",data_level="原始数据层",create_time="20250101",update_time="20260511",version="v2.0.0",status="在用",build_unit="X省公司客服部",build_target="全量采集投诉工单数据",dataset_desc="X省用户投诉工单全量数据",scene_online_time="25年3月",oper_type="0",oper_time=now))
    for d in ds:
        db.add(d)
    db.commit()
    print("[OK] datasets:",len(ds))

    # --- Quality ---
    ql=[]
    for did,dim,sc in [("JT-KF-HWXJ-RGHWXJLJ-0001","完整性",95.0),("JT-KF-HWXJ-RGHWXJLJ-0001","准确性",92.5),("JT-KF-HWXJ-RGHWXJLJ-0001","时效性",88.0),("JT-KF-KHFW-CJWTK-0002","完整性",90.0),("JT-KF-KHFW-CJWTK-0002","准确性",88.5),("JT-KF-YWWH-YWDH-0003","完整性",85.0),("JT-KF-YWWH-YWDH-0003","准确性",93.0),("JT-KF-KHZL-KEZH-0004","完整性",91.0),("JT-KF-KHZL-KEZH-0004","准确性",89.0),("JT-KF-YWWH-YWZSS-0005","完整性",97.0),("JT-KF-YWWH-YWZSS-0005","一致性",94.0),("JT-KF-YWWH-JZGJ-0006","完整性",99.0),("JT-KF-YWWH-JZGJ-0006","时效性",98.5),("JT-KF-KHFW-YHTGD-0007","完整性",96.0),("JT-KF-KHFW-YHTGD-0007","准确性",93.5)]:
        ql.append(DatasetQuality(dataset_id=did,quality_dim=dim,quality_score=sc))
    for q in ql:
        db.add(q)
    db.commit()
    print("[OK] quality:",len(ql))

    # --- Audit rules ---
    for code,name,desc,rtype,target in [
        ("MM-001","非空校验","必填字段不能为空","非空","全部"),
        ("MM-002","唯一标识格式","统一标识符合命名规范","格式","高质量数据集"),
        ("MM-003","知识库字段一致性","知识库类型扩展字段必填","一致性","高质量数据集"),
        ("MM-004","语料字段一致性","语料类型扩展字段必填","一致性","高质量数据集"),
        ("MM-005","入湖一致性","入湖是时存储位置必填","一致性","全部"),
        ("MM-006","共享一致性","非不共享时样例数据必填","一致性","全部"),
        ("MM-007","敏感数据一致性","敏感是时敏感信息必填","一致性","全部"),
        ("MM-008","样例数据条数","样例数据不少于10条","数量","全部"),
    ]:
        db.add(AuditRule(rule_code=code,rule_name=name,rule_desc=desc,rule_type=rtype,target_asset=target,is_enabled="是"))
    db.commit()
    print("[OK] audit rules: 8 items")

    # --- Audit Results (日账期 + 月账期 样例数据) ---
    from datetime import datetime
    now_ts = datetime.now()
    period_daily = now_ts.strftime("%Y%m%d")
    period_monthly = now_ts.strftime("%Y%m")
    daily_results = [
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-HWXJ-RGHWXJLJ-0001",rule_code="MM-001",is_pass="是",reason="",period_type="日",period=period_daily,check_time=now_ts),
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-HWXJ-RGHWXJLJ-0001",rule_code="MM-002",is_pass="是",reason="",period_type="日",period=period_daily,check_time=now_ts),
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-HWXJ-RGHWXJLJ-0001",rule_code="MM-003",is_pass="是",reason="",period_type="日",period=period_daily,check_time=now_ts),
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-KHFW-CJWTK-0002",rule_code="MM-001",is_pass="是",reason="",period_type="日",period=period_daily,check_time=now_ts),
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-KHFW-CJWTK-0002",rule_code="MM-002",is_pass="是",reason="",period_type="日",period=period_daily,check_time=now_ts),
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-KHZL-KEZH-0004",rule_code="MM-001",is_pass="否",reason="必填字段为空: sensitive_info",period_type="日",period=period_daily,check_time=now_ts),
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-KHZL-KEZH-0004",rule_code="MM-007",is_pass="否",reason="敏感数据信息不能为空",period_type="日",period=period_daily,check_time=now_ts),
        AuditResult(asset_type="系统",asset_id="JT-KF-HWXJ-SYS-0001",rule_code="MM-001",is_pass="是",reason="",period_type="日",period=period_daily,check_time=now_ts),
        AuditResult(asset_type="系统",asset_id="JT-KF-KHFW-SYS-0002",rule_code="MM-001",is_pass="是",reason="",period_type="日",period=period_daily,check_time=now_ts),
        AuditResult(asset_type="表",asset_id="TBL-001",rule_code="TABLE_NO_FIELD",is_pass="是",reason="",period_type="日",period=period_daily,check_time=now_ts),
    ]
    monthly_results = [
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-HWXJ-RGHWXJLJ-0001",rule_code="MM-001",is_pass="是",reason="",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-HWXJ-RGHWXJLJ-0001",rule_code="MM-002",is_pass="是",reason="",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-HWXJ-RGHWXJLJ-0001",rule_code="MM-003",is_pass="是",reason="",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-KHFW-CJWTK-0002",rule_code="MM-001",is_pass="是",reason="",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-KHFW-CJWTK-0002",rule_code="MM-002",is_pass="是",reason="",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-KHZL-KEZH-0004",rule_code="MM-001",is_pass="否",reason="必填字段为空: sensitive_info",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="高质量数据集",asset_id="JT-KF-KHZL-KEZH-0004",rule_code="MM-007",is_pass="否",reason="敏感数据信息不能为空",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="系统",asset_id="JT-KF-HWXJ-SYS-0001",rule_code="MM-001",is_pass="是",reason="",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="系统",asset_id="JT-KF-KHFW-SYS-0002",rule_code="MM-001",is_pass="是",reason="",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="数据库",asset_id="JT-KF-HWXJ-DB-0001",rule_code="MM-001",is_pass="是",reason="",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="数据库",asset_id="JT-KF-HWXJ-DB-0002",rule_code="MM-001",is_pass="是",reason="",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="表",asset_id="TBL-001",rule_code="TABLE_NO_FIELD",is_pass="是",reason="",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="表",asset_id="TBL-002",rule_code="TABLE_NO_FIELD",is_pass="否",reason="表下无字段记录",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="字段",asset_id="FIELD-001",rule_code="MM-001",is_pass="是",reason="",period_type="月",period=period_monthly,check_time=now_ts),
        AuditResult(asset_type="字段",asset_id="FIELD-002",rule_code="MM-001",is_pass="是",reason="",period_type="月",period=period_monthly,check_time=now_ts),
    ]
    for r in daily_results + monthly_results:
        db.add(r)
    db.commit()
    print(f"[OK] audit results: {len(daily_results)} daily + {len(monthly_results)} monthly")

    # --- Upload multimodal ---
    for u in [
        UploadMultimodalDataset(ust_id="JT-KF-HWXJ-RGHWXJLJ-0001",sys_name="智能运维平台",asset_type="高质量数据集",asset_format="txt,csv,json",data_size="500GB",update_freq="日",dataset_type="知识库",biz_scene="运行维护",biz_sub_scene="故障处理",is_in_lake="是",share_requirement="全集团",is_compliant="是",upload_status="待上传",oper_type="0",oper_time="20260511000000"),
        UploadMultimodalDataset(ust_id="JT-KF-KHFW-CJWTK-0002",sys_name="客服知识管理系统",asset_type="高质量数据集",asset_format="json,csv",data_size="200GB",update_freq="周",dataset_type="知识库",biz_scene="服务管理",biz_sub_scene="客户咨询",is_in_lake="是",share_requirement="全集团",is_compliant="是",upload_status="待上传",oper_type="0",oper_time="20260511000000"),
        UploadMultimodalDataset(ust_id="JT-KF-YWWH-YWDH-0003",sys_name="运维工单系统",asset_type="高质量数据集",asset_format="json,txt",data_size="1TB",update_freq="日",dataset_type="语料",biz_scene="运行维护",biz_sub_scene="运维调度",is_in_lake="是",share_requirement="业务条线",is_compliant="是",upload_status="待上传",oper_type="0",oper_time="20260511000000"),
        UploadMultimodalDataset(ust_id="JT-KF-KHZL-KEZH-0004",sys_name="客服录音系统",asset_type="高质量数据集",asset_format="json",data_size="300GB",update_freq="周",dataset_type="语料",biz_scene="质量监督",biz_sub_scene="服务质检",is_in_lake="是",share_requirement="业务条线",is_compliant="否",upload_status="待上传",non_compliant_reason="敏感数据未脱敏",oper_type="0",oper_time="20260511000000"),
    ]:
        db.add(u)
    db.commit()
    print("[OK] upload multimodal: 4 items")

    # --- Systems ---
    s1=UploadResourceSystem(sys_group_id="JT-KF-HWXJ-SYS-0001",sys_code="HWXJPT",sys_name="智能运维平台",record_name="等保三级",org_unit="集团",org_dept="云网运营部",biz_owner="张明",status="在用",sys_func_type="3",if_managed="1",online_time="20230101",is_uploaded="否",is_compliant="是",oper_type="0",oper_time="20260511000000")
    s2=UploadResourceSystem(sys_group_id="JT-KF-KHFW-SYS-0002",sys_code="KHFWPT",sys_name="客服知识管理系统",record_name="等保三级",org_unit="集团",org_dept="客户服务部",biz_owner="王芳",status="在用",sys_func_type="3",if_managed="1",online_time="20220601",is_uploaded="否",is_compliant="是",oper_type="0",oper_time="20260511000000")
    s3=UploadResourceSystem(sys_group_id="JT-KF-FIN-SYS-0003",sys_code="CWGLPT",sys_name="财务管理系统",record_name="财务系统",org_unit="集团",org_dept="财务部",biz_owner="李会计",status="建设中",sys_func_type="1",if_managed="0",online_time="",is_uploaded="否",is_compliant="是",oper_type="0",oper_time="20260511000000")
    s4=UploadResourceSystem(sys_group_id="JT-KF-HR-SYS-0004",sys_code="RLZYPT",sys_name="人力资源管理系统",record_name="HR系统",org_unit="集团",org_dept="人力部",biz_owner="赵主管",status="在用",sys_func_type="2",if_managed="1",online_time="20240101",is_uploaded="否",is_compliant="是",oper_type="0",oper_time="20260511000000")
    s5=UploadResourceSystem(sys_group_id="JT-KF-OA-SYS-0005",sys_code="OAPT",sys_name="办公自动化系统",record_name="OA系统",org_unit="集团",org_dept="综合部",biz_owner="陈主任",status="已下线",sys_func_type="3",if_managed="1",online_time="20200101",is_uploaded="否",is_compliant="是",oper_type="0",oper_time="20260511000000")
    s6=UploadResourceSystem(sys_group_id="JT-KF-DATA-SYS-0006",sys_code="YYSJPT",sys_name="运营数据分析平台",record_name="数据平台",org_unit="X省公司",org_dept="市场部",biz_owner="刘经理",status="在用",sys_func_type="1",if_managed="0",online_time="20250201",is_uploaded="否",is_compliant="是",oper_type="0",oper_time="20260511000000")
    s7=UploadResourceSystem(sys_group_id="JT-KF-BIZ-SYS-0007",sys_code="ZHYWPT",sys_name="综合业务支撑系统",record_name="业务支撑平台",org_unit="X省公司",org_dept="信息化部",biz_owner="孙主管",status="在用",sys_func_type="3",if_managed="1",online_time="20240101",is_uploaded="否",is_compliant="是",oper_type="0",oper_time="20260511000000")
    db.add_all([s1, s2, s3, s4, s5, s6, s7]); db.commit(); db.flush()
    d1=UploadResourceDatabase(db_group_id="JT-KF-HWXJ-DB-0001",sys_id=s1.id,db_name="fault_kb_db",db_type="MySQL",is_compliant="是",oper_type="0",oper_time="20260511000000")
    d2=UploadResourceDatabase(db_group_id="JT-KF-HWXJ-DB-0002",sys_id=s1.id,db_name="alarm_ods_db",db_type="Hive",is_compliant="是",oper_type="0",oper_time="20260511000000")
    d3=UploadResourceDatabase(db_group_id="JT-KF-KHFW-DB-0001",sys_id=s2.id,db_name="faq_kb_db",db_type="MySQL",is_compliant="是",oper_type="0",oper_time="20260511000000")
    db.add(d1); db.add(d2); db.add(d3); db.commit(); db.flush()
    print("[OK] upload systems+databases")

    # Seed tables & fields (use dynamic IDs, not hardcoded)
    tbl1_1 = UploadResourceTable(tbl_group_id="JT-KF-HWXJ-TABLE-0001",db_id=d1.id,table_name_en="fault_ticket",table_name_cn="故障工单表",table_desc="记录网络故障工单信息",topic_domain="运维管理",is_compliant="是",oper_type="0",oper_time="20260511000000")
    tbl1_2 = UploadResourceTable(tbl_group_id="JT-KF-HWXJ-TABLE-0002",db_id=d1.id,table_name_en="kb_article",table_name_cn="知识库文章表",table_desc="知识库文章内容",topic_domain="知识管理",is_compliant="是",oper_type="0",oper_time="20260511000000")
    tbl2_1 = UploadResourceTable(tbl_group_id="JT-KF-HWXJ-TABLE-0003",db_id=d2.id,table_name_en="alarm_event",table_name_cn="告警事件表",table_desc="基站告警事件记录",topic_domain="运维管理",is_compliant="是",oper_type="0",oper_time="20260511000000")
    db.add(tbl1_1); db.add(tbl1_2); db.add(tbl2_1); db.commit(); db.flush()
    db.add(UploadResourceField(field_group_id="JT-KF-HWXJ-FIELD-0001",tbl_id=tbl1_1.id,field_name_en="ticket_id",field_name_cn="工单ID",field_type="VARCHAR",is_compliant="是",oper_type="0",oper_time="20260511000000"))
    db.add(UploadResourceField(field_group_id="JT-KF-HWXJ-FIELD-0002",tbl_id=tbl1_1.id,field_name_en="title",field_name_cn="标题",field_type="VARCHAR",is_compliant="是",oper_type="0",oper_time="20260511000000"))
    db.add(UploadResourceField(field_group_id="JT-KF-HWXJ-FIELD-0003",tbl_id=tbl1_1.id,field_name_en="severity",field_name_cn="严重等级",field_type="VARCHAR",is_compliant="是",oper_type="0",oper_time="20260511000000"))
    db.add(UploadResourceField(field_group_id="JT-KF-HWXJ-FIELD-0004",tbl_id=tbl1_1.id,field_name_en="status_cd",field_name_cn="状态编码",field_type="VARCHAR",is_compliant="是",oper_type="0",oper_time="20260511000000"))
    db.add(UploadResourceField(field_group_id="JT-KF-HWXJ-FIELD-0005",tbl_id=tbl1_2.id,field_name_en="article_id",field_name_cn="文章ID",field_type="BIGINT",is_compliant="是",oper_type="0",oper_time="20260511000000"))
    db.add(UploadResourceField(field_group_id="JT-KF-HWXJ-FIELD-0006",tbl_id=tbl1_2.id,field_name_en="content",field_name_cn="文章内容",field_type="TEXT",is_compliant="是",oper_type="0",oper_time="20260511000000"))
    db.add(UploadResourceField(field_group_id="JT-KF-HWXJ-FIELD-0007",tbl_id=tbl2_1.id,field_name_en="alarm_id",field_name_cn="告警ID",field_type="VARCHAR",is_compliant="是",oper_type="0",oper_time="20260511000000"))
    db.add(UploadResourceField(field_group_id="JT-KF-HWXJ-FIELD-0008",tbl_id=tbl2_1.id,field_name_en="device_ip",field_name_cn="设备IP",field_type="VARCHAR",is_compliant="是",oper_type="0",oper_time="20260511000000"))
    db.commit(); print("[OK] tables+fields seeded")

    # --- Unstructured ---
    for u in [
        UploadMultimodalUnstructured(ust_id="UST-001",file_name_cn="网络拓扑图_v3",file_name_en="network_topology_v3",sys_name="智能运维平台",is_compliant="是",oper_type="0",oper_time="20260511000000"),
        UploadMultimodalUnstructured(ust_id="UST-002",file_name_cn="客服通话录音202605",file_name_en="service_call_recording_202605",sys_name="客服录音系统",is_compliant="否",non_compliant_reason="缺少分类标签",oper_type="0",oper_time="20260511000000"),
        UploadMultimodalUnstructured(ust_id="UST-003",file_name_cn="网络配置备份",file_name_en="network_config_backup",sys_name="网管系统",is_compliant="是",oper_type="0",oper_time="20260511000000"),
    ]: db.add(u)
    db.commit(); print("[OK] unstructured: 3 items")

    # --- Labels ---
    for l in [
        UploadAssetLabel(label_group_id="JT-KF-HWXJ-BQ-0001",label_name="高优先级工单",category_l1="业务标签",category_l2="工单类",biz_definition="需要2小时内响应的工单",is_compliant="是",oper_type="0",oper_time="20260511000000"),
        UploadAssetLabel(label_group_id="JT-KF-KHFW-BQ-0002",label_name="VIP客户",category_l1="客户标签",category_l2="客户等级",biz_definition="年消费超1万元的客户",is_compliant="是",oper_type="0",oper_time="20260511000000"),
        UploadAssetLabel(label_group_id="JT-KF-KHFW-BQ-0003",label_name="频繁投诉",category_l1="业务标签",category_l2="投诉类",biz_definition="本月投诉超3次的客户",is_compliant="否",non_compliant_reason="业务口径不清晰",oper_type="0",oper_time="20260511000000"),
    ]: db.add(l)
    db.commit(); print("[OK] labels: 3 items")

    # --- Indicators ---
    for ind in [
        UploadAssetIndicator(indicator_group_id="JT-KF-HWXJ-ZB-0001",indicator_name="网络可用率",unit="%",period="月",is_compliant="是",oper_type="0",oper_time="20260511000000"),
        UploadAssetIndicator(indicator_group_id="JT-KF-KHFW-ZB-0002",indicator_name="客户满意度",unit="分",period="季",is_compliant="是",oper_type="0",oper_time="20260511000000"),
    ]: db.add(ind)
    db.commit(); print("[OK] indicators: 2 items")

    # --- APIs ---
    for a in [
        UploadAssetApi(api_group_id="JT-KF-HWXJ-API-0001",api_name="工单查询",api_url="/api/v1/ticket/query",method="POST",is_compliant="是",oper_type="0",oper_time="20260511000000"),
        UploadAssetApi(api_group_id="JT-KF-KHFW-API-0002",api_name="客户信息查询",api_url="/api/v1/customer/info",method="GET",is_compliant="是",oper_type="0",oper_time="20260511000000"),
    ]: db.add(a)
    db.commit(); print("[OK] APIs: 2 items")

    # --- Products ---
    for p in [
        UploadAssetProduct(product_group_id="JT-KF-HWXJ-PRD-0001",product_name="智能运维平台",biz_domain="云网运营",category="运维工具",is_effective="是",shelf_time="20230101",expire_time="20281231",is_compliant="是",oper_type="0",oper_time="20260511000000"),
        UploadAssetProduct(product_group_id="JT-KF-KHFW-PRD-0002",product_name="智能客服机器人",biz_domain="客户服务",category="AI应用",is_effective="是",shelf_time="20240301",expire_time="20271231",is_compliant="是",oper_type="0",oper_time="20260511000000"),
    ]: db.add(p)
    db.commit(); print("[OK] products: 2 items")

    # ==================== 元模型字段配置 (56字段) ====================
    import json
    fields = []
    def F(field_id, field_name, field_group, field_type="VARCHAR", source_type="manual", is_required="是", enum_values=None, default_value=None, max_length=None, sort_order=0, condition_expr=None, display_width=2):
        fields.append(MetaFieldConfig(
            field_id=field_id, field_name=field_name, field_group=field_group,
            field_type=field_type, source_type=source_type, is_required=is_required,
            enum_values=json.dumps(enum_values, ensure_ascii=False) if enum_values else None,
            default_value=default_value, max_length=max_length,
            sort_order=sort_order,
            condition_expr=json.dumps(condition_expr, ensure_ascii=False) if condition_expr else None,
            display_width=display_width,
        ))

    # --- 基础信息组 (13个字段) ---
    F("DATASET_NAME", "数据集名称", "基础信息组", sort_order=1, default_value="子场景名称+知识库/语料数据集")
    F("DATASET_ID", "数据集唯一标识", "基础信息组", source_type="system", sort_order=2)
    F("DATASET_TYPE", "数据集类型", "基础信息组", field_type="SELECT", enum_values=["原始数据","知识库","语料","提示词"], sort_order=3)
    F("BIZ_OWNER", "业务负责人", "基础信息组", sort_order=4)
    F("BIZ_OWNER_PHONE", "业务负责人联系电话", "基础信息组", sort_order=5)
    F("CONTACT_NAME", "数据集接口人姓名", "基础信息组", sort_order=6)
    F("CONTACT_PHONE", "数据集接口人联系方式", "基础信息组", sort_order=7)
    F("ORG_UNIT", "所属单位", "基础信息组", sort_order=8)
    F("ORG_DEPT", "所属部门", "基础信息组", sort_order=9)
    F("BIZ_SCENE", "业务场景名称", "基础信息组", sort_order=10)
    F("BIZ_SUB_SCENE", "业务子场景名称", "基础信息组", sort_order=11)
    F("APPLICATION", "应用", "基础信息组", sort_order=12)
    F("WORK_ORDER_NO", "工单号", "基础信息组", sort_order=13)

    # --- 存储信息组 (8个字段) ---
    F("EXPECTED_SIZE", "预计数据集大小", "存储信息组", sort_order=1)
    F("ACTUAL_SIZE", "实际采集大小", "存储信息组", source_type="system", is_required="否", sort_order=2)
    F("STORAGE_LOCATION", "存储位置", "存储信息组", source_type="system", is_required="否", sort_order=3,
      condition_expr={"field":"is_in_lake","eq":"是","required_fields":["STORAGE_LOCATION"]})
    F("IS_IN_LAKE", "是否入湖", "存储信息组", field_type="SELECT", enum_values=["是","否"], sort_order=4)
    F("NOT_IN_LAKE_REASON", "不入湖原因", "存储信息组", field_type="TEXT", is_required="否", sort_order=5,
      condition_expr={"field":"is_in_lake","eq":"否","required_fields":["NOT_IN_LAKE_REASON"]})
    F("RESOURCE_POOL", "数据所在资源池", "存储信息组", sort_order=6, enum_values=["内蒙","南京","公有云","天翼云"])
    F("NETWORK_TYPE", "网络类型", "存储信息组", sort_order=7, enum_values=["CN2-1124","CN2-BIGDATA"])
    F("HOST_IP", "主机IP", "存储信息组", field_type="TEXT", sort_order=8)

    # --- 结构属性信息组 (9个基础 + 知识库4 + 语料8 + 提示词5 = 26个字段) ---
    F("DATASET_FORMAT", "数据集格式", "结构属性信息组", field_type="MULTI_SELECT", sort_order=1,
      enum_values=["txt","csv","json","xml","xlsx","jpg","png","pdf","md","parquet","avro"])
    F("SOURCE_SYSTEM", "来源系统", "结构属性信息组", sort_order=2)
    F("UPDATE_FREQ", "更新频率", "结构属性信息组", field_type="SELECT", sort_order=3,
      enum_values=["年","月","周","日","实时","不定时"])
    F("IS_SENSITIVE", "是否敏感", "结构属性信息组", field_type="SELECT", sort_order=4, enum_values=["是","否"])
    F("SENSITIVE_INFO", "敏感数据信息", "结构属性信息组", field_type="TEXT", is_required="否", sort_order=5,
      condition_expr={"field":"is_sensitive","eq":"是","required_fields":["SENSITIVE_INFO"]})
    F("SHARE_REQUIREMENT", "内部共享要求", "结构属性信息组", sort_order=6, enum_values=["全集团","业务条线","不共享"])
    F("USE_STRUCTURED", "是否使用结构化数据", "结构属性信息组", field_type="SELECT", sort_order=7, enum_values=["是","否"])
    F("DATASET_SCOPE", "数据集范围", "结构属性信息组", is_required="否", sort_order=8)
    F("DATA_LEVEL", "数据层级", "结构属性信息组", source_type="system", sort_order=9,
      enum_values=["原始数据层","预处理层","场景化层"])

    # 知识库扩展
    F("KB_TYPE", "知识库数据集类型", "结构属性信息组", is_required="否", sort_order=10,
      enum_values=["技术知识库","业务知识库","FAQ知识库","产品知识库"],
      condition_expr={"field":"dataset_type","eq":"知识库","required_fields":["KB_TYPE","KB_MODALITY","KB_EXPECTED_SCALE"]})
    F("KB_MODALITY", "知识库数据集模态", "结构属性信息组", is_required="否", sort_order=11,
      enum_values=["文本","图片","音频","视频","多模态"],
      condition_expr={"field":"dataset_type","eq":"知识库","required_fields":["KB_TYPE","KB_MODALITY","KB_EXPECTED_SCALE"]})
    F("KB_EXPECTED_SCALE", "知识库数据集预期规模", "结构属性信息组", is_required="否", sort_order=12,
      condition_expr={"field":"dataset_type","eq":"知识库","required_fields":["KB_TYPE","KB_MODALITY","KB_EXPECTED_SCALE"]})
    F("KB_ACTUAL_SCALE", "知识库数据集实际规模", "结构属性信息组", source_type="system", is_required="否", sort_order=13)

    # 语料扩展
    F("CORPUS_TYPE", "语料数据集类型", "结构属性信息组", is_required="否", sort_order=14,
      enum_values=["对话语料","质检语料","训练语料","评测语料"],
      condition_expr={"field":"dataset_type","eq":"语料","required_fields":["CORPUS_TYPE","CORPUS_MODALITY","CORPUS_EXPECTED_SCALE"]})
    F("CORPUS_MODALITY", "语料数据集模态", "结构属性信息组", is_required="否", sort_order=15,
      enum_values=["文本","音频","视频","文本+音频","多模态"],
      condition_expr={"field":"dataset_type","eq":"语料","required_fields":["CORPUS_TYPE","CORPUS_MODALITY","CORPUS_EXPECTED_SCALE"]})
    F("CORPUS_EXPECTED_SCALE", "语料数据集预期规模", "结构属性信息组", is_required="否", sort_order=16,
      condition_expr={"field":"dataset_type","eq":"语料","required_fields":["CORPUS_TYPE","CORPUS_MODALITY","CORPUS_EXPECTED_SCALE"]})
    F("CORPUS_ACTUAL_SCALE", "语料数据集实际规模", "结构属性信息组", source_type="system", is_required="否", sort_order=17)
    F("IS_ANNOTATED", "语料是否标注", "结构属性信息组", field_type="SELECT", is_required="否", sort_order=18, enum_values=["是","否"])
    F("ANNOTATION_LABELS", "语料标注标签", "结构属性信息组", is_required="否", sort_order=19)
    F("ANNOTATION_METHOD", "语料标注方式", "结构属性信息组", is_required="否", sort_order=20, enum_values=["人工标注","自动标注","人工+AI辅助"])
    F("ANNOTATOR_TYPE", "语料标注人员类型", "结构属性信息组", is_required="否", sort_order=21, enum_values=["运维专家","质检专员","客服专员","AI"])

    # 提示词扩展
    F("PROMPT_EXPECTED_SCALE", "提示词预期规模", "结构属性信息组", is_required="否", sort_order=22,
      condition_expr={"field":"dataset_type","eq":"提示词","required_fields":["PROMPT_EXPECTED_SCALE"]})
    F("PROMPT_ACTUAL_SCALE", "提示词实际规模", "结构属性信息组", source_type="system", is_required="否", sort_order=23)
    F("PROMPT_TARGET_MODEL", "提示词目标模型", "结构属性信息组", is_required="否", sort_order=24)
    F("PROMPT_TASK", "提示词适用任务", "结构属性信息组", is_required="否", sort_order=25)
    F("PROMPT_APP_SYS", "提示词应用系统", "结构属性信息组", is_required="否", sort_order=26)

    # --- 生命周期组 (9个字段) ---
    F("CREATE_TIME", "数据集创建时间", "生命周期组", field_type="DATE", sort_order=1)
    F("UPDATE_TIME", "数据集最新更新时间", "生命周期组", field_type="DATE", source_type="system", sort_order=2)
    F("VERSION", "版本信息", "生命周期组", source_type="system", sort_order=3)
    F("STATUS", "状态标识", "生命周期组", field_type="SELECT", source_type="system", sort_order=4,
      enum_values=["在用","入湖","回流","共享","下线"])
    F("BUILD_UNIT", "数据集建设单位", "生命周期组", sort_order=5)
    F("BUILD_TARGET", "数据集建设目标", "生命周期组", field_type="TEXT", is_required="否", sort_order=6)
    F("BUILD_PLAN", "数据集建设计划", "生命周期组", field_type="TEXT", is_required="否", sort_order=7)
    F("DATASET_DESC", "数据集描述", "生命周期组", field_type="TEXT", is_required="否", sort_order=8)
    F("SCENE_ONLINE_TIME", "子场景实际/预计上线时间", "生命周期组", field_type="DATE", sort_order=9)
    F("SAMPLE_DATA", "样例数据", "生命周期组", field_type="TEXT", source_type="system", is_required="否", sort_order=10,
      condition_expr={"field":"share_requirement","eq":"不共享","required_fields":[]})

    for f in fields:
        db.add(f)
    db.commit()
    print(f"[OK] meta field configs: {len(fields)} items")

    # --- 中间表字段生成规则 ---
    from app.models.upload_mid import MidFieldGenRule, MetadataFieldMapping, UploadMidSystem, UploadMidDatabase, UploadMidTable, UploadMidField, UploadOperationLog
    rules_data = [
        ("table", "group_unique_id", "FORMULA", '[]', "", "group_id_generated=0", "集团表唯一标识生成"),
        ("table", "oper_time", "COPY", '[]', "", "oper_time IS NULL", "操作时间自动生成"),
        ("table", "uploaded_to_big_lake", "ENUM_MAP", '[]', "0", "uploaded_to_big_lake IS NULL", "湖外系统默认0"),
        ("table", "premium_model_in_lake", "ENUM_MAP", '[]', "0", "premium_model_in_lake IS NULL", "湖外系统默认0"),
        ("table", "is_shared", "ENUM_MAP", '[]', "0", "is_shared IS NULL", "非共享默认0"),
    ]
    for at, tf, rt, sf, expr, cond, rmk in rules_data:
        db.add(MidFieldGenRule(asset_type=at, target_field=tf, rule_type=rt,
                                rule_expr=expr, trigger_condition=cond, remark=rmk))
    db.commit()
    print(f"[OK] mid field gen rules: {len(rules_data)} items")

    # --- 字段映射 ---
    mappings = [
        ("system", "sys_code", "sys_code"), ("system", "sys_name", "sys_name"),
        ("system", "record_name", "record_name"), ("system", "master_data_code", "master_data_code"),
        ("system", "org_unit", "org_unit"), ("system", "org_dept", "org_dept"),
        ("system", "biz_owner", "biz_owner"), ("system", "status", "status"),
        ("system", "online_time", "online_time"),
        ("database", "db_name", "db_name"), ("database", "db_type", "db_type"),
        ("table", "table_name_en", "table_name_en"), ("table", "table_name_cn", "table_name"),
        ("table", "table_desc", "table_introduct"), ("table", "topic_domain", "table_domain"),
        ("table", "sample_data", "sample_data"),
        ("field", "field_name_en", "field_name_en"), ("field", "field_name_cn", "field_name_cn"),
        ("field", "field_type", "field_type"),
    ]
    for at, lf, mf in mappings:
        db.add(MetadataFieldMapping(asset_type=at, local_field=lf, mid_field=mf))
    db.commit()
    print(f"[OK] metadata field mappings: {len(mappings)} items")

    # ─── 中间表数据（覆盖各状态组合） ────────────────────────

    # -- 系统 (7个，覆盖状态/功能类型/是否盘点/稽核状态/上传状态各种组合) --
    mid_systems = [
        UploadMidSystem(local_biz_id="SYS-001", sys_code="HWXJ", sys_name="网络故障智能运维系统",
            record_name="智能运维平台", master_data_code="MD-CLOUD-001",
            org_unit="集团", org_dept="云网运营部", biz_owner="张明",
            status="在用", sys_func_type="3", if_managed="1", online_time="202501",
            audit_status="pass", upload_status="synced"),
        UploadMidSystem(local_biz_id="SYS-002", sys_code="KHFW", sys_name="客户服务知识管理系统",
            record_name="客服知识平台", master_data_code="MD-CUSTOMER-002",
            org_unit="X省公司", org_dept="客户服务部", biz_owner="王芳",
            status="在用", sys_func_type="3", if_managed="1", online_time="202503",
            audit_status="fail", non_compliant_reason="[MM-001]必填字段为空: biz_scene",
            upload_status="pending"),
        UploadMidSystem(local_biz_id="SYS-003", sys_code="CWGL", sys_name="财务管理系统",
            record_name="财务管控平台", master_data_code="MD-FIN-003",
            org_unit="集团", org_dept="财务部", biz_owner="李会计",
            status="建设中", sys_func_type="1", if_managed="0", online_time="",
            audit_status="pending", upload_status="pending"),  # 建设中不盘，待稽核
        UploadMidSystem(local_biz_id="SYS-004", sys_code="RLZY", sys_name="人力资源管理系统",
            record_name="HR平台", master_data_code="MD-HR-004",
            org_unit="集团", org_dept="人力部", biz_owner="赵主管",
            status="在用", sys_func_type="2", if_managed="1", online_time="202401",
            audit_status="pass", upload_status="uploaded"),  # 纯功能但需盘点，已上传
        UploadMidSystem(local_biz_id="SYS-005", sys_code="OA", sys_name="办公自动化系统",
            record_name="OA协同平台", master_data_code="MD-OA-005",
            org_unit="集团", org_dept="综合部", biz_owner="陈主任",
            status="已下线", sys_func_type="3", if_managed="1", online_time="202001",
            audit_status="pass", upload_status="synced"),  # 已下线但仍盘，已同步
        UploadMidSystem(local_biz_id="SYS-006", sys_code="YYSJ", sys_name="运营数据分析平台",
            record_name="运营数据平台", master_data_code="MD-DATA-006",
            org_unit="X省公司", org_dept="市场部", biz_owner="刘经理",
            status="在用", sys_func_type="1", if_managed="0", online_time="202502",
            audit_status="fail", non_compliant_reason="[MM-001]必填字段为空: biz_owner",
            upload_status="pending"),  # 纯数据但不盘点，稽核不通过
        UploadMidSystem(local_biz_id="SYS-007", sys_code="ZHYW", sys_name="综合业务支撑系统",
            record_name="业务支撑平台", master_data_code="",
            org_unit="X省公司", org_dept="信息化部", biz_owner="孙主管",
            status="在用", sys_func_type="3", if_managed="1", online_time="202401",
            audit_status="pending", upload_status="pending"),  # 待稽核待上传，集团主数据编码为空
    ]
    db.add_all(mid_systems)
    db.flush()
    print(f"[OK] mid systems: {len(mid_systems)} items")

    # -- 数据库 (6个，覆盖各状态 + 关联不同系统) --
    mid_databases = [
        UploadMidDatabase(local_biz_id="DB-001", sys_local_biz_id="SYS-001",
            db_name="fault_analysis_db", db_type="MySQL",
            audit_status="pass", upload_status="synced"),
        UploadMidDatabase(local_biz_id="DB-002", sys_local_biz_id="SYS-001",
            db_name="network_topology_db", db_type="PostgreSQL",
            audit_status="pass", upload_status="synced"),
        UploadMidDatabase(local_biz_id="DB-003", sys_local_biz_id="SYS-002",
            db_name="customer_service_db", db_type="MySQL",
            audit_status="fail", non_compliant_reason="[MM-001]数据库类型为空",
            upload_status="pending"),
        UploadMidDatabase(local_biz_id="DB-004", sys_local_biz_id="SYS-004",
            db_name="hr_employee_db", db_type="Oracle",
            audit_status="pending", upload_status="pending"),
        UploadMidDatabase(local_biz_id="DB-005", sys_local_biz_id="SYS-005",
            db_name="oa_archive_db", db_type="MySQL",
            audit_status="pass", upload_status="uploaded"),
        UploadMidDatabase(local_biz_id="DB-006", sys_local_biz_id="SYS-007",
            db_name="biz_order_db", db_type="MySQL",
            audit_status="pass", upload_status="failed"),  # 上传失败的场景
    ]
    db.add_all(mid_databases)
    db.flush()
    print(f"[OK] mid databases: {len(mid_databases)} items")

    # -- 表 (8个，覆盖各状态 + 样例数据不同情况) --
    mid_tables = [
        UploadMidTable(local_biz_id="TBL-001", db_local_biz_id="DB-001",
            table_name_en="fault_alarm", table_name="故障告警表",
            table_introduct="存储网络设备告警信息", table_domain="运行维护",
            sample_data='[{"id":"1","level":"critical"},{"id":"2","level":"major"},{"id":"3","level":"minor"}]',
            audit_status="pass", upload_status="synced"),
        UploadMidTable(local_biz_id="TBL-002", db_local_biz_id="DB-001",
            table_name_en="fault_recovery", table_name="故障恢复记录表",
            table_introduct="", table_domain="运行维护",
            audit_status="fail", non_compliant_reason="表简介为空",
            upload_status="pending"),
        UploadMidTable(local_biz_id="TBL-003", db_local_biz_id="DB-001",
            table_name_en="network_device", table_name="网络设备表",
            table_introduct="存储全网网络设备清单", table_domain="运行维护",
            sample_data='[{"id":"1","ip":"10.0.1.1","type":"router"},{"id":"2","ip":"10.0.1.2","type":"switch"}]',
            audit_status="pending", upload_status="pending"),
        UploadMidTable(local_biz_id="TBL-004", db_local_biz_id="DB-002",
            table_name_en="topology_link", table_name="网络拓扑链路表",
            table_introduct="网络设备间链路关系数据", table_domain="运行维护",
            sample_data='[{"id":"1","src":"10.0.1.1","dst":"10.0.2.1"}]',
            audit_status="pass", upload_status="uploaded"),
        UploadMidTable(local_biz_id="TBL-005", db_local_biz_id="DB-003",
            table_name_en="customer_info", table_name="客户信息表",
            table_introduct="存储客户基本信息", table_domain="客户服务",
            audit_status="pending", upload_status="pending"),
        UploadMidTable(local_biz_id="TBL-006", db_local_biz_id="DB-003",
            table_name_en="complaint_record", table_name="投诉记录表", table_introduct="",
            table_domain="",  # 主题域为空，稽核会不通过
            audit_status="fail", non_compliant_reason="[MM-001]必填字段为空: table_introduct, table_domain",
            upload_status="pending"),
        UploadMidTable(local_biz_id="TBL-007", db_local_biz_id="DB-005",
            table_name_en="oa_document", table_name="OA公文表",
            table_introduct="存储OA系统公文流转数据", table_domain="综合管理",
            audit_status="pass", upload_status="synced"),
        UploadMidTable(local_biz_id="TBL-008", db_local_biz_id="DB-006",
            table_name_en="biz_order", table_name="业务订单表",
            table_introduct="核心业务订单数据", table_domain="业务支撑", sample_data='[{"orderId":"ORD001","amount":100},{"orderId":"ORD002","amount":200}]',
            audit_status="pass", upload_status="failed"),
    ]
    db.add_all(mid_tables)
    db.flush()
    print(f"[OK] mid tables: {len(mid_tables)} items")

    # -- 字段 (10个，覆盖各状态 + 分属不同表) --
    mid_fields = [
        UploadMidField(local_biz_id="FIELD-001", tbl_local_biz_id="TBL-001",
            field_name_en="alarm_id", field_name_cn="告警ID", field_type="varchar",
            audit_status="pass", upload_status="synced"),
        UploadMidField(local_biz_id="FIELD-002", tbl_local_biz_id="TBL-001",
            field_name_en="alarm_level", field_name_cn="告警级别", field_type="int",
            audit_status="pass", upload_status="synced"),
        UploadMidField(local_biz_id="FIELD-003", tbl_local_biz_id="TBL-002",
            field_name_en="recovery_id", field_name_cn="恢复记录ID", field_type="",
            audit_status="fail", non_compliant_reason="[MM-001]字段类型为空",
            upload_status="pending"),
        UploadMidField(local_biz_id="FIELD-004", tbl_local_biz_id="TBL-001",
            field_name_en="device_ip", field_name_cn="设备IP", field_type="varchar",
            audit_status="pending", upload_status="pending"),
        UploadMidField(local_biz_id="FIELD-005", tbl_local_biz_id="TBL-002",
            field_name_en="recovery_time", field_name_cn="恢复时间", field_type="datetime",
            audit_status="pass", upload_status="uploaded"),
        UploadMidField(local_biz_id="FIELD-006", tbl_local_biz_id="TBL-004",
            field_name_en="link_id", field_name_cn="链路ID", field_type="varchar",
            audit_status="pass", upload_status="synced"),
        UploadMidField(local_biz_id="FIELD-007", tbl_local_biz_id="TBL-005",
            field_name_en="cust_id", field_name_cn="客户编号", field_type="varchar",
            audit_status="pending", upload_status="pending"),
        UploadMidField(local_biz_id="FIELD-008", tbl_local_biz_id="TBL-005",
            field_name_en="cust_name", field_name_cn="客户名称", field_type="varchar",
            audit_status="pending", upload_status="pending"),
        UploadMidField(local_biz_id="FIELD-009", tbl_local_biz_id="TBL-007",
            field_name_en="doc_number", field_name_cn="公文编号", field_type="varchar",
            audit_status="pass", upload_status="synced"),
        UploadMidField(local_biz_id="FIELD-010", tbl_local_biz_id="TBL-008",
            field_name_en="order_amount", field_name_cn="订单金额", field_type="decimal",
            audit_status="pass", upload_status="failed"),
    ]
    db.add_all(mid_fields)
    db.commit()
    print(f"[OK] mid fields: {len(mid_fields)} items")

    # --- 操作日志 ---
    ops = [
        UploadOperationLog(operation_type="SYNC", asset_type="system", scope_type="ALL",
                           operator="管理员", result="SUCCESS", result_msg="全量同步: 7条"),
        UploadOperationLog(operation_type="AUDIT", asset_type="system", scope_type="ALL",
                           operator="管理员", result="PARTIAL", result_msg="通过4条，不通过2条，跳过1条"),
        UploadOperationLog(operation_type="SYNC_TO_RESULT", asset_type="system", scope_type="ALL",
                           operator="管理员", result="SUCCESS", result_msg="同步2条"),
        UploadOperationLog(operation_type="UPLOAD", asset_type="system", scope_type="ALL",
                           operator="管理员", result="SUCCESS", result_msg="成功1条，失败0条"),
        UploadOperationLog(operation_type="SYNC", asset_type="database", scope_type="ALL",
                           operator="管理员", result="SUCCESS", result_msg="全量同步: 6条"),
        UploadOperationLog(operation_type="AUDIT", asset_type="database", scope_type="ALL",
                           operator="管理员", result="PARTIAL", result_msg="通过4条，不通过1条"),
        UploadOperationLog(operation_type="SYNC", asset_type="table", scope_type="ALL",
                           operator="管理员", result="SUCCESS", result_msg="全量同步: 8条"),
        UploadOperationLog(operation_type="AUDIT", asset_type="table", scope_type="ALL",
                           operator="管理员", result="PARTIAL", result_msg="通过5条，不通过2条"),
        UploadOperationLog(operation_type="MID_MODIFY", asset_type="system", scope_type="single",
                           scope_id="SYS-002", operator="管理员",
                           result="SUCCESS", result_msg="修改2个字段"),
        UploadOperationLog(operation_type="MID_MODIFY", asset_type="table", scope_type="single",
                           scope_id="TBL-002", operator="管理员",
                           result="SUCCESS", result_msg="修改1个字段"),
        UploadOperationLog(operation_type="UPLOAD", asset_type="database", scope_type="ALL",
                           operator="管理员", result="FAIL", result_msg="成功3条，失败1条"),
    ]
    for o in ops:
        db.add(o)
    db.commit()
    print(f"[OK] operation logs: {len(ops)} items")

    # --- 集团上传中间结果表（已上传成功的记录） ---
    import json
    result_data = [
        UploadResultTable(asset_type="system", local_biz_id="SYS-004",
                          group_unique_id="JT-SYSTEM-HR-0001",
                          data_snapshot=json.dumps(
                              {"sys_code":"RLZY","sys_name":"人力资源管理系统","status":"在用","sys_func_type":"2","if_managed":"1"},
                              ensure_ascii=False),
                          upload_status="uploaded", upload_batch_no="BATCH-20260525-001"),
        UploadResultTable(asset_type="database", local_biz_id="DB-005",
                          group_unique_id="JT-DATABASE-OA-0001",
                          data_snapshot=json.dumps(
                              {"db_name":"oa_archive_db","db_type":"MySQL"},
                              ensure_ascii=False),
                          upload_status="uploaded", upload_batch_no="BATCH-20260525-001"),
        UploadResultTable(asset_type="table", local_biz_id="TBL-004",
                          group_unique_id="JT-TABLE-TOPO-0001",
                          data_snapshot=json.dumps(
                              {"table_name_en":"topology_link","table_name":"网络拓扑链路表","table_domain":"运行维护"},
                              ensure_ascii=False),
                          upload_status="pending"),
        UploadResultTable(asset_type="field", local_biz_id="FIELD-005",
                          group_unique_id="JT-FIELD-REC-0001",
                          data_snapshot=json.dumps(
                              {"field_name_en":"recovery_time","field_name_cn":"恢复时间","field_type":"datetime"},
                              ensure_ascii=False),
                          upload_status="pending"),
    ]
    for r in result_data:
        if not r.sync_to_result_time:
            r.sync_to_result_time = datetime.now()
        if not r.upload_time and r.upload_status == "uploaded":
            r.upload_time = datetime.now()
        db.add(r)
    db.commit()
    print(f"[OK] upload result table: {len(result_data)} items")

    # --- 中间表修改日志 ---
    modify_logs = [
        MidFieldModifyLog(asset_type="system", local_biz_id="SYS-002",
                          field_name="org_unit", old_value="", new_value="X省公司",
                          operator="管理员", modify_reason="补全所属单位字段"),
        MidFieldModifyLog(asset_type="system", local_biz_id="SYS-002",
                          field_name="biz_owner", old_value="", new_value="王芳",
                          operator="管理员", modify_reason="补全业务负责人字段"),
        MidFieldModifyLog(asset_type="table", local_biz_id="TBL-002",
                          field_name="table_introduct", old_value="", new_value="存储故障恢复操作记录数据",
                          operator="管理员", modify_reason="补充表简介使稽核通过"),
        MidFieldModifyLog(asset_type="field", local_biz_id="FIELD-003",
                          field_name="field_type", old_value="", new_value="varchar",
                          operator="管理员", modify_reason="补充字段类型"),
    ]
    for m in modify_logs:
        db.add(m)
    db.commit()
    print(f"[OK] modify logs: {len(modify_logs)} items")

    # --- 分级分类中间表数据（覆盖有效/无效/待定三种状态） ---
    from datetime import datetime
    classify_data = [
        # 有效的分类记录（可通过sync_to_result）
        ClassifyMid(local_biz_id="SYS-001", asset_type="system", data_level="3", data_category="生产数据", classify_status="valid"),
        ClassifyMid(local_biz_id="SYS-004", asset_type="system", data_level="2", data_category="内部管理", classify_status="valid"),
        ClassifyMid(local_biz_id="SYS-005", asset_type="system", data_level="4", data_category="历史归档", classify_status="valid"),
        ClassifyMid(local_biz_id="DB-001", asset_type="database", data_level="3", data_category="生产数据", classify_status="valid"),
        ClassifyMid(local_biz_id="DB-002", asset_type="database", data_level="3", data_category="生产数据", classify_status="valid"),
        ClassifyMid(local_biz_id="DB-005", asset_type="database", data_level="2", data_category="内部管理", classify_status="valid"),
        ClassifyMid(local_biz_id="TBL-001", asset_type="table", data_level="3", data_category="生产数据", classify_status="valid"),
        ClassifyMid(local_biz_id="TBL-004", asset_type="table", data_level="3", data_category="生产数据", classify_status="valid"),
        ClassifyMid(local_biz_id="TBL-007", asset_type="table", data_level="2", data_category="内部管理", classify_status="valid"),
        ClassifyMid(local_biz_id="FIELD-001", asset_type="field", data_level="3", data_category="生产数据", classify_status="valid"),
        ClassifyMid(local_biz_id="FIELD-002", asset_type="field", data_level="3", data_category="生产数据", classify_status="valid"),
        ClassifyMid(local_biz_id="FIELD-005", asset_type="field", data_level="2", data_category="内部管理", classify_status="valid"),
        ClassifyMid(local_biz_id="FIELD-006", asset_type="field", data_level="3", data_category="生产数据", classify_status="valid"),
        ClassifyMid(local_biz_id="FIELD-009", asset_type="field", data_level="2", data_category="内部管理", classify_status="valid"),
        # 分类无效的记录（sync_to_result会跳过）
        ClassifyMid(local_biz_id="SYS-002", asset_type="system", data_level="3", data_category="生产数据", classify_status="invalid"),
        ClassifyMid(local_biz_id="DB-003", asset_type="database", data_level="3", data_category="生产数据", classify_status="invalid"),
        ClassifyMid(local_biz_id="TBL-002", asset_type="table", data_level="3", data_category="生产数据", classify_status="invalid"),
        ClassifyMid(local_biz_id="FIELD-003", asset_type="field", data_level="3", data_category="生产数据", classify_status="invalid"),
        # 分类待定的记录（sync_to_result也会跳过）
        ClassifyMid(local_biz_id="TBL-005", asset_type="table", data_level="1", data_category="待分类", classify_status="pending"),
        ClassifyMid(local_biz_id="FIELD-007", asset_type="field", data_level="1", data_category="待分类", classify_status="pending"),
        ClassifyMid(local_biz_id="FIELD-008", asset_type="field", data_level="1", data_category="待分类", classify_status="pending"),
        # 注意：SYS-006, SYS-007, DB-004, DB-006, TBL-003, TBL-006, TBL-008, FIELD-004, FIELD-010
        # 没有对应的ClassifyMid记录，sync_to_result也会跳过
    ]
    for c in classify_data:
        c.classify_time = datetime.now()
        c.source = "自动分类"
        db.add(c)
    db.commit()
    print(f"[OK] classify mid: {len(classify_data)} items")

    print("\n=== ALL SEED DATA INSERTED ===")
finally:
    db.close()
