import React, { useState, useEffect } from 'react'
import { Tabs, Table, Button, Select, Input, Tag, message, Space } from 'antd'
import { CloudUploadOutlined } from '@ant-design/icons'
import api from '../services/api'

const { TabPane } = Tabs
const { Option } = Select

/** 通用的上报列表组件 */
function UploadTable({ apiPath, uploadPath, columns, filters, rowKey = 'id' }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedRowKeys, setSelectedRowKeys] = useState([])
  const [localFilters, setLocalFilters] = useState({})

  const mergedFilters = { ...localFilters, ...filters }

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await api.get(apiPath, { params: { ...mergedFilters, page: 1, size: 100 } })
      if (res.code === '000000') {
        setData(res.data.list || [])
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [apiPath, JSON.stringify(mergedFilters)])

  const handleUpload = async () => {
    if (!selectedRowKeys.length) {
      message.warning('请选择合规的记录')
      return
    }
    const res = await api.post(uploadPath, selectedRowKeys)
    if (res.code === '000000') {
      message.success(`上传成功: ${res.data?.uploaded || 0} 条`)
      setSelectedRowKeys([])
      fetchData()
    }
  }

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
    getCheckboxProps: (record) => ({
      disabled: record.is_compliant !== '是',
    }),
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <Input
          placeholder="名称关键字"
          allowClear
          style={{ width: 180 }}
          onPressEnter={(e) => setLocalFilters({ ...localFilters, search: e.target.value })}
        />
        <Select
          placeholder="是否合规"
          allowClear style={{ width: 120 }}
          onChange={(v) => setLocalFilters({ ...localFilters, is_compliant: v })}
        >
          <Option value="是">是</Option>
          <Option value="否">否</Option>
        </Select>
        <Button type="primary" icon={<CloudUploadOutlined />} onClick={handleUpload}>上传集团</Button>
      </div>
      <Table
        rowKey={rowKey}
        columns={columns}
        dataSource={data}
        loading={loading}
        rowSelection={rowSelection}
        size="small"
      />
    </div>
  )
}

export default function UploadGroup() {
  const [activeKey, setActiveKey] = useState('dataset')

  // 高质量数据集列
  const datasetColumns = [
    { title: '唯一标识', dataIndex: 'ust_id', ellipsis: true },
    { title: '数据集类型', dataIndex: 'dataset_type' },
    { title: '业务场景', dataIndex: 'biz_scene' },
    { title: '是否合规', dataIndex: 'is_compliant', render: (v) => v === '是' ? <Tag color="green">是</Tag> : <Tag color="red">否</Tag> },
    { title: '不合规原因', dataIndex: 'non_compliant_reason', ellipsis: true },
    { title: '上传状态', dataIndex: 'upload_status', render: (v) => v === '已上传' ? <Tag color="blue">已上传</Tag> : <Tag>待上传</Tag> },
  ]

  // 非结构化列
  const unstructuredColumns = [
    { title: '唯一标识', dataIndex: 'ust_id' },
    { title: '中文名', dataIndex: 'file_name_cn' },
    { title: '英文名', dataIndex: 'file_name_en' },
    { title: '所属系统', dataIndex: 'sys_name' },
    { title: '是否合规', dataIndex: 'is_compliant', render: (v) => v === '是' ? <Tag color="green">是</Tag> : <Tag color="red">否</Tag> },
  ]

  // 标签列
  const labelColumns = [
    { title: '唯一标识', dataIndex: 'label_group_id' },
    { title: '标签名称', dataIndex: 'label_name' },
    { title: '一级分类', dataIndex: 'category_l1' },
    { title: '二级分类', dataIndex: 'category_l2' },
    { title: '业务口径', dataIndex: 'biz_definition', ellipsis: true },
    { title: '是否合规', dataIndex: 'is_compliant', render: (v) => v === '是' ? <Tag color="green">是</Tag> : <Tag color="red">否</Tag> },
  ]

  // 指标列
  const indicatorColumns = [
    { title: '唯一标识', dataIndex: 'indicator_group_id' },
    { title: '指标名称', dataIndex: 'indicator_name' },
    { title: '计量单位', dataIndex: 'unit' },
    { title: '周期', dataIndex: 'period' },
    { title: '是否合规', dataIndex: 'is_compliant', render: (v) => v === '是' ? <Tag color="green">是</Tag> : <Tag color="red">否</Tag> },
  ]

  // API列
  const apiColumns = [
    { title: '唯一标识', dataIndex: 'api_group_id' },
    { title: 'API名称', dataIndex: 'api_name' },
    { title: 'URL', dataIndex: 'api_url', ellipsis: true },
    { title: '请求方式', dataIndex: 'method' },
    { title: '是否合规', dataIndex: 'is_compliant', render: (v) => v === '是' ? <Tag color="green">是</Tag> : <Tag color="red">否</Tag> },
  ]

  // 产品列
  const productColumns = [
    { title: '唯一标识', dataIndex: 'product_group_id' },
    { title: '产品名称', dataIndex: 'product_name' },
    { title: '业务领域', dataIndex: 'biz_domain' },
    { title: '分类', dataIndex: 'category' },
    { title: '是否生效', dataIndex: 'is_effective', render: (v) => v === '是' ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
    { title: '是否合规', dataIndex: 'is_compliant', render: (v) => v === '是' ? <Tag color="green">是</Tag> : <Tag color="red">否</Tag> },
  ]

  return (
    <div>
      <h2>集团上报</h2>
      <Tabs activeKey={activeKey} onChange={setActiveKey}>
        <TabPane tab="高质量数据集上报" key="dataset">
          <UploadTable
            apiPath="/upload/multimodal/dataset"
            uploadPath="/upload/multimodal/dataset/upload"
            columns={datasetColumns}
          />
        </TabPane>
        <TabPane tab="非结构化数据上报" key="unstructured">
          <UploadTable
            apiPath="/upload/multimodal/unstructured"
            uploadPath="/upload/multimodal/unstructured/upload"
            columns={unstructuredColumns}
          />
        </TabPane>
        <TabPane tab="标签上报" key="label">
          <UploadTable
            apiPath="/upload/asset/label"
            uploadPath="/upload/asset/label/upload"
            columns={labelColumns}
          />
        </TabPane>
        <TabPane tab="指标上报" key="indicator">
          <UploadTable
            apiPath="/upload/asset/indicator"
            uploadPath="/upload/asset/indicator/upload"
            columns={indicatorColumns}
          />
        </TabPane>
        <TabPane tab="API上报" key="api">
          <UploadTable
            apiPath="/upload/asset/api"
            uploadPath="/upload/asset/api/upload"
            columns={apiColumns}
          />
        </TabPane>
        <TabPane tab="产品上报" key="product">
          <UploadTable
            apiPath="/upload/asset/product"
            uploadPath="/upload/asset/product/upload"
            columns={productColumns}
          />
        </TabPane>
      </Tabs>
    </div>
  )
}
