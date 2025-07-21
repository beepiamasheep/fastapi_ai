<!--
 * @Author: 熊泽仁
 * 2025-07-03
 * 更新记录:
    完成minio数据列表拉取，文件下载功能
-->
<template>
  <div class="header">Media Files</div>
  <a-spin :spinning="loading" :delay="1000" tip="downloading" size="large">
    <div class="media-panel-wrapper">
      <a-table class="media-table" :columns="columns" :data-source="mediaData.data" row-key="fingerprint"
        :pagination="paginationProp" :scroll="{ x: '100%', y: 600 }" @change="refreshData"
        >
        <template v-for="col in ['name', 'path']" #[col]="{ text }" :key="col">
          <a-tooltip :title="text">
              <a v-if="col === 'name'">{{ text }}</a>
              <span v-else>{{ text }}</span>
          </a-tooltip>
        </template>
        <template #original="{ text }">
          {{ text }}
        </template>
        <template #action="{ record }">
          <a-tooltip title="download">
            <a class="fz18" @click="handleDownload(record)"><DownloadOutlined /></a>
          </a-tooltip>
        </template>
      </a-table>
    </div>
  </a-spin>
</template>

<script setup lang="ts">
import { ref } from '@vue/reactivity'
import { TableState } from 'ant-design-vue/lib/table/interface'
import { onMounted, reactive } from 'vue'
import { IPage } from '../api/http/type'
import { ELocalStorageKey } from '../types/enums'
import { downloadFile } from '../utils/common'
import { downloadMediaFile, getMediaFiles } from '/@/api/media'
import { DownloadOutlined } from '@ant-design/icons-vue'
import { message, Pagination } from 'ant-design-vue'
import { load } from '@amap/amap-jsapi-loader'
import { CURRENT_CONFIG } from '/@/api/http/config'

const workspaceId = localStorage.getItem(ELocalStorageKey.WorkspaceId)!
const loading = ref(false)

const columns = [
  {
    title: 'File Name',
    dataIndex: 'file_name',
    ellipsis: true,
    slots: { customRender: 'name' }
  },
  {
    title: 'File Path',
    dataIndex: 'file_path',
    ellipsis: true,
    slots: { customRender: 'path' }
  },
  // {
  //   title: 'FileSize',
  //   dataIndex: 'size',
  // },
  {
    title: 'Drone',
    dataIndex: 'drone'
  },
  {
    title: 'Payload Type',
    dataIndex: 'payload'
  },
  {
    title: 'Original',
    dataIndex: 'is_original',
    slots: { customRender: 'original' }
  },
  {
    title: 'Created',
    dataIndex: 'create_time'
  },
  {
    title: 'Action',
    slots: { customRender: 'action' }
  }
]
const body: IPage = {
  page: 1,
  total: 0,
  page_size: 50
}
const paginationProp = reactive({
  pageSizeOptions: ['20', '50', '100'],
  showQuickJumper: true,
  showSizeChanger: true,
  pageSize: 50,
  current: 1,
  total: 0
})

type Pagination = TableState['pagination']

interface MediaFile {
  fingerprint: string,
  drone: string,
  payload: string,
  is_original: string,
  file_name: string,
  file_path: string,
  create_time: string,
  file_id: string,
}

const mediaData = reactive({
  data: [] as MediaFile[]
})

// 定义props
const props = defineProps({
  record: {
    type: Object,
    required: true
  }
})

// 状态管理
const error = ref('')

// 后端API基础URL，可根据环境配置
const apiBaseUrl = 'http://192.168.101.6:8000'

onMounted(() => {
  const ws = new WebSocket(`${CURRENT_CONFIG.aiWebSocketURL || 'ws://192.168.101.6:8000'}/ws/minio`)
  ws.onmessage = (event) => {
    const mockResponse = JSON.parse(event.data)
    mediaData.data = mockResponse.data.list
    paginationProp.total = mockResponse.data.pagination.total
    paginationProp.current = mockResponse.data.pagination.page
    console.info(mediaData.data[0])
    console.log('【调试】getFiles传入参数：')
  }
})

// 文件列表获取
function getFiles () {
  console.log('【调试】getFiles传入参数：')
  console.log('workspaceId:', workspaceId)
  console.log('body:', body)
  getMediaFiles(workspaceId, body).then(res => {
    const mockResponse = {
      code: 0,
      message: 'success',
      data: {
        list: [
          {
            fingerprint: 'mock1',
            drone: 'Test Drone122',
            payload: 'Camera',
            is_original: 'true',
            file_name: 'mock.jpg',
            file_path: '/mock/path',
            create_time: '2025-07-04 12:00:00',
            file_id: '1'
          }
        ],
        pagination: {
          total: 1,
          page: 1,
          page_size: 50
        }
      }
    }
    mediaData.data = mockResponse.data.list
    paginationProp.total = mockResponse.data.pagination.total
    paginationProp.current = mockResponse.data.pagination.page
    console.info(mediaData.data[0])
    console.log('【调试】getFiles传入参数：')
  })
}

// 数据刷新
function refreshData (page: Pagination) {
  body.page = page?.current!
  body.page_size = page?.pageSize!
  getFiles()
}

// 媒体文件下载
function downloadMedia (media: MediaFile) {
  loading.value = true
  downloadMediaFile(workspaceId, media.file_id).then(res => {
    if (!res) {
      return
    }
    const data = new Blob([res])
    downloadFile(data, media.file_name)
  }).finally(() => {
    loading.value = false
  })
}

// 处理下载逻辑
const handleDownload = async (record) => {
  try {
    // 重置状态
    loading.value = true
    error.value = ''

    // 从记录中获取文件信息
    const { file_id: objectName, file_name: fileName } = record

    // 构建API请求URL
    const downloadUrl = `${CURRENT_CONFIG.aiServiceURL}/download/videos/${fileName}`

    // 发送请求
    const response = await fetch(downloadUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`下载失败: ${response.statusText}`)
    }

    // 从响应头获取文件名（如果有）
    const contentDisposition = response.headers.get('content-disposition')
    let downloadFileName = fileName || 'downloaded_file'

    if (contentDisposition) {
      const fileNameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
      if (fileNameMatch && fileNameMatch[1]) {
        downloadFileName = fileNameMatch[1]
      }
    }

    // 处理二进制响应
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)

    // 创建下载链接并触发下载
    const a = document.createElement('a')
    a.href = url
    a.download = downloadFileName
    document.body.appendChild(a)
    a.click()

    // 清理
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    console.log('文件下载成功')
  } catch (err) {
    error.value = err.message || '下载过程中发生错误'
    console.error('文件下载失败:', err)
    // 这里可以添加错误提示组件
  } finally {
    loading.value = false
  }
}

</script>

<style lang="scss" scoped>
.media-panel-wrapper {
  width: 100%;
  padding: 16px;
  .media-table {
    background: #fff;
    margin-top: 10px;
  }
  .action-area {
    color: $primary;
    cursor: pointer;
  }
}
.header {
  width: 100%;
  height: 60px;
  background: #fff;
  padding: 16px;
  font-size: 20px;
  font-weight: bold;
  text-align: start;
  color: #000;
}
</style>
