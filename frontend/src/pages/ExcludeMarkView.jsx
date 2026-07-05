import React, { useState, useEffect } from "react"
import { Table, Select, Input, Button, Tag, Space, message, Popconfirm } from "antd"
import { SearchOutlined, ReloadOutlined, UndoOutlined } from "@ant-design/icons"
import api from "../services/api"

const { Option } = Select

const ASSET_TYPE_LABELS = {
  database: "数据库",
  table: "表",
}

export default function ExcludeMarkView() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [filters, setFilters] = useState({ assetType: "" })

  const fetchData = async (page = 1, size = 10) => {
    setLoading(true)
    try {
      const params = { page, size }
      if (filters.assetType) params.asset_type = filters.assetType
      const res = await api.get("/upload/exclude-marks", { params })
      if (res.code === "000000") {
        setData(res.data.list || [])
        setPagination({ current: res.data.page, pageSize: res.data.size, total: res.data.total })
      }
    } catch {
      message.error("加载失败")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const handleRestore = async (record) => {
    try {
      const res = await api.post("/upload/mark-exclude", {
        asset_type: record.assetType,
        asset_id: record.assetId,
        exclude_flag: false,
      })
      if (res.code === "000000") {
        message.success("已恢复上传")
        fetchData()
      }
    } catch {
      message.error("恢复失败")
    }
  }

  const columns = [
    { title: "资产类型", dataIndex: "assetType", width: 80,
      render: (v) => ASSET_TYPE_LABELS[v] || v },
    { title: "资产名称", dataIndex: "assetName", width: 200 },
    { title: "归属系统", dataIndex: "sysName", width: 160 },
    { title: "排除原因", dataIndex: "excludeReason", width: 200, ellipsis: true },
    { title: "操作人", dataIndex: "operator", width: 100 },
    { title: "操作时间", dataIndex: "createTime", width: 160 },
    { title: "操作", key: "action", width: 100,
      render: (_, r) => (
        <Popconfirm title="确认恢复上传？" onConfirm={() => handleRestore(r)}>
          <Button size="small" icon={<UndoOutlined />}>恢复上传</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <div>
      <h2>排除上传标记查询</h2>
      <div style={{ marginBottom: 16, display: "flex", gap: 8 }}>
        <Select placeholder="资产类型" allowClear style={{ width: 140 }}
          onChange={(v) => setFilters({ ...filters, assetType: v || "" })}>
          <Option value="">全部</Option>
          <Option value="database">数据库</Option>
          <Option value="table">表</Option>
        </Select>
        <Button icon={<SearchOutlined />} onClick={() => fetchData(1)}>查询</Button>
        <Button icon={<ReloadOutlined />} onClick={() => fetchData()}>刷新</Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading} size="small"
        pagination={{ ...pagination, showSizeChanger: true, onChange: (p, s) => fetchData(p, s) }}
        scroll={{ x: 1100 }} />
    </div>
  )
}
