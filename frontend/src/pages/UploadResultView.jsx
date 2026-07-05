import React, { useState, useEffect } from "react"
import { Table, Tabs, Select, Input, Button, Tag, Space, message, Descriptions } from "antd"
import { SearchOutlined, ReloadOutlined, CloudUploadOutlined, SafetyCertificateOutlined } from "@ant-design/icons"
import api from "../services/api"

const { Option } = Select

const ASSET_TYPE_LABELS = {
  system: "系统",
  database: "数据库",
  table: "表",
  field: "字段",
}

const STATUS_LABELS = {
  pending: ["default", "待上传"],
  uploaded: ["green", "已上传"],
  failed: ["red", "上传失败"],
}

const RESULT_STATUS_LABELS = {
  pending: ["default", "待审"],
  audited: ["blue", "已审"],
  uploaded: ["green", "已上传"],
  merged: ["orange", "已合并"],
}

export default function UploadResultView() {
  const [viewTab, setViewTab] = useState("result-mid")
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [filters, setFilters] = useState({
    assetType: "",
    uploadStatus: "",
    batchNo: "",
    billMonth: "",
    resultStatus: "",
    groupUniqueId: "",
  })
  const [currentBillMonth, setCurrentBillMonth] = useState("")

  useEffect(() => {
    api.get("/upload/bill-months").then(res => {
      if (res.code === "000000") setCurrentBillMonth(res.data.current)
    }).catch(() => {})
    fetchData()
  }, [])

  const fetchData = async (page = 1, size = 10) => {
    setLoading(true)
    try {
      const params = { page, size }
      if (viewTab === "result-mid") {
        if (filters.assetType) params.asset_type = filters.assetType
        if (filters.billMonth) params.bill_month = filters.billMonth
        if (filters.resultStatus) params.result_status = filters.resultStatus
        if (filters.groupUniqueId) params.group_unique_id = filters.groupUniqueId
        const res = await api.get("/upload/result-mid-list", { params })
        if (res.code === "000000") {
          setData(res.data.list || [])
          setPagination({ current: res.data.page, pageSize: res.data.size, total: res.data.total })
        }
      } else {
        // 集团结果表
        if (filters.assetType) params.asset_type = filters.assetType
        if (filters.groupUniqueId) params.group_unique_id = filters.groupUniqueId
        const res = await api.get("/upload/group-result-list", { params })
        if (res.code === "000000") {
          setData(res.data.list || [])
          setPagination({ current: res.data.page, pageSize: res.data.size, total: res.data.total })
        }
      }
    } catch {
      message.error("加载失败")
    } finally {
      setLoading(false)
    }
  }

  const handleReAudit = async (record) => {
    try {
      const res = await api.post("/upload/audit", {
        asset_type: record.assetType,
        scope_ids: [record.midLocalBizId],
      })
      if (res.code === "000000") {
        message.success("重新稽核完成")
        fetchData()
      }
    } catch {
      message.error("稽核失败")
    }
  }

  const handleConfirmUpload = async (record) => {
    try {
      const res = await api.post("/upload/confirm-upload", {
        asset_type: record.assetType,
        scope_ids: [record.midLocalBizId],
        bill_month: record.billMonth,
      })
      if (res.code === "000000") {
        message.success("确认上传成功")
        fetchData()
      }
    } catch {
      message.error("上传失败")
    }
  }

  const resultMidColumns = [
    { title: "资产类型", dataIndex: "assetType", width: 80,
      render: (v) => ASSET_TYPE_LABELS[v] || v },
    { title: "中间表标识", dataIndex: "midLocalBizId", width: 180, ellipsis: true },
    { title: "集团唯一标识", dataIndex: "groupUniqueId", width: 200, ellipsis: true },
    { title: "账期", dataIndex: "billMonth", width: 80 },
    { title: "结果状态", dataIndex: "resultStatus", width: 80,
      render: (v) => {
        const [color, text] = RESULT_STATUS_LABELS[v] || ["default", v]
        return <Tag color={color}>{text}</Tag>
      },
    },
    { title: "稽核状态", dataIndex: "auditStatus", width: 80,
      render: (v) => {
        const m = { pass: ["green", "通过"], fail: ["red", "不通过"], pending: ["default", "待稽核"] }
        const [color, text] = m[v] || ["default", v]
        return <Tag color={color}>{text}</Tag>
      },
    },
    { title: "同步时间", dataIndex: "syncTime", width: 160 },
    { title: "操作", key: "action", width: 200, render: (_, r) => (
      <Space size="small">
        <Button size="small" icon={<SafetyCertificateOutlined />}
          onClick={() => handleReAudit(r)}>重新稽核</Button>
        <Button size="small" type="primary" icon={<CloudUploadOutlined />}
          disabled={r.auditStatus !== "pass"}
          onClick={() => handleConfirmUpload(r)}>上传集团</Button>
      </Space>
    )},
  ]

  const groupResultColumns = [
    { title: "资产类型", dataIndex: "assetType", width: 80,
      render: (v) => ASSET_TYPE_LABELS[v] || v },
    { title: "集团唯一标识", dataIndex: "groupUniqueId", width: 200, ellipsis: true },
    { title: "操作类型", dataIndex: "operType", width: 80,
      render: (v) => ({ "0": "新增", "1": "修改", "2": "删除" })[v] || v },
    { title: "操作时间", dataIndex: "operTime", width: 160 },
    { title: "同步时间", dataIndex: "syncTime", width: 160 },
  ]

  const columns = viewTab === "result-mid" ? resultMidColumns : groupResultColumns

  return (
    <div>
      <h2>资源类集团上传结果查看</h2>

      {/* 账期显示 */}
      {currentBillMonth && (
        <Descriptions size="small" style={{ marginBottom: 12 }}>
          <Descriptions.Item label="当前账期">{currentBillMonth}</Descriptions.Item>
        </Descriptions>
      )}

      {/* 视图切换 */}
      <Tabs activeKey={viewTab} onChange={(k) => { setViewTab(k); setPagination({ current: 1, pageSize: 10, total: 0 }) }}
        style={{ marginBottom: 8 }}
        items={[
          { key: "result-mid", label: "中间结果表（带账期）" },
          { key: "group-result", label: "集团结果表（全量-只读）" },
        ]} />

      {/* 筛选栏 */}
      <div style={{ marginBottom: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Select placeholder="资产类型" allowClear style={{ width: 130 }}
          onChange={(v) => setFilters({ ...filters, assetType: v || "" })}>
          <Option value="">全部</Option>
          {Object.entries(ASSET_TYPE_LABELS).map(([k, v]) => (
            <Option key={k} value={k}>{v}</Option>
          ))}
        </Select>
        {viewTab === "result-mid" && (
          <>
            <Input placeholder="账期 YYYYMM" allowClear style={{ width: 130 }}
              value={filters.billMonth}
              onChange={(e) => setFilters({ ...filters, billMonth: e.target.value })} />
            <Select placeholder="结果状态" allowClear style={{ width: 120 }}
              onChange={(v) => setFilters({ ...filters, resultStatus: v || "" })}>
              <Option value="">全部</Option>
              <Option value="pending">待审</Option>
              <Option value="audited">已审</Option>
              <Option value="uploaded">已上传</Option>
              <Option value="merged">已合并</Option>
            </Select>
          </>
        )}
        <Input placeholder="集团唯一标识" allowClear style={{ width: 180 }}
          value={filters.groupUniqueId}
          onChange={(e) => setFilters({ ...filters, groupUniqueId: e.target.value })}
          onPressEnter={() => fetchData(1)} />
        <Button icon={<SearchOutlined />} onClick={() => fetchData(1)}>查询</Button>
        <Button icon={<ReloadOutlined />} onClick={() => fetchData()}>刷新</Button>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        size="small"
        pagination={{
          ...pagination,
          showSizeChanger: true,
          onChange: (p, s) => fetchData(p, s),
        }}
        scroll={{ x: 1200 }}
      />
    </div>
  )
}
