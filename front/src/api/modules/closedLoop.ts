import { get } from '@/api/request'

/**
 * 闭环接口（对应后端 /api/v1/closed-loop）。
 * TODO: 待后端确认响应结构后补充泛型类型。
 */
export const closedLoopApi = {
  /** 获取闭环最新状态 */
  getStatus: () => get<unknown>('/closed-loop/status'),

  /** 获取最近 N 条判定记录 */
  getHistory: (limit = 20) => get<unknown[]>('/closed-loop/history', { limit }),
}
