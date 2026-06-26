import { ref, onMounted } from 'vue'

export interface WeatherData {
  temp: number        // 当前温度 °C
  condition: string   // 天气状况（晴/多云/雨...）
  tip: string         // 出行提示
  clothing: string    // 穿衣建议
  humidity: number    // 湿度 %
  wind: string        // 风力
  city: string        // 城市名
}

/** 英文城市名 → 中文映射（常见城市） */
const CITY_ZH: Record<string, string> = {
  'Beijing': '北京', 'Shanghai': '上海', 'Guangzhou': '广州', 'Shenzhen': '深圳',
  'Chengdu': '成都', 'Hangzhou': '杭州', 'Wuhan': '武汉', 'Nanjing': '南京',
  'Chongqing': '重庆', 'Tianjin': '天津', 'Xi An': '西安', "Xi'an": '西安',
  'Suzhou': '苏州', 'Zhengzhou': '郑州', 'Changsha': '长沙', 'Dongguan': '东莞',
  'Shenyang': '沈阳', 'Qingdao': '青岛', 'Dalian': '大连', 'Xiamen': '厦门',
  'Kunming': '昆明', 'Hefei': '合肥', 'Fuzhou': '福州', 'Jinan': '济南',
  'Ningbo': '宁波', 'Wenzhou': '温州', 'Harbin': '哈尔滨', 'Nanning': '南宁',
  'Changchun': '长春', 'Guiyang': '贵阳', 'Urumqi': '乌鲁木齐', 'Lhasa': '拉萨',
  'Lanzhou': '兰州', 'Yinchuan': '银川', 'Hohhot': '呼和浩特', 'Haikou': '海口',
  'Sanya': '三亚', 'Zhuhai': '珠海', 'Foshan': '佛山', 'Wuxi': '无锡',
}

/** 根据温度生成穿衣建议 */
function getClothingSuggestion(temp: number): string {
  if (temp >= 35) return '👕 轻薄透气短袖，注意防暑'
  if (temp >= 30) return '👕 短袖短裤，可带件薄外套防空调'
  if (temp >= 25) return '👔 薄衬衫或T恤，舒适为主'
  if (temp >= 20) return '🧥 薄外套或长袖，早晚稍凉'
  if (temp >= 15) return '🧥 夹克或卫衣，注意保暖'
  if (temp >= 10) return '🧣 厚外套或毛衣，谨防感冒'
  if (temp >= 5) return '🧤 棉衣或羽绒服，注意防寒'
  if (temp >= 0) return '🧤 羽绒服+围巾，全副武装'
  return '🧤 厚羽绒服+帽子围巾，减少外出'
}

const WEATHER_TIPS: Record<string, string> = {
  'Sunny': '阳光充足，外出请做好防晒',
  'Clear': '天气晴朗，适合外出活动',
  'Partly cloudy': '多云天气，适合外出',
  'Cloudy': '阴天，外出请携带雨具',
  'Overcast': '阴天，注意保暖',
  'Mist': '有薄雾，出行注意安全',
  'Fog': '有雾，能见度低，请慢行',
  'Light rain': '小雨，出门记得带伞',
  'Moderate rain': '中雨，建议减少外出',
  'Heavy rain': '大雨，非必要不出门',
  'Light snow': '小雪，路面可能湿滑',
  'Moderate snow': '中雪，注意防滑保暖',
  'Heavy snow': '大雪，建议居家',
  'Thunderstorm': '雷雨天气，避免户外活动',
  'Drizzle': '毛毛雨，出门带把伞',
}

function getTip(condition: string, temp: number): string {
  // 优先匹配天气状况
  for (const [key, tip] of Object.entries(WEATHER_TIPS)) {
    if (condition.toLowerCase().includes(key.toLowerCase())) {
      // 高温追加提醒
      if (temp >= 35) return '高温预警！' + tip
      if (temp >= 33) return '天气炎热，' + tip
      return tip
    }
  }
  // 温度兜底提示
  if (temp >= 35) return '高温预警！请减少户外活动，注意防暑'
  if (temp >= 33) return '天气炎热，外出请做好防暑防晒'
  if (temp <= 0) return '气温零下，请注意保暖防寒'
  if (temp <= 5) return '天气寒冷，外出请穿厚外套'
  return '天气不错，适合外出'
}

