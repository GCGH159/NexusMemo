import request from '../utils/request';
import type { RegisterRequest, LoginRequest, ApiResponse, User, Category } from '../types';

// 获取一级分类
export const getPrimaryCategories = async (): Promise<ApiResponse<Category[]>> => {
  const res: any = await request.get('/api/v1/auth/categories/primary');
  if (res.code === 200 && res.categories) {
    // 将字符串数组转换为Category对象数组
    return {
      code: res.code,
      message: res.message,
      data: res.categories.map((name: string) => ({ name, level: 1 }))
    };
  }
  return res as ApiResponse<Category[]>;
};

// 生成二级分类
export const generateSubCategories = async (primaryCategories: string[]): Promise<ApiResponse<string[]>> => {
  const res: any = await request.post('/api/v1/auth/categories/generate-sub', {
    primary_categories: primaryCategories,
  });
  if (res.code === 200 && res.categories) {
    return {
      code: res.code,
      message: res.message,
      data: res.categories
    };
  }
  return res as ApiResponse<string[]>;
};

// 用户注册
export const register = (data: RegisterRequest): Promise<ApiResponse<User>> => {
  return request.post('/api/v1/auth/register', data);
};

// 用户登录
export const login = (data: LoginRequest): Promise<ApiResponse<{ token: string; user: User }>> => {
  return request.post('/api/v1/auth/login', data);
};

// 用户注销
export const logout = (token: string): Promise<ApiResponse<void>> => {
  return request.post('/api/v1/auth/logout', { token });
};

// 获取当前用户信息
export const getCurrentUser = (): Promise<ApiResponse<User>> => {
  return request.get('/api/v1/auth/me');
};

// 检查用户名是否已存在
export const checkUsername = (username: string): Promise<ApiResponse<{ exists: boolean; message: string }>> => {
  return request.get('/api/v1/auth/check-username', { params: { username } });
};
