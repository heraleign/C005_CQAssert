import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Button, Input, Select, Form, Space, Tag, message, Popconfirm } from 'antd'
import { SearchOutlined, PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select

export default function DatasetList() {
  const navigate = useNavigate()
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [form] = Form.useForm()

  const fetchData = async (page = 1, size = 10) => {
    setLoading(true)
    try {
      const values = form.getFieldsValue()
      const res = await api.post('/dataset/list', { ...values, page, size })
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
  }, [])

  const handleDelete = async (id) => {
    await api.post(`/dataset/delete/${id}`)
    message.success('删除成功')
    fetchData(pagination.current, pagination.pageSize)
  }

  const columns = [
    { title: '数据集名称', dataIndex: 'dataset_name', width: 200 },
    { title: '唯一标识', dataIndex: 'dataset_id', width: 220 },
    { title: '类型', dataIndex: 'dataset_type', width: 100 },
    { title: '所属单位', dataIndex: 'org_unit', width: 120 },
    { title: '业务场景', dataIndex: 'biz_scene', width: 140 },
    { title: '更新频率', dataIndex: 'update_freq', width: 100 },
    { title: '状态', dataIndex: 'status', width: 80, render: (v) => <Tag>{v}</Tag> },
    {
      title: '是否合规',
      dataIndex: 'is_compliant',
      width: 90,
      render: (v) => v === '是' ? <Tag color="green">是</Tag> : <Tag color="red">否</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/datasets/${record.dataset_id}`)}>详情</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => navigate(`/datasets/${record.dataset_id}?mode=edit`)}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.dataset_id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h2>高质量数据集管理</h2>
      <Form form={form} layout="inline" style={{ marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
        <Form.Item name="dataset_name">
          <Input placeholder="数据集名称" allowClear />
        </Form.Item>
        <Form.Item name="dataset_type">
          <Select placeholder="数据集类型" allowClear style={{ width: 140 }}>
            <Option value="原始数据">原始数据</Option>
            <Option value="知识库">知识库</Option>
            <Option value="语料">语料</Option>
            <Option value="提示词">提示词</Option>
          </Select>
        </Form.Item>
        <Form.Item name="org_unit">
          <Input placeholder="所属单位" allowClear style={{ width: 120 }} />
        </Form.Item>
        <Form.Item name="biz_scene">
          <Input placeholder="业务场景" allowClear style={{ width: 120 }} />
        </Form.Item>
        <Form.Item name="biz_sub_scene">
          <Input placeholder="子场景" allowClear style={{ width: 100 }} />
        </Form.Item>
        <Form.Item name="is_in_lake">
          <Select placeholder="是否入湖" allowClear style={{ width: 110 }}>
            <Option value="是">是</Option>
            <Option value="否">否</Option>
          </Select>
        </Form.Item>
        <Form.Item name="status">
          <Select placeholder="状态" allowClear style={{ width: 110 }}>
            <Option value="在用">在用</Option>
            <Option value="入湖">入湖</Option>
            <Option value="回流">回流</Option>
            <Option value="共享">共享</Option>
            <Option value="下线">下线</Option>
          </Select>
        </Form.Item>
        <Form.Item name="is_compliant">
          <Select placeholder="是否合规" allowClear style={{ width: 110 }}>
            <Option value="是">是</Option>
            <Option value="否">否</Option>
          </Select>
        </Form.Item>
        <Button type="primary" icon={<SearchOutlined />} onClick={() => fetchData(1, pagination.pageSize)}>查询</Button>
      </Form>

      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/datasets/new')}>新增数据集</Button>
      </div>

      <Table
        rowKey="dataset_id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{
          ...pagination,
          showSizeChanger: true,
          onChange: (page, size) => fetchData(page, size),
        }}
        scroll={{ x: 1400 }}
      />
    </div>
  )
}
