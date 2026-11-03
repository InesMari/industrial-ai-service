import { get } from '@/api/request'

/**
 * 传感器接口（对应后端 /api/v1/sensor）。
 * TODO: 待后端确认响应结构后补充泛型类型。
 */
export const sensorApi = {
  /** 查询指定产线温度，line_id 形如 line1 */
  getTemperature: (lineId: string) =>
    get<unknown>('/sensor/temperature', { line_id: lineId }),
}
