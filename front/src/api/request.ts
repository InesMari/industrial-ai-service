import axios, { type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

import type { ApiRes } from '@/types/api'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15000,
})

// 请求拦截器
request.interceptors.request.use((config) => {
  // TODO: 后端接入鉴权后在此注入 Authorization 头
  return config
})

// 响应拦截器：统一解包 APIResponse
request.interceptors.response.use(
  (response): AxiosResponse => {
    const res = response.data as ApiRes
    if (res !== null && typeof res === 'object' && 'code' in res) {
      if (res.code === 0) {
        // 成功：直接把 data 写回，调用方拿到的就是业务数据
        response.data = res.data
        return response
      }
      const errMsg = res.msg ?? res.message ?? '请求失败'
      console.error('[api] 业务错误:', res.code, errMsg)
      ElMessage.error(errMsg)
      return Promise.reject(new Error(errMsg)) as unknown as AxiosResponse
    }
    // 非 APIResponse 结构（如 /health）原样返回
    return response
  },
  (error) => {
    const data = error.response?.data as ApiRes | undefined
    const errMsg = data?.message ?? data?.msg ?? error.message ?? '网络异常，请稍后重试'
    console.error('[api] 请求异常:', error.config?.url, errMsg)
    ElMessage.error(errMsg)
    return Promise.reject(error)
  },
)

/** GET 请求，返回解包后的业务数据；config 可透传 timeout 等 */
export async function get<T>(url: string, params?: object, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await request.get<T>(url, { params, ...config })
  return data
}

/** POST 请求，返回解包后的业务数据；config 可透传 timeout 等 */
export async function post<T>(
  url: string,
  body?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const { data } = await request.post<T>(url, body, config)
  return data
}

export default request
