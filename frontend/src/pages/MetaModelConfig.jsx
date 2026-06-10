import React, { useState, useEffect } from 'react'
import {
  Table, Button, Modal, Form, Input, Select, InputNumber, Tag,
  message, Space, Switch, Tabs, Card, Descriptions, Alert, Tooltip,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, QuestionCircleOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select
const { TabPane } = Tabs
const { TextArea } = Input

const GROUP_ORDER = ["基础信息组", "存储信息组", "结构属性信息组", "生命周期组"]
const FIELD_TYPE_OPTIONS = [
  { value: 'VARCHAR', label: '文本' },
  { value: 'TEXT', label: '长文本' },
  { value: 'SELECT', label: '单选' },
  { value: 'MULTI_SELECT', label: '多选' },
  { value: 'BOOLEAN', label: '布尔' },
  { value: 'DATE', label: '日期' },
]
const SOURCE_TYPE_OPTIONS = [
  { value: 'manual', label: '手工录入' },
  { value: 'system', label: '系统回传' },
  { value: 'enum', label: '枚举选择' },
]

function ConditionExprInput({ value, onChange }) {
  const [text, setText] = useState(value ? JSON.stringify(value, null, 2) : '')
  const [error, setError] = useState('')

  useEffect(() => { setText(value ? JSON.stringify(value, null, 2) : '') }, [value])

  const handleBlur = () => {
    if (!text || !text.trim()) {
      onChange(null)
      setError('')
      return
    }
    try {
      const parsed = JSON.parse(text)
      if (!parsed.field || !parsed.eq) {
        setError('需要包含 field 和 eq 字段')
        return
      }
      onChange(parsed)
      setError('')
    } catch {
      setError('JSON 格式错误')
    }
  }

  return (
    <div>
      <TextArea rows={3} value={text} onChange={(e) => setText(e.target.value)}
        onBlur={handleBlur}
        placeholder={'{\n  "field": "dataset_type",\n  "eq": "知识库",\n  "required_fields": ["KB_TYPE", "KB_MODALITY"]\n}'}
      />
      {error && <div style={{ color: 'red', fontSize: 12 }}>{error}</div>}
      <div style={{ color: '#888', fontSize: 12, marginTop: 4 }}>
        格式：{'{ "field": "触发字段", "eq": "触发值", "required_fields": ["字段1","字段2"] }'}
      </div>
    </div>
  )
}

export default function MetaModelConfig() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editing, setEditing] = useState(null)
  const [activeGroup, setActiveGroup] = useState('all')
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewGroups, setPreviewGroups] = useState([])
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const params = activeGroup !== 'all' ? { field_group: activeGroup, size: 100 } : { size: 100 }
      const res = await api.get('/meta-config/fields', { params })
      if (res.code === '000000') setData(res.data.list || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [activeGroup])

  const handleAdd = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ is_required: '否', is_active: '是', source_type: 'manual', field_type: 'VARCHAR', display_width: 2, sort_order: 0 })
    setModalVisible(true)
  }

  const handleEdit = (record) => {
    setEditing(record)
    form.setFieldsValue({
      ...record,
      enum_values: record.enum_values ? (Array.isArray(record.enum_values) ? record.enum_values.join('\n') : '') : '',
      condition_expr: record.condition_expr || null,
    })
    setModalVisible(true)
  }

  const handleDelete = async (fieldId) => {
    await api.post(`/meta-config/fields/delete/${fieldId}`)
    message.success('已禁用')
    fetchData()
  }

  const handleSubmit = async () => {
    const values = await form.validateFields()
    // Convert enum_values from newline-separated to array
    const payload = { ...values }
    if (payload.enum_values && typeof payload.enum_values === 'string') {
      payload.enum_values = payload.enum_values.split('\n').map(s => s.trim()).filter(Boolean)
    } else {
      delete payload.enum_values
    }

    if (editing) {
      await api.post(`/meta-config/fields/update/${editing.field_id}`, payload)
      message.success('更新成功')
    } else {
      await api.post('/meta-config/fields/create', payload)
      message.success('创建成功')
    }
    setModalVisible(false)
    fetchData()
  }

  const handleShowGroups = async () => {
    const res = await api.get('/meta-config/fields/groups')
    if (res.code === '000000') {
      // 从 groups API 获取全量数据，不依赖表格过滤后的 data
      const groupsData = res.data.groups || {}
      const order = res.data.group_order || GROUP_ORDER
      const grouped = order.map(group => ({
        group,
        fields: groupsData[group] || [],
        count: (groupsData[group] || []).length,
      }))
      setPreviewGroups(grouped)
      setPreviewVisible(true)
    }
  }

  const columns = [
    { title: '字段标识', dataIndex: 'field_id', width: 160 },
    { title: '字段中文名', dataIndex: 'field_name', width: 140 },
    { title: '分组', dataIndex: 'field_group', width: 100, render: (v) => <Tag>{v}</Tag> },
    { title: '类型', dataIndex: 'field_type', width: 80 },
    { title: '来源', dataIndex: 'source_type', width: 80 },
    {
      title: '必填', dataIndex: 'is_required', width: 60,
      render: (v) => v === '是' ? <Tag color="red">是</Tag> : <Tag>否</Tag>,
    },
    { title: '排序', dataIndex: 'sort_order', width: 50 },
    {
      title: '启用', dataIndex: 'is_active', width: 60,
      render: (v) => v === '是' ? <Tag color="green">是</Tag> : <Tag color="#999">否</Tag>,
    },
    {
      title: '枚举值', dataIndex: 'enum_values', ellipsis: true,
      render: (v) => v ? v.join(', ') : '-',
    },
    {
      title: '条件必填', dataIndex: 'condition_expr', width: 60,
      render: (v) => v ? <Tag color="orange">有</Tag> : '-',
    },
    {
      title: '操作', width: 160,
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.field_id)}>禁用</Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>元模型配置管理</h2>
        <Space>
          <Button icon={<EyeOutlined />} onClick={handleShowGroups}>预览分组</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>新增字段</Button>
        </Space>
      </div>

      <Alert
        message="元模型采用可配置方式：支持新增/修改字段定义、配置条件必填规则、配置字段展示分组。所有修改即时生效。"
        type="info" showIcon style={{ marginBottom: 16 }}
      />

      <div style={{ marginBottom: 16 }}>
        <Select value={activeGroup} onChange={setActiveGroup} style={{ width: 200 }}>
          <Option value="all">全部分组</Option>
          {GROUP_ORDER.map(g => <Option key={g} value={g}>{g}</Option>)}
        </Select>
        <span style={{ marginLeft: 12, color: '#888' }}>共 {data.length} 个字段配置</span>
      </div>

      <Table
        rowKey="field_id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={false}
        size="small"
        scroll={{ x: 1400 }}
      />

      {/* Edit Modal */}
      <Modal
        title={editing ? '编辑字段配置' : '新增字段配置'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={720}
      >
        <Form form={form} layout="vertical">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 24px' }}>
            {!editing && (
              <Form.Item name="field_id" label="字段标识" rules={[{ required: true }]}>
                <Input placeholder="如：DATASET_NAME" />
              </Form.Item>
            )}
            <Form.Item name="field_name" label="字段中文名" rules={[{ required: true }]}>
              <Input placeholder="如：数据集名称" />
            </Form.Item>
            <Form.Item name="field_group" label="所属分组" rules={[{ required: true }]}>
              <Select>
                {GROUP_ORDER.map(g => <Option key={g} value={g}>{g}</Option>)}
              </Select>
            </Form.Item>
            <Form.Item name="field_type" label="字段类型" rules={[{ required: true }]}>
              <Select>
                {FIELD_TYPE_OPTIONS.map(o => <Option key={o.value} value={o.value}>{o.label}</Option>)}
              </Select>
            </Form.Item>
            <Form.Item name="source_type" label="数据来源">
              <Select>
                {SOURCE_TYPE_OPTIONS.map(o => <Option key={o.value} value={o.value}>{o.label}</Option>)}
              </Select>
            </Form.Item>
            <Form.Item name="is_required" label="是否必填">
              <Select>
                <Option value="是">是</Option>
                <Option value="否">否</Option>
              </Select>
            </Form.Item>
            <Form.Item name="sort_order" label="排序号">
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="display_width" label="展示宽度" tooltip="1=半行，2=整行">
              <Select>
                <Option value={1}>半行</Option>
                <Option value={2}>整行</Option>
              </Select>
            </Form.Item>
            <Form.Item name="default_value" label="默认值">
              <Input />
            </Form.Item>
            <Form.Item name="max_length" label="最大长度">
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </div>
          <Form.Item name="enum_values" label="枚举值（每行一个）" tooltip="SELECT/MULTI_SELECT 类型时填写">
            <TextArea rows={3} placeholder={"原始数据\n知识库\n语料\n提示词"} />
          </Form.Item>
          <Form.Item name="condition_expr" label={
            <span>条件必填规则 <Tooltip title="当指定字段等于某值时，哪些字段变为必填"><QuestionCircleOutlined /></Tooltip></span>
          }>
            <ConditionExprInput />
          </Form.Item>
        </Form>
      </Modal>

      {/* Preview Modal */}
      <Modal
        title="元模型字段分组预览"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={800}
      >
        <Tabs defaultActiveKey="0">
          {previewGroups.map(({ group, fields, count }, idx) => (
            <TabPane tab={`${group} (${count})`} key={String(idx)}>
              <Descriptions bordered column={1} size="small">
                {fields.map(f => (
                  <Descriptions.Item key={f.field_id}
                    label={
                      <span>
                        {f.field_name}
                        {f.is_required === '是' && <span style={{ color: 'red', marginLeft: 4 }}>*</span>}
                        <Tag style={{ marginLeft: 8 }}>{f.field_type}</Tag>
                      </span>
                    }
                  >
                    <div>
                      <span style={{ color: '#888' }}>{f.field_id}</span>
                      {f.enum_values && <div style={{ fontSize: 12, color: '#666' }}>可选：{f.enum_values.join(', ')}</div>}
                      {f.condition_expr && (
                        <div style={{ fontSize: 12, color: 'orange' }}>
                          条件：当 {f.condition_expr.field}={f.condition_expr.eq} 时必填
                        </div>
                      )}
                    </div>
                  </Descriptions.Item>
                ))}
              </Descriptions>
            </TabPane>
          ))}
        </Tabs>
      </Modal>
    </div>
  )
}
