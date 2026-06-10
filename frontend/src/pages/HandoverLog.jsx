import React, { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, message } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import api from '../services/api'

export default function HandoverLog() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await api.get('/handover/list', { params: { page: 1, size: 50 } })
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

  const handleSubmit = async () => {
    const values = await form.validateFields()
    await api.post('/handover/create', values)
    message.success('交接记录创建成功')
    setModalVisible(false)
    form.resetFields()
    fetchData()
  }

  const columns = [
    { title: '资产类型', dataIndex: 'asset_type' },
    { title: '资产ID', dataIndex: 'asset_id' },
    { title: '原维护人', dataIndex: 'from_user' },
    { title: '接收人', dataIndex: 'to_user' },
    { title: '操作人', dataIndex: 'operator' },
    { title: '交接时间', dataIndex: 'operate_time' },
    { title: '备注', dataIndex: 'remark' },
  ]

  return (
    <div>
      <h2>资产交接日志</h2>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)} style={{ marginBottom: 16 }}>
        新增交接
      </Button>
      <Table rowKey="log_id" columns={columns} dataSource={data} loading={loading} />

      <Modal
        title="系统元数据交接"
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="asset_id" label="资产唯一标识" rules={[{ required: true }]} >
            <Input placeholder="系统集团唯一标识" />
          </Form.Item>
          <Form.Item name="from_user" label="原维护人" rules={[{ required: true }]} >
            <Input />
          </Form.Item>
          <Form.Item name="to_user" label="接收人" rules={[{ required: true }]} >
            <Input />
          </Form.Item>
          <Form.Item name="operator" label="操作人" rules={[{ required: true }]} >
            <Input />
          </Form.Item>
          <Form.Item name="remark" label="备注" >
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
