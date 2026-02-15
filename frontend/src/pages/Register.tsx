import { useState, useEffect } from 'react';
import { Form, Input, Button, Checkbox, Card, Steps, message, Spin, Alert } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getPrimaryCategories, generateSubCategories, register, checkUsername } from '../api/auth';
import type { RegisterRequest, Category } from '../types';

const Register = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [primaryCategories, setPrimaryCategories] = useState<Category[]>([]);
  const [subCategories, setSubCategories] = useState<string[]>([]);
  const [selectedPrimary, setSelectedPrimary] = useState<string[]>([]);
  const [selectedSub, setSelectedSub] = useState<string[]>([]);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  // 加载一级分类
  useEffect(() => {
    const loadPrimaryCategories = async () => {
      try {
        const res = await getPrimaryCategories();
        if (res.code === 200 && res.data) {
          setPrimaryCategories(res.data);
        }
      } catch (error: any) {
        message.error(error.message || '加载分类失败');
      }
    };
    loadPrimaryCategories();
  }, []);

  // 生成二级分类
  const handleGenerateSubCategories = async () => {
    if (selectedPrimary.length === 0) {
      message.warning('请至少选择一个一级分类');
      return;
    }

    setLoading(true);
    try {
      const res = await generateSubCategories(selectedPrimary);
      if (res.code === 200 && res.data) {
        setSubCategories(res.data);
        // 默认全选二级分类
        setSelectedSub(res.data);
        setCurrentStep(2);
      }
    } catch (error: any) {
      message.error(error.message || '生成二级分类失败');
    } finally {
      setLoading(false);
    }
  };

  // 提交注册
  const handleSubmit = async (values: any) => {
    if (selectedPrimary.length === 0) {
      message.warning('请至少选择一个一级分类');
      return;
    }

    setLoading(true);
    try {
      const registerData: RegisterRequest = {
        username: values.username,
        password: values.password,
        email: values.email,
        primary_categories: selectedPrimary,
        sub_categories: selectedSub,
      };

      const res = await register(registerData);
      if (res.code === 200) {
        message.success('注册成功！即将跳转到登录页面...');
        setTimeout(() => {
          navigate('/login');
        }, 1500);
      }
    } catch (error: any) {
      message.error(error.message || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  // 一级分类选择变化
  const handlePrimaryChange = (checkedValues: string[]) => {
    setSelectedPrimary(checkedValues);
  };

  // 二级分类选择变化
  const handleSubChange = (checkedValues: string[]) => {
    setSelectedSub(checkedValues);
  };

  // 下一步
  const nextStep = async () => {
    if (currentStep === 0) {
      try {
        const values = await form.validateFields();
        
        // 检查用户名是否已注册
        const checkRes = await checkUsername(values.username);
        if (checkRes.code === 200 && checkRes.data?.exists) {
          message.error(checkRes.data.message || '用户名已被注册');
          return;
        }
        
        // 用户名可用，进入下一步
        setCurrentStep(1);
      } catch (error: any) {
        // 表单验证失败，不处理
      }
    } else if (currentStep === 1) {
      handleGenerateSubCategories();
    }
  };

  // 上一步
  const prevStep = () => {
    setCurrentStep(currentStep - 1);
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <Card 
        style={{ 
          width: '100%', 
          maxWidth: 800,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 30 }}>
          <h1 style={{ fontSize: 28, fontWeight: 'bold', marginBottom: 8 }}>
            NexusMemo 注册
          </h1>
          <p style={{ color: '#666' }}>智能速记系统，让知识更有序</p>
        </div>

        <Steps 
          current={currentStep} 
          style={{ marginBottom: 40 }}
          items={[
            { title: '基本信息', description: '填写账号信息' },
            { title: '选择分类', description: '选择兴趣分类' },
            { title: '确认注册', description: '完成注册' },
          ]}
        />

        <Spin spinning={loading}>
          {/* 步骤 0: 基本信息 */}
          {currentStep === 0 && (
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
              autoComplete="off"
            >
              <Form.Item
                label="用户名"
                name="username"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, message: '用户名至少3个字符' },
                  { max: 20, message: '用户名最多20个字符' },
                ]}
              >
                <Input 
                  prefix={<UserOutlined />} 
                  placeholder="请输入用户名" 
                  size="large"
                />
              </Form.Item>

              <Form.Item
                label="密码"
                name="password"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 6, message: '密码至少6个字符' },
                ]}
              >
                <Input.Password 
                  prefix={<LockOutlined />} 
                  placeholder="请输入密码" 
                  size="large"
                />
              </Form.Item>

              <Form.Item
                label="确认密码"
                name="confirmPassword"
                dependencies={['password']}
                rules={[
                  { required: true, message: '请确认密码' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('password') === value) {
                        return Promise.resolve();
                      }
                      return Promise.reject(new Error('两次输入的密码不一致'));
                    },
                  }),
                ]}
              >
                <Input.Password 
                  prefix={<LockOutlined />} 
                  placeholder="请再次输入密码" 
                  size="large"
                />
              </Form.Item>

              <Form.Item
                label="邮箱（可选）"
                name="email"
                rules={[
                  { type: 'email', message: '请输入有效的邮箱地址' },
                ]}
              >
                <Input 
                  prefix={<MailOutlined />} 
                  placeholder="请输入邮箱" 
                  size="large"
                />
              </Form.Item>

              <Form.Item>
                <Button type="primary" onClick={nextStep} size="large" block>
                  下一步
                </Button>
              </Form.Item>

              <div style={{ textAlign: 'center' }}>
                已有账号？{' '}
                <a onClick={() => navigate('/login')}>立即登录</a>
              </div>
            </Form>
          )}

          {/* 步骤 1: 选择一级分类 */}
          {currentStep === 1 && (
            <div>
              <Alert
                message="选择您感兴趣的一级分类"
                description="系统将根据您选择的分类生成更具体的二级分类"
                type="info"
                showIcon
                style={{ marginBottom: 20 }}
              />
              
              <Checkbox.Group 
                style={{ width: '100%' }} 
                onChange={handlePrimaryChange}
                value={selectedPrimary}
              >
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
                  {primaryCategories.map((cat) => (
                    <Card 
                      key={cat.name}
                      size="small"
                      hoverable
                      style={{ 
                        cursor: 'pointer',
                        borderColor: selectedPrimary.includes(cat.name) ? '#1890ff' : '#d9d9d9',
                        backgroundColor: selectedPrimary.includes(cat.name) ? '#e6f7ff' : '#fff'
                      }}
                      onClick={() => {
                        const newSelected = selectedPrimary.includes(cat.name)
                          ? selectedPrimary.filter(c => c !== cat.name)
                          : [...selectedPrimary, cat.name];
                        handlePrimaryChange(newSelected);
                      }}
                    >
                      <Checkbox value={cat.name} style={{ width: '100%' }}>
                        {cat.name}
                      </Checkbox>
                    </Card>
                  ))}
                </div>
              </Checkbox.Group>

              <div style={{ marginTop: 30, display: 'flex', justifyContent: 'space-between' }}>
                <Button onClick={prevStep} size="large">
                  上一步
                </Button>
                <Button 
                  type="primary" 
                  onClick={nextStep} 
                  size="large"
                  disabled={selectedPrimary.length === 0}
                >
                  生成二级分类
                </Button>
              </div>
            </div>
          )}

          {/* 步骤 2: 确认二级分类并注册 */}
          {currentStep === 2 && (
            <div>
              <Alert
                message="确认您的分类偏好"
                description="系统已根据您选择的一级分类生成以下二级分类，您可以取消不需要的分类"
                type="success"
                showIcon
                style={{ marginBottom: 20 }}
              />

              <Checkbox.Group 
                style={{ width: '100%' }} 
                onChange={handleSubChange}
                value={selectedSub}
              >
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '12px' }}>
                  {subCategories.map((cat) => (
                    <Card 
                      key={cat}
                      size="small"
                      style={{ 
                        borderColor: selectedSub.includes(cat) ? '#52c41a' : '#d9d9d9',
                        backgroundColor: selectedSub.includes(cat) ? '#f6ffed' : '#fff'
                      }}
                    >
                      <Checkbox value={cat}>
                        {cat}
                      </Checkbox>
                    </Card>
                  ))}
                </div>
              </Checkbox.Group>

              <div style={{ marginTop: 30, display: 'flex', justifyContent: 'space-between' }}>
                <Button onClick={prevStep} size="large">
                  上一步
                </Button>
                <Button 
                  type="primary" 
                  onClick={() => form.submit()} 
                  size="large"
                  disabled={selectedSub.length === 0}
                  icon={<CheckCircleOutlined />}
                >
                  完成注册
                </Button>
              </div>
            </div>
          )}
        </Spin>
      </Card>
    </div>
  );
};

export default Register;
