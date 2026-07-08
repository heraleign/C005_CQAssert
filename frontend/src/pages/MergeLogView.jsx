import React, { useState, useEffect } from "react"
import { Table, Select, Input, Button, Tag, Space, message, Descriptions, Modal } from "antd"
import { SearchOutlined, ReloadOutlined, ExpandOutlined } from "@ant-design/icons"
import api from "../services/api"

const { Option } = Select

const ASSET_TYPE_LABELS = {
  system: "系统",
  database: "数据库",
  table: "表",
  field: "字段",
}

export default function MergeLogView() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [filters, setFilters] = useState({ assetType: "" })
  const [detailVisible, setDetailVisible] = useState(false)
  const [detailData, setDetailData] = useState(null)

  const fetchData = async (page = 1, size = 10) => {
    setLoading(true)
    try {
      const params = { page, size }
      if (filters.assetType) params.asset_type = filters.assetType
      const res = await api.get("/upload/merge-logs", { params })
      if (res.code === "000000") {
        setData(res.data.list || [])
        setPagination({ current: res.data.page, pageSize: res.data.size, total: res.data.total })
      }
    } catch {
      message.error("加载失败")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const columns = [
    { title: "操作时间", dataIndex: "createTime", width: 160 },
    { title: "操作人", dataIndex: "operator", width: 100 },
    { title: "资产类型", dataIndex: "assetType", width: 80,
      render: (v) => ASSET_TYPE_LABELS[v] || v },
    { title: "合并目标", dataIndex: "targetLocalBizId", width: 180, ellipsis: true },
    { title: "来源记录数", dataIndex: "sourceLocalBizIds", width: 100,
      render: (v) => Array.isArray(v) ? v.length : 0 },
    { title: "合并原因", dataIndex: "mergeReason", width: 200, ellipsis: true },
    { title: "操作", key: "action", width: 80,
      render: (_, r) => (
        <Button size="small" icon={<ExpandOutlined />}
          onClick={() => { setDetailData(r); setDetailVisible(true) }}>
          详情
        </Button>
      ),
    },
  ]

  return (
    <div>
      <h2>合并日志查询</h2>
      <div style={{ marginBottom: 16, display: "flex", gap: 8 }}>
        <Select placeholder="资产类型" allowClear style={{ width: 140 }}
          onChange={(v) => setFilters({ ...filters, assetType: v || "" })}>
          <Option value="">全部</Option>
          {Object.entries(ASSET_TYPE_LABELS).map(([k, v]) => (
            <Option key={k} value={k}>{v}</Option>
          ))}
        </Select>
        <Button icon={<SearchOutlined />} onClick={() => fetchData(1)}>查询</Button>
        <Button icon={<ReloadOutlined />} onClick={() => fetchData()}>刷新</Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading} size="small"
        pagination={{ ...pagination, showSizeChanger: true, onChange: (p, s) => fetchData(p, s) }}
        scroll={{ x: 1100 }} />

      <Modal title="合并详情" open={detailVisible}
        onCancel={() => setDetailVisible(false)} footer={null} width={640}>
        {detailData && (
          <div>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="资产类型">{ASSET_TYPE_LABELS[detailData.assetType] || detailData.assetType}</Descriptions.Item>
              <Descriptions.Item label="合并原因">{detailData.mergeReason}</Descriptions.Item>
              <Descriptions.Item label="操作人">{detailData.operator}</Descriptions.Item>
              <Descriptions.Item label="操作时间">{detailData.createTime}</Descriptions.Item>
            </Descriptions>

            {/* 解析 mergeDetail */}
            {detailData.mergeDetail && detailData.mergeDetail.primary ? (() => {
              const md = detailData.mergeDetail
              return (
                <div style={{ marginTop: 16 }}>
                  <h4 style={{ color: "#1890ff", marginBottom: 8 }}>系统合并详情</h4>
                  <Descriptions bordered column={1} size="small">
                    <Descriptions.Item label={<span style={{ color: "#1890ff", fontWeight: "bold" }}>✅ 主系统</span>}>
                      <Tag color="blue" style={{ fontWeight: "bold" }}>{md.primary.name || md.primary.id}</Tag>
                      {md.primary.code ? `（${md.primary.code}）` : ""}
                      <span style={{ color: "#999", marginLeft: 8 }}>ID: {md.primary.id}</span>
                    </Descriptions.Item>
                    {md.secondary && md.secondary.length > 0 && (
                      <Descriptions.Item label={<span style={{ color: "#fa8c16", fontWeight: "bold" }}>📌 副系统（{md.secondary.length}个）</span>}>
                        {md.secondary.map((s, idx) => (
                          <div key={s.id} style={{ marginBottom: idx < md.secondary.length - 1 ? 6 : 0 }}>
                            <Tag color="orange">{s.name || s.id}</Tag>
                            {s.code ? `（${s.code}）` : ""}
                            <span style={{ color: "#999", marginLeft: 8 }}>ID: {s.id}</span>
                          </div>
                        ))}
                      </Descriptions.Item>
                    )}
                  </Descriptions>
                </div>
              )
            })() : (
              <div style={{ marginTop: 16 }}>
                <Descriptions bordered column={1} size="small">
                  <Descriptions.Item label="合并目标标识">{detailData.targetLocalBizId}</Descriptions.Item>
                  <Descriptions.Item label="来源记录标识">
                    {Array.isArray(detailData.sourceLocalBizIds) ? detailData.sourceLocalBizIds.join(", ") : "-"}
                  </Descriptions.Item>
                </Descriptions>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
