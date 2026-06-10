import React, { useState, useEffect } from 'react'
import { Table, Select, Input, Button, Tag } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select

export default function UploadOperationLog() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [filters, setFilters] = useState({ assetType: '', operator: '' })

  const fetchData = async (page = 1, size = 10) => {
    setLoading(true)
    try {
      const params = { page, size }
      if (filters.assetType) params.asset_type = filters.assetType
      if (filters.operator) params.operator = filters.operator
      const res = await api.get('/upload/upload-log', { params })
      if (res.code === '000000') {
        setData(res.data.list || [])
        setPagination({ current: res.data.page, pageSize: res.data.size, total: res.data.total })
      }
    } finally { setLoading(false) }
  }

  useEffect(() => { fetchData() }, [])

  const renderStatus = (v) => {
    const m = { SUCCESS: 'green', FAIL: 'red', PARTIAL: 'orange' }
    return <Tag color={m[v] || 'default'}>{v}</Tag>
  }

  const columns = [
    { title: '批次号', dataIndex: 'batchNo', width: 200 },
    { title: '上传时间', dataIndex: 'uploadTime', width: 160 },
    { title: '操作人', dataIndex: 'operator', width: 100 },
    { title: '资产类型', dataIndex: 'assetType', width: 100 },
    { title: '上传范围', dataIndex: 'scopeDesc', width: 200 },
    { title: '成功条数', dataIndex: 'successCount', width: 90 },
    { title: '失败条数', dataIndex: 'failCount', width: 90 },
    { title: '状态', dataIndex: 'uploadStatus', width: 100, render: renderStatus },
  ]

  return (
    <div>
      <h2>上传记录查询</h2>
      <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
        <Select placeholder="资产类型" allowClear style={{ width: 140 }}
          onChange={(v) => setFilters({ ...filters, assetType: v || '' })}>
          <Option value="system">系统</Option>
          <Option value="database">数据库</Option>
          <Option value="table">表</Option>
          <Option value="field">字段</Option>
        </Select>
        <Input placeholder="操作人" style={{ width: 130 }}
          onChange={(e) => setFilters({ ...filters, operator: e.target.value })} allowClear />
        <Button icon={<SearchOutlined />} onClick={() => fetchData(1)}>查询</Button>
      </div>
      <Table rowKey="batchNo" columns={columns} dataSource={data} loading={loading} size="small"
        pagination={{ ...pagination, showSizeChanger: true, onChange: (p, s) => fetchData(p, s) }}
        scroll={{ x: 1100 }} />
    </div>
  )
}
