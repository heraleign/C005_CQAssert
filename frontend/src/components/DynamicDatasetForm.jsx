import React, { useState, useEffect } from 'react'
import { Form, Input, Select, DatePicker, Radio, Checkbox, Tag, Spin, Card, Row, Col } from 'antd'
import api from '../services/api'

const { TextArea } = Input
const { Option } = Select

/**
 * 动态数据集表单组件
 * 读取 /api/meta-config/fields/groups 的字段配置，动态渲染表单
 */
export default function DynamicDatasetForm({ form, initialValues, onFieldsChange }) {
  const [groups, setGroups] = useState({})
  const [groupOrder, setGroupOrder] = useState([])
  const [loading, setLoading] = useState(true)
  const [formValues, setFormValues] = useState(initialValues || {})

  useEffect(() => {
    fetchFieldConfig()
  }, [])

  // Watch dataset_type changes for conditional required display
  const datasetType = Form.useWatch('dataset_type', form)

  const fetchFieldConfig = async () => {
    setLoading(true)
    try {
      const res = await api.get('/meta-config/fields/groups')
      if (res.code === '000000') {
        setGroups(res.data.groups || {})
        setGroupOrder(res.data.group_order || [])
      }
    } finally {
      setLoading(false)
    }
  }

  const renderField = (field) => {
    const isRequired = field.is_required === '是'
    const isConditional = field.condition_expr && field.condition_expr.field

    // Check if condition is met for conditional required
    let conditionMet = false
    if (isConditional) {
      const triggerValue = formValues[field.condition_expr.field]
      conditionMet = triggerValue === field.condition_expr.eq
    }
    const showRequired = isRequired || conditionMet

    const commonProps = {
      placeholder: `请输入${field.field_name}`,
      disabled: field.source_type === 'system',
    }

    switch (field.field_type) {
      case 'SELECT': {
        const options = field.enum_values || []
        return (
          <Select {...commonProps} allowClear style={{ width: '100%' }}>
            {options.map(opt => <Option key={opt} value={opt}>{opt}</Option>)}
          </Select>
        )
      }
      case 'MULTI_SELECT': {
        const options = field.enum_values || []
        return (
          <Select {...commonProps} mode="multiple" allowClear style={{ width: '100%' }}
            placeholder={`请选择${field.field_name}`}>
            {options.map(opt => <Option key={opt} value={opt}>{opt}</Option>)}
          </Select>
        )
      }
      case 'BOOLEAN':
        return (
          <Radio.Group>
            <Radio value="是">是</Radio>
            <Radio value="否">否</Radio>
          </Radio.Group>
        )
      case 'DATE':
        return <DatePicker style={{ width: '100%' }} picker="date" placeholder={commonProps.placeholder} />
      case 'TEXT':
        return <TextArea rows={3} {...commonProps} />
      default:
        return <Input {...commonProps} maxLength={field.max_length || undefined} />
    }
  }

  const handleValuesChange = (changedValues, allValues) => {
    setFormValues(allValues)
    if (onFieldsChange) onFieldsChange(changedValues, allValues)
  }

  if (loading) return <Spin style={{ display: 'block', margin: '24px auto' }} />

  return (
    <div>
      {groupOrder.map(groupName => {
        const fields = groups[groupName]
        if (!fields || fields.length === 0) return null

        return (
          <Card
            key={groupName}
            title={<span>{groupName} <Tag style={{ marginLeft: 8 }}>{fields.length} 项</Tag></span>}
            style={{ marginBottom: 16 }}
            size="small"
          >
            <Row gutter={24}>
              {fields.map(field => {
                const isSystemField = field.source_type === 'system'
                const hasCondition = field.condition_expr && field.condition_expr.field
                let showField = true
                if (hasCondition && field.condition_expr.required_fields) {
                  // For conditionally required fields, check trigger
                  const triggerValue = formValues[field.condition_expr.field]
                  showField = true // always show but mark required based on condition
                }

                return (
                  <Col key={field.field_id} span={field.display_width === 1 ? 12 : 24}>
                    <Form.Item
                      name={field.field_id}
                      label={
                        <span>
                          {field.field_name}
                          {hasCondition && (
                            <Tag color="orange" style={{ fontSize: 10, marginLeft: 4 }}>
                              当{field.condition_expr.field}={field.condition_expr.eq}时必填
                            </Tag>
                          )}
                          {isSystemField && <Tag style={{ fontSize: 10, marginLeft: 4 }}>系统回传</Tag>}
                        </span>
                      }
                      rules={[
                        { required: field.is_required === '是', message: `请输入${field.field_name}` },
                        {
                          validator: (_, value) => {
                            if (hasCondition) {
                              const triggerValue = formValues[field.condition_expr.field]
                              if (triggerValue === field.condition_expr.eq && (!value || !String(value).trim())) {
                                return Promise.reject(new Error(`当${field.condition_expr.field}=${field.condition_expr.eq}时，${field.field_name}为必填`))
                              }
                            }
                            return Promise.resolve()
                          }
                        }
                      ]}
                    >
                      {renderField(field)}
                    </Form.Item>
                  </Col>
                )
              })}
            </Row>
          </Card>
        )
      })}
    </div>
  )
}
