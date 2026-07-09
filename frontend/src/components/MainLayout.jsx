import React from 'react'
import { Layout, Menu, Button, Space, Typography, Avatar } from 'antd'
import {
  DashboardOutlined,
  DatabaseOutlined,
  FolderOpenOutlined,
  CloudUploadOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  SwapOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const { Header, Sider, Content } = Layout
const { Text } = Typography

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '首页' },
  { key: '/datasets', icon: <DatabaseOutlined />, label: '高质量数据集' },
  { key: '/catalog', icon: <FolderOpenOutlined />, label: '数据集目录' },
  { key: '/upload', icon: <CloudUploadOutlined />, label: '集团上报',
    children: [
      { key: '/upload', label: '资产类/多模态上报' },
      // { key: '/upload/resource', label: '资源类集团上报' },
      { key: '/upload/resource-v2', label: '资源类集团上报（优化）' },
      { key: '/upload/modify-log', label: '修改记录查询' },
      { key: '/upload/upload-log', label: '上传记录查询' },
      // { key: '/upload/result-view', label: '上传结果查看（只读）' },
      { key: '/upload/exclude-marks', label: '排除上传标记' },
      { key: '/upload/merge-logs', label: '合并日志查询' },
    ],
  },
  {
    key: 'audit',
    icon: <SafetyCertificateOutlined />,
    label: '稽核管理',
    children: [
      { key: '/audit/rules', label: '稽核规则' },
      { key: '/audit/results', label: '稽核结果' },
    ],
  },
  { key: '/system', icon: <SettingOutlined />, label: '系统管理' },
  { key: '/handover', icon: <SwapOutlined />, label: '资产交接' },
  { key: '/meta-config', icon: <SettingOutlined />, label: '元模型配置' },
]

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" collapsible>
        <div style={{ height: 48, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', borderBottom: '1px solid #f0f0f0' }}>
          多模态数据管理
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text strong>夯实多模态数据管理能力</Text>
          <Space>
            <Avatar size="small">管</Avatar>
            <Text>管理员</Text>
            <Button type="link" icon={<LogoutOutlined />} onClick={handleLogout}>退出</Button>
          </Space>
        </Header>
        <Content style={{ margin: 16, padding: 16, background: '#fff', borderRadius: 4, overflow: 'auto' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