function mapCondition(desc: string): string {
  const lower = desc.toLowerCase()
  if (lower.includes('sunny') || lower.includes('clear')) return '晴'
  if (lower.includes('partly cloudy')) return '多云'
  if (lower.includes('cloudy') || lower.includes('overcast')) return '阴'
  if (lower.includes('fog') || lower.includes('mist')) return '雾'
  if (lower.includes('thunder')) return '雷阵雨'
  if (lower.includes('heavy rain') || lower.includes('heavy')) return '大雨'
  if (lower.includes('moderate rain')) return '中雨'
  if (lower.includes('light rain') || lower.includes('drizzle')) return '小雨'
  if (lower.includes('snow')) return '雪'
  if (lower.includes('rain')) return '雨'
  return desc || '晴'
}

/** 通过多个 IP 服务获取中文城市名 */
async function getCityByIP(): Promise<string> {
  // 尝试多个服务，按优先级
  const services = [
    { url: 'https://whois.pconline.com.cn/ipJson.jsp?json=true', parse: (d: any) => d.city },
    { url: 'https://ipapi.co/json/', parse: (d: any) => d.city },
  ]
  for (const svc of services) {
    try {
      const resp = await fetch(svc.url, { signal: AbortSignal.timeout(3000) })
      if (!resp.ok) continue
      const data = await resp.json()
      const city = svc.parse(data)
      if (city) return city
    } catch { continue }
  }
  return ''
}

/** 解析 wttr.in JSON 响应 */
function parseWttrResponse(data: any, ipCity?: string): WeatherData {
  const current = data.current_condition?.[0] || {}
  const area = data.nearest_area?.[0]
  const rawCity = area?.areaName?.[0]?.value || ''
  const region = area?.region?.[0]?.value || ''
  // 优先用 IP 获取的中文城市名，其次映射，最后原始名
  const city = ipCity || CITY_ZH[rawCity] || CITY_ZH[region] || rawCity.replace(/_/g, '') || '本地'
  const temp = parseInt(current.temp_C) || 26
  const condition = current.weatherDesc?.[0]?.value || ''
  const humidity = parseInt(current.humidity) || 0
  const wind = current.windspeedKmph ? `${current.windspeedKmph}km/h` : ''

  return {
    temp,
    condition: mapCondition(condition),
    tip: getTip(condition, temp),
    clothing: getClothingSuggestion(temp),
    humidity,
    wind,
    city,
  }
}

export function useWeather() {
  const weather = ref<WeatherData>({
    temp: 26,
    condition: '晴',
    tip: '正在获取天气信息...',
    clothing: '👔 薄衬衫或T恤，舒适为主',
    humidity: 0,
    wind: '',
    city: '',
  })
  const loading = ref(true)

  onMounted(async () => {
    try {
      // 先通过 IP 获取城市名，再查天气
      const city = await getCityByIP()
      // wttr.in 支持中文城市名查询
      const query = city ? encodeURIComponent(city) : ''
      const url = `https://wttr.in/${query}?format=j1&lang=zh`

      const resp = await fetch(url, {
        headers: { 'Accept': 'application/json' },
      })
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      const data = await resp.json()
      weather.value = parseWttrResponse(data, city)
    } catch (e) {
      console.warn('获取天气失败，使用默认值:', e)
      weather.value = {
        temp: 26,
        condition: '晴',
        tip: '今日紫外线中等，外出请做好防晒',
        clothing: '👔 薄衬衫或T恤，舒适为主',
        humidity: 60,
        wind: '微风',
        city: '本地',
      }
    } finally {
      loading.value = false
    }
  })

  return { weather, loading }
}
