import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import MainLayout from './components/MainLayout'
import Dashboard from './pages/Dashboard'
import DatasetList from './pages/DatasetList'
import DatasetDetail from './pages/DatasetDetail'
import CatalogTree from './pages/CatalogTree'
import UploadGroup from './pages/UploadGroup'
import ResourceUpload from './pages/ResourceUpload'
import ResourceUploadV2 from './pages/ResourceUploadV2'
import AuditRules from './pages/AuditRules'
import AuditResults from './pages/AuditResults'
import SystemMgmt from './pages/SystemMgmt'
import HandoverLog from './pages/HandoverLog'
import MetaModelConfig from './pages/MetaModelConfig'
import UploadModifyLog from './pages/UploadModifyLog'
import UploadOperationLog from './pages/UploadOperationLog'
import UploadResultView from './pages/UploadResultView'
import ExcludeMarkView from './pages/ExcludeMarkView'
import MergeLogView from './pages/MergeLogView'

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'))

  useEffect(() => {
    const handler = () => setToken(localStorage.getItem('token'))
    window.addEventListener('storage', handler)
    return () => window.removeEventListener('storage', handler)
  }, [])

  if (!token) {
    return (
      <Routes>
        <Route path="/login" element={<Login onLogin={() => setToken(localStorage.getItem('token'))} />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="datasets" element={<DatasetList />} />
        <Route path="datasets/:id" element={<DatasetDetail />} />
        <Route path="catalog" element={<CatalogTree />} />
        <Route path="upload" element={<UploadGroup />} />
        <Route path="upload/resource" element={<ResourceUpload />} />
        <Route path="upload/resource-v2" element={<ResourceUploadV2 />} />
        <Route path="audit/rules" element={<AuditRules />} />
        <Route path="audit/results" element={<AuditResults />} />
        <Route path="system" element={<SystemMgmt />} />
        <Route path="handover" element={<HandoverLog />} />
        <Route path="meta-config" element={<MetaModelConfig />} />
        <Route path="upload/modify-log" element={<UploadModifyLog />} />
        <Route path="upload/upload-log" element={<UploadOperationLog />} />
        <Route path="upload/result-view" element={<UploadResultView />} />
        <Route path="upload/exclude-marks" element={<ExcludeMarkView />} />
        <Route path="upload/merge-logs" element={<MergeLogView />} />
      </Route>
      <Route path="/login" element={<Navigate to="/" />} />
    </Routes>
  )
}

export default App
