import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Table } from 'antd'
import { DatabaseOutlined, SafetyCertificateOutlined, CloudUploadOutlined, FolderOpenOutlined, AppstoreOutlined } from '@ant-design/icons'
import api from '../services/api'

export default function Dashboard() {
  const [stats, setStats] = useState({
    datasetCount: 0,
    catalogCount: 0,
    pendingUpload: 0,
    ruleCount: 0,
    systemCount: 0,
  })

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const [dsRes, catRes, uploadRes, ruleRes, sysRes] = await Promise.all([
        api.post('/dataset/list', { page: 1, size: 1 }).catch(() => ({ data: { total: 0 } })),
        api.get('/catalog/tree').catch(() => ({ data: [] })),
        api.get('/upload/multimodal/dataset', { params: { page: 1, size: 1 } }).catch(() => ({ data: { total: 0 } })),
        api.get('/audit/rules', { params: { page: 1, size: 1 } }).catch(() => ({ data: { total: 0 } })),
        api.get('/system/status/list', { params: { page: 1, size: 1 } }).catch(() => ({ data: { total: 0 } })),
      ])
      setStats({
        datasetCount: dsRes.data?.total || 0,
        catalogCount: catRes.data?.length || 0,
        pendingUpload: uploadRes.data?.total || 0,
        ruleCount: ruleRes.data?.total || 0,
        systemCount: sysRes.data?.total || 0,
      })
    } catch {
      // use defaults on error
    }
  }

  return (
    <div>
      <h2>首页概览</h2>
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={4}>
          <Card><Statistic title="高质量数据集" value={stats.datasetCount} prefix={<DatabaseOutlined />} /></Card>
        </Col>
        <Col span={4}>
          <Card><Statistic title="目录节点" value={stats.catalogCount} prefix={<FolderOpenOutlined />} /></Card>
        </Col>
        <Col span={4}>
          <Card><Statistic title="待上报集团" value={stats.pendingUpload} prefix={<CloudUploadOutlined />} /></Card>
        </Col>
        <Col span={4}>
          <Card><Statistic title="稽核规则" value={stats.ruleCount} prefix={<SafetyCertificateOutlined />} /></Card>
        </Col>
        <Col span={4}>
          <Card><Statistic title="系统数量" value={stats.systemCount} prefix={<AppstoreOutlined />} /></Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card title="功能模块索引">
            <Table
              rowKey="key"
              pagination={false}
              size="small"
              columns={[
                { title: '模块', dataIndex: 'module', width: 120 },
                { title: '功能', dataIndex: 'feature' },
                { title: '入口', dataIndex: 'entry', width: 200 },
              ]}
              dataSource={[
                { key: 1, module: '模块一', feature: '高质量数据集元数据管理（56字段/4组）', entry: '左侧菜单 → 高质量数据集' },
                { key: 2, module: '模块二', feature: '多模态数据集目录（树形结构/多层级）', entry: '左侧菜单 → 数据集目录' },
                { key: 3, module: '模块三/四', feature: '9类资产：资源类+资产类+多模态类上报', entry: '左侧菜单 → 集团上报' },
                { key: 4, module: '模块三', feature: '稽核规则引擎（8+条可配置规则）', entry: '左侧菜单 → 稽核管理 → 稽核规则' },
                { key: 5, module: '模块五', feature: '系统状态管理/主数据编码同步', entry: '左侧菜单 → 系统管理' },
                { key: 6, module: '模块五', feature: '资产交接（原维护人→接收人）', entry: '左侧菜单 → 资产交接' },
                { key: 7, module: '模块六', feature: '数据脱敏/查询频次控制/AI补全能力', entry: '后端API集成' },
                { key: 8, module: '模块六', feature: 'EOP能力开放平台（23接口网关封装）', entry: '后端API集成' },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
