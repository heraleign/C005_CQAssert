import React, { useState, useEffect } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { Card, Descriptions, Tabs, Table, Tag, Spin, message, Button, Space } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import api from '../services/api'

export default function DatasetDetail() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const isEdit = searchParams.get('mode') === 'edit'
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [qualities, setQualities] = useState([])

  useEffect(() => {
    if (id && id !== 'new') {
      fetchDetail()
      fetchQualities()
    }
  }, [id])

  const fetchDetail = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/dataset/detail/${id}`)
      if (res.code === '000000') setData(res.data)
    } finally {
      setLoading(false)
    }
  }

  const fetchQualities = async () => {
    const res = await api.get(`/dataset/quality/list/${id}`)
    if (res.code === '000000') setQualities(res.data || [])
  }

  if (loading) return <Spin style={{ display: 'block', margin: '40px auto' }} />

  if (!data && id !== 'new') return <div>未找到数据</div>

  const qualityColumns = [
    { title: '质量维度', dataIndex: 'quality_dim' },
    { title: '得分', dataIndex: 'quality_score' },
    { title: '描述', dataIndex: 'quality_desc' },
  ]

  const items = [
    { key: '1', label: '基础信息', children: data && (
      <Descriptions bordered column={2}>
        <Descriptions.Item label="数据集名称">{data.dataset_name}</Descriptions.Item>
        <Descriptions.Item label="唯一标识">{data.dataset_id}</Descriptions.Item>
        <Descriptions.Item label="数据集类型">{data.dataset_type}</Descriptions.Item>
        <Descriptions.Item label="业务负责人">{data.biz_owner}</Descriptions.Item>
        <Descriptions.Item label="联系电话">{data.biz_owner_phone}</Descriptions.Item>
        <Descriptions.Item label="接口人">{data.contact_name}</Descriptions.Item>
        <Descriptions.Item label="接口人电话">{data.contact_phone}</Descriptions.Item>
        <Descriptions.Item label="所属单位">{data.org_unit}</Descriptions.Item>
        <Descriptions.Item label="所属部门">{data.org_dept}</Descriptions.Item>
        <Descriptions.Item label="业务场景">{data.biz_scene}</Descriptions.Item>
        <Descriptions.Item label="业务子场景">{data.biz_sub_scene}</Descriptions.Item>
        <Descriptions.Item label="应用">{data.application}</Descriptions.Item>
        <Descriptions.Item label="工单号">{data.work_order_no}</Descriptions.Item>
      </Descriptions>
    )},
    { key: '2', label: '质量信息', children: (
      <Table rowKey="quality_id" columns={qualityColumns} dataSource={qualities} pagination={false} />
    )},
    { key: '3', label: '存储信息', children: data && (
      <Descriptions bordered column={2}>
        <Descriptions.Item label="预计大小">{data.expected_size}</Descriptions.Item>
        <Descriptions.Item label="实际大小">{data.actual_size}</Descriptions.Item>
        <Descriptions.Item label="存储位置">{data.storage_location}</Descriptions.Item>
        <Descriptions.Item label="是否入湖"><Tag>{data.is_in_lake}</Tag></Descriptions.Item>
        <Descriptions.Item label="资源池">{data.resource_pool}</Descriptions.Item>
        <Descriptions.Item label="网络类型">{data.network_type}</Descriptions.Item>
        <Descriptions.Item label="主机IP">{data.host_ip}</Descriptions.Item>
      </Descriptions>
    )},
    { key: '4', label: '生命周期', children: data && (
      <Descriptions bordered column={2}>
        <Descriptions.Item label="创建时间">{data.create_time}</Descriptions.Item>
        <Descriptions.Item label="更新时间">{data.update_time}</Descriptions.Item>
        <Descriptions.Item label="版本">{data.version}</Descriptions.Item>
        <Descriptions.Item label="状态">{data.status}</Descriptions.Item>
        <Descriptions.Item label="建设单位">{data.build_unit}</Descriptions.Item>
        <Descriptions.Item label="建设目标">{data.build_target}</Descriptions.Item>
        <Descriptions.Item label="建设计划">{data.build_plan}</Descriptions.Item>
        <Descriptions.Item label="预计上线">{data.scene_online_time}</Descriptions.Item>
      </Descriptions>
    )},
  ]

  return (
    <Card
      title={
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/datasets')} type="text" />
          <span>数据集详情{isEdit ? '（编辑模式）' : ''}</span>
        </Space>
      }
    >
      <Tabs items={items} />
    </Card>
  )
}
