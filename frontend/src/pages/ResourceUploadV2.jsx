import React, { useState, useEffect, useCallback } from "react"
import { Table, Tabs, Select, Input, Button, Tag, Space, Modal, Form, message, Alert, Descriptions, Breadcrumb } from "antd"
import { SyncOutlined, SafetyCertificateOutlined, SendOutlined, CloudUploadOutlined, HistoryOutlined, EditOutlined, SearchOutlined, WarningOutlined, StopOutlined, MergeCellsOutlined, TableOutlined, FileTextOutlined } from "@ant-design/icons"
import dayjs from "dayjs"
import { useNavigate } from "react-router-dom"
import api from "../services/api"

const { Option } = Select
const { TextArea } = Input
const LEVELS = ["system", "database", "table", "field"]
const LEVEL_LABELS = { system: "系统", database: "数据库", table: "表", field: "字段" }

// ─── API Helpers ───────────────────────────────

async function fetchOptions(assetType, parentLocalBizId) {
  const params = { asset_type: assetType }
  if (parentLocalBizId) params.parent_local_biz_id = parentLocalBizId
  const res = await api.get("/upload/mid-options", { params })
  return res.code === "000000" ? (res.data || []) : []
}

async function fetchMidList(assetType, parentLocalBizId, extraFilters, page, size) {
  const params = { asset_type: assetType, page, size }
  if (parentLocalBizId) params.parent_local_biz_id = parentLocalBizId
  if (extraFilters?.parent_level) {
    params.parent_level = extraFilters.parent_level
    delete extraFilters.parent_level
  }
  Object.entries(extraFilters || {}).forEach(([k, v]) => { if (v) params[k] = v })
  const res = await api.get("/upload/mid-list", { params })
  return res.code === "000000" ? res.data : { list: [], total: 0, page, size }
}

// ─── Constants ─────────────────────────────────

const PARENT_LABEL_MAP = {
  database: { label: "所属系统", nameKey: "sysName" },
  table: { label: "所属数据库", nameKey: "dbName" },
  field: { label: "所属表", nameKey: "tableName" },
}

const EDITABLE_FIELDS = {
  system: ["sys_code", "sys_name", "record_name", "org_unit", "org_dept", "biz_owner", "status"],
  database: ["db_name", "db_type"],
  table: ["table_name_en", "table_name", "table_introduct", "table_domain", "sample_data"],
  field: ["field_name_en", "field_name_cn", "field_type"],
}

const REQUIRED_FIELDS = {
  system: ["sys_name", "record_name", "org_unit", "org_dept"],
  database: ["db_name", "db_type"],
  table: ["table_name", "table_introduct", "table_domain"],
  field: ["field_name_cn"],
}

// ─── Table columns per level ───────────────────

const TYPE_COLUMNS = {
  system: [
    { title: "子系统编码", dataIndex: "sys_code", width: 100 },
    { title: "系统名称", dataIndex: "sys_name", width: 160 },
    { title: "定级备案名称", dataIndex: "record_name", width: 140 },
    { title: "状态", dataIndex: "status", width: 80, render: (v) => <Tag>{v}</Tag> },
    { title: "功能类型", dataIndex: "sys_func_type", width: 90,
      render: (v) => ({ "1": "纯数据", "2": "纯功能", "3": "数据+功能" })[v] || v },
    { title: "是否盘点", dataIndex: "if_managed", width: 80,
      render: (v) => v === "1" ? <Tag color="blue">是</Tag> : <Tag>否</Tag> },
  ],
  database: [
    { title: "数据库名", dataIndex: "db_name", width: 160 },
    { title: "数据库类型", dataIndex: "db_type", width: 120 },
    { title: "IP", dataIndex: "db_ip", width: 120 },
    { title: "端口", dataIndex: "db_port", width: 80 },
    { title: "上传标记", dataIndex: "upload_flag", width: 90,
      render: (v, r) => <Switch checked={v !== "0"} checkedChildren="上传" unCheckedChildren="不上传" size="small" /> },
  ],
  table: [
    { title: "表英文名", dataIndex: "table_name_en", width: 140 },
    { title: "表中文名", dataIndex: "table_name", width: 140 },
    { title: "主题域", dataIndex: "table_domain", width: 100 },
    { title: "上传标记", dataIndex: "upload_flag", width: 90,
      render: (v, r) => <Switch checked={v !== "0"} checkedChildren="上传" unCheckedChildren="不上传" size="small" /> },
  ],
  field: [
    { title: "字段英文名", dataIndex: "field_name_en", width: 140 },
    { title: "字段中文名", dataIndex: "field_name_cn", width: 140 },
    { title: "字段类型", dataIndex: "field_type", width: 100 },
  ],
}

