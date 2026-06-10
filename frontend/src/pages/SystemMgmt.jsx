import React, { useState, useEffect } from 'react'
import { Table, Button, Input, Select, Tag, message, Modal, Form } from 'antd'
import { SyncOutlined, SearchOutlined, KeyOutlined, AuditOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select

export default function SystemMgmt() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({})
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [syncModalVisible, setSyncModalVisible] = useState(false)
  const [syncForm] = Form.useForm()
  const [auditModalVisible, setAuditModalVisible] = useState(false)
  const [auditForm] = Form.useForm()

  const fetchData = async (page = 1, size = 10) => {
    setLoading(true)
    try {
      const res = await api.get('/system/status/list', { params: { ...filters, page, size } })
      if (res.code === '000000') {
        setData(res.data.list)
        setPagination({ current: res.data.page, pageSize: res.data.size, total: res.data.total })
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [filters])

  const handleBatchUpdate = async () => {
    const res = await api.post('/system/status/batch-update')
    if (res.code === '000000') {
      message.success(`批量更新完成，共更新 ${res.data.updated} 条`)
      fetchData()
    }
  }

  const handleSyncMasterData = async () => {
    const values = await syncForm.validateFields()
    const res = await api.post('/system/master-data/sync', null, {
      params: { sys_group_id: values.sys_group_id, master_data_code: values.master_data_code }
    })
    if (res.code === '000000') {
      message.success(`主数据编码同步成功: ${res.data.old_code || '无'} -> ${res.data.new_code}`)
      setSyncModalVisible(false)
      syncForm.resetFields()
      fetchData()
    }
  }

  const handleAudit = async () => {
    const values = await auditForm.validateFields()
    const res = await api.post('/audit/execute', {
      asset_type: '系统',
      asset_id: values.sys_group_id || null,
      batch_ids: null,
    })
    if (res.code === '000000') {
      message.success('稽核执行完成')
      setAuditModalVisible(false)
      auditForm.resetFields()
      fetchData()
    }
  }

  const columns = [
    { title: '集团唯一标识', dataIndex: 'sys_group_id', width: 200 },
    { title: '系统编码', dataIndex: 'sys_code', width: 120 },
    { title: '系统名称', dataIndex: 'sys_name', width: 160 },
    { title: '定级备案名称', dataIndex: 'record_name', width: 140 },
    { title: '维护单位', dataIndex: 'org_unit', width: 100 },
    { title: '状态', dataIndex: 'status', width: 80, render: (v) => <Tag>{v}</Tag> },
    { title: '上线时间', dataIndex: 'online_time', width: 100 },
    {
      title: '是否合规', dataIndex: 'is_compliant', width: 90,
      render: (v) => v === '是' ? <Tag color="green">是</Tag> : <Tag color="red">否</Tag>,
    },
    { title: '主数据编码', dataIndex: 'master_data_code', width: 120 },
    { title: '已上传', dataIndex: 'is_uploaded', width: 80, render: (v) => v === '是' ? <Tag color="blue">是</Tag> : <Tag>否</Tag> },
  ]

  return (
    <div>
      <h2>系统状态管理</h2>

      <div style={{ marginBottom: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <Input
          placeholder="系统名称"
          allowClear style={{ width: 160 }}
          onPressEnter={(e) => setFilters({ ...filters, sys_name: e.target.value })}
        />
        <Input
          placeholder="定级备案名称"
          allowClear style={{ width: 160 }}
          onPressEnter={(e) => setFilters({ ...filters, record_name: e.target.value })}
        />
        <Input
          placeholder="维护单位"
          allowClear style={{ width: 140 }}
          onPressEnter={(e) => setFilters({ ...filters, org_unit: e.target.value })}
        />
        <Select placeholder="状态" allowClear style={{ width: 120 }} onChange={(v) => setFilters({ ...filters, status: v })}>
          <Option value="在用">在用</Option>
          <Option value="建设中">建设中</Option>
          <Option value="下线">下线</Option>
        </Select>
        <Select placeholder="是否合规" allowClear style={{ width: 110 }} onChange={(v) => setFilters({ ...filters, is_compliant: v })}>
          <Option value="是">是</Option>
          <Option value="否">否</Option>
        </Select>
        <Select placeholder="已上传" allowClear style={{ width: 110 }} onChange={(v) => setFilters({ ...filters, is_uploaded: v })}>
          <Option value="是">是</Option>
          <Option value="否">否</Option>
        </Select>
        <Button type="primary" icon={<SearchOutlined />} onClick={() => fetchData()}>查询</Button>
      </div>

      <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
        <Button icon={<SyncOutlined />} onClick={handleBatchUpdate}>执行状态批量更新</Button>
        <Button icon={<KeyOutlined />} onClick={() => setSyncModalVisible(true)}>同步主数据编码</Button>
        <Button icon={<AuditOutlined />} onClick={() => setAuditModalVisible(true)}>执行稽核</Button>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{
          ...pagination,
          showSizeChanger: true,
          onChange: (page, size) => fetchData(page, size),
        }}
        scroll={{ x: 1300 }}
        size="small"
      />

      <Modal title="同步集团主数据编码" open={syncModalVisible} onOk={handleSyncMasterData} onCancel={() => setSyncModalVisible(false)}>
        <Form form={syncForm} layout="vertical">
          <Form.Item name="sys_group_id" label="系统集团唯一标识" rules={[{ required: true }]}>
            <Input placeholder="如：JT-KF-HWXJ-SYS-0001" />
          </Form.Item>
          <Form.Item name="master_data_code" label="集团主数据编码" rules={[{ required: true }]}>
            <Input placeholder="由主数据系统分配的编码" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="执行系统稽核" open={auditModalVisible} onOk={handleAudit} onCancel={() => setAuditModalVisible(false)}>
        <Form form={auditForm} layout="vertical">
          <Form.Item name="sys_group_id" label="系统集团唯一标识（可选，留空稽核全部）">
            <Input placeholder="留空则稽核所有系统" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
