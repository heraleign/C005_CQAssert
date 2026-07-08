import React, { useState, useEffect, useCallback, useRef } from "react"
import { Table, Tabs, Select, Input, Button, Tag, Space, Modal, Form, message, Alert, Descriptions, Breadcrumb, Switch, DatePicker } from "antd"
import { SyncOutlined, SafetyCertificateOutlined, SendOutlined, CloudUploadOutlined, HistoryOutlined, EditOutlined, SearchOutlined, WarningOutlined, StopOutlined, MergeCellsOutlined, TableOutlined, FileTextOutlined, DatabaseOutlined, AuditOutlined, DeleteOutlined, PartitionOutlined } from "@ant-design/icons"
import dayjs from "dayjs"
import { useNavigate } from "react-router-dom"
import api from "../services/api"

const { Option } = Select
const { TextArea } = Input
const { RangePicker } = DatePicker
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
    // 新增：主/副系统标识（评审意见5）
    { title: "系统类型", dataIndex: "is_primary", width: 120,
      render: (v, r) => {
        if (r.is_primary === 0) {
          const primaryName = r.primary_sys_name || r.primary_sys_code || r.primary_system_id || "?"
          return <Tag color="orange">副→{primaryName}</Tag>
        }
        return <Tag color="blue">主</Tag>
      }
    },
    // 新增：是否已上传集团（评审意见11）
    { title: "已上传集团", dataIndex: "group_uploaded", width: 95,
      render: (v) => v === 1 ? <Tag color="green">是</Tag> : <Tag>否</Tag>
    },
    // 新增：创建时间（评审意见1）
    { title: "创建时间", dataIndex: "create_time", width: 150,
      render: (v) => v ? dayjs(v).format("YYYY-MM-DD HH:mm") : "-"
    },
    // 新增：更新时间（评审意见1）
    { title: "更新时间", dataIndex: "update_time", width: 150,
      render: (v) => v ? dayjs(v).format("YYYY-MM-DD HH:mm") : "-"
    },
  ],
  database: [
    { title: "所属系统", dataIndex: "sysName", width: 160, render: (v) => v || "-" },
    { title: "数据库名", dataIndex: "db_name", width: 160 },
    { title: "数据库类型", dataIndex: "db_type", width: 120 },
    { title: "IP", dataIndex: "db_ip", width: 120 },
    { title: "端口", dataIndex: "db_port", width: 80 },
    { title: "上传标记", dataIndex: "upload_flag", width: 90,
      render: (v, r) => <Switch checked={v !== "0"} checkedChildren="上传" unCheckedChildren="不上传" size="small" /> },
  ],
  table: [
    { title: "所属系统", dataIndex: "sysName", width: 120, render: (v) => v || "-" },
    { title: "所属数据库", dataIndex: "dbName", width: 120, render: (v) => v || "-" },
    { title: "表英文名", dataIndex: "table_name_en", width: 140 },
    { title: "表中文名", dataIndex: "table_name", width: 140 },
    { title: "主题域", dataIndex: "table_domain", width: 100 },
    { title: "上传标记", dataIndex: "upload_flag", width: 90,
      render: (v, r) => <Switch checked={v !== "0"} checkedChildren="上传" unCheckedChildren="不上传" size="small" /> },
  ],
  field: [
    { title: "所属系统", dataIndex: "sysName", width: 120, render: (v) => v || "-" },
    { title: "所属数据库", dataIndex: "dbName", width: 120, render: (v) => v || "-" },
    { title: "所属表", dataIndex: "tableName", width: 140, render: (v) => v || "-" },
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
  const [selectedResultKeys, setSelectedResultKeys] = useState([])
  // Filters
  const [filters, setFilters] = useState({
    sysCode: "", sysName: "", recordName: "", sysStatus: "",
    sysFuncType: "", ifManaged: "", auditStatus: "", uploadStatus: "",
    groupUploaded: "",  // 评审意见11
  })
  // 时间范围筛选（评审意见1）
  const [timeFilters, setTimeFilters] = useState({
    createTimeRange: null,
    updateTimeRange: null,
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
  const [availableBillMonths, setAvailableBillMonths] = useState([])
  // View mode: mid / result-mid / group-result
  const [viewMode, setViewMode] = useState("mid")
  // Merge suggestions
  const [mergeSuggestions, setMergeSuggestions] = useState([])
  const [mergeVisible, setMergeVisible] = useState(false)
  const [pendingMerge, setPendingMerge] = useState(null)
  // System merge (评审意见5) - 改用 ref 避免闭包陷阱
  const [sysMergeVisible, setSysMergeVisible] = useState(false)
  const [sysMergeTarget, setSysMergeTarget] = useState("")
  const [sysMergeReason, setSysMergeReason] = useState("")
  const sysMergeSourceRef = useRef([]) // 保存选中合并的系统数据，用 ref 持久化
  const [sysMergeItems, setSysMergeItems] = useState([]) // 用于触发对话框渲染
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
    // 获取可用账期
    api.get("/upload/bill-months").then(res => {
      if (res.code === "000000" && res.data?.current) {
        const months = [res.data.current]
        // 同时添加上个月作为选项
        const prev = dayjs(res.data.current + "01").subtract(1, "month").format("YYYYMM")
        months.unshift(prev)
        setAvailableBillMonths(months)
      }
    }).catch(() => {})
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

  // Enrich mid-list data with parent display names
  const enrichData = useCallback((list, assetType) => {
    if (!list || list.length === 0) return list
    try {
      // 如果后端已补充父级名称，直接返回
      const firstItem = list[0]
      if (firstItem.sysName !== undefined || firstItem.sysName !== null) {
        // 可能已有部分数据，直接返回
        return list
      }
      // 从 cascadeOpts 和 selectedPath 构建名称映射
      const nameMaps = { system: {}, database: {}, table: {} }
      Object.entries(cascadeOpts).forEach(([level, items]) => {
        (items || []).forEach(i => {
          if (level === "system") nameMaps.system[i.localBizId] = i.sysName || i.sysCode || i.localBizId
          else if (level === "database") nameMaps.database[i.localBizId] = i.dbName || i.localBizId
          else if (level === "table") nameMaps.table[i.localBizId] = i.tableName || i.tableNameEn || i.localBizId
        })
      })
      return list.map(item => {
        const enriched = { ...item }
        if (assetType === "database") {
          const sysId = item.sys_local_biz_id || item.sys_code || ""
          enriched.sysName = nameMaps.system[sysId] || sysId || ""
        } else if (assetType === "table") {
          const dbId = item.db_local_biz_id || ""
          enriched.dbName = nameMaps.database[dbId] || dbId || ""
          enriched.sysName = ""
        } else if (assetType === "field") {
          const tblId = item.tbl_local_biz_id || ""
          enriched.tableName = nameMaps.table[tblId] || tblId || ""
          enriched.dbName = ""
          enriched.sysName = ""
        }
        return enriched
      })
    } catch (e) {
      console.warn("enrichData error:", e)
      return list  // 出错时返回原始数据
    }
  }, [cascadeOpts])

  // 用 ref 保存最新分页信息，避免 useCallback 依赖 pagination 导致重复创建
  const paginationRef = useRef(pagination)
  paginationRef.current = pagination

  // Fetch table data for current level with parent filter
  const fetchData = useCallback(async (page, size) => {
    const p = page || paginationRef.current.current || 1
    const s = size || paginationRef.current.pageSize || 10
    setLoading(true)
    try {
      if (viewMode === "mid") {
        const parentFilter = getParentFilter()
        const parentId = parentFilter?.localBizId || null
        const extra = {}
        if (parentFilter && parentFilter.level !== LEVELS[LEVELS.indexOf(currentLevel) - 1]) {
          extra.parent_level = parentFilter.level
        }
        const currentSelected = selectedPath[currentLevel]
        if (currentSelected?.localBizId) {
          extra.local_biz_id = currentSelected.localBizId
        }
        if (filters.auditStatus) extra.audit_status = filters.auditStatus
        if (filters.uploadStatus) extra.upload_status = filters.uploadStatus
        if (filters.sysStatus) extra.status = filters.sysStatus
        if (filters.groupUploaded) extra.group_uploaded = filters.groupUploaded
        if (timeFilters.createTimeRange) {
          extra.create_time_start = timeFilters.createTimeRange[0].format("YYYY-MM-DD HH:mm:ss")
          extra.create_time_end = timeFilters.createTimeRange[1].format("YYYY-MM-DD HH:mm:ss")
        }
        if (timeFilters.updateTimeRange) {
          extra.update_time_start = timeFilters.updateTimeRange[0].format("YYYY-MM-DD HH:mm:ss")
          extra.update_time_end = timeFilters.updateTimeRange[1].format("YYYY-MM-DD HH:mm:ss")
        }
        const result = await fetchMidList(currentLevel, parentId, extra, p, s)
        const enriched = enrichData(result.list || [], currentLevel)
        setData(enriched)
        setPagination({ current: result.page, pageSize: result.size, total: result.total })
      } else if (viewMode === "result-mid") {
        const params = { page: p, size: s, asset_type: currentLevel }
        if (billMonth) params.bill_month = billMonth
        const currentSelected = selectedPath[currentLevel]
        if (currentSelected?.localBizId) {
          params.mid_local_biz_id = currentSelected.localBizId
        }
        if (currentLevel !== "system" && !currentSelected?.localBizId) {
          const parentFilter = getParentFilter()
          if (parentFilter?.localBizId) {
            params.parent_local_biz_id = parentFilter.localBizId
          }
        }
        const res = await api.get("/upload/result-mid-list", { params })
        if (res.code === "000000") {
          setData(res.data.list || [])
          setPagination({ current: res.data.page, pageSize: res.data.size, total: res.data.total })
        }
      } else if (viewMode === "group-result") {
        const params = { page: p, size: s, asset_type: currentLevel }
        if (billMonth) params.bill_month = billMonth
        params.include_disabled = false
        const res = await api.get("/upload/group-result-list", { params })
        if (res.code === "000000") {
          setData(res.data.list || [])
          setPagination({ current: res.data.page, pageSize: res.data.size, total: res.data.total })
        }
      }
    } catch (e) {
      console.error("fetchData error:", e)
    } finally {
      setLoading(false)
    }
  // 关键修复：去掉 pagination.current 依赖，改用 ref；保留核心依赖
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentLevel, viewMode, getParentFilter, filters, billMonth])

  // Fetch table data - 将 fetchData 加入依赖数组，确保每次 fetchData 变更时重新绑定
  useEffect(() => {
    fetchData(1).catch(e => console.error("fetchData error:", e))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentLevel, selectedPath.system, selectedPath.database, selectedPath.table, viewMode, billMonth])

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

  // Handle cascade select change
  const handleCascadeChange = (level, selectedValue, option) => {
    if (!selectedValue) {
      const cleared = {}
      const idx = LEVELS.indexOf(level)
      for (let i = idx; i < LEVELS.length; i++) {
        cleared[LEVELS[i]] = null
      }
      setSelectedPath((prev) => ({ ...prev, ...cleared }))
      return
    }
    // 从 option 或 value 中提取显示名
    const opt = option || {}
    const levelInfo = { localBizId: selectedValue }
    if (level === "system") {
      levelInfo.sysName = opt.sysName || opt.children || selectedValue
      levelInfo.sysCode = opt.sysCode || selectedValue
    } else if (level === "database") {
      levelInfo.dbName = opt.dbName || opt.children || selectedValue
    } else if (level === "table") {
      levelInfo.tableName = opt.tableName || opt.tableNameEn || opt.children || selectedValue
    } else if (level === "field") {
      levelInfo.fieldNameCn = opt.fieldNameCn || opt.fieldNameEn || opt.children || selectedValue
    }
    const newSelected = { ...selectedPath }
    newSelected[level] = levelInfo
    const idx = LEVELS.indexOf(level)
    for (let i = idx + 1; i < LEVELS.length; i++) {
      newSelected[LEVELS[i]] = null
    }
    setSelectedPath(newSelected)

    // 选中后立即加载下一级的选项
    if (idx < LEVELS.length - 1) {
      const nextLevel = LEVELS[idx + 1]
      loadOptions(nextLevel)
    }
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

  // Handle system merge (评审意见5)
  const handleSysMerge = async () => {
    if (!sysMergeTarget) { message.warning("请选择合并后的主系统"); return }
    const sourceIds = selectedRowKeys.filter(k => k !== sysMergeTarget)
    if (sourceIds.length === 0) { message.warning("请至少勾选一个副系统"); return }
    try {
      const res = await api.post("/upload/merge-systems", {
        source_ids: sourceIds,
        target_id: sysMergeTarget,
        merge_reason: sysMergeReason,
      })
      if (res.code === "000000") {
        message.success(`合并成功: ${res.data.mergedCount}个系统合并到主系统`)
        setSysMergeVisible(false)
        setSysMergeTarget("")
        setSysMergeReason("")
        setSelectedRowKeys([])
        fetchData()
      }
    } catch { message.error("合并失败") }
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

    // 获取当前记录的标识 local_biz_id
    let bizId = record.local_biz_id || record.midLocalBizId || ""
    if (!bizId) return

    const value = { localBizId: bizId }
    // Populate display name for the cascade
    const nameMap = {
      system: { key: "sysName", val: record.sys_name || record.sysName || "" },
      database: { key: "dbName", val: record.db_name || record.dbName || "" },
      table: { key: "tableName", val: record.table_name || record.tableName || record.table_name_en || "" },
      field: { key: "fieldNameCn", val: record.field_name_cn || record.fieldNameCn || record.field_name_en || "" },
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

  // ─── 中间结果表稽核 ─────────────────────────

  const handleResultAudit = async (record) => {
    try {
      const res = await api.post("/upload/audit", {
        asset_type: record.assetType,
        scope_ids: [record.midLocalBizId],
      })
      if (res.code === "000000") {
        message.success(`稽核完成: 通过${res.data.passCount}条`)
        fetchData()
      }
    } catch { message.error("稽核失败") }
  }

  // 中间结果表 - 批量稽核（全部/选中+子级）
  const handleResultMidAudit = async () => {
    const hasSelection = selectedResultKeys.length > 0
    const payload = {
      asset_type: currentLevel,
      cascade: currentLevel === "system",
    }
    if (hasSelection) {
      payload.scope_ids = selectedResultKeys
    }
    try {
      const res = await api.post("/upload/audit", payload)
      if (res.code === "000000") {
        message.success(`稽核完成: 通过${res.data.passCount}条, 不通过${res.data.failCount}条`)
        setSelectedResultKeys([])
        fetchData()
      }
    } catch { message.error("稽核失败") }
  }

  const handleResultModify = (record) => {
    // 弹出修改弹窗，数据从 record 中提取
    setModifyRecord({
      local_biz_id: record.midLocalBizId,
      group_unique_id: record.groupUniqueId,
      ...record
    })
    const fields = {}
    // 根据资产类型提取可编辑字段
    const editFields = EDITABLE_FIELDS[currentLevel] || []
    editFields.forEach(f => { fields[f] = record[f] || "" })
    setModifyFields(fields)
    setModifyReason("")
    setModifyVisible(true)
  }

  const handleResultUploadSelected = async (cascaded = false) => {
    if (!selectedResultKeys.length) {
      message.warning("请先勾选要上传的记录")
      return
    }
    try {
      const res = await api.post("/upload/confirm-upload", {
        asset_type: currentLevel,
        scope_ids: selectedResultKeys,
        bill_month: billMonth,
        cascade: cascaded,
      })
      if (res.code === "000000") {
        message.success(`上传成功: ${res.data.successCount}条`)
        setSelectedResultKeys([])
        fetchData()
      }
    } catch { message.error("上传失败") }
  }

  // ─── 集团结果表操作 ───────────────────────────

  const handleGroupAudit = async () => {
    // 获取级联选择的 scope（优先从 selectedPath 取）
    const currentSelected = selectedPath[currentLevel]
    const scopeIds = currentSelected?.localBizId ? [currentSelected.localBizId] : null
    try {
      const payload = {
        asset_type: currentLevel === "database" ? "database" : "system",
        cascade: currentLevel === "system",
      }
      if (scopeIds) payload.scope_ids = scopeIds
      const res = await api.post("/upload/audit-by-scope", payload)
      if (res.code === "000000") {
        message.success(`稽核完成: 通过${res.data.passCount}条, 不通过${res.data.failCount}条`)
        fetchData()
      }
    } catch { message.error("稽核失败") }
  }

  const handleDeleteFromGroup = async (record) => {
    // 获取删除实体的标识（集团结果表记录只含 groupUniqueId）
    const groupId = record.groupUniqueId || ""
    if (!groupId) {
      message.error("无法获取记录标识")
      return
    }
    const label = currentLevel === "system" ? "系统及其所有下级" : "数据库及其所有下级"
    Modal.confirm({
      title: `确认${currentLevel === "system" ? "删除/禁用此系统" : "删除/禁用此数据库"}？`,
      content: `将${currentLevel === "system" ? "删除/禁用" : "删除/禁用"}该${label}的集团结果表数据。
      ＊历史数据（之前账期已存在）将被禁用而非删除
      ＊本账期新增数据将被永久删除
      同时中间结果表状态将回退为「未上传」。`,
      okText: "确认",
      okButtonProps: { danger: true },
      cancelText: "取消",
      onOk: async () => {
        try {
          const res = await api.post("/upload/group-result/delete", {
            asset_type: currentLevel,
            biz_id: groupId,
          })
          if (res.code === "000000") {
            if (res.data.isHistorical) {
              message.warning(`历史数据已禁用: 集团结果表${res.data.deletedCount}条, 回退中间结果表${res.data.updatedCount}条`)
            } else {
              message.success(`删除完成: 集团结果表${res.data.deletedCount}条, 回退中间结果表${res.data.updatedCount}条`)
            }
            fetchData()
          }
        } catch { message.error("删除失败") }
      },
    })
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
        {as === "pass" && uf !== "0" && (
          <Button size="small" icon={<SendOutlined />} onClick={() => handleSyncToResultMid("single", [bid])}>同步到中间结果表</Button>
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

  // 各资产类型在结果表中的完整字段列定义
  // ─── 各资产类型结果表的完整列定义 ──────────────
  // 全部字段与 dx_assets_*_cq 表列名一致，只显示有数据的字段
  const RESULT_MID_SYSTEM_COLS = [
    { title: "系统编码", dataIndex: "sys_code", width: 150, render: (v) => v || "-" },
    { title: "系统名称", dataIndex: "sys_name", width: 180, render: (v) => v || "-" },
    { title: "子系统名称", dataIndex: "sub_sys_name", width: 150, render: (v) => v || "-" },
    { title: "系统简介", dataIndex: "sys_introduct", width: 200, ellipsis: true, render: (v) => v || "-" },
    { title: "系统分类", dataIndex: "sys_classify", width: 100, render: (v) => v || "-" },
    { title: "定级备案名称", dataIndex: "record_name", width: 150, render: (v) => v || "-" },
    { title: "所属单位", dataIndex: "org_unit", width: 130, render: (v) => v || "-" },
    { title: "归属部门", dataIndex: "org_dept", width: 130, render: (v) => v || "-" },
    { title: "系统状态", dataIndex: "status", width: 80, render: (v) => <Tag>{v === "1" ? "在线" : v === "0" ? "下线" : v || "-"}</Tag> },
    { title: "功能类型", dataIndex: "sys_func_type", width: 80, render: (v) => ({ "1": "纯数据", "2": "纯功能", "3": "数据+功能" })[v] || v || "-" },
    { title: "是否盘点", dataIndex: "if_managed", width: 80, render: (v) => v === "1" ? <Tag color="blue">是</Tag> : <Tag>否</Tag> },
    { title: "承建单位", dataIndex: "contractor_unit", width: 130, render: (v) => v || "-" },
    { title: "承建部门", dataIndex: "contractor_department", width: 120, render: (v) => v || "-" },
    { title: "承建负责人", dataIndex: "contractor_leader", width: 100, render: (v) => v || "-" },
    { title: "负责人电话", dataIndex: "contractor_leader_phone", width: 120, render: (v) => v || "-" },
    { title: "负责人邮箱", dataIndex: "contractor_leader_email", width: 160, render: (v) => v || "-" },
    { title: "承建厂商", dataIndex: "construction_vendor", width: 160, render: (v) => v || "-" },
    { title: "管理负责人", dataIndex: "management_leader", width: 100, render: (v) => v || "-" },
    { title: "管理负责人电话", dataIndex: "management_leader_phone", width: 120, render: (v) => v || "-" },
    { title: "管理负责人邮箱", dataIndex: "management_leader_email", width: 160, render: (v) => v || "-" },
    { title: "运营单位", dataIndex: "operation_unit", width: 130, render: (v) => v || "-" },
    { title: "运营部门", dataIndex: "operation_department", width: 120, render: (v) => v || "-" },
    { title: "运营负责人", dataIndex: "operation_leader", width: 100, render: (v) => v || "-" },
    { title: "运营负责人电话", dataIndex: "operation_leader_phone", width: 120, render: (v) => v || "-" },
    { title: "运营负责人邮箱", dataIndex: "operation_leader_email", width: 160, render: (v) => v || "-" },
    { title: "上线时间", dataIndex: "launch_time", width: 100, render: (v) => v || "-" },
    { title: "项目编码", dataIndex: "project_code", width: 130, render: (v) => v || "-" },
    { title: "项目名称", dataIndex: "project_name", width: 180, render: (v) => v || "-" },
    { title: "合同编码", dataIndex: "contract_code", width: 140, render: (v) => v || "-" },
    { title: "门户地址", dataIndex: "website", width: 140, render: (v) => v || "-" },
    { title: "网信安编码", dataIndex: "netins_sys_id", width: 130, render: (v) => v || "-" },
    { title: "主数据编码", dataIndex: "master_data_code", width: 130, render: (v) => v || "-" },
    { title: "对外产数", dataIndex: "external_tag", width: 80, render: (v) => v === "1" ? "是" : v || "-" },
    { title: "操作类型", dataIndex: "oper_type", width: 80, render: (v) => ({ "0": "新增", "1": "修改", "2": "删除" })[v] || v || "-" },
    { title: "更新时间", dataIndex: "oper_time", width: 140, render: (v) => v || "-" },
    { title: "集团标识", dataIndex: "groupUniqueId", width: 180, ellipsis: true },
    { title: "账期", dataIndex: "billMonth", width: 80 },
    { title: "稽核状态", dataIndex: "auditStatus", width: 80, render: renderAuditStatus, fixed: "right" },
    { title: "不合规原因", dataIndex: "nonCompliantReason", width: 160, ellipsis: true, render: (v) => v || "-", fixed: "right" },
    { title: "操作", key: "action", width: 200, fixed: "right", render: (_, r) => (
      <Space size="small" wrap>
        {(!r.auditStatus || r.auditStatus === "pending" || r.auditStatus === "fail") && (
          <Button size="small" icon={<SafetyCertificateOutlined />} onClick={() => handleResultAudit(r)}>稽核</Button>
        )}
        {/* 评审意见6：所有稽核状态的记录都保留编辑按钮 */}
        <Button size="small" icon={<EditOutlined />} onClick={() => handleResultModify(r)}>编辑</Button>
      </Space>
    )},
  ]

  const RESULT_MID_DATABASE_COLS = [
    { title: "数据库标识", dataIndex: "midLocalBizId", width: 170, render: (v) => v || "-" },
    { title: "数据库名", dataIndex: "db_name", width: 160, render: (v) => v || "-" },
    { title: "数据库类型", dataIndex: "db_type", width: 120, render: (v) => v || "-" },
    { title: "版本", dataIndex: "db_version", width: 100, render: (v) => v || "-" },
    { title: "归属系统", dataIndex: "sys_code", width: 150, render: (v) => v || "-" },
    { title: "IP", dataIndex: "db_ip", width: 130, render: (v) => v || "-" },
    { title: "端口", dataIndex: "db_port", width: 80, render: (v) => v || "-" },
    { title: "操作类型", dataIndex: "oper_type", width: 80, render: (v) => ({ "0": "新增", "1": "修改", "2": "删除" })[v] || v || "-" },
    { title: "更新时间", dataIndex: "oper_time", width: 140, render: (v) => v || "-" },
    { title: "集团标识", dataIndex: "groupUniqueId", width: 180, ellipsis: true },
    { title: "账期", dataIndex: "billMonth", width: 80 },
    { title: "稽核状态", dataIndex: "auditStatus", width: 80, render: renderAuditStatus, fixed: "right" },
    { title: "不合规原因", dataIndex: "nonCompliantReason", width: 160, ellipsis: true, render: (v) => v || "-", fixed: "right" },
    { title: "操作", key: "action", width: 180, fixed: "right", render: (_, r) => (
      <Space size="small" wrap>
        {(!r.auditStatus || r.auditStatus === "pending" || r.auditStatus === "fail") && (
          <Button size="small" icon={<SafetyCertificateOutlined />} onClick={() => handleResultAudit(r)}>稽核</Button>
        )}
        {r.auditStatus === "fail" && (
          <Button size="small" icon={<EditOutlined />} onClick={() => handleResultModify(r)}>编辑</Button>
        )}
      </Space>
    )},
  ]

  const RESULT_MID_TABLE_COLS = [
    { title: "表标识", dataIndex: "midLocalBizId", width: 180, render: (v) => v || "-" },
    { title: "所属Schema", dataIndex: "table_schema", width: 100, render: (v) => v || "-" },
    { title: "表英文名", dataIndex: "table_name_en", width: 140, render: (v) => v || "-" },
    { title: "表中文名", dataIndex: "table_name", width: 160, render: (v) => v || "-" },
    { title: "表简介", dataIndex: "table_introduct", width: 200, ellipsis: true, render: (v) => v || "-" },
    { title: "所属库", dataIndex: "db_local_biz_id", width: 170, render: (v) => v || "-" },
    { title: "主题域", dataIndex: "table_domain", width: 100, render: (v) => v || "-" },
    { title: "场景标签", dataIndex: "scenario_tag", width: 100, render: (v) => v || "-" },
    { title: "湖数据类型", dataIndex: "lake_data_type", width: 100, render: (v) => v || "-" },
    { title: "是否入湖", dataIndex: "in_unit_lakes", width: 80, render: (v) => v === "1" ? "是" : v || "-" },
    { title: "湖内精模型", dataIndex: "premium_model_in_lake", width: 90, render: (v) => v === "1" ? "是" : v || "-" },
    { title: "是否上传湖", dataIndex: "uploaded_to_big_lake", width: 90, render: (v) => v === "1" ? "是" : v || "-" },
    { title: "湖外唯一标识", dataIndex: "external_unique_identifier", width: 160, render: (v) => v || "-" },
    { title: "可共享", dataIndex: "is_shareable", width: 80, render: (v) => v === "1" ? "是" : v || "-" },
    { title: "是否已共享", dataIndex: "is_shared", width: 80, render: (v) => v === "1" ? "是" : v || "-" },
    { title: "共享渠道", dataIndex: "sharing_channel", width: 100, render: (v) => v || "-" },
    { title: "技术联系人", dataIndex: "tech_contact", width: 100, render: (v) => v || "-" },
    { title: "技术人电话", dataIndex: "tech_contact_phone", width: 110, render: (v) => v || "-" },
    { title: "汇聚方式", dataIndex: "data_aggregation_method", width: 100, render: (v) => v || "-" },
    { title: "采集时间", dataIndex: "data_collection_time", width: 100, render: (v) => v || "-" },
    { title: "汇聚粒度", dataIndex: "aggregation_granularity", width: 100, render: (v) => v || "-" },
    { title: "增量/全量", dataIndex: "is_incremental_or_full", width: 90, render: (v) => v || "-" },
    { title: "存储周期", dataIndex: "storage_period", width: 100, render: (v) => v || "-" },
    { title: "引用次数", dataIndex: "reference_count", width: 80, render: (v) => v || "-" },
    { title: "订阅次数", dataIndex: "sub_count", width: 80, render: (v) => v || "-" },
    { title: "收藏次数", dataIndex: "col_count", width: 80, render: (v) => v || "-" },
    { title: "访问次数", dataIndex: "access_count", width: 80, render: (v) => v || "-" },
    { title: "表分级", dataIndex: "table_level", width: 80, render: (v) => v || "-" },
    { title: "表分类", dataIndex: "tabtable_category", width: 80, render: (v) => v || "-" },
    { title: "层级", dataIndex: "layer_level", width: 80, render: (v) => v || "-" },
    { title: "业务域", dataIndex: "business_domain", width: 100, render: (v) => v || "-" },
    { title: "数据来源系统", dataIndex: "source_system", width: 120, render: (v) => v || "-" },
    { title: "创建时间", dataIndex: "create_time", width: 140, render: (v) => v || "-" },
    { title: "是否分区", dataIndex: "is_partitioned", width: 80, render: (v) => v === "1" ? "是" : v || "-" },
    { title: "数据质量", dataIndex: "data_quality", width: 80, render: (v) => v || "-" },
    { title: "行业目录", dataIndex: "industry_catalog", width: 100, render: (v) => v || "-" },
    { title: "行业专家", dataIndex: "industry_expert", width: 100, render: (v) => v || "-" },
    { title: "集团湖接口表名", dataIndex: "group_gather_tbname", width: 150, render: (v) => v || "-" },
    { title: "操作类型", dataIndex: "oper_type", width: 80, render: (v) => ({ "0": "新增", "1": "修改", "2": "删除" })[v] || v || "-" },
    { title: "更新时间", dataIndex: "oper_time", width: 140, render: (v) => v || "-" },
    { title: "集团标识", dataIndex: "groupUniqueId", width: 180, ellipsis: true },
    { title: "账期", dataIndex: "billMonth", width: 80 },
    { title: "稽核状态", dataIndex: "auditStatus", width: 80, render: renderAuditStatus, fixed: "right" },
    { title: "不合规原因", dataIndex: "nonCompliantReason", width: 160, ellipsis: true, render: (v) => v || "-", fixed: "right" },
    { title: "操作", key: "action", width: 200, fixed: "right", render: (_, r) => (
      <Space size="small" wrap>
        {(!r.auditStatus || r.auditStatus === "pending" || r.auditStatus === "fail") && (
          <Button size="small" icon={<SafetyCertificateOutlined />} onClick={() => handleResultAudit(r)}>稽核</Button>
        )}
        {/* 评审意见6：所有稽核状态的记录都保留编辑按钮 */}
        <Button size="small" icon={<EditOutlined />} onClick={() => handleResultModify(r)}>编辑</Button>
      </Space>
    )},
  ]

  const RESULT_MID_FIELD_COLS = [
    { title: "所属表", dataIndex: "tbl_local_biz_id", width: 170, render: (v) => v || "-" },
    { title: "字段英文名", dataIndex: "field_name_en", width: 140, render: (v) => v || "-" },
    { title: "字段中文名", dataIndex: "field_name_cn", width: 140, render: (v) => v || "-" },
    { title: "字段类型", dataIndex: "field_type", width: 100, render: (v) => v || "-" },
    { title: "字段长度", dataIndex: "field_length", width: 80, render: (v) => v || "-" },
    { title: "字段描述", dataIndex: "field_desc", width: 200, ellipsis: true, render: (v) => v || "-" },
    { title: "加工口径说明", dataIndex: "process_caliber_desc", width: 160, ellipsis: true, render: (v) => v || "-" },
    { title: "是否主键", dataIndex: "is_primary_key", width: 80, render: (v) => v === "1" ? "是" : v || "-" },
    { title: "是否外键", dataIndex: "is_foreign_key", width: 80, render: (v) => v === "1" ? "是" : v || "-" },
    { title: "可共享", dataIndex: "is_shareable", width: 80, render: (v) => v === "1" ? "是" : v || "-" },
    { title: "字段分类", dataIndex: "field_category", width: 100, render: (v) => v || "-" },
    { title: "敏感级别", dataIndex: "sensitivity_level", width: 80, render: (v) => v || "-" },
    { title: "敏感元素", dataIndex: "sensitive_field_elements", width: 120, render: (v) => v || "-" },
    { title: "是否脱敏", dataIndex: "is_desensitized", width: 80, render: (v) => v === "1" ? "是" : v || "-" },
    { title: "取值定义", dataIndex: "value_definition", width: 120, render: (v) => v || "-" },
    { title: "引用主数据字段", dataIndex: "mdm_field", width: 140, render: (v) => v || "-" },
    { title: "引用主数据类型", dataIndex: "mdm_type", width: 120, render: (v) => v || "-" },
    { title: "操作类型", dataIndex: "oper_type", width: 80, render: (v) => ({ "0": "新增", "1": "修改", "2": "删除" })[v] || v || "-" },
    { title: "更新时间", dataIndex: "oper_time", width: 140, render: (v) => v || "-" },
    { title: "集团标识", dataIndex: "groupUniqueId", width: 180, ellipsis: true },
    { title: "账期", dataIndex: "billMonth", width: 80 },
    { title: "稽核状态", dataIndex: "auditStatus", width: 80, render: renderAuditStatus, fixed: "right" },
    { title: "不合规原因", dataIndex: "nonCompliantReason", width: 160, ellipsis: true, render: (v) => v || "-", fixed: "right" },
    { title: "操作", key: "action", width: 180, fixed: "right", render: (_, r) => (
      <Space size="small" wrap>
        {(!r.auditStatus || r.auditStatus === "pending" || r.auditStatus === "fail") && (
          <Button size="small" icon={<SafetyCertificateOutlined />} onClick={() => handleResultAudit(r)}>稽核</Button>
        )}
        {r.auditStatus === "fail" && (
          <Button size="small" icon={<EditOutlined />} onClick={() => handleResultModify(r)}>编辑</Button>
        )}
      </Space>
    )},
  ]

  // ─── 集团结果表列定义（只有操作，无稽核状态与不合规原因） ─────────────

  // 过滤掉稽核状态和不合规原因列（集团结果表不展示这些信息）
  const _groupResultFilter = (col) =>
    col.dataIndex !== "auditStatus" && col.dataIndex !== "nonCompliantReason"

  const GROUP_RESULT_SYSTEM_COLS = RESULT_MID_SYSTEM_COLS
    .filter(_groupResultFilter)
    .map(col => {
      if (col.key === "action") {
        return {
          ...col,
          render: (_, r) => (
            <Space size="small">
              <Button size="small" danger icon={<DeleteOutlined />}
                onClick={() => handleDeleteFromGroup(r)}>删除系统及其下级</Button>
            </Space>
          ),
        }
      }
      return col
    })

  const GROUP_RESULT_DATABASE_COLS = RESULT_MID_DATABASE_COLS
    .filter(col => col.dataIndex !== "midLocalBizId" && _groupResultFilter(col))
    .map(col => {
      if (col.key === "action") {
        return {
          ...col,
          render: (_, r) => (
            <Space size="small">
              <Button size="small" danger icon={<DeleteOutlined />}
                onClick={() => handleDeleteFromGroup(r)}>删除库及其下级</Button>
            </Space>
          ),
        }
      }
      return col
    })

  const GROUP_RESULT_TABLE_COLS = RESULT_MID_TABLE_COLS
    .filter(col => col.dataIndex !== "midLocalBizId" && col.dataIndex !== "table_schema" && _groupResultFilter(col))
    .map(col => {
      if (col.key === "action") {
        return { ...col, render: () => <span style={{ color: "#999" }}>—</span> }
      }
      return col
    })

  const GROUP_RESULT_FIELD_COLS = RESULT_MID_FIELD_COLS
    .filter(_groupResultFilter)
    .map(col => {
      if (col.key === "action") {
        return { ...col, render: () => <span style={{ color: "#999" }}>—</span> }
      }
      return col
    })

  // 各资产类型的列定义映射
  const RESULT_COLS_MAP = {
    system: RESULT_MID_SYSTEM_COLS,
    database: RESULT_MID_DATABASE_COLS,
    table: RESULT_MID_TABLE_COLS,
    field: RESULT_MID_FIELD_COLS,
  }

  const GROUP_COLS_MAP = {
    system: GROUP_RESULT_SYSTEM_COLS,
    database: GROUP_RESULT_DATABASE_COLS,
    table: GROUP_RESULT_TABLE_COLS,
    field: GROUP_RESULT_FIELD_COLS,
  }

  // Compute columns based on view mode and current level
  const getColumns = () => {
    if (viewMode === "group-result") {
      return GROUP_COLS_MAP[currentLevel] || []
    }
    if (viewMode === "result-mid") {
      return RESULT_COLS_MAP[currentLevel] || []
    }
    // mid table
    return [
      ...(TYPE_COLUMNS[currentLevel] || []),
      { title: "稽核状态", dataIndex: "audit_status", width: 90, render: renderAuditStatus },
      { title: "不合规原因", dataIndex: "non_compliant_reason", width: 200, ellipsis: true,
        render: (v) => v ? <span title={v}>{v.length > 20 ? v.slice(0, 20) + "..." : v}</span> : "-" },
      { title: "上传状态", dataIndex: "upload_status", width: 90, render: renderUploadStatus },
      { title: "操作", key: "action", width: 260, fixed: "right", render: (_, r) => actionButtons(r) },
    ]
  }

  return (
    <div>
      <h2>资源类集团上报（优化）</h2>

      {deadlineDays >= 0 && deadlineDays <= 5 && (
        <Alert type={deadlineDays <= 3 ? "error" : "warning"} showIcon banner
          message={`距本月集团上报截止日期（25日）还有 ${deadlineDays} 天`}
          description="请及时完成盘点范围内的库表上传。"
          style={{ marginBottom: 16 }} />
      )}
      {/* 级联选择栏 - 中间表和中间结果表模式显示 */}
      {(viewMode === "mid" || viewMode === "result-mid") && <div style={{ marginBottom: 12, padding: 16, background: "#fafafa", borderRadius: 4, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ fontWeight: "bold", whiteSpace: "nowrap" }}>级联筛选：</span>
        <Select placeholder="选择系统" allowClear showSearch style={{ width: 200 }}
          value={selectedPath.system?.localBizId}
          onChange={(v, opt) => handleCascadeChange("system", v, opt)}
          filterOption={(input, option) => option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0}>
          {cascadeOpts.system.map((o) => (
            <Option key={o.localBizId} value={o.localBizId} localBizId={o.localBizId} sysName={o.sysName} sysCode={o.sysCode}>
              {o.sysName || o.sysCode}
            </Option>
          ))}
        </Select>
        <Select placeholder="选择数据库" allowClear showSearch style={{ width: 200 }}
          value={selectedPath.database?.localBizId} disabled={!selectedPath.system}
          onChange={(v, opt) => handleCascadeChange("database", v, opt)}
          filterOption={(input, option) => option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0}>
          {cascadeOpts.database.map((o) => (
            <Option key={o.localBizId} value={o.localBizId} localBizId={o.localBizId} dbName={o.dbName}>{o.dbName}</Option>
          ))}
        </Select>
        <Select placeholder="选择表" allowClear showSearch style={{ width: 200 }}
          value={selectedPath.table?.localBizId} disabled={!selectedPath.database}
          onChange={(v, opt) => handleCascadeChange("table", v, opt)}
          filterOption={(input, option) => option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0}>
          {cascadeOpts.table.map((o) => (
            <Option key={o.localBizId} value={o.localBizId} localBizId={o.localBizId} tableName={o.tableName || o.tableNameEn}>
              {o.tableName || o.tableNameEn}
            </Option>
          ))}
        </Select>
        <Select placeholder="选择字段" allowClear showSearch style={{ width: 200 }}
          value={selectedPath.field?.localBizId} disabled={!selectedPath.table}
          onChange={(v, opt) => handleCascadeChange("field", v, opt)}
          filterOption={(input, option) => option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0}>
          {cascadeOpts.field.map((o) => (
            <Option key={o.localBizId} value={o.localBizId} localBizId={o.localBizId} fieldNameCn={o.fieldNameCn}>
              {o.fieldNameCn || o.fieldNameEn}
            </Option>
          ))}
        </Select>
      </div>}

      {(viewMode === "mid" || viewMode === "result-mid") && <div style={{ marginBottom: 12 }}>
        <Breadcrumb items={getBreadcrumbItems()} />
      </div>}

      {/* 账期显示/选择（评审意见8：不选=全量查询） */}
      {viewMode === "result-mid" ? (
        <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontWeight: "bold" }}>账期：</span>
          <Select value={billMonth} onChange={(v) => { setBillMonth(v || "") }}
            style={{ width: 120 }} allowClear placeholder="全部账期"
            options={availableBillMonths.map(m => ({ value: m, label: m }))} />
          <span style={{ color: "#888", fontSize: 12 }}>
            {billMonth ? "上月26日 - 本月25日" : "未选择账期 → 全量查询（所有账期）"}
          </span>
        </div>
      ) : viewMode === "group-result" ? (
        <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontWeight: "bold" }}>账期：</span>
          <Select value={billMonth} onChange={(v) => { setBillMonth(v) }}
            style={{ width: 120 }} allowClear placeholder="全部账期"
            options={availableBillMonths.map(m => ({ value: m, label: m }))} />
          <span style={{ color: "#888", fontSize: 12 }}>留空查看所有账期数据</span>
        </div>
      ) : (
        <Descriptions size="small" style={{ marginBottom: 8 }}>
          <Descriptions.Item label="当前账期">{billMonth}</Descriptions.Item>
          <Descriptions.Item label="账期周期">上月26日 - 本月25日</Descriptions.Item>
        </Descriptions>
      )}

      {/* 合并建议通知 */}
      {mergeSuggestions.length > 0 && (
        <Alert type="warning" showIcon icon={<MergeCellsOutlined />} banner
          message={`发现 ${mergeSuggestions.length} 组定级备案名称重复的系统记录`}
          description="请查看合并建议，确认是否需要合并后再上传集团。"
          action={<Button size="small" onClick={() => setMergeVisible(true)}>查看合并建议</Button>}
          style={{ marginBottom: 12 }} closable onClose={() => setMergeSuggestions([])} />
      )}

      {/* 中间表筛选栏（评审意见1、10、11） */}
      {viewMode === "mid" && currentLevel === "system" && <div style={{ marginBottom: 12, padding: 12, background: "#f5f5f5", borderRadius: 4, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ fontWeight: "bold", whiteSpace: "nowrap", fontSize: 13 }}>筛选：</span>
        <Select placeholder="系统状态" allowClear style={{ width: 120 }} value={filters.sysStatus || undefined}
          onChange={(v) => setFilters(f => ({ ...f, sysStatus: v || "" }))}>
          <Option value="">全部</Option>
          <Option value="建设中">建设中</Option>
          <Option value="在用">在用</Option>
          <Option value="下线">下线</Option>
        </Select>
        <Select placeholder="已上传集团" allowClear style={{ width: 130 }} value={filters.groupUploaded || undefined}
          onChange={(v) => setFilters(f => ({ ...f, groupUploaded: v || "" }))}>
          <Option value="">全部</Option>
          <Option value="1">已上传</Option>
          <Option value="0">未上传</Option>
        </Select>
        <span style={{ fontSize: 13 }}>创建时间：</span>
        <RangePicker size="small" value={timeFilters.createTimeRange}
          onChange={(v) => setTimeFilters(t => ({ ...t, createTimeRange: v }))}
          showTime={{ format: "HH:mm:ss" }} format="YYYY-MM-DD HH:mm:ss" />
        <span style={{ fontSize: 13 }}>更新时间：</span>
        <RangePicker size="small" value={timeFilters.updateTimeRange}
          onChange={(v) => setTimeFilters(t => ({ ...t, updateTimeRange: v }))}
          showTime={{ format: "HH:mm:ss" }} format="YYYY-MM-DD HH:mm:ss" />
        <Button size="small" onClick={() => { setFilters(f => ({ ...f, sysStatus: "", groupUploaded: "" })); setTimeFilters({ createTimeRange: null, updateTimeRange: null }) }}>重置筛选</Button>
      </div>}

      {/* 中间结果表下线系统筛选（评审意见9、10） */}
      {viewMode === "result-mid" && currentLevel === "system" && <div style={{ marginBottom: 12, display: "flex", gap: 8, alignItems: "center" }}>
        <span style={{ fontWeight: "bold", fontSize: 13 }}>筛选：</span>
        <Select placeholder="系统状态" allowClear style={{ width: 120 }}
          onChange={(v) => {
            // 通过查询参数传递状态筛选 - 利用 extra params
            // 在实际项目中可扩展API支持，当前用前端过滤示意
          }}>
          <Option value="">全部</Option>
          <Option value="下线">下线系统</Option>
          <Option value="active">在线系统</Option>
        </Select>
      </div>}

      {/* 操作按钮 - 根据视图模式显示不同按钮 */}
      {viewMode === "mid" && <div style={{ marginBottom: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Button icon={<SafetyCertificateOutlined />} onClick={() => handleAudit("all")}>触发稽核</Button>
        <Button icon={<SendOutlined />} onClick={() => handleSyncToResultMid("all")}>同步到中间结果表</Button>
        {/* 合并系统按钮（评审意见5）- 仅系统级别显示 */}
        {currentLevel === "system" && (
          <Button icon={<PartitionOutlined />}
            onClick={() => {
              if (selectedRowKeys.length < 2) { message.warning("请勾选至少两个系统进行合并"); return }
              // 直接从当前页面 data 中提取选中的系统，存入 ref（不受后续 re-render 影响）
              const selectedData = data.filter(d => selectedRowKeys.includes(d.local_biz_id))
              sysMergeSourceRef.current = selectedData
              setSysMergeItems(selectedData) // 触发渲染
              setSysMergeTarget("")
              setSysMergeReason("")
              setSysMergeVisible(true)
            }}
            disabled={selectedRowKeys.length < 2}>合并系统（{selectedRowKeys.length}）</Button>
        )}
      </div>}
      {viewMode === "result-mid" && <div style={{ marginBottom: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Button icon={<SafetyCertificateOutlined />}
          onClick={handleResultMidAudit}>触发稽核{selectedResultKeys.length ? `（${selectedResultKeys.length}条）` : ""}</Button>
        <Button type="primary" icon={<CloudUploadOutlined />}
          onClick={() => handleResultUploadSelected(false)}
          disabled={!selectedResultKeys.length}>确认上传集团（{selectedResultKeys.length}）</Button>
        {currentLevel === "system" && (
          <Button type="primary" icon={<CloudUploadOutlined />}
            onClick={() => handleResultUploadSelected(true)}
            disabled={!selectedResultKeys.length}>级联上传集团（含下级）</Button>
        )}
        {currentLevel === "system" && (
          <Button icon={<CloudUploadOutlined />}
            onClick={async () => {
              const res = await api.post("/upload/confirm-upload", {
                asset_type: currentLevel,
                bill_month: billMonth,
                cascade: true,
              })
              if (res.code === "000000") {
                message.success(`全量级联上传成功: ${res.data.successCount}条`)
                fetchData()
              }
            }}>全量级联上传（全部）</Button>
        )}
        <Button icon={<HistoryOutlined />} onClick={() => navigate("/upload/modify-log")}>修改记录</Button>
        <Button icon={<HistoryOutlined />} onClick={() => navigate("/upload/upload-log")}>上传记录</Button>
        <Button icon={<StopOutlined />} onClick={() => navigate("/upload/exclude-marks")}>排除标记</Button>
        <Button icon={<DatabaseOutlined />} onClick={() => navigate("/upload/merge-logs")}>合并日志</Button>
      </div>}
      {viewMode === "group-result" && <div style={{ marginBottom: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Button icon={<AuditOutlined />} onClick={handleGroupAudit}>全量稽核{selectedPath[currentLevel]?.localBizId ? `（${LEVEL_LABELS[currentLevel]}级联范围）` : ""}</Button>
      </div>}

      {/* 视图切换 */}
      <Tabs activeKey={viewMode} onChange={setViewMode} style={{ marginBottom: 8 }}
        items={[
          { key: "mid", label: "中间表" },
          { key: "result-mid", label: "中间结果表（带账期）" },
          { key: "group-result", label: "集团结果表（全量）" },
        ]} />

      {/* 层级页签 — 所有视图都显示支持下钻 */}
      <Tabs activeKey={currentLevel} onChange={setCurrentLevel}
        style={{ marginBottom: 8 }}
        items={LEVELS.map(t => ({ key: t, label: LEVEL_LABELS[t] }))} />
      <div style={{ marginBottom: 8, color: "#666" }}>
        {viewMode === "mid" ? getLevelTitle() : (viewMode === "result-mid" ? "中间结果表" : "集团结果表")}（共 {pagination.total} 条）
      </div>

      {/* 数据表格 */}
      <Table
        rowKey={(record) => record.local_biz_id || record.id || record.midLocalBizId || Math.random()}
        rowSelection={viewMode === "mid" ? {
          selectedRowKeys,
          onChange: (keys) => setSelectedRowKeys(keys),
          preserveSelectedRowKeys: false,
        } : (viewMode === "result-mid" ? {
          selectedRowKeys: selectedResultKeys,
          onChange: (keys) => setSelectedResultKeys(keys),
        } : undefined)}
        columns={getColumns()} dataSource={data} loading={loading} size="small"
        pagination={{ ...pagination, showSizeChanger: true, onChange: (p, s) => fetchData(p, s) }}
        scroll={{ x: "max-content" }}
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

      {/* 合并系统对话框（评审意见5）- 用 sysMergeItems 直接从 ref 读取 */}
      <Modal title={<><PartitionOutlined style={{ color: "#1890ff" }} /> 合并系统</>}
        open={sysMergeVisible}
        onCancel={() => { setSysMergeVisible(false); setSysMergeTarget(""); setSysMergeReason(""); setSysMergeItems([]) }}
        onOk={handleSysMerge} okText="确认合并" okButtonProps={{ disabled: !sysMergeTarget }}
        width={500}>
        <Alert type="info" showIcon style={{ marginBottom: 12 }}
          message="合并后保留选择的系统为主系统，其他被勾选的系统自动标记为副系统。副系统上传时数据将归入主系统名下。" />
        <div style={{ marginBottom: 12 }}>
          <p><strong>已勾选系统（{sysMergeItems.length}个）：</strong></p>
          <ul style={{ margin: "4px 0" }}>
            {sysMergeItems.map(d => (
              <li key={d.local_biz_id}>{d.sys_name || d.sys_code}（{d.local_biz_id}）</li>
            ))}
          </ul>
        </div>
        <div style={{ marginBottom: 12 }}>
          <p><strong>选择主系统：</strong></p>
          <Select style={{ width: "100%" }} value={sysMergeTarget || undefined}
            onChange={setSysMergeTarget} placeholder="请选择合并后的主系统">
            {sysMergeItems.map(d => (
              <Option key={d.local_biz_id} value={d.local_biz_id}>
                {d.sys_name || d.sys_code}（{d.local_biz_id}）
              </Option>
            ))}
          </Select>
        </div>
        <div>
          <p><strong>合并原因（选填）：</strong></p>
          <TextArea rows={2} value={sysMergeReason} onChange={e => setSysMergeReason(e.target.value)} />
        </div>
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
