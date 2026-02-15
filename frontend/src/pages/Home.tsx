import { useEffect, useState } from 'react';
import { Layout, Button, message, Spin, Menu } from 'antd';
import { LogoutOutlined, FileTextOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser } from '../api/auth';
import type { User } from '../types';

const { Header, Content, Sider } = Layout;

const Home = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedKey, setSelectedKey] = useState<string>('all');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const res = await getCurrentUser();
        if (res.code === 200 && res.data) {
          setUser(res.data);
        }
      } catch (error: any) {
        message.error(error.message || '获取用户信息失败');
      } finally {
        setLoading(false);
      }
    };

    fetchUserInfo();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    message.success('已退出登录');
    navigate('/login');
  };

  if (loading) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center' 
      }}>
        <Spin size="large" />
      </div>
    );
  }

  // 构建菜单项
  const menuItems = [
    {
      key: 'all',
      icon: <FileTextOutlined />,
      label: '全部',
    },
    ...(user?.preferences?.primary_categories || []).map((category) => ({
      key: category,
      icon: <FileTextOutlined />,
      label: category,
    })),
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={200} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          borderBottom: '1px solid #f0f0f0',
          fontSize: 18,
          fontWeight: 'bold',
          color: '#1890ff'
        }}>
          NexusMemo
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          style={{ height: 'calc(100vh - 64px)', borderRight: 0 }}
          items={menuItems}
          onClick={({ key }) => setSelectedKey(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          background: '#fff',
          padding: '0 24px',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{ fontSize: 16, fontWeight: 'bold' }}>
            {selectedKey === 'all' ? '全部速记' : selectedKey}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span>欢迎, {user?.username}</span>
            <Button 
              type="primary" 
              icon={<LogoutOutlined />}
              onClick={handleLogout}
            >
              退出登录
            </Button>
          </div>
        </Header>
        <Content style={{ padding: '24px' }}>
          <div style={{ 
            background: '#fff', 
            padding: '24px', 
            borderRadius: '8px',
            minHeight: 'calc(100vh - 112px)'
          }}>
            <h2>欢迎使用 NexusMemo</h2>
            <p>智能速记系统，让知识更有序</p>
            <p style={{ color: '#666', marginTop: 20 }}>
              功能开发中...
            </p>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default Home;
