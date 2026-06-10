import React, { useState, useEffect } from 'react'
import { Table, Select, Input, Button, Space, Tag } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select

export default function UploadModifyLog() {
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
      const res = await api.get('/upload/modify-log', { params })
      if (res.code === '000000') {
        setData(res.data.list || [])
        setPagination({ current: res.data.page, pageSize: res.data.size, total: res.data.total })
      }
    } finally { setLoading(false) }
  }

  useEffect(() => { fetchData() }, [])

  const columns = [
    { title: '操作时间', dataIndex: 'modifyTime', width: 160 },
    { title: '操作人', dataIndex: 'operator', width: 100 },
    { title: '资产类型', dataIndex: 'assetType', width: 100 },
    { title: '记录标识', dataIndex: 'localBizId', width: 200 },
    { title: '字段名', dataIndex: 'fieldName', width: 120 },
    { title: '修改前值', dataIndex: 'oldValue', width: 200, ellipsis: true },
    { title: '修改后值', dataIndex: 'newValue', width: 200, ellipsis: true },
    { title: '修改原因', dataIndex: 'modifyReason', width: 200, ellipsis: true },
  ]

  return (
    <div>
      <h2>修改记录查询</h2>
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
      <Table rowKey="logId" columns={columns} dataSource={data} loading={loading} size="small"
        pagination={{ ...pagination, showSizeChanger: true, onChange: (p, s) => fetchData(p, s) }}
        scroll={{ x: 1400 }} />
    </div>
  )
}
