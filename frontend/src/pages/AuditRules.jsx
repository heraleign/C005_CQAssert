import React, { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, Select, message, Tag } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select

export default function AuditRules() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await api.get('/audit/rules')
      if (res.code === '000000') {
        setData(res.data.list)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleAdd = () => {
    setEditing(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record) => {
    setEditing(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleSubmit = async () => {
    const values = await form.validateFields()
    if (editing) {
      await api.post(`/audit/rules/update/${editing.rule_id}`, values)
      message.success('更新成功')
    } else {
      await api.post('/audit/rules/create', values)
      message.success('创建成功')
    }
    setModalVisible(false)
    fetchData()
  }

  const columns = [
    { title: '规则编码', dataIndex: 'rule_code' },
    { title: '规则名称', dataIndex: 'rule_name' },
    { title: '规则类型', dataIndex: 'rule_type' },
    { title: '适用对象', dataIndex: 'target_asset' },
    {
      title: '状态',
      dataIndex: 'is_enabled',
      render: (v) => v === '是' ? <Tag color="green">启用</Tag> : <Tag>禁用</Tag>,
    },
    {
      title: '操作',
      render: (_, record) => (
        <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
      ),
    },
  ]

  return (
    <div>
      <h2>稽核规则配置</h2>
      <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd} style={{ marginBottom: 16 }}>
        新增规则
      </Button>
      <Table rowKey="rule_id" columns={columns} dataSource={data} loading={loading} />

      <Modal
        title={editing ? '编辑规则' : '新增规则'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="rule_code" label="规则编码" rules={[{ required: true }]} >
            <Input placeholder="如：MM-001" />
          </Form.Item>
          <Form.Item name="rule_name" label="规则名称" rules={[{ required: true }]} >
            <Input />
          </Form.Item>
          <Form.Item name="rule_type" label="规则类型" rules={[{ required: true }]} >
            <Select>
              <Option value="非空">非空</Option>
              <Option value="格式">格式</Option>
              <Option value="一致性">一致性</Option>
              <Option value="数量">数量</Option>
            </Select>
          </Form.Item>
          <Form.Item name="target_asset" label="适用对象" rules={[{ required: true }]} >
            <Select>
              <Option value="全部">全部</Option>
              <Option value="系统">系统</Option>
              <Option value="数据库">数据库</Option>
              <Option value="表">表</Option>
              <Option value="字段">字段</Option>
              <Option value="高质量数据集">高质量数据集</Option>
            </Select>
          </Form.Item>
          <Form.Item name="rule_desc" label="规则描述" >
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="expression" label="规则表达式" >
            <Input.TextArea rows={3} placeholder="伪代码或逻辑表达式" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