// ─── Component ─────────────────────────────────

export default function ResourceUploadV2() {
  const navigate = useNavigate()

  // Cascade state: selected items at each level
  const [selectedPath, setSelectedPath] = useState({
    system: null,
    database: null,
    table: null,
    field: null,
  })
  // Current display level
  const [currentLevel, setCurrentLevel] = useState("system")
  // Options for cascade selects
  const [cascadeOpts, setCascadeOpts] = useState({ system: [], database: [], table: [], field: [] })
  // Table data
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [selectedRowKeys, setSelectedRowKeys] = useState([])
  // Filters
  const [filters, setFilters] = useState({
    sysCode: "", sysName: "", recordName: "", sysStatus: "",
    sysFuncType: "", ifManaged: "", auditStatus: "", uploadStatus: "",
  })
  // Modify modal
  const [modifyVisible, setModifyVisible] = useState(false)
  const [modifyRecord, setModifyRecord] = useState(null)
  const [modifyFields, setModifyFields] = useState({})
  const [modifyReason, setModifyReason] = useState("")
  // Sync warning modal
  const [syncWarnings, setSyncWarnings] = useState([])
  const [syncVisible, setSyncVisible] = useState(false)
  const [pendingSync, setPendingSync] = useState(null)
  // Deadline
  const [deadlineDays, setDeadlineDays] = useState(0)
  // Bill month
  const [billMonth, setBillMonth] = useState("")
  // View mode: mid / result-mid / group-result
  const [viewMode, setViewMode] = useState("mid")
  // Merge suggestions
  const [mergeSuggestions, setMergeSuggestions] = useState([])
  const [mergeVisible, setMergeVisible] = useState(false)
  const [pendingMerge, setPendingMerge] = useState(null)
  // Exclude modal
  const [excludeVisible, setExcludeVisible] = useState(false)
  const [excludeRecord, setExcludeRecord] = useState(null)
  const [excludeReason, setExcludeReason] = useState("")

  useEffect(() => {
    const today = dayjs()
    setDeadlineDays(25 - today.date())
    // 计算当前账期
    const d = today.date()
    let bm = ""
    if (d >= 26) {
      bm = today.add(1, "month").format("YYYYMM")
    } else {
      bm = today.format("YYYYMM")
    }
    setBillMonth(bm)
  }, [])

  // Walk up cascade to find nearest ancestor filter for current tab
  const getParentFilter = useCallback(() => {
    const idx = LEVELS.indexOf(currentLevel)
    if (idx <= 0) return null
    for (let i = idx - 1; i >= 0; i--) {
      const ancestor = selectedPath[LEVELS[i]]
      if (ancestor?.localBizId) {
        return { level: LEVELS[i], localBizId: ancestor.localBizId }
      }
    }
    return null
  }, [currentLevel, selectedPath])

  // Generate display title for current level
  const getLevelTitle = useCallback(() => {
    const parts = [LEVEL_LABELS[currentLevel]]
    const parentInfo = PARENT_LABEL_MAP[currentLevel]
    if (parentInfo) {
      const parentLevel = LEVELS[LEVELS.indexOf(currentLevel) - 1]
      const parent = selectedPath[parentLevel]
      if (parent) {
        parts.unshift(parent[parentInfo.nameKey] || "")
      }
    }
    return parts.join(" - ")
  }, [currentLevel, selectedPath])

  // Fetch cascade options for a specific level
  const loadOptions = useCallback(async (level) => {
    if (level === "system") {
      const opts = await fetchOptions("system")
      setCascadeOpts((prev) => ({ ...prev, system: opts }))
      return
    }
    const idx = LEVELS.indexOf(level)
    if (idx <= 0) return
    const parentLevel = LEVELS[idx - 1]
    const parent = selectedPath[parentLevel]
    if (!parent) {
      setCascadeOpts((prev) => ({ ...prev, [level]: [] }))
      return
    }
    const opts = await fetchOptions(level, parent.localBizId)
    setCascadeOpts((prev) => ({ ...prev, [level]: opts }))
  }, [selectedPath])

  // Fetch table data for current level with parent filter
  const fetchData = useCallback(async (page, size) => {
    const p = page || pagination.current
    const s = size || pagination.pageSize
    setLoading(true)
    try {
      const parentFilter = getParentFilter()
      const parentId = parentFilter?.localBizId || null
      const extra = {}
      if (parentFilter && parentFilter.level !== LEVELS[LEVELS.indexOf(currentLevel) - 1]) {
        // Indirect parent — pass parent_level hint for backend cascade filtering
        extra.parent_level = parentFilter.level
      }
      if (filters.auditStatus) extra.audit_status = filters.auditStatus
      if (filters.uploadStatus) extra.upload_status = filters.uploadStatus
      const result = await fetchMidList(currentLevel, parentId, extra, p, s)
      setData(result.list || [])
      setPagination({ current: result.page, pageSize: result.size, total: result.total })
    } finally {
      setLoading(false)
    }
  }, [currentLevel, getParentFilter, filters, pagination.current, pagination.pageSize])

  // Load options for current level and its next level
  useEffect(() => {
    const idx = LEVELS.indexOf(currentLevel)
    // Load current level options (for cascade)
    loadOptions(currentLevel)
    // Also load next level if current has a parent selected
    if (idx > 0 && idx < LEVELS.length - 1) {
      const nextLevel = LEVELS[idx + 1]
      loadOptions(nextLevel)
    }
  }, [currentLevel, loadOptions])

  // Fetch table data when level or parent changes
  useEffect(() => {
    fetchData(1)
  }, [currentLevel, selectedPath.system, selectedPath.database, selectedPath.table])

  // Handle cascade select change — only updates filter selections, does NOT switch tab
  const handleCascadeChange = (level, value) => {
    if (!value) {
      const cleared = {}
      const idx = LEVELS.indexOf(level)
      for (let i = idx; i < LEVELS.length; i++) {
        cleared[LEVELS[i]] = null
      }
      setSelectedPath((prev) => ({ ...prev, ...cleared }))
      return
    }
    const newSelected = { ...selectedPath }
    newSelected[level] = value
    const idx = LEVELS.indexOf(level)
    for (let i = idx + 1; i < LEVELS.length; i++) {
      newSelected[LEVELS[i]] = null
    }
    setSelectedPath(newSelected)
  }

  // Breadcrumb navigation — clicking resets cascade to that level
  const getBreadcrumbItems = () => {
    const items = [{ title: <a onClick={() => { setSelectedPath({ system: null, database: null, table: null, field: null }); setCurrentLevel("system") }}>系统列表</a> }]
    for (const level of LEVELS) {
      const item = selectedPath[level]
      if (!item) break
      const idx = LEVELS.indexOf(level)
      const label = item[{
        system: "sysName",
        database: "dbName",
        table: "tableName",
        field: "fieldNameCn",
      }[level]] || level
      if (idx < LEVELS.length - 1 && selectedPath[LEVELS[idx + 1]]) {
        items.push({ title: <a onClick={() => { setCurrentLevel(LEVELS[idx + 1]) }}>{label}</a> })
      } else {
        items.push({ title: label })
      }
    }
    return items
  }

  // Handle merge action
  const handleMerge = async (sourceIds, targetId) => {
    try {
      const res = await api.post("/upload/merge-records", {
        asset_type: currentLevel,
        source_ids: sourceIds,
        target_id: targetId,
        bill_month: billMonth,
      })
      if (res.code === "000000") {
        message.success("合并成功")
        setMergeVisible(false)
        setMergeSuggestions([])
        fetchData()
      }
    } catch { message.error("合并失败") }
  }

  // Handle exclude toggle
  const handleExcludeToggle = (record, checked) => {
    setExcludeRecord(record)
    setExcludeReason("")
    setExcludeVisible(true)
  }

  const handleExcludeConfirm = async () => {
    try {
      const res = await api.post("/upload/mark-exclude", {
        asset_type: currentLevel,
        asset_id: excludeRecord.local_biz_id,
        exclude_flag: true,
        reason: excludeReason,
      })
      if (res.code === "000000") {
        message.success("已标记不上传")
        setExcludeVisible(false)
        fetchData()
      }
    } catch { message.error("操作失败") }
  }

  const handleRestoreUpload = async (record) => {
    try {
      const res = await api.post("/upload/mark-exclude", {
        asset_type: currentLevel,
        asset_id: record.local_biz_id,
        exclude_flag: false,
      })
      if (res.code === "000000") {
        message.success("已恢复上传")
        fetchData()
      }
    } catch { message.error("操作失败") }
  }

  // Row drill-down
  const handleRowClick = (record) => {
    const idx = LEVELS.indexOf(currentLevel)
    if (idx >= LEVELS.length - 1) return
    const nextLevel = LEVELS[idx + 1]
    const value = { localBizId: record.local_biz_id }
    // Populate display name for the cascade
    const nameMap = {
      system: { key: "sysName", val: record.sys_name },
      database: { key: "dbName", val: record.db_name },
      table: { key: "tableName", val: record.table_name || record.table_name_en },
      field: { key: "fieldNameCn", val: record.field_name_cn || record.field_name_en },
    }
    const m = nameMap[currentLevel]
    if (m) value[m.key] = m.val
    const newSelected = { ...selectedPath }
    newSelected[currentLevel] = value
    for (let i = idx + 1; i < LEVELS.length; i++) {
      newSelected[LEVELS[i]] = null
    }
    setSelectedPath(newSelected)
    setCurrentLevel(nextLevel)
    setSelectedRowKeys([])
  }

  // ─── API Actions ──────────────────────────────

  const handleSync = async (scopeType, scopeIds) => {
    try {
      const payload = { asset_type: currentLevel, scope_type: scopeType, overwrite_empty: false }
      if (scopeIds) payload.scope_ids = scopeIds
      const res = await api.post("/upload/sync-to-mid", payload)
      if (res.code === "000000") {
        if (res.data.emptyOverwriteWarnings?.length > 0) {
          setSyncWarnings(res.data.emptyOverwriteWarnings)
          setPendingSync(payload)
          setSyncVisible(true)
        } else {
          message.success(`同步完成: ${res.data.syncCount}条`)
          fetchData()
        }
      }
    } catch { message.error("同步失败") }
  }

  const handleSyncConfirm = async (overwrite) => {
    pendingSync.overwrite_empty = overwrite
    const res = await api.post("/upload/sync-to-mid", pendingSync)
    if (res.code === "000000") message.success(`同步完成: ${res.data.syncCount}条`)
    setSyncVisible(false)
    setSyncWarnings([])
    setPendingSync(null)
    fetchData()
  }

  const handleAudit = async (scopeType, scopeIds) => {
    try {
      const payload = { asset_type: currentLevel, scope_type: scopeType }
      if (scopeIds) payload.scope_ids = scopeIds
      const res = await api.post("/upload/audit", payload)
      if (res.code === "000000") {
        message.success(`稽核完成: 通过${res.data.passCount}条, 不通过${res.data.failCount}条`)
        fetchData()
      }
    } catch { message.error("稽核失败") }
  }

  const handleSyncToResult = async (scopeType, scopeIds) => {
    try {
      const payload = { asset_type: currentLevel, scope_type: scopeType }
      if (scopeIds) payload.scope_ids = scopeIds
      const res = await api.post("/upload/sync-to-result", payload)
      if (res.code === "000000") {
        message.success(`同步到结果表: ${res.data.syncCount}条`)
        fetchData()
      }
    } catch { message.error("同步失败") }
  }

  const handleSyncToResultMid = async (scopeType, scopeIds) => {
    try {
      const payload = { asset_type: currentLevel, scope_type: scopeType, bill_month: billMonth }
      if (scopeIds) payload.scope_ids = scopeIds
      const res = await api.post("/upload/sync-to-result-mid", payload)
      if (res.code === "000000") {
        message.success(`同步到中间结果表: ${res.data.syncCount}条`)
        if (res.data.mergeSuggestions?.length > 0) {
          setMergeSuggestions(res.data.mergeSuggestions)
          message.warning(`发现 ${res.data.mergeSuggestions.length} 组合并建议`)
        }
        fetchData()
      }
    } catch { message.error("同步失败") }
  }

  const handleConfirmUpload = async (scopeType, scopeIds) => {
    try {
      const payload = { asset_type: currentLevel, scope_type: scopeType, bill_month: billMonth }
      if (scopeIds) payload.scope_ids = scopeIds
      const res = await api.post("/upload/confirm-upload", payload)
      if (res.code === "000000") {
        message.success(`确认上传: ${res.data.successCount}条`)
        fetchData()
      }
    } catch { message.error("上传失败") }
  }

  const handleUpload = async (scopeType, scopeIds) => {
    try {
      const payload = { asset_type: currentLevel, scope_type: scopeType }
      if (scopeIds) payload.scope_ids = scopeIds
      const res = await api.post("/upload/upload-to-group", payload)
      if (res.code === "000000") {
        message.success(`上传完成: 成功${res.data.successCount}条`)
        fetchData()
      }
    } catch { message.error("上传失败") }
  }

  // ─── Modify Modal ─────────────────────────────

  const openModify = (record) => {
    setModifyRecord(record)
    const initial = {}
    EDITABLE_FIELDS[currentLevel].forEach((f) => { initial[f] = record[f] || "" })
    setModifyFields(initial)
    setModifyReason("")
    setModifyVisible(true)
  }

  const handleModifySave = async (reAudit) => {
    if (!modifyReason.trim()) { message.warning("请填写修改原因"); return }
    const changed = {}
    Object.entries(modifyFields).forEach(([k, v]) => {
      if (v !== (modifyRecord[k] || "")) changed[k] = v
    })
    if (!Object.keys(changed).length) { message.warning("没有修改"); return }
    await api.put("/upload/mid-modify", {
      asset_type: currentLevel,
      local_biz_id: modifyRecord.local_biz_id,
      modify_fields: changed,
      modify_reason: modifyReason,
    })
    message.success("修改成功")
    setModifyVisible(false)
    if (reAudit) await handleAudit("single", [modifyRecord.local_biz_id])
    fetchData()
  }

  // ─── Render helpers ────────────────────────────

  const renderAuditStatus = (v) => {
    const m = { pending: ["default", "待稽核"], pass: ["green", "通过"], fail: ["red", "不通过"] }
    const [color, text] = m[v] || ["default", v]
    return <Tag color={color}>{text}</Tag>
  }

  const renderUploadStatus = (v) => {
    const m = { pending: ["default", "待上传"], synced: ["blue", "已同步"], uploaded: ["green", "已上传"], failed: ["red", "失败"] }
    const [color, text] = m[v] || ["default", v]
    return <Tag color={color}>{text}</Tag>
  }

  const actionButtons = (record) => {
    const as = record.audit_status || "pending"
    const us = record.upload_status || "pending"
    const bid = record.local_biz_id
    const uf = record.upload_flag
    return (
      <Space size="small" wrap>
        {(as === "pending" || as === "fail") && (
          <>
            <Button size="small" icon={<EditOutlined />} onClick={() => openModify(record)}>修改</Button>
            <Button size="small" icon={<SafetyCertificateOutlined />} onClick={() => handleAudit("single", [bid])}>稽核</Button>
          </>
        )}
        {as === "pass" && us === "pending" && uf !== "0" && (
          <Button size="small" icon={<SendOutlined />} onClick={() => handleSyncToResultMid("single", [bid])}>同步结果表</Button>
        )}
        {as === "pass" && uf !== "0" && (
          <Button size="small" type="primary" icon={<CloudUploadOutlined />} onClick={() => handleConfirmUpload("single", [bid])}>上传集团</Button>
        )}
      </Space>
    )
  }

  const renderModifyForm = () => {
    if (!modifyRecord) return null
    const requiredFields = REQUIRED_FIELDS[currentLevel] || []
    const reasons = modifyRecord.non_compliant_reason || ""
    return (
      <div>
        {reasons && (
          <Alert type="error" showIcon icon={<WarningOutlined />}
            message="不合规原因" description={reasons} style={{ marginBottom: 16 }} />
        )}
        <Descriptions bordered column={1} size="small" style={{ marginBottom: 16 }}>
          <Descriptions.Item label="本地标识">{modifyRecord.local_biz_id}</Descriptions.Item>
          <Descriptions.Item label="集团标识">{modifyRecord.group_unique_id || "-"}</Descriptions.Item>
        </Descriptions>
        <Form layout="vertical">
          {EDITABLE_FIELDS[currentLevel].map((f) => (
            <Form.Item key={f} label={f}
              validateStatus={requiredFields.includes(f) && !modifyFields[f] ? "error" : undefined}
              help={requiredFields.includes(f) && !modifyFields[f] ? "必填字段不能为空" : undefined}>
              <TextArea rows={f === "sample_data" ? 4 : 1}
                value={modifyFields[f] || ""}
                onChange={(e) => setModifyFields({ ...modifyFields, [f]: e.target.value })} />
            </Form.Item>
          ))}
          <Form.Item label="修改原因（必填）">
            <TextArea rows={2} value={modifyReason}
              onChange={(e) => setModifyReason(e.target.value)} />
          </Form.Item>
        </Form>
      </div>
    )
  }

  // Compute columns for current level
  const columns = [
    ...(TYPE_COLUMNS[currentLevel] || []),
    { title: "稽核状态", dataIndex: "audit_status", width: 90, render: renderAuditStatus },
    { title: "不合规原因", dataIndex: "non_compliant_reason", width: 200, ellipsis: true,
      render: (v) => v ? <span title={v}>{v.length > 20 ? v.slice(0, 20) + "..." : v}</span> : "-" },
    { title: "上传状态", dataIndex: "upload_status", width: 90, render: renderUploadStatus },
    { title: "操作", key: "action", width: 260, fixed: "right", render: (_, r) => actionButtons(r) },
  ]

  return (
    <div>
      <h2>资源类集团上报（优化）</h2>

      {deadlineDays >= 0 && deadlineDays <= 5 && (
        <Alert type={deadlineDays <= 3 ? "error" : "warning"} showIcon banner
          message={`距本月集团上报截止日期（25日）还有 ${deadlineDays} 天`}
          description="请及时完成盘点范围内的库表上传。"
          style={{ marginBottom: 16 }} />
      )}
      {/* 级联选择栏 */}
      <div style={{ marginBottom: 12, padding: 16, background: "#fafafa", borderRadius: 4, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ fontWeight: "bold", whiteSpace: "nowrap" }}>级联筛选：</span>
        <Select placeholder="选择系统" allowClear showSearch style={{ width: 200 }}
          value={selectedPath.system}
          onChange={(v, opt) => handleCascadeChange("system", opt)}
          filterOption={(input, option) => option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0}>
          {cascadeOpts.system.map((o) => (
            <Option key={o.localBizId} value={o.localBizId} localBizId={o.localBizId} sysName={o.sysName} sysCode={o.sysCode}>
              {o.sysName || o.sysCode}
            </Option>
          ))}
        </Select>
        <Select placeholder="选择数据库" allowClear showSearch style={{ width: 200 }}
          value={selectedPath.database} disabled={!selectedPath.system}
          onChange={(v, opt) => handleCascadeChange("database", opt)}
          filterOption={(input, option) => option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0}>
          {cascadeOpts.database.map((o) => (
            <Option key={o.localBizId} value={o.localBizId} localBizId={o.localBizId} dbName={o.dbName}>{o.dbName}</Option>
          ))}
        </Select>
        <Select placeholder="选择表" allowClear showSearch style={{ width: 200 }}
          value={selectedPath.table} disabled={!selectedPath.database}
          onChange={(v, opt) => handleCascadeChange("table", opt)}
          filterOption={(input, option) => option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0}>
          {cascadeOpts.table.map((o) => (
            <Option key={o.localBizId} value={o.localBizId} localBizId={o.localBizId} tableName={o.tableName || o.tableNameEn}>
              {o.tableName || o.tableNameEn}
            </Option>
          ))}
        </Select>
        <Select placeholder="选择字段" allowClear showSearch style={{ width: 200 }}
          value={selectedPath.field} disabled={!selectedPath.table}
          onChange={(v, opt) => handleCascadeChange("field", opt)}
          filterOption={(input, option) => option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0}>
          {cascadeOpts.field.map((o) => (
            <Option key={o.localBizId} value={o.localBizId} localBizId={o.localBizId} fieldNameCn={o.fieldNameCn}>
              {o.fieldNameCn || o.fieldNameEn}
            </Option>
          ))}
        </Select>
      </div>

      {/* 面包屑导航 */}
      <div style={{ marginBottom: 12 }}>
        <Breadcrumb items={getBreadcrumbItems()} />
      </div>

      {/* 账期显示 */}
      <Descriptions size="small" style={{ marginBottom: 8 }}>
        <Descriptions.Item label="当前账期">{billMonth}</Descriptions.Item>
        <Descriptions.Item label="账期周期">上月26日 - 本月25日</Descriptions.Item>
      </Descriptions>

      {/* 合并建议通知 */}
      {mergeSuggestions.length > 0 && (
        <Alert type="warning" showIcon icon={<MergeCellsOutlined />} banner
          message={`发现 ${mergeSuggestions.length} 组定级备案名称重复的系统记录`}
          description="请查看合并建议，确认是否需要合并后再上传集团。"
          action={<Button size="small" onClick={() => setMergeVisible(true)}>查看合并建议</Button>}
          style={{ marginBottom: 12 }} closable onClose={() => setMergeSuggestions([])} />
      )}

      {/* 操作按钮 */}
      <div style={{ marginBottom: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Button icon={<SyncOutlined />} onClick={() => handleSync("all")}>同步到中间表</Button>
        <Button icon={<SafetyCertificateOutlined />} onClick={() => handleAudit("all")}>触发稽核</Button>
        <Button icon={<SendOutlined />} onClick={() => handleSyncToResultMid("all")}>同步到中间结果表</Button>
        <Button type="primary" icon={<CloudUploadOutlined />} onClick={() => handleConfirmUpload("all")}>确认上传集团</Button>
        <Button icon={<HistoryOutlined />} onClick={() => navigate("/upload/modify-log")}>修改记录</Button>
        <Button icon={<HistoryOutlined />} onClick={() => navigate("/upload/upload-log")}>上传记录</Button>
        <Button icon={<StopOutlined />} onClick={() => navigate("/upload/exclude-marks")}>排除标记</Button>
        <Button icon={<MergeCellsOutlined />} onClick={() => navigate("/upload/merge-logs")}>合并日志</Button>
      </div>

      {/* 视图切换 */}
      <Tabs activeKey={viewMode} onChange={setViewMode} style={{ marginBottom: 8 }}
        items={[
          { key: "mid", label: "中间表" },
          { key: "result-mid", label: "中间结果表（带账期）" },
          { key: "group-result", label: "集团结果表（全量）" },
        ]} />

      {/* 层级页签 — 让用户手动切换查看系统/数据库/表/字段 */}
      <Tabs activeKey={currentLevel} onChange={setCurrentLevel}
        style={{ marginBottom: 8 }}
        items={LEVELS.map(t => ({ key: t, label: LEVEL_LABELS[t] }))} />

      {/* 当前层级标题 */}
      <div style={{ marginBottom: 8, color: "#666" }}>
        {getLevelTitle()}（共 {pagination.total} 条）
      </div>

      {/* 数据表格 */}
      <Table
        rowKey="local_biz_id"
        rowSelection={{ selectedRowKeys, onChange: setSelectedRowKeys }}
        columns={columns} dataSource={data} loading={loading} size="small"
        pagination={{ ...pagination, showSizeChanger: true, onChange: (p, s) => fetchData(p, s) }}
        scroll={{ x: 1200 }}
        onRow={(record) => ({
          style: { cursor: LEVELS.indexOf(currentLevel) < LEVELS.length - 1 ? "pointer" : "default" },
          onDoubleClick: () => handleRowClick(record),
        })}
      />

      {/* 修改弹窗 */}
      <Modal title={`修改 - 中间表`} open={modifyVisible}
        onCancel={() => setModifyVisible(false)} width={640}
        footer={
          <Space>
            <Button onClick={() => setModifyVisible(false)}>取消</Button>
            <Button onClick={() => handleModifySave(false)}>保存</Button>
            <Button type="primary" onClick={() => handleModifySave(true)}>保存并重新稽核</Button>
          </Space>
        }>
        {renderModifyForm()}
      </Modal>

      {/* 合并建议对话框 */}
      <Modal title={<><MergeCellsOutlined style={{ color: "#faad14" }} /> 合并建议</>}
        open={mergeVisible}
        onCancel={() => { setMergeVisible(false); setMergeSuggestions([]) }} width={600}
        footer={null}>
        {mergeSuggestions.map((sg, idx) => (
          <div key={idx} style={{ marginBottom: 16, padding: 12, background: "#fafafa", borderRadius: 4 }}>
            <p><strong>定级备案名称：</strong>{sg.recordName}</p>
            <p><strong>重复记录数：</strong>{sg.count} 条</p>
            <p><strong>记录标识：</strong>{sg.ids.join(", ")}</p>
            <Space>
              <Button type="primary" size="small" onClick={() => handleMerge(sg.ids.slice(1), sg.ids[0])}>
                合并到第一条记录
              </Button>
              <Button size="small" onClick={() => setMergeSuggestions(mergeSuggestions.filter((_, i) => i !== idx))}>
                忽略
              </Button>
            </Space>
          </div>
        ))}
        {mergeSuggestions.length === 0 && <p>暂无可合并的记录</p>}
      </Modal>

      {/* 排除上传原因对话框 */}
      <Modal title="标记不上传" open={excludeVisible}
        onCancel={() => setExcludeVisible(false)}
        onOk={handleExcludeConfirm}
        okText="确认标记" okButtonProps={{ danger: true }}>
        <p>确定标记以下记录不上传？</p>
        {excludeRecord && (
          <Descriptions size="small" column={1}>
            <Descriptions.Item label="标识">{excludeRecord.local_biz_id}</Descriptions.Item>
            <Descriptions.Item label="名称">{excludeRecord.db_name || excludeRecord.table_name || excludeRecord.table_name_en}</Descriptions.Item>
          </Descriptions>
        )}
        <div style={{ marginTop: 12 }}>
          <p>排除原因（选填）：</p>
          <TextArea rows={2} value={excludeReason} onChange={(e) => setExcludeReason(e.target.value)} />
        </div>
      </Modal>

      {/* 同步空值覆盖警告 */}
      <Modal title={<><WarningOutlined style={{ color: "#faad14" }} /> 发现空值覆盖风险</>}
        open={syncVisible}
        onCancel={() => { setSyncVisible(false); setSyncWarnings([]) }} width={600}
        footer={
          <Space>
            <Button onClick={() => { setSyncVisible(false); setSyncWarnings([]) }}>取消同步</Button>
            <Button onClick={() => handleSyncConfirm(false)}>跳过空值，保留中间表现有值</Button>
            <Button type="primary" danger onClick={() => handleSyncConfirm(true)}>全部覆盖</Button>
          </Space>
        }>
        <p>以下字段在中间表已有值，本次同步源数据为空：</p>
        <Table rowKey={(r) => r.localBizId + r.fieldName}
          dataSource={syncWarnings} size="small" pagination={false}
          columns={[
            { title: "资产标识", dataIndex: "localBizId" },
            { title: "字段名", dataIndex: "fieldName" },
            { title: "中间表当前值", dataIndex: "currentValue" },
            { title: "源数据值", render: () => <Tag color="red">空</Tag> },
          ]} />
      </Modal>
    </div>
  )
}
