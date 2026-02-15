import axios, { AxiosInstance, AxiosResponse } from 'axios';

// 创建 axios 实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse): any => {
    return response.data;
  },
  (error: any) => {
    if (error.response) {
      const { status, data } = error.response;
      
      // 处理 401 未授权
      if (status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      
      // 返回错误信息
      return Promise.reject({
        code: status,
        message: data?.detail || data?.message || '请求失败',
        data: data,
      });
    }
    
    // 网络错误
    return Promise.reject({
      code: -1,
      message: '网络连接失败',
      data: null,
    });
  }
);

export default request;
