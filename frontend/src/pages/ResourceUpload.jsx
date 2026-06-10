import React, { useState, useEffect, useCallback } from 'react'
import { Table, Tabs, Select, Input, Button, Tag, Space, Modal, Form, message, Alert, Descriptions } from 'antd'
import {
  SyncOutlined, SafetyCertificateOutlined, SendOutlined, CloudUploadOutlined,
  HistoryOutlined, EditOutlined, SearchOutlined, WarningOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const { Option } = Select
const { TextArea } = Input

const ASSET_TYPES = ['system', 'database', 'table', 'field']
const TAB_LABELS = { system: '系统', database: '数据库', table: '表', field: '字段' }

export default function ResourceUpload() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('system')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [selectedRowKeys, setSelectedRowKeys] = useState([])

  const [filters, setFilters] = useState({
    sysCode: '', sysName: '', recordName: '', sysStatus: '',
    sysFuncType: '', ifManaged: '', auditStatus: '', uploadStatus: '',
  })

  // Modify modal
  const [modifyVisible, setModifyVisible] = useState(false)
  const [modifyRecord, setModifyRecord] = useState(null)
  const [modifyFields, setModifyFields] = useState({})
  const [modifyReason, setModifyReason] = useState('')

  // Sync warning modal
  const [syncWarnings, setSyncWarnings] = useState([])
  const [syncVisible, setSyncVisible] = useState(false)
  const [pendingSync, setPendingSync] = useState(null)

  // Deadline warning
  const [deadlineDays, setDeadlineDays] = useState(0)

  useEffect(() => {
    const today = dayjs()
    setDeadlineDays(25 - today.date())
  }, [])

  const fetchData = useCallback(async (page = 1, size = 10) => {
    setLoading(true)
    try {
      const params = { asset_type: activeTab, page, size }
      if (filters.sysCode) params.sys_code = filters.sysCode
      if (filters.sysName) params.sys_name = filters.sysName
      if (filters.recordName) params.record_name = filters.recordName
      if (filters.sysStatus) params.sys_status = filters.sysStatus
      if (filters.sysFuncType) params.sys_func_type = filters.sysFuncType
      if (filters.ifManaged) params.if_managed = filters.ifManaged
      if (filters.auditStatus) params.audit_status = filters.auditStatus
      if (filters.uploadStatus) params.upload_status = filters.uploadStatus
      const res = await api.get('/upload/mid-list', { params })
      if (res.code === '000000') {
        setData(res.data.list || [])
        setPagination({ current: res.data.page, pageSize: res.data.size, total: res.data.total })
      }
    } finally {
      setLoading(false)
    }
  }, [activeTab, filters])

  useEffect(() => { fetchData() }, [fetchData])

  // ─── API Actions ──────────────────────────────

  const handleSync = async (scopeType = 'all', scopeIds = null) => {
    try {
      const payload = { asset_type: activeTab, scope_type: scopeType, overwrite_empty: false }
      if (scopeIds) payload.scope_ids = scopeIds
      const res = await api.post('/upload/sync-to-mid', payload)
      if (res.code === '000000') {
        if (res.data.emptyOverwriteWarnings?.length > 0) {
          setSyncWarnings(res.data.emptyOverwriteWarnings)
          setPendingSync(payload)
          setSyncVisible(true)
        } else {
          message.success(`同步完成: ${res.data.syncCount}条`)
          fetchData()
        }
      }
    } catch { message.error('同步失败') }
  }

  const handleSyncConfirm = async (overwrite) => {
    pendingSync.overwrite_empty = overwrite
    const res = await api.post('/upload/sync-to-mid', pendingSync)
    if (res.code === '000000') message.success(`同步完成: ${res.data.syncCount}条`)
    setSyncVisible(false)
    setSyncWarnings([])
    setPendingSync(null)
    fetchData()
  }

  const handleAudit = async (scopeType = 'all', scopeIds = null) => {
    try {
      const payload = { asset_type: activeTab, scope_type: scopeType }
      if (scopeIds) payload.scope_ids = scopeIds
      const res = await api.post('/upload/audit', payload)
      if (res.code === '000000') {
        message.success(`稽核完成: 通过${res.data.passCount}条, 不通过${res.data.failCount}条`)
        fetchData()
      }
    } catch { message.error('稽核失败') }
  }

  const handleSyncToResult = async (scopeType = 'all', scopeIds = null) => {
    try {
      const payload = { asset_type: activeTab, scope_type: scopeType }
      if (scopeIds) payload.scope_ids = scopeIds
      const res = await api.post('/upload/sync-to-result', payload)
      if (res.code === '000000') {
        message.success(`同步到结果表: ${res.data.syncCount}条`)
        fetchData()
      }
    } catch { message.error('同步失败') }
  }

  const handleUpload = async (scopeType = 'all', scopeIds = null) => {
    try {
      const payload = { asset_type: activeTab, scope_type: scopeType }
      if (scopeIds) payload.scope_ids = scopeIds
      const res = await api.post('/upload/upload-to-group', payload)
      if (res.code === '000000') {
        message.success(`上传完成: 成功${res.data.successCount}条`)
        fetchData()
      }
    } catch { message.error('上传失败') }
  }

  // ─── Modify Modal ─────────────────────────────

  const openModify = (record) => {
    setModifyRecord(record)
    const initial = {}
    getEditableFields(activeTab).forEach(f => { initial[f] = record[f] || '' })
    setModifyFields(initial)
    setModifyReason('')
    setModifyVisible(true)
  }

  const handleModifySave = async (reAudit = false) => {
    if (!modifyReason.trim()) { message.warning('请填写修改原因'); return }
    const changed = {}
    Object.entries(modifyFields).forEach(([k, v]) => {
      if (v !== (modifyRecord[k] || '')) changed[k] = v
    })
    if (!Object.keys(changed).length) { message.warning('没有修改'); return }

    await api.put('/upload/mid-modify', {
      asset_type: activeTab,
      local_biz_id: modifyRecord.local_biz_id,
      modify_fields: changed,
      modify_reason: modifyReason,
    })
    message.success('修改成功')
    setModifyVisible(false)
    if (reAudit) await handleAudit('single', [modifyRecord.local_biz_id])
    fetchData()
  }

  // ─── Helpers ──────────────────────────────────

  const getEditableFields = (type) => ({
    system: ['sys_code', 'sys_name', 'record_name', 'org_unit', 'org_dept', 'biz_owner', 'status'],
    database: ['db_name', 'db_type'],
    table: ['table_name_en', 'table_name', 'table_introduct', 'table_domain', 'sample_data'],
    field: ['field_name_en', 'field_name_cn', 'field_type'],
  })[type] || []

  const getRequiredFields = (type) => ({
    system: ['sys_name', 'record_name', 'org_unit', 'org_dept'],
    database: ['db_name', 'db_type'],
    table: ['table_name', 'table_introduct', 'table_domain'],
    field: ['field_name_cn'],
  })[type] || []

  const renderAuditStatus = (v) => {
    const m = { pending: ['default', '待稽核'], pass: ['green', '通过'], fail: ['red', '不通过'] }
    const [color, text] = m[v] || ['default', v]
    return <Tag color={color}>{text}</Tag>
  }

  const renderUploadStatus = (v) => {
    const m = { pending: ['default', '待上传'], synced: ['blue', '已同步'], uploaded: ['green', '已上传'], failed: ['red', '失败'] }
    const [color, text] = m[v] || ['default', v]
    return <Tag color={color}>{text}</Tag>
  }

  const actionButtons = (record) => {
    const as = record.audit_status || 'pending'
    const us = record.upload_status || 'pending'
    const bid = record.local_biz_id
    return (
      <Space size="small" wrap>
        {(as === 'pending' || as === 'fail') && (
          <>
            <Button size="small" icon={<EditOutlined />} onClick={() => openModify(record)}>修改</Button>
            <Button size="small" icon={<SafetyCertificateOutlined />} onClick={() => handleAudit('single', [bid])}>稽核</Button>
          </>
        )}
        {as === 'pass' && us === 'pending' && (
          <Button size="small" icon={<SendOutlined />} onClick={() => handleSyncToResult('single', [bid])}>同步结果表</Button>
        )}
        {us === 'synced' && (
          <Button size="small" type="primary" icon={<CloudUploadOutlined />} onClick={() => handleUpload('single', [bid])}>上传</Button>
        )}
      </Space>
    )
  }

  // ─── Table Columns ────────────────────────────

  const typeColumns = {
    system: [
      { title: '子系统编码', dataIndex: 'sys_code', width: 100 },
      { title: '系统名称', dataIndex: 'sys_name', width: 160 },
      { title: '定级备案名称', dataIndex: 'record_name', width: 140 },
      { title: '状态', dataIndex: 'status', width: 80, render: (v) => <Tag>{v}</Tag> },
      { title: '功能类型', dataIndex: 'sys_func_type', width: 90,
        render: (v) => ({ '1': '纯数据', '2': '纯功能', '3': '数据+功能' })[v] || v },
      { title: '是否盘点', dataIndex: 'if_managed', width: 80,
        render: (v) => v === '1' ? <Tag color="blue">是</Tag> : <Tag>否</Tag> },
    ],
    database: [
      { title: '数据库名', dataIndex: 'db_name', width: 160 },
      { title: '数据库类型', dataIndex: 'db_type', width: 120 },
    ],
    table: [
      { title: '表英文名', dataIndex: 'table_name_en', width: 140 },
      { title: '表中文名', dataIndex: 'table_name', width: 140 },
      { title: '主题域', dataIndex: 'table_domain', width: 100 },
    ],
    field: [
      { title: '字段英文名', dataIndex: 'field_name_en', width: 140 },
      { title: '字段中文名', dataIndex: 'field_name_cn', width: 140 },
      { title: '字段类型', dataIndex: 'field_type', width: 100 },
    ],
  }

  const columns = [
    ...(typeColumns[activeTab] || []),
    { title: '稽核状态', dataIndex: 'audit_status', width: 90, render: renderAuditStatus },
    { title: '不合规原因', dataIndex: 'non_compliant_reason', width: 200, ellipsis: true,
      render: (v) => v ? <span title={v}>{v.length > 20 ? v.slice(0, 20) + '...' : v}</span> : '-' },
    { title: '上传状态', dataIndex: 'upload_status', width: 90, render: renderUploadStatus },
    { title: '操作', key: 'action', width: 260, fixed: 'right', render: (_, r) => actionButtons(r) },
  ]

  // ─── Modify Modal Content ────────────────────

  const renderModifyForm = () => {
    if (!modifyRecord) return null
    const requiredFields = getRequiredFields(activeTab)
    const reasons = modifyRecord.non_compliant_reason || ''
    return (
      <div>
        {reasons && (
          <Alert type="error" showIcon icon={<WarningOutlined />}
            message="不合规原因" description={reasons} style={{ marginBottom: 16 }} />
        )}
        <Descriptions bordered column={1} size="small" style={{ marginBottom: 16 }}>
          <Descriptions.Item label="本地标识">{modifyRecord.local_biz_id}</Descriptions.Item>
          <Descriptions.Item label="集团标识">{modifyRecord.group_unique_id || '-'}</Descriptions.Item>
        </Descriptions>
        <Form layout="vertical">
          {getEditableFields(activeTab).map(f => (
            <Form.Item key={f} label={f}
              validateStatus={requiredFields.includes(f) && !modifyFields[f] ? 'error' : undefined}
              help={requiredFields.includes(f) && !modifyFields[f] ? '必填字段不能为空' : undefined}
            >
              <TextArea rows={f === 'sample_data' ? 4 : 1}
                value={modifyFields[f] || ''}
                onChange={(e) => setModifyFields({ ...modifyFields, [f]: e.target.value })} />
            </Form.Item>
          ))}
          <Form.Item label="修改原因（必填）">
            <TextArea rows={2} value={modifyReason} onChange={(e) => setModifyReason(e.target.value)} />
          </Form.Item>
        </Form>
      </div>
    )
  }

  return (
    <div>
      <h2>资源类集团上报</h2>

      {deadlineDays >= 0 && deadlineDays <= 5 && (
        <Alert
          type={deadlineDays <= 3 ? 'error' : 'warning'} showIcon banner
          message={`距本月集团上报截止日期（25日）还有 ${deadlineDays} 天`}
          description="请及时完成盘点范围内的库表上传。"
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Filters */}
      <div style={{ marginBottom: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <Input placeholder="子系统编码" style={{ width: 120 }}
          value={filters.sysCode} onChange={(e) => setFilters({ ...filters, sysCode: e.target.value })} allowClear />
        <Input placeholder="系统名称" style={{ width: 130 }}
          value={filters.sysName} onChange={(e) => setFilters({ ...filters, sysName: e.target.value })} allowClear />
        <Input placeholder="定级备案名称" style={{ width: 130 }}
          value={filters.recordName} onChange={(e) => setFilters({ ...filters, recordName: e.target.value })} allowClear />
        <Select placeholder="系统状态" allowClear style={{ width: 110 }}
          value={undefined} onChange={(v) => setFilters({ ...filters, sysStatus: v || '' })}>
          <Option value="">全部</Option>
          <Option value="建设中">建设中</Option>
          <Option value="在用">在用</Option>
          <Option value="已下线">已下线</Option>
        </Select>
        <Select placeholder="功能类型" allowClear style={{ width: 110 }}
          value={undefined} onChange={(v) => setFilters({ ...filters, sysFuncType: v || '' })}>
          <Option value="">全部</Option>
          <Option value="1">纯数据</Option>
          <Option value="2">纯功能</Option>
          <Option value="3">数据+功能</Option>
        </Select>
        <Select placeholder="是否盘点" allowClear style={{ width: 100 }}
          value={undefined} onChange={(v) => setFilters({ ...filters, ifManaged: v || '' })}>
          <Option value="">全部</Option>
          <Option value="1">是</Option>
          <Option value="0">否</Option>
        </Select>
        <Select placeholder="稽核状态" allowClear style={{ width: 110 }}
          value={undefined} onChange={(v) => setFilters({ ...filters, auditStatus: v || '' })}>
          <Option value="">全部</Option>
          <Option value="pass">通过</Option>
          <Option value="fail">不通过</Option>
          <Option value="pending">待稽核</Option>
        </Select>
        <Select placeholder="上传状态" allowClear style={{ width: 110 }}
          value={undefined} onChange={(v) => setFilters({ ...filters, uploadStatus: v || '' })}>
          <Option value="">全部</Option>
          <Option value="pending">待上传</Option>
          <Option value="synced">已同步</Option>
          <Option value="uploaded">已上传</Option>
        </Select>
        <Button icon={<SearchOutlined />} onClick={() => fetchData(1)}>查询</Button>
      </div>

      {/* Actions */}
      <div style={{ marginBottom: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <Button icon={<SyncOutlined />} onClick={() => handleSync()}>同步到中间表</Button>
        <Button icon={<SafetyCertificateOutlined />} onClick={() => handleAudit()}>触发稽核</Button>
        <Button icon={<SendOutlined />} onClick={() => handleSyncToResult()}>同步到结果表</Button>
        <Button type="primary" icon={<CloudUploadOutlined />} onClick={() => handleUpload()}>上传集团</Button>
        <Button icon={<HistoryOutlined />} onClick={() => navigate('/upload/modify-log')}>查看修改记录</Button>
        <Button icon={<HistoryOutlined />} onClick={() => navigate('/upload/upload-log')}>查看上传记录</Button>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab}
        items={ASSET_TYPES.map(t => ({ key: t, label: TAB_LABELS[t] }))} />

      <Table
        rowKey="local_biz_id"
        rowSelection={{ selectedRowKeys, onChange: setSelectedRowKeys }}
        columns={columns} dataSource={data} loading={loading} size="small"
        pagination={{ ...pagination, showSizeChanger: true, onChange: (p, s) => fetchData(p, s) }}
        scroll={{ x: 1200 }}
      />

      {/* Modify Modal */}
      <Modal title={`修改中间表`} open={modifyVisible}
        onCancel={() => setModifyVisible(false)} width={640}
        footer={
          <Space>
            <Button onClick={() => setModifyVisible(false)}>取消</Button>
            <Button onClick={() => handleModifySave(false)}>保存</Button>
            <Button type="primary" onClick={() => handleModifySave(true)}>保存并重新稽核</Button>
          </Space>
        }>
        {renderModifyForm()}
      </Modal>

      {/* Sync Warning Modal */}
      <Modal title={<><WarningOutlined style={{ color: '#faad14' }} /> 发现空值覆盖风险</>}
        open={syncVisible}
        onCancel={() => { setSyncVisible(false); setSyncWarnings([]) }} width={600}
        footer={
          <Space>
            <Button onClick={() => { setSyncVisible(false); setSyncWarnings([]) }}>取消同步</Button>
            <Button onClick={() => handleSyncConfirm(false)}>跳过空值，保留中间表现有值</Button>
            <Button type="primary" danger onClick={() => handleSyncConfirm(true)}>全部覆盖</Button>
          </Space>
        }>
        <p>以下字段在中间表已有值，本次同步源数据为空：</p>
        <Table rowKey={(r) => r.localBizId + r.fieldName}
          dataSource={syncWarnings} size="small" pagination={false}
          columns={[
            { title: '资产标识', dataIndex: 'localBizId' },
            { title: '字段名', dataIndex: 'fieldName' },
            { title: '中间表当前值', dataIndex: 'currentValue' },
            { title: '源数据值', render: () => <Tag color="red">空</Tag> },
          ]} />
      </Modal>
    </div>
  )
}
