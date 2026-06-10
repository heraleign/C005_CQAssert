import React, { useState, useEffect } from 'react'
import { Tree, Card, Button, Modal, Form, Input, InputNumber, Select, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select

export default function CatalogTree() {
  const [treeData, setTreeData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingNode, setEditingNode] = useState(null)
  const [form] = Form.useForm()

  const fetchTree = async () => {
    setLoading(true)
    try {
      const res = await api.get('/catalog/tree')
      if (res.code === '000000') {
        setTreeData(res.data)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTree()
  }, [])

  const handleAdd = (parentNode = null) => {
    setEditingNode(null)
    form.resetFields()
    if (parentNode) {
      form.setFieldsValue({
        parent_id: parentNode.catalog_id,
        catalog_level: (parentNode.catalog_level || 1) + 1,
      })
    } else {
      form.setFieldsValue({ catalog_level: 1 })
    }
    setModalVisible(true)
  }

  const handleEdit = (node) => {
    setEditingNode(node)
    form.setFieldsValue(node)
    setModalVisible(true)
  }

  const handleDelete = async (catalog_id) => {
    await api.post(`/catalog/delete/${catalog_id}`)
    message.success('删除成功')
    fetchTree()
  }

  const handleSubmit = async () => {
    const values = await form.validateFields()
    if (editingNode) {
      await api.post(`/catalog/update/${editingNode.catalog_id}`, values)
      message.success('更新成功')
    } else {
      await api.post('/catalog/create', values)
      message.success('创建成功')
    }
    setModalVisible(false)
    fetchTree()
  }

  const renderTreeNodes = (nodes) =>
    nodes.map((node) => ({
      title: (
        <span>
          {node.catalog_name}
          <span style={{ marginLeft: 8 }}>
            <Button size="small" type="link" icon={<PlusOutlined />} onClick={() => handleAdd(node)}></Button>
            <Button size="small" type="link" icon={<EditOutlined />} onClick={() => handleEdit(node)}></Button>
            <Popconfirm title="确定删除？" onConfirm={() => handleDelete(node.catalog_id)}>
              <Button size="small" type="link" danger icon={<DeleteOutlined />}></Button>
            </Popconfirm>
          </span>
        </span>
      ),
      key: node.catalog_id,
      children: node.children?.length ? renderTreeNodes(node.children) : undefined,
    }))

  return (
    <Card
      title="数据集目录树"
      extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => handleAdd()}>新增根节点</Button>}
    >
      <Tree treeData={renderTreeNodes(treeData)} blockNode defaultExpandAll />

      <Modal
        title={editingNode ? '编辑目录' : '新增目录'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          {!editingNode && (
            <Form.Item name="catalog_id" label="目录ID" rules={[{ required: true }]} >
              <Input placeholder="如：YW-YWWH" />
            </Form.Item>
          )}
          <Form.Item name="catalog_name" label="目录名称" rules={[{ required: true }]} >
            <Input />
          </Form.Item>
          <Form.Item name="parent_id" label="父节点ID" >
            <Input disabled placeholder="自动填充" />
          </Form.Item>
          <Form.Item name="catalog_level" label="层级" rules={[{ required: true }]} >
            <InputNumber min={1} max={4} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="catalog_type" label="目录类型" >
            <Select placeholder="请选择">
              <Option value="领域">领域</Option>
              <Option value="场景">场景</Option>
              <Option value="细类">细类</Option>
            </Select>
          </Form.Item>
          <Form.Item name="sort_order" label="排序" >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
