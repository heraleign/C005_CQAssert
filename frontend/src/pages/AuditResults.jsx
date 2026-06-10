import React, { useState, useEffect } from 'react'
import { Table, Select, Tag, DatePicker } from 'antd'
import dayjs from 'dayjs'
import api from '../services/api'

const { Option } = Select

export default function AuditResults() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [assetType, setAssetType] = useState('')
  const [periodType, setPeriodType] = useState('')
  const [period, setPeriod] = useState('')
  const [isPass, setIsPass] = useState('')

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = { page: 1, size: 50 }
      if (assetType) params.asset_type = assetType
      if (periodType) params.period_type = periodType
      if (period) params.period = period
      if (isPass) params.is_pass = isPass
      const res = await api.get('/audit/results', { params })
      if (res.code === '000000') {
        setData(res.data.list)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [assetType, periodType, period, isPass])

  const onPeriodChange = (date, dateString) => {
    if (!date) {
      setPeriod('')
      return
    }
    if (periodType === '月') {
      setPeriod(dateString)
    } else {
      setPeriod(dateString.replace(/-/g, ''))
    }
  }

  const columns = [
    { title: '资产类型', dataIndex: 'asset_type' },
    { title: '资产ID', dataIndex: 'asset_id' },
    { title: '规则编码', dataIndex: 'rule_code' },
    {
      title: '是否通过',
      dataIndex: 'is_pass',
      render: (v) => v === '是' ? <Tag color="green">通过</Tag> : <Tag color="red">未通过</Tag>,
    },
    { title: '原因', dataIndex: 'reason' },
    { title: '账期类型', dataIndex: 'period_type' },
    { title: '账期', dataIndex: 'period' },
    { title: '检查时间', dataIndex: 'check_time' },
  ]

  return (
    <div>
      <h2>稽核结果</h2>
      <div style={{ marginBottom: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <Select
          placeholder="资产类型"
          allowClear
          style={{ width: 160 }}
          onChange={setAssetType}
          value={assetType || undefined}
        >
          <Option value="系统">系统</Option>
          <Option value="数据库">数据库</Option>
          <Option value="表">表</Option>
          <Option value="字段">字段</Option>
          <Option value="高质量数据集">高质量数据集</Option>
        </Select>
        <Select
          placeholder="账期类型"
          allowClear
          style={{ width: 140 }}
          onChange={(v) => { setPeriodType(v || ''); setPeriod('') }}
          value={periodType || undefined}
        >
          <Option value="日">日</Option>
          <Option value="月">月</Option>
        </Select>
        <DatePicker
          placeholder={periodType === '月' ? '选择月份' : '选择日期'}
          picker={periodType === '月' ? 'month' : 'date'}
          style={{ width: 160 }}
          value={period ? (periodType === '月' ? dayjs(period, 'YYYYMM') : dayjs(period, 'YYYYMMDD')) : null}
          onChange={onPeriodChange}
        />
        <Select
          placeholder="是否通过"
          allowClear
          style={{ width: 130 }}
          onChange={(v) => setIsPass(v || '')}
          value={isPass || undefined}
        >
          <Option value="是">通过</Option>
          <Option value="否">未通过</Option>
        </Select>
      </div>
      <Table rowKey="result_id" columns={columns} dataSource={data} loading={loading} />
    </div>
  )
}
